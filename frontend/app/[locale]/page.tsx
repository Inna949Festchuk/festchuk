'use client';

import {useEffect, useState} from 'react';
import {useTranslations, useLocale} from 'next-intl';
import {Link} from '@/i18n/navigation';
import {motion} from 'framer-motion';
import {
  Github,
  Mail,
  Send,
  Brain,
  Shield,
  Eye,
  Cpu,
  Sparkles,
  ArrowUpRight,
  BookOpen,
  Clock,
} from 'lucide-react';
import Hologram from '@/components/Hologram';
import Odometer from '@/components/Odometer';

interface Project {
  id: number;
  title: string;
  slug: string;
  summary: string;
  technologies: string[];
  cover_image: string | null;
  is_featured: boolean;
}

interface Post {
  id: number;
  title: string;
  slug: string;
  excerpt: string;
  published_at: string;
  reading_time_minutes: number;
}

function toList<T>(data: unknown): T[] {
  // The API returns a plain array (pagination disabled) or the older
  // {results: []} envelope.
  if (Array.isArray(data)) return data as T[];
  if (data && typeof data === 'object' && Array.isArray((data as {results?: T[]}).results)) {
    return (data as {results: T[]}).results;
  }
  return [];
}

export default function HomePage() {
  const t = useTranslations('home');
  const locale = useLocale();

  const [projects, setProjects] = useState<Project[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    let active = true;
    Promise.all([
      fetch(`/api/projects/?lang=${locale}`).then((r) => (r.ok ? r.json() : [])),
      fetch(`/api/posts/?lang=${locale}`).then((r) => (r.ok ? r.json() : [])),
    ])
      .then(([p, b]) => {
        if (!active) return;
        setProjects(toList<Project>(p));
        setPosts(toList<Post>(b));
        setLoaded(true);
      })
      .catch(() => active && setLoaded(true));
    return () => {
      active = false;
    };
  }, [locale]);

  const dateLocale = locale === 'ru' ? 'ru-RU' : 'en-US';
  const featuredProjects = projects.slice(0, 4);
  const latestPosts = posts.slice(0, 3);

  const modules = [
    {icon: Brain, code: t('moduleAiCode'), name: t('moduleAiName'), desc: t('moduleAiDesc'), hex: 'hex-cyan'},
    {icon: Shield, code: t('moduleSecCode'), name: t('moduleSecName'), desc: t('moduleSecDesc'), hex: 'hex-purple'},
    {icon: Eye, code: t('moduleFrontCode'), name: t('moduleFrontName'), desc: t('moduleFrontDesc'), hex: 'hex-cyan'},
    {icon: Cpu, code: t('moduleBackCode'), name: t('moduleBackName'), desc: t('moduleBackDesc'), hex: 'hex-purple'},
  ];

  // Project and article counts come from the API once loaded; the rest are
  // static by nature (years, uptime) and can't be derived from the database.
  const stats = [
    {n: loaded ? projects.length : 15, suffix: '+', label: t('statProjects')},
    {n: 5, suffix: '+', label: t('statYears')},
    {n: loaded ? posts.length : 10, suffix: '+', label: t('statArticles')},
    {n: 24, suffix: '/7', label: t('statAi')},
  ];

  return (
    <main className="relative">
      {/* ============ HERO ============ */}
      <section className="relative min-h-[calc(100vh-4rem)] flex items-center px-4 py-12">
        <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-12 items-center">
          <motion.div
            initial={{opacity: 0, x: -30}}
            animate={{opacity: 1, x: 0}}
            transition={{duration: 0.7}}
          >
            <div className="mb-7 inline-flex items-center gap-2.5 px-4 py-2 border border-neon-cyan/50 bg-[#070c1c]/80 backdrop-blur-md shadow-[0_0_20px_rgba(0,243,255,0.18)]">
              <span className="w-2 h-2 rounded-full bg-[#22c55e] animate-neon-pulse" />
              <span className="text-xs text-neon-cyan font-mono tracking-[0.24em]">
                {t('heroBadge')}
              </span>
            </div>

            <h1 className="font-display font-black leading-[0.94] mb-5 text-5xl sm:text-7xl lg:text-8xl tracking-tight">
              <span className="glitch block" data-text="FESTCHUK">
                FESTCHUK
              </span>
            </h1>

            <p className="font-display font-bold text-xl sm:text-2xl text-zinc-100 tracking-wide mb-5 flex items-center gap-3">
              <span>{t('nameFirst')}</span>
              <span className="text-neon-cyan text-glow-cyan">{t('nameLast')}</span>
            </p>

            <p className="text-base md:text-lg text-zinc-200/90 mb-9 max-w-xl leading-relaxed bg-[#070b18]/65 backdrop-blur-sm p-4 border-l-2 border-neon-cyan">
              {t('heroText')}
            </p>

            <div className="flex flex-wrap gap-4 mb-9">
              <Link href="/projects" className="cyber-btn btn-primary px-8 py-4 font-display font-bold text-xs sm:text-sm tracking-[0.16em]">
                <Sparkles className="w-4 h-4" />
                <span>{t('ctaProjects')}</span>
              </Link>
              <Link href="/blog" className="cyber-btn btn-ghost px-8 py-4 font-display font-semibold text-xs sm:text-sm tracking-[0.16em]">
                <span>{t('ctaBlog')}</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="flex items-center gap-3">
              <a href="https://github.com/Inna949Festchuk" target="_blank" rel="noopener noreferrer" className="cyber-btn btn-ghost !p-3" aria-label="GitHub" title="GitHub">
                <Github className="w-5 h-5" />
              </a>
              <a href="mailto:contact@festchuk.dev" className="cyber-btn btn-ghost !p-3" aria-label="Email" title="Email">
                <Mail className="w-5 h-5" />
              </a>
              <a href="https://t.me/festchuk" target="_blank" rel="noopener noreferrer" className="cyber-btn btn-ghost !p-3" aria-label="Telegram" title="Telegram">
                <Send className="w-5 h-5" />
              </a>
              <span className="ml-2 font-mono text-[11px] tracking-[0.2em] text-zinc-400 hidden sm:inline">
                {t('uplink')}
              </span>
            </div>
          </motion.div>

          <div className="hidden lg:flex justify-center">
            <Hologram />
          </div>
        </div>
      </section>

      {/* ============ CORE MODULES ============ */}
      <section className="relative px-4 py-16">
        <div className="max-w-7xl mx-auto">
          <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10 gap-4">
            <div>
              <div className="font-mono text-xs tracking-[0.28em] text-neon-cyan mb-2">
                {t('systemArchitecture')}
              </div>
              <h2 className="glitch font-display font-black text-3xl sm:text-4xl inline-block" data-text={t('coreModules')}>
                {t('coreModules')}
              </h2>
            </div>
            <div className="font-mono text-xs tracking-[0.2em] text-emerald-400 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              {t('allNominal')}
            </div>
          </div>

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {modules.map((m, i) => (
              <motion.div
                key={m.name}
                initial={{opacity: 0, y: 30}}
                whileInView={{opacity: 1, y: 0}}
                viewport={{once: true}}
                transition={{delay: i * 0.1}}
                className="cyber-frame group"
              >
                <div className="cyber-frame-body p-6 h-full flex flex-col">
                  <span className="cb cb-tl" />
                  <span className="cb cb-br" />
                  <div className="flex items-center justify-between mb-5">
                    <div className={`hex-icon ${m.hex}`}>
                      <m.icon className="w-6 h-6" />
                    </div>
                    <span className="font-mono text-[10px] tracking-[0.22em] text-zinc-500">
                      0{i + 1} // MOD
                    </span>
                  </div>
                  <div className="module-eyebrow mb-2">{m.code}</div>
                  <h3 className="font-display font-bold text-lg text-white mb-2 group-hover:text-neon-cyan transition-colors">
                    {m.name}
                  </h3>
                  <p className="text-sm text-zinc-300/90 leading-relaxed">{m.desc}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ FEATURED PROJECTS ============ */}
      {featuredProjects.length > 0 && (
        <section className="relative px-4 py-8">
          <div className="max-w-7xl mx-auto">
            <div className="flex items-end justify-between mb-8 gap-4">
              <div>
                <div className="font-mono text-xs tracking-[0.28em] text-neon-cyan mb-2">
                  {t('featuredCode')}
                </div>
                <h2 className="font-display font-black text-3xl sm:text-4xl text-white">
                  {t('featuredTitle1')} <span className="text-neon-cyan text-glow-cyan">{t('featuredTitle2')}</span>
                </h2>
              </div>
              <Link href="/projects" className="cyber-btn btn-ghost px-5 py-2.5 text-xs font-bold shrink-0">
                <span>{t('featuredAll')}</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="bento-grid">
              {featuredProjects.map((project, i) => (
                <motion.div
                  key={project.id}
                  initial={{opacity: 0, y: 20}}
                  whileInView={{opacity: 1, y: 0}}
                  viewport={{once: true}}
                  transition={{delay: i * 0.08}}
                  className={`cyber-frame group ${i % 4 === 0 ? 'bento-lg' : 'bento-sm'}`}
                >
                  <div className="cyber-frame-body overflow-hidden flex flex-col h-full">
                    <span className="cb cb-tl" />
                    <span className="cb cb-br" />
                    <Link href={`/projects/${project.slug}`} className="flex flex-col h-full">
                      <div className="h-40 sm:h-48 bg-[#070b18] overflow-hidden border-b border-neon-cyan/20 relative">
                        {project.cover_image ? (
                          <img src={project.cover_image} alt={project.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500" />
                        ) : (
                          <div className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#101935] via-[#090e20] to-[#1a0b2e] relative">
                            <div className="absolute inset-0 opacity-25 bg-[radial-gradient(#00F3FF_1px,transparent_1px)] [background-size:18px_18px]" />
                            <span className="font-display font-black text-neon-cyan/35 text-glow-cyan text-6xl">
                              {project.title.charAt(0)}
                            </span>
                          </div>
                        )}
                      </div>
                      <div className="p-5 flex-1 flex flex-col">
                        <h3 className="text-lg font-display font-bold text-white mb-2 group-hover:text-neon-cyan transition-colors line-clamp-1">
                          {project.title}
                        </h3>
                        <p className="text-sm text-zinc-300/90 line-clamp-2 mb-4 leading-relaxed">
                          {project.summary}
                        </p>
                        <div className="mt-auto flex flex-wrap gap-1.5">
                          {project.technologies?.slice(0, 3).map((tech) => (
                            <span key={tech} className="px-2 py-0.5 text-[10px] font-mono tracking-wider bg-neon-cyan/10 text-neon-cyan border border-neon-cyan/30">
                              {tech}
                            </span>
                          ))}
                        </div>
                      </div>
                    </Link>
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ============ LATEST ARTICLES ============ */}
      {latestPosts.length > 0 && (
        <section className="relative px-4 py-8">
          <div className="max-w-5xl mx-auto">
            <div className="flex items-end justify-between mb-8 gap-4">
              <div>
                <div className="font-mono text-xs tracking-[0.28em] text-neon-magenta mb-2">
                  {t('latestCode')}
                </div>
                <h2 className="font-display font-black text-3xl sm:text-4xl text-white">
                  {t('latestTitle1')} <span className="text-neon-purple text-glow-purple">{t('latestTitle2')}</span>
                </h2>
              </div>
              <Link href="/blog" className="cyber-btn btn-ghost px-5 py-2.5 text-xs font-bold shrink-0">
                <span>{t('latestAll')}</span>
                <ArrowUpRight className="w-3.5 h-3.5" />
              </Link>
            </div>

            <div className="space-y-4">
              {latestPosts.map((post, i) => (
                <motion.article
                  key={post.id}
                  initial={{opacity: 0, y: 16}}
                  whileInView={{opacity: 1, y: 0}}
                  viewport={{once: true}}
                  transition={{delay: i * 0.08}}
                  className="cyber-frame group"
                >
                  <div className="cyber-frame-body relative">
                    <span className="cb cb-tl" />
                    <span className="cb cb-br" />
                    <Link href={`/blog/${post.slug}`} className="flex items-center gap-4 p-5">
                      <div className="hidden sm:grid place-items-center w-12 h-12 shrink-0 hex-icon hex-purple">
                        <BookOpen className="w-5 h-5" />
                      </div>
                      <div className="min-w-0 flex-1">
                        <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] font-mono text-zinc-400 mb-1">
                          {post.published_at && (
                            <span className="text-neon-cyan">
                              {new Date(post.published_at).toLocaleDateString(dateLocale, {year: 'numeric', month: 'long', day: 'numeric'})}
                            </span>
                          )}
                          <span className="flex items-center gap-1 text-acid-yellow">
                            <Clock className="w-3 h-3" />
                            {post.reading_time_minutes} {t('min').toUpperCase()}
                          </span>
                        </div>
                        <h3 className="text-base sm:text-lg font-display font-bold text-white line-clamp-1 group-hover:text-neon-cyan transition-colors">
                          {post.title}
                        </h3>
                      </div>
                      <ArrowUpRight className="w-4 h-4 text-neon-cyan shrink-0 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                    </Link>
                  </div>
                </motion.article>
              ))}
            </div>
          </div>
        </section>
      )}

      {/* ============ STATS ============ */}
      <section className="relative px-4 py-12">
        <div className="max-w-6xl mx-auto cyber-frame">
          <div className="cyber-frame-body px-6 py-9">
            <span className="cb cb-tl" />
            <span className="cb cb-br" />
            <div className="grid grid-cols-2 md:grid-cols-4 gap-y-8">
              {stats.map((s, i) => (
                <motion.div
                  key={s.label}
                  initial={{opacity: 0}}
                  whileInView={{opacity: 1}}
                  viewport={{once: true}}
                  transition={{delay: i * 0.1}}
                  className={`flex flex-col items-center justify-center px-4 ${
                    i < stats.length - 1 ? 'md:border-r md:border-cyber-border' : ''
                  }`}
                >
                  <div className="stat-num text-4xl md:text-5xl">
                    <Odometer value={s.n} suffix={s.suffix} />
                  </div>
                  <div className="text-[11px] font-mono text-zinc-300 tracking-[0.22em] mt-3 text-center">
                    {s.label}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}
