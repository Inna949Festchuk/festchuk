'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, Heart, Clock, Tag, BookOpen, ArrowUpRight } from 'lucide-react';
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
      .then((r) => r.json())
      .then((data) => {
        setPosts(data.results || data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [activeTag]);

  const allTags = Array.from(new Set(posts.flatMap((p) => p.tags || []))).sort();

  const handleLike = async (id: number) => {
    try {
      await fetch(`/api/posts/${id}/like/`, { method: 'POST' });
      setPosts((prev) =>
        prev.map((p) => (p.id === id ? { ...p, likes_count: p.likes_count + 1 } : p)),
      );
    } catch {}
  };

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="cyber-frame">
          <div className="cyber-frame-body px-8 py-5 text-neon-cyan font-mono tracking-[0.2em] animate-pulse">
            ЗАГРУЗКА АРХИВА СТАТЕЙ...
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-12">
      <div className="max-w-5xl mx-auto">
        <div className="mb-10 flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-neon-cyan/20 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 font-mono text-xs tracking-[0.25em] text-neon-magenta mb-2">
              <BookOpen className="w-3.5 h-3.5" />
              <span>KNOWLEDGE MATRIX // LOGS</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-display font-black tracking-wide">
              <span className="text-white">ТЕХНИЧЕСКИЙ</span>{' '}
              <span className="text-neon-purple text-glow-purple">БЛОГ</span>
            </h1>
          </div>
          <p className="text-zinc-300 font-mono text-xs sm:text-sm max-w-sm">
            Практические разборы архитектуры, LLM/RAG-систем, векторных БД и продакшн-инфраструктуры.
          </p>
        </div>

        {/* Tags filter */}
        {allTags.length > 0 && (
          <div className="flex flex-wrap gap-2.5 mb-10">
            <button
              type="button"
              onClick={() => setActiveTag(null)}
              className={`cyber-btn px-4 py-2 text-xs font-bold ${
                !activeTag ? 'btn-primary' : 'btn-ghost'
              }`}
            >
              ВСЕ ЗАПИСИ
            </button>
            {allTags.map((tag) => (
              <button
                key={tag}
                type="button"
                onClick={() => setActiveTag(tag)}
                className={`cyber-btn px-4 py-2 text-xs font-bold ${
                  activeTag === tag ? 'btn-primary' : 'btn-ghost'
                }`}
              >
                <Tag className="w-3 h-3" />
                <span>{tag}</span>
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
              className="cyber-frame group"
            >
              <div className="cyber-frame-body relative overflow-hidden">
                <span className="cb cb-tl" />
                <span className="cb cb-br" />

                <Link href={`/blog/${post.slug}`} className="block">
                  <div className="flex flex-col md:flex-row">
                    {post.cover_image && (
                      <div className="md:w-64 h-48 md:h-auto overflow-hidden shrink-0 border-b md:border-b-0 md:border-r border-neon-cyan/20">
                        <img
                          src={post.cover_image}
                          alt={post.title}
                          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                        />
                      </div>
                    )}

                    <div className="p-6 md:p-7 flex-1">
                      <div className="flex flex-wrap items-center justify-between gap-2 mb-3">
                        <div className="flex flex-wrap items-center gap-4 text-xs font-mono text-zinc-400">
                          {post.published_at && (
                            <time dateTime={post.published_at} className="text-neon-cyan">
                              {new Date(post.published_at).toLocaleDateString('ru-RU', {
                                year: 'numeric',
                                month: 'long',
                                day: 'numeric',
                              })}
                            </time>
                          )}
                          <span className="flex items-center gap-1">
                            <Clock className="w-3.5 h-3.5 text-acid-yellow" />
                            {post.reading_time_minutes} МИН
                          </span>
                          <span className="flex items-center gap-1">
                            <Eye className="w-3.5 h-3.5 text-neon-cyan" />
                            {post.views_count}
                          </span>
                          <button
                            type="button"
                            onClick={(e) => {
                              e.preventDefault();
                              handleLike(post.id);
                            }}
                            className="flex items-center gap-1 hover:text-neon-magenta transition-colors"
                          >
                            <Heart className="w-3.5 h-3.5 text-neon-magenta" />
                            {post.likes_count}
                          </button>
                        </div>

                        <span className="inline-flex items-center gap-1 font-display text-xs font-bold text-neon-cyan group-hover:translate-x-1 transition-transform">
                          <span>ЧИТАТЬ</span>
                          <ArrowUpRight className="w-4 h-4" />
                        </span>
                      </div>

                      <h2 className="text-xl sm:text-2xl font-display font-bold text-white mb-2.5 group-hover:text-neon-cyan transition-colors">
                        {post.title}
                      </h2>
                      <p className="text-sm sm:text-base text-zinc-300/90 mb-5 line-clamp-3 leading-relaxed">
                        {post.excerpt}
                      </p>

                      {post.tags?.length > 0 && (
                        <div className="flex flex-wrap gap-2">
                          {post.tags.map((tag) => (
                            <button
                              key={tag}
                              type="button"
                              onClick={(e) => {
                                e.preventDefault();
                                setActiveTag(tag);
                              }}
                              className="px-2.5 py-1 text-xs font-mono tracking-wider bg-neon-purple/15 text-neon-cyan border border-neon-cyan/30 hover:border-neon-magenta hover:text-white transition-colors"
                            >
                              #{tag}
                            </button>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </Link>
              </div>
            </motion.article>
          ))}
        </div>

        {posts.length === 0 && (
          <div className="cyber-frame">
            <div className="cyber-frame-body text-center py-20 text-zinc-400 font-mono">
              Статьи скоро будут опубликованы
            </div>
          </div>
        )}
      </div>
    </main>
  );
}
