'use client';

import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { Eye, Heart } from 'lucide-react';
import Link from 'next/link';

interface Project {
  id: number;
  title: string;
  slug: string;
  summary: string;
  technologies: string[];
  image_preview: string | null;
  cover_image: string | null;
  github_url: string;
  views_count: number;
  likes_count: number;
  is_featured: boolean;
}

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('/api/projects/')
      .then(r => r.json())
      .then(data => {
        setProjects(data.results || data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  const handleLike = async (id: number) => {
    try {
      await fetch(`/api/projects/${id}/like/`, { method: 'POST' });
      setProjects(prev =>
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
      <div className="max-w-6xl mx-auto">
        <h1 className="text-4xl font-display font-bold mb-4">
          <span className="text-foreground">Мои</span>{' '}
          <span className="text-neon-cyan text-glow-cyan">проекты</span>
        </h1>
        <p className="text-zinc-500 mb-10">
          Избранные работы и эксперименты
        </p>

        <div className="bento-grid">
          {projects.map((project, i) => {
            const isLarge = i === 0 || project.is_featured;
            const sizeClass = isLarge ? 'bento-lg' : 'bento-sm';
            const coverClass = isLarge ? 'h-48 sm:h-56' : 'h-36 sm:h-40';
            return (
              <motion.div
                key={project.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.08 }}
                className={`glass-card rounded-xl overflow-hidden group flex flex-col ${sizeClass}`}
              >
                {/* Cover */}
                <div className={`relative ${coverClass} bg-zinc-900 overflow-hidden`}>
                  {project.cover_image ? (
                    <img
                      src={project.cover_image}
                      alt={project.title}
                      className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
                    />
                  ) : (
                    <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-cyber-card to-cyber-dark">
                      <span className={`font-display text-neon-cyan/20 ${isLarge ? 'text-7xl' : 'text-4xl'}`}>
                        {project.title.charAt(0)}
                      </span>
                    </div>
                  )}
                  <span className="cb cb-tl" />
                  <span className="cb cb-br" />
                </div>

                {/* Content */}
                <div className="p-5 flex-1 flex flex-col">
                  <h3 className="text-lg font-display font-semibold text-foreground mb-2 group-hover:text-neon-cyan transition-colors">
                    {project.title}
                  </h3>
                  <p className="text-sm text-zinc-500 mb-4 line-clamp-3">
                    {project.summary}
                  </p>

                  {/* Tech badges */}
                  <div className="flex flex-wrap gap-2 mb-4">
                    {project.technologies?.slice(0, isLarge ? 6 : 4).map(tech => (
                      <span
                        key={tech}
                        className="px-2 py-1 text-xs rounded bg-neon-purple/10 text-neon-purple border border-neon-purple/20"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>

                  {/* Stats & actions */}
                  <div className="mt-auto flex items-center justify-between pt-4 border-t border-zinc-800">
                    <div className="flex items-center gap-4 text-sm text-zinc-600">
                      <span className="flex items-center gap-1">
                        <Eye className="w-4 h-4" />
                        {project.views_count}
                      </span>
                      <button
                        onClick={() => handleLike(project.id)}
                        className="flex items-center gap-1 hover:text-neon-cyan transition-colors"
                      >
                        <Heart className="w-4 h-4" />
                        {project.likes_count}
                      </button>
                    </div>

                    <Link
                      href={`/projects/${project.slug}`}
                      className="text-sm text-neon-cyan hover:underline"
                    >
                      Подробнее →
                    </Link>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {projects.length === 0 && (
          <div className="text-center py-20 text-zinc-600">
            Проекты скоро будут добавлены
          </div>
        )}
      </div>
    </main>
  );
}
