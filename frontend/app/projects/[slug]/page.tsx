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
  Github,
  ExternalLink,
  Clock,
  ArrowLeft,
} from 'lucide-react';
import Link from 'next/link';

interface Project {
  id: number;
  title: string;
  slug: string;
  description: string;
  summary: string;
  github_url: string;
  demo_url: string;
  technologies: string[];
  readme_content: string;
  cover_image: string | null;
  views_count: number;
  likes_count: number;
  created_at: string;
}

export default function ProjectDetailPage() {
  const params = useParams();
  const slug = params.slug as string;

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [liked, setLiked] = useState(false);

  useEffect(() => {
    fetch(`/api/projects/${slug}/`)
      .then(r => r.json())
      .then(data => {
        setProject(data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug]);

  const handleLike = useCallback(async () => {
    if (!project || liked) return;
    try {
      await fetch(`/api/projects/${project.id}/like/`, { method: 'POST' });
      setLiked(true);
      setProject(prev => prev ? { ...prev, likes_count: prev.likes_count + 1 } : null);
    } catch {}
  }, [project, liked]);

  if (loading) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="text-neon-cyan font-mono animate-pulse">Загрузка...</div>
      </main>
    );
  }

  if (!project) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-4">
        <div className="text-2xl text-zinc-500">Проект не найден</div>
        <Link href="/projects" className="text-neon-cyan hover:underline">
          ← Ко всем проектам
        </Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-8">
      <div className="max-w-4xl mx-auto">
        {/* Back */}
        <Link
          href="/projects"
          className="inline-flex items-center gap-2 text-sm text-zinc-500 hover:text-neon-cyan transition-colors mb-6"
        >
          <ArrowLeft className="w-4 h-4" />
          Ко всем проектам
        </Link>

        {/* Header */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="mb-8"
        >
          <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
            <div>
              <h1 className="text-4xl font-display font-bold text-foreground mb-2">
                {project.title}
              </h1>
              {project.summary && (
                <p className="text-lg text-zinc-400">{project.summary}</p>
              )}
            </div>

            <div className="flex gap-3">
              {project.github_url && (
                <a
                  href={project.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="cyber-btn px-4 py-2 bg-transparent border border-zinc-600 text-zinc-300 hover:border-neon-cyan hover:text-neon-cyan flex items-center gap-2 text-sm"
                >
                  <Github className="w-4 h-4" />
                  GitHub
                </a>
              )}
              {project.demo_url && (
                <a
                  href={project.demo_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="cyber-btn px-4 py-2 bg-transparent border border-zinc-600 text-zinc-300 hover:border-acid-yellow hover:text-acid-yellow flex items-center gap-2 text-sm"
                >
                  <ExternalLink className="w-4 h-4" />
                  Демо
                </a>
              )}
            </div>
          </div>

          {/* Stats */}
          <div className="flex flex-wrap items-center gap-6 text-sm text-zinc-500">
            <span className="flex items-center gap-1">
              <Eye className="w-4 h-4" />
              {project.views_count} просмотров
            </span>
            <button
              onClick={handleLike}
              className={`flex items-center gap-1 transition-colors ${
                liked ? 'text-neon-cyan' : 'hover:text-neon-cyan'
              }`}
            >
              <Heart className={`w-4 h-4 ${liked ? 'fill-neon-cyan' : ''}`} />
              {project.likes_count}
            </button>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              {new Date(project.created_at).toLocaleDateString('ru-RU')}
            </span>
          </div>
        </motion.div>

        {/* Technologies */}
        {project.technologies?.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-8">
            {project.technologies.map(tech => (
              <span
                key={tech}
                className="px-3 py-1.5 text-sm rounded-full bg-neon-purple/10 text-neon-purple border border-neon-purple/20"
              >
                {tech}
              </span>
            ))}
          </div>
        )}

        {/* README Content */}
        {project.readme_content ? (
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
              {project.readme_content}
            </ReactMarkdown>
          </motion.div>
        ) : (
          <div className="glass-card rounded-xl p-8 text-center text-zinc-500">
            README пока не доступен
          </div>
        )}
      </div>
    </main>
  );
}
