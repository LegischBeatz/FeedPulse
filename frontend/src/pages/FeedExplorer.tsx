import { useQuery } from '@tanstack/react-query';

interface Article {
  title: string;
  link: string;
  date: string;
  content: string;
}

async function fetchArticles(): Promise<Article[]> {
  const res = await fetch('/api/articles');
  const data = await res.json();
  return data.articles;
}

export default function FeedExplorer() {
  const { data, isLoading } = useQuery(['articles'], fetchArticles);

  if (isLoading) return <p>Loading...</p>;

  return (
    <div className="space-y-4">
      {data?.map((a) => (
        <div key={a.link} className="border p-4 rounded shadow">
          <h3 className="font-semibold">{a.title}</h3>
          <p className="text-sm text-gray-500">{a.date}</p>
          <p className="mt-2 text-gray-700">{a.content}</p>
          <a href={a.link} className="text-blue-600" target="_blank" rel="noreferrer">Read more</a>
        </div>
      ))}
    </div>
  );
}
