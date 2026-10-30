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
  Github,
  ExternalLink,
  Clock,
  ArrowLeft,
  Cpu,
} from 'lucide-react';
import {Link} from '@/i18n/navigation';

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
  const t = useTranslations('project');
  const locale = useLocale();
  const params = useParams();
  const slug = params.slug as string;

  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(true);
  const [liked, setLiked] = useState(false);

  const dateLocale = locale === 'ru' ? 'ru-RU' : 'en-US';

  // Кастомный рендерер для картинок: преобразует относительные пути в GitHub raw URL
  const markdownComponents = {
    img: ({src, alt, ...props}: any) => {
      if (!src) return null;
      
      // Если URL абсолютный — оставить как есть
      if (src.startsWith('http://') || src.startsWith('https://')) {
        return <img src={src} alt={alt} {...props} />;
      }
      
      // Преобразовать относительный путь в GitHub raw URL
      if (project?.github_url) {
        try {
          const url = new URL(project.github_url);
          const pathParts = url.pathname.split('/').filter(Boolean);
          if (pathParts.length >= 2) {
            const [owner, repo] = pathParts;
            // Убрать .git если есть
            const repoName = repo.replace(/\.git$/, '');
            // Убрать ведущий слеш из относительного пути
            const cleanSrc = src.replace(/^\//, '');
            const rawUrl = `https://raw.githubusercontent.com/${owner}/${repoName}/main/${cleanSrc}`;
            return <img src={rawUrl} alt={alt} {...props} />;
          }
        } catch {}
      }
      
      // Fallback — оставить как есть (будет 404)
      return <img src={src} alt={alt} {...props} />;
    },
  };

  useEffect(() => {
    fetch(`/api/projects/${slug}/?lang=${locale}`)
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        setProject(data && data.id ? data : null);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [slug, locale]);

  const handleLike = useCallback(async () => {
    if (!project || liked) return;
    try {
      await fetch(`/api/projects/${slug}/like/`, {method: 'POST'});
      setLiked(true);
      setProject((prev) => (prev ? {...prev, likes_count: prev.likes_count + 1} : null));
    } catch {}
  }, [project, liked, slug]);

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

  if (!project) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-5">
        <div className="text-2xl font-display text-zinc-300">{t('notFound')}</div>
        <Link href="/projects" className="cyber-btn btn-ghost px-6 py-3 text-xs font-bold">
          <ArrowLeft className="w-4 h-4" />
          <span>{t('back')}</span>
        </Link>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-4 py-10">
      <div className="max-w-4xl mx-auto">
        <Link
          href="/projects"
          className="cyber-btn btn-ghost px-4 py-2 text-xs font-bold mb-8 inline-flex"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>{t('back')}</span>
        </Link>

        <motion.div
          initial={{opacity: 0, y: 20}}
          animate={{opacity: 1, y: 0}}
          className="cyber-frame mb-8"
        >
          <div className="cyber-frame-body p-6 md:p-8 relative">
            <span className="cb cb-tl" />
            <span className="cb cb-br" />

            <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
              <div>
                <div className="font-mono text-xs tracking-[0.24em] text-neon-cyan mb-2 flex items-center gap-2">
                  <Cpu className="w-3.5 h-3.5" />
                  <span>{t('spec')}</span>
                </div>
                <h1 className="text-3xl sm:text-4xl font-display font-black text-white mb-2">
                  {project.title}
                </h1>
                {project.summary && (
                  <p className="text-base sm:text-lg text-zinc-300 leading-relaxed">
                    {project.summary}
                  </p>
                )}
              </div>

              <div className="flex flex-wrap gap-3">
                {project.github_url && (
                  <a
                    href={project.github_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="cyber-btn btn-ghost px-5 py-2.5 text-xs font-bold"
                  >
                    <Github className="w-4 h-4" />
                    <span>{t('github')}</span>
                  </a>
                )}
                {project.demo_url && (
                  <a
                    href={project.demo_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="cyber-btn btn-primary px-5 py-2.5 text-xs font-bold"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>{t('demo')}</span>
                  </a>
                )}
              </div>
            </div>

            {project.technologies?.length > 0 && (
              <div className="flex flex-wrap gap-2 mb-6">
                {project.technologies.map((tech) => (
                  <span
                    key={tech}
                    className="px-3 py-1 text-xs font-mono tracking-wider bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/35"
                  >
                    {tech}
                  </span>
                ))}
              </div>
            )}

            <div className="flex flex-wrap items-center gap-6 pt-4 border-t border-cyber-border text-xs font-mono text-zinc-400">
              <span className="flex items-center gap-1.5">
                <Eye className="w-4 h-4 text-neon-cyan" />
                {project.views_count} {t('views').toUpperCase()}
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
                {project.likes_count} {t('likes').toUpperCase()}
              </button>
              <span className="flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-acid-yellow" />
                {new Date(project.created_at).toLocaleDateString(dateLocale)}
              </span>
            </div>
          </div>
        </motion.div>

        {project.readme_content ? (
          <motion.div
            initial={{opacity: 0}}
            animate={{opacity: 1}}
            transition={{delay: 0.15}}
            className="cyber-frame"
          >
            <div className="cyber-frame-body p-6 md:p-9 prose-cyber relative">
              <span className="cb cb-tl" />
              <span className="cb cb-br" />
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                rehypePlugins={[rehypeHighlight]}
                components={markdownComponents}
              >
                {project.readme_content}
              </ReactMarkdown>
            </div>
          </motion.div>
        ) : (
          <div className="cyber-frame">
            <div className="cyber-frame-body p-8 text-center text-zinc-400 font-mono">
              {t('noReadme')}
            </div>
          </div>
        )}
      </div>
    </main>
  );
}