import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useState } from 'react';

interface Article {
  id: number;
  title: string;
  link: string;
  date: string;
  content: string;
  category: string | null;
}

async function fetchArticles(): Promise<Article[]> {
  const res = await fetch('/api/articles');
  const data = await res.json();
  return data.articles;
}

export default function Dashboard() {
  const queryClient = useQueryClient();
  const { data, isLoading } = useQuery(['articles'], fetchArticles);

  const deleteMutation = useMutation(
    async (id: number) => {
      await fetch(`/api/articles/${id}`, { method: 'DELETE' });
    },
    { onSuccess: () => queryClient.invalidateQueries(['articles']) }
  );

  const categoryMutation = useMutation(
    async ({ id, category }: { id: number; category: string }) => {
      await fetch(`/api/articles/${id}/category`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ category }),
      });
    },
    { onSuccess: () => queryClient.invalidateQueries(['articles']) }
  );

  if (isLoading) return <p>Loading...</p>;

  function ArticleRow({ article }: { article: Article }) {
    const [cat, setCat] = useState(article.category || '');
    return (
      <div className="border p-4 rounded shadow flex justify-between items-start">
        <div>
          <h3 className="font-semibold">
            <a href={article.link} target="_blank" rel="noreferrer">
              {article.title}
            </a>
          </h3>
          <p className="text-sm text-gray-500 mb-2">{article.date}</p>
          <input
            className="border rounded px-2 py-1 text-sm"
            value={cat}
            onChange={(e) => setCat(e.target.value)}
            onBlur={() =>
              categoryMutation.mutate({ id: article.id, category: cat })
            }
            placeholder="Category"
          />
        </div>
        <button
          className="text-red-600 hover:underline"
          onClick={() => deleteMutation.mutate(article.id)}
        >
          Delete
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {data?.map((a) => (
        <ArticleRow key={a.id} article={a} />
      ))}
    </div>
  );
}
