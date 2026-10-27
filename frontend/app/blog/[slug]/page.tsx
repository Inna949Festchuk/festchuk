'use client';

import { useEffect, useState, useCallback } from 'react';
import { useParams } from 'next/navigation';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import { motion } from 'framer-motion';
import {
  Eye,
  Heart,
  Clock,
  ArrowLeft,
  Volume2,
  VolumeX,
  Tag,
} from 'lucide-react';
import Link from 'next/link';

interface Post {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  content: string;
  cover_image: string | null;
  tags: string[];
  published_at: string;
  views_count: number;
  likes_count: number;
  tts_audio_url: string;
  reading_time_minutes: number;
}

export default function BlogPostPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [liked, setLiked] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  useEffect(() => {
    fetch(`/api/posts/${slug}/`)
      .then(r => r.json())
      .then(data => {
        setPost(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug]);

  useEffect(() => {
    return () => {
      if (audio) audio.pause();
    };
  }, [audio]);

  const handleLike = useCallback(async () => {
    if (!post || liked) return;
    try {
      await fetch(`/api/posts/${post.id}/like/`, { method: 'POST' });
      setLiked(true);
      setPost(prev => prev ? { ...prev, likes_count: prev.likes_count + 1 } : null);
    } catch {}
  }, [post, liked]);

  const toggleAudio = useCallback(async () => {
    if (!post) return;

    if (isPlaying && audio) {
      audio.pause();
      setIsPlaying(false);
      return;
    }

    if (post.tts_audio_url) {
      const a = new Audio(post.tts_audio_url);
      setAudio(a);
      a.onended = () => setIsPlaying(false);
      a.play().then(() => setIsPlaying(true)).catch(() => {});
      return;
    }

    // Generate TTS on the fly
    try {
      const res = await fetch(`/api/posts/${post.id}/tts/`, { method: 'POST' });
      if (!res.ok) return;
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = new Audio(url);
      setAudio(a);
      a.onended = () => {
        setIsPlaying(false);
        URL.revokeObjectURL(url);
      };
      await a.play();
      setIsPlaying(true);
    } catch {}
  }, [post, isPlaying, audio]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-neon-cyan font-mono animate-pulse">Загрузка...</div>
      </main>
    );
  }

  if (!post) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4">
        <div className="text-2xl text-zinc-500">Статья не найдена</div>
        <Link href="/blog" className="text-neon-cyan hover:underline">← Ко всем статьям</Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8">
      <article className="max-w-3xl mx-auto">
        {/* Back */}
        <Link
          href="/blog"
          className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-neon-cyan transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Ко всем статьям
        </Link>

        {/* Header */}
        <motion.header
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <h1 className="text-4xl font-display font-bold text-foreground mb-4 leading-tight">
            {post.title}
          </h1>

          {/* Meta */}
          <div className="flex flex-wrap items-center gap-4 text-sm text-zinc-500 mb-6">
            {post.published_at && (
              <time dateTime={post.published_at}>
                {new Date(post.published_at).toLocaleDateString('ru-RU', {
                  year: 'numeric', month: 'long', day: 'numeric',
                })}
              </time>
            )}
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {post.reading_time_minutes} мин чтения
            </span>
            <span className="flex items-center gap-1">
              <Eye className="w-4 h-4" />
              {post.views_count}
            </span>
            <button
              onClick={handleLike}
              className={`flex items-center gap-1 transition-colors ${
                liked ? 'text-neon-cyan' : 'hover:text-neon-cyan'
              }`}
            >
              <Heart className={`w-4 h-4 ${liked ? 'fill-neon-cyan' : ''}`} />
              {post.likes_count}
            </button>
          </div>

          {/* TTS button */}
          <button
            onClick={toggleAudio}
            className="cyber-btn px-4 py-2 bg-neon-purple/10 border border-neon-purple/30 text-neon-purple text-sm flex items-center gap-2 hover:bg-neon-purple/20 mb-4"
          >
            {isPlaying ? (
              <>
                <VolumeX className="w-4 h-4" />
                Остановить озвучку
              </>
            ) : (
              <>
                <Volume2 className="w-4 h-4" />
                Слушать статью
              </>
            )}
          </button>

          {/* Tags */}
          {post.tags?.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {post.tags.map(tag => (
                <span
                  key={tag}
                  className="px-3 py-1 text-xs rounded-full bg-neon-purple/10 text-neon-purple border border-neon-purple/20 flex items-center gap-1"
                >
                  <Tag className="w-3 h-3" />
                  {tag}
                </span>
              ))}
            </div>
          )}
        </motion.header>

        {/* Cover */}
        {post.cover_image && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="rounded-xl overflow-hidden mb-8 border border-zinc-800"
          >
            <img
              src={post.cover_image}
              alt={post.title}
              className="w-full object-cover"
            />
          </motion.div>
        )}

        {/* Content */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
          className="glass-card rounded-xl p-6 md:p-8 prose-cyber"
        >
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            rehypePlugins={[rehypeHighlight]}
          >
            {post.content}
          </ReactMarkdown>
        </motion.div>

        {/* Footer */}
        <footer className="mt-10 pt-8 border-t border-zinc-800 flex items-center justify-between">
          <Link
            href="/blog"
            className="text-sm text-zinc-500 hover:text-neon-cyan transition-colors"
          >
            ← Все статьи
          </Link>
          <div className="text-sm text-zinc-600">
            Спасибо за чтение
          </div>
        </footer>
      </article>
    </main>
  );
}
