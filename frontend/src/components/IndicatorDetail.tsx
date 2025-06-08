interface Props {
  article: {
    title: string;
    content: string;
    link: string;
    date: string;
  } | null;
  onClose: () => void;
}

export default function IndicatorDetail({ article, onClose }: Props) {
  if (!article) return null;
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center" onClick={onClose}>
      <div className="bg-white p-6 rounded shadow max-w-lg" onClick={e => e.stopPropagation()}>
        <h3 className="font-semibold text-lg mb-2">{article.title}</h3>
        <p className="text-sm text-gray-500 mb-4">{article.date}</p>
        <p className="mb-4">{article.content}</p>
        <a href={article.link} className="text-blue-600" target="_blank" rel="noreferrer">Original link</a>
      </div>
    </div>
  );
}
