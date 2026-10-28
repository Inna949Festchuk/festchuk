'use client';

import {useEffect, useState, useCallback} from 'react';
import {useParams} from 'next/navigation';
import {useTranslations, useLocale} from 'next-intl';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import {motion} from 'framer-motion';
import {
  Eye,
  Heart,
  Clock,
  ArrowLeft,
  Volume2,
  VolumeX,
  Tag,
  BookOpen,
} from 'lucide-react';
import {Link} from '@/i18n/navigation';

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
  const t = useTranslations('post');
  const locale = useLocale();
  const params = useParams();
  const slug = params.slug as string;

  const [post, setPost] = useState<Post | null>(null);
  const [loading, setLoading] = useState(true);
  const [liked, setLiked] = useState(false);
  const [audio, setAudio] = useState<HTMLAudioElement | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);

  const dateLocale = locale === 'ru' ? 'ru-RU' : 'en-US';

  useEffect(() => {
    fetch(`/api/posts/${slug}/?lang=${locale}`)
      .then((r) => r.json())
      .then((data) => {
        setPost(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug, locale]);

  useEffect(() => {
    return () => {
      if (audio) audio.pause();
    };
  }, [audio]);

  const handleLike = useCallback(async () => {
    if (!post || liked) return;
    try {
      await fetch(`/api/posts/${post.id}/like/`, {method: 'POST'});
      setLiked(true);
      setPost((prev) => (prev ? {...prev, likes_count: prev.likes_count + 1} : null));
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
      a.play()
        .then(() => setIsPlaying(true))
        .catch(() => {});
      return;
    }

    try {
      const res = await fetch(`/api/posts/${post.id}/tts/?lang=${locale}`, {method: 'POST'});
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
  }, [post, isPlaying, audio, locale]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="cyber-frame">
          <div className="cyber-frame-body px-8 py-5 text-neon-cyan font-mono tracking-[0.2em] animate-pulse">
            {t('loading')}
          </div>
        </div>
      </main>
    );
  }

  if (!post) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-5">
        <div className="text-2xl font-display text-zinc-300">{t('notFound')}</div>
        <Link href="/blog" className="cyber-btn btn-ghost px-6 py-3 text-xs font-bold">
          <ArrowLeft className="w-4 h-4" />
          <span>{t('back')}</span>
        </Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-10">
      <article className="max-w-3xl mx-auto">
        <Link
          href="/blog"
          className="cyber-btn btn-ghost px-4 py-2 text-xs font-bold mb-8 inline-flex"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{t('back')}</span>
        </Link>

        {/* Header Card */}
        <motion.header
          initial={{opacity: 0, y: 20}}
          animate={{opacity: 1, y: 0}}
          className="cyber-frame mb-8"
        >
          <div className="cyber-frame-body p-6 md:p-8 relative">
            <span className="cb cb-tl" />
            <span className="cb cb-br" />

            <div className="font-mono text-xs tracking-[0.24em] text-neon-magenta mb-2 flex items-center gap-2">
              <BookOpen className="w-3.5 h-3.5" />
              <span>{t('entry')}</span>
            </div>

            <h1 className="text-3xl sm:text-4xl font-display font-black text-white mb-5 leading-tight">
              {post.title}
            </h1>

            <div className="flex flex-wrap items-center gap-5 text-xs font-mono text-zinc-400 mb-6">
              {post.published_at && (
                <time dateTime={post.published_at} className="text-neon-cyan">
                  {new Date(post.published_at).toLocaleDateString(dateLocale, {
                    year: 'numeric',
                    month: 'long',
                    day: 'numeric',
                  })}
                </time>
              )}
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-acid-yellow" />
                {post.reading_time_minutes} {t('minRead').toUpperCase()}
              </span>
              <span className="flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-neon-cyan" />
                {post.views_count}
              </span>
              <button
                type="button"
                onClick={handleLike}
                className={`flex items-center gap-1.5 transition-colors ${
                  liked ? 'text-neon-magenta' : 'hover:text-neon-magenta'
                }`}
              >
                <Heart
                  className={`w-4 h-4 ${
                    liked ? 'fill-neon-magenta text-neon-magenta' : 'text-neon-magenta'
                  }`}
                />
                {post.likes_count}
              </button>
            </div>

            <div className="flex flex-wrap items-center justify-between gap-4 pt-4 border-t border-cyber-border">
              {post.tags?.length > 0 && (
                <div className="flex flex-wrap gap-2">
                  {post.tags.map((tag) => (
                    <span
                      key={tag}
                      className="px-2.5 py-1 text-xs font-mono bg-neon-purple/15 text-neon-cyan border border-neon-cyan/30 flex items-center gap-1"
                    >
                      <Tag className="w-3 h-3" />
                      {tag}
                    </span>
                  ))}
                </div>
              )}

              <button
                type="button"
                onClick={toggleAudio}
                className={`cyber-btn px-5 py-2.5 text-xs font-bold ${
                  isPlaying ? 'btn-primary' : 'btn-ghost'
                }`}
              >
                {isPlaying ? (
                  <>
                    <VolumeX className="w-4 h-4" />
                    <span>{t('stop').toUpperCase()}</span>
                  </>
                ) : (
                  <>
                    <Volume2 className="w-4 h-4" />
                    <span>{t('listen').toUpperCase()}</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </motion.header>

        {post.cover_image && (
          <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            transition={{delay: 0.1}}
            className="cyber-frame mb-8"
          >
            <div className="cyber-frame-body overflow-hidden">
              <img
                src={post.cover_image}
                alt={post.title}
                className="w-full object-cover"
              />
            </div>
          </motion.div>
        )}

        {/* Content */}
        <motion.div
          initial={{opacity: 0}}
          animate={{opacity: 1}}
          transition={{delay: 0.2}}
          className="cyber-frame"
        >
          <div className="cyber-frame-body p-6 md:p-9 prose-cyber relative">
            <span className="cb cb-tl" />
            <span className="cb cb-br" />
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              rehypePlugins={[rehypeHighlight]}
            >
              {post.content}
            </ReactMarkdown>
          </div>
        </motion.div>

        <footer className="mt-10 pt-8 border-t border-cyber-border flex items-center justify-between">
          <Link href="/blog" className="cyber-btn btn-ghost px-5 py-2.5 text-xs font-bold">
            <ArrowLeft className="w-4 h-4" />
            <span>{t('allArticles').toUpperCase()}</span>
          </Link>
          <div className="text-xs font-mono text-zinc-400 tracking-wider">
            {t('end')}
          </div>
        </footer>
      </article>
    </main>
  );
}