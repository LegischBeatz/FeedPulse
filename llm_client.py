import json
import logging
import re
import time
from configparser import ConfigParser
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List

import requests
from tenacity import Retrying, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config.ini"

@dataclass
class LLMConfig:
    api_url: str
    model_name: str
    timeout: int = 60
    max_retries: int = 3

    @classmethod
    def load(cls, path: Optional[Path] = None, section: str = "LLM") -> "LLMConfig":
        cfg_path = path or DEFAULT_CONFIG_PATH
        parser = ConfigParser(interpolation=None)
        read = parser.read(cfg_path)
        if not read:
            raise FileNotFoundError(f"Config file not found: {cfg_path}")
        api_url = parser.get(section, "api_url", fallback=None)
        model_name = parser.get(section, "model_name", fallback=None)
        timeout = parser.getint(section, "timeout", fallback=60)
        max_retries = parser.getint(section, "max_retries", fallback=3)
        if not api_url or not model_name:
            raise ValueError(f"Both 'api_url' and 'model_name' must be set in [{section}] of {cfg_path}")
        return cls(api_url=api_url, model_name=model_name, timeout=timeout, max_retries=max_retries)

class LLMClient:
    def __init__(self, config: LLMConfig, session: Optional[requests.Session] = None):
        self.config = config
        self.session = session or requests.Session()

    def __enter__(self) -> "LLMClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def _send_request(self, payload: dict) -> str:
        tokens: List[str] = []
        with self.session.post(
            self.config.api_url,
            json=payload,
            stream=True,
            timeout=self.config.timeout,
        ) as resp:
            resp.raise_for_status()
            for raw in resp.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                try:
                    obj = json.loads(raw)
                    tokens.append(obj.get("response", ""))
                except json.JSONDecodeError:
                    tokens.append(raw)
        return "".join(tokens)

    def _clean_output(self, text: str) -> str:
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def generate(self, prompt: str, temperature: float = 0.1, strip_tags: bool = True) -> str:
        payload = {
            "model": self.config.model_name,
            "prompt": prompt,
            "temperature": temperature,
        }
        retryer = Retrying(
            retry=retry_if_exception_type(requests.RequestException),
            stop=stop_after_attempt(self.config.max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=10),
            reraise=True,
        )

        start = time.perf_counter()
        try:
            for attempt in retryer:
                with attempt:
                    logger.debug("Sending prompt to model: %s", prompt)
                    raw = self._send_request(payload)
                    return self._clean_output(raw) if strip_tags else raw
        finally:
            duration = time.perf_counter() - start
            logger.info("LLM request completed in %.2f seconds", duration)
