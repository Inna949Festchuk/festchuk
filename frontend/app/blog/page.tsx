'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, Heart, Clock, Tag } from 'lucide-react';
import Link from 'next/link';

interface Post {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  cover_image: string | null;
  tags: string[];
  published_at: string;
  views_count: number;
  likes_count: number;
  reading_time_minutes: number;
}

export default function BlogPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTag, setActiveTag] = useState<string | null>(null);

  useEffect(() => {
    const url = activeTag
      ? `/api/posts/?tag=${encodeURIComponent(activeTag)}`
      : '/api/posts/';
    fetch(url)
      .then(r => r.json())
      .then(data => {
        setPosts(data.results || data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [activeTag]);

  const allTags = Array.from(
    new Set(posts.flatMap(p => p.tags || []))
  ).sort();

  const handleLike = async (id: number) => {
    try {
      await fetch(`/api/posts/${id}/like/`, { method: 'POST' });
      setPosts(prev =>
        prev.map(p => p.id === id ? { ...p, likes_count: p.likes_count + 1 } : p)
      );
    } catch {}
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-neon-cyan font-mono animate-pulse">Загрузка...</div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-12">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-4xl font-display font-bold mb-4">
          <span className="text-foreground">Технический</span>{' '}
          <span className="text-neon-purple text-glow-purple">блог</span>
        </h1>
        <p className="text-zinc-500 mb-8">
          Статьи о разработке, AI и архитектуре
        </p>

        {/* Tags filter */}
        {allTags.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-8">
            <button
              onClick={() => setActiveTag(null)}
              className={`px-3 py-1.5 text-sm rounded-full border transition-colors ${
                !activeTag
                  ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan'
                  : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'
              }`}
            >
              Все
            </button>
            {allTags.map(tag => (
              <button
                key={tag}
                onClick={() => setActiveTag(tag)}
                className={`px-3 py-1.5 text-sm rounded-full border transition-colors flex items-center gap-1 ${
                  activeTag === tag
                    ? 'bg-neon-cyan/20 border-neon-cyan text-neon-cyan'
                    : 'border-zinc-700 text-zinc-400 hover:border-zinc-500'
                }`}
              >
                <Tag className="w-3 h-3" />
                {tag}
              </button>
            ))}
          </div>
        )}

        {/* Posts list */}
        <div className="space-y-6">
          {posts.map((post, i) => (
            <motion.article
              key={post.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08 }}
              className="glass-card rounded-xl overflow-hidden group"
            >
              <Link href={`/blog/${post.slug}`}>
                <div className="flex flex-col md:flex-row">
                  {/* Cover */}
                  {post.cover_image && (
                    <div className="md:w-64 h-48 md:h-auto overflow-hidden shrink-0">
                      <img
                        src={post.cover_image}
                        alt={post.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                      />
                    </div>
                  )}

                  {/* Content */}
                  <div className="p-6 flex-1">
                    <h2 className="text-xl font-display font-semibold text-foreground mb-2 group-hover:text-neon-cyan transition-colors">
                      {post.title}
                    </h2>
                    <p className="text-sm text-zinc-500 mb-4 line-clamp-3">
                      {post.excerpt}
                    </p>

                    {/* Meta */}
                    <div className="flex flex-wrap items-center gap-4 text-xs text-zinc-600">
                      {post.published_at && (
                        <time dateTime={post.published_at}>
                          {new Date(post.published_at).toLocaleDateString('ru-RU', {
                            year: 'numeric',
                            month: 'long',
                            day: 'numeric',
                          })}
                        </time>
                      )}
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {post.reading_time_minutes} мин
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="w-3 h-3" />
                        {post.views_count}
                      </span>
                      <button
                        onClick={(e) => {
                          e.preventDefault();
                          handleLike(post.id);
                        }}
                        className="flex items-center gap-1 hover:text-neon-cyan transition-colors"
                      >
                        <Heart className="w-3 h-3" />
                        {post.likes_count}
                      </button>
                    </div>

                    {/* Tags */}
                    {post.tags?.length > 0 && (
                      <div className="flex flex-wrap gap-2 mt-4">
                        {post.tags.map(tag => (
                          <button
                            key={tag}
                            onClick={(e) => {
                              e.preventDefault();
                              setActiveTag(tag);
                            }}
                            className="px-2 py-0.5 text-xs rounded bg-neon-purple/10 text-neon-purple border border-neon-purple/20 hover:bg-neon-purple/20 transition-colors"
                          >
                            {tag}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              </Link>
            </motion.article>
          ))}
        </div>

        {posts.length === 0 && (
          <div className="text-center py-20 text-zinc-600">
            Статьи скоро будут опубликованы
          </div>
        )}
      </div>
    </main>
  );
}
