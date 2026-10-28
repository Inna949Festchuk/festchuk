'use client';

import {useEffect, useState} from 'react';
import {useTranslations, useLocale} from 'next-intl';
import {motion} from 'framer-motion';
import {Eye, Heart, ArrowUpRight, Github, Layers} from 'lucide-react';
import {Link} from '@/i18n/navigation';

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
  const t = useTranslations('projects');
  const locale = useLocale();

  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/projects/?lang=${locale}`)
      .then((r) => r.json())
      .then((data) => {
        setProjects(data.results || data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [locale]);

  const handleLike = async (id: number) => {
    try {
      await fetch(`/api/projects/${id}/like/`, {method: 'POST'});
      setProjects((prev) =>
        prev.map((p) => (p.id === id ? {...p, likes_count: p.likes_count + 1} : p)),
      );
    } catch {}
  };

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

  return (
    <main className="min-h-screen px-4 py-12">
      <div className="max-w-7xl mx-auto">
        {/* Page Header */}
        <div className="mb-12 flex flex-col md:flex-row md:items-end justify-between gap-6 border-b border-neon-cyan/20 pb-6">
          <div>
            <div className="inline-flex items-center gap-2 font-mono text-xs tracking-[0.25em] text-neon-cyan mb-2">
              <Layers className="w-3.5 h-3.5" />
              <span>{t('headerCode')}</span>
            </div>
            <h1 className="text-4xl sm:text-5xl font-display font-black tracking-wide">
              <span className="text-white">{t('title1')}</span>{' '}
              <span className="text-neon-cyan text-glow-cyan">{t('title2')}</span>
            </h1>
          </div>
          <p className="text-zinc-300 font-mono text-xs sm:text-sm max-w-md">
            {t('headerDesc')}
          </p>
        </div>

        <div className="bento-grid">
          {projects.map((project, i) => {
            const isLarge = i === 0 || project.is_featured;
            const sizeClass = isLarge ? 'bento-lg' : 'bento-sm';
            const coverClass = isLarge ? 'h-52 sm:h-64' : 'h-40 sm:h-44';
            return (
              <motion.div
                key={project.id}
                initial={{opacity: 0, y: 20}}
                animate={{opacity: 1, y: 0}}
                transition={{delay: i * 0.08}}
                className={`cyber-frame group ${sizeClass}`}
              >
                <div className="cyber-frame-body overflow-hidden flex flex-col h-full">
                  <span className="cb cb-tl" />
                  <span className="cb cb-br" />

                  {/* Cover */}
                  <div
                    className={`relative ${coverClass} bg-[#070b18] overflow-hidden border-b border-neon-cyan/20`}
                  >
                    {project.cover_image ? (
                      <img
                        src={project.cover_image}
                        alt={project.title}
                        className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                      />
                    ) : (
                      <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#101935] via-[#090e20] to-[#1a0b2e] relative">
                        <div className="absolute inset-0 opacity-25 bg-[radial-gradient(#00F3FF_1px,transparent_1px)] [background-size:18px_18px]" />
                        <span
                          className={`font-display font-black text-neon-cyan/35 text-glow-cyan ${
                            isLarge ? 'text-7xl' : 'text-5xl'
                          }`}
                        >
                          {project.title.charAt(0)}
                        </span>
                      </div>
                    )}
                    {project.is_featured && (
                      <span className="absolute top-3 left-3 px-2.5 py-1 text-[10px] font-mono tracking-[0.2em] bg-neon-magenta/25 border border-neon-magenta text-white backdrop-blur-md">
                        {t('featured')}
                      </span>
                    )}
                  </div>

                  {/* Content */}
                  <div className="p-6 flex-1 flex flex-col">
                    <h3 className="text-xl font-display font-bold text-white mb-2.5 group-hover:text-neon-cyan transition-colors">
                      {project.title}
                    </h3>
                    <p className="text-sm text-zinc-300/90 mb-5 line-clamp-3 leading-relaxed">
                      {project.summary}
                    </p>

                    {/* Tech badges */}
                    <div className="flex flex-wrap gap-2 mb-6">
                      {project.technologies?.slice(0, isLarge ? 7 : 4).map((tech) => (
                        <span
                          key={tech}
                          className="px-2.5 py-1 text-[11px] font-mono tracking-wider bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30"
                        >
                          {tech}
                        </span>
                      ))}
                    </div>

                    {/* Stats & actions */}
                    <div className="mt-auto flex items-center justify-between gap-3 pt-4 border-t border-cyber-border">
                      <div className="flex items-center gap-4 text-xs font-mono text-zinc-400">
                        <span className="flex items-center gap-1.5" title="views">
                          <Eye className="w-4 h-4 text-neon-cyan" />
                          {project.views_count}
                        </span>
                        <button
                          type="button"
                          onClick={() => handleLike(project.id)}
                          className="flex items-center gap-1.5 hover:text-neon-magenta transition-colors"
                          title="like"
                        >
                          <Heart className="w-4 h-4 text-neon-magenta" />
                          {project.likes_count}
                        </button>
                        {project.github_url && (
                          <a
                            href={project.github_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="hover:text-white transition-colors"
                            title="GitHub"
                          >
                            <Github className="w-4 h-4" />
                          </a>
                        )}
                      </div>

                      <Link
                        href={`/projects/${project.slug}`}
                        className="cyber-btn btn-ghost px-4 py-2 text-xs font-bold"
                      >
                        <span>{t('open')}</span>
                        <ArrowUpRight className="w-3.5 h-3.5" />
                      </Link>
                    </div>
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>

        {projects.length === 0 && (
          <div className="cyber-frame">
            <div className="cyber-frame-body text-center py-20 text-zinc-400 font-mono">
              {t('empty')}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}