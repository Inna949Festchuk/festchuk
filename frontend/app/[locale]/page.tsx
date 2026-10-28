'use client';

import {useTranslations} from 'next-intl';
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
} from 'lucide-react';
import Hologram from '@/components/Hologram';
import Odometer from '@/components/Odometer';

export default function HomePage() {
  const t = useTranslations('home');

  const modules = [
    {
      icon: Brain,
      code: t('moduleAiCode'),
      name: t('moduleAiName'),
      desc: t('moduleAiDesc'),
      hex: 'hex-cyan',
    },
    {
      icon: Shield,
      code: t('moduleSecCode'),
      name: t('moduleSecName'),
      desc: t('moduleSecDesc'),
      hex: 'hex-purple',
    },
    {
      icon: Eye,
      code: t('moduleFrontCode'),
      name: t('moduleFrontName'),
      desc: t('moduleFrontDesc'),
      hex: 'hex-cyan',
    },
    {
      icon: Cpu,
      code: t('moduleBackCode'),
      name: t('moduleBackName'),
      desc: t('moduleBackDesc'),
      hex: 'hex-purple',
    },
  ];

  const stats = [
    {n: 15, suffix: '+', label: t('statProjects')},
    {n: 5, suffix: '+', label: t('statYears')},
    {n: 10, suffix: '+', label: t('statArticles')},
    {n: 24, suffix: '/7', label: t('statAi')},
  ];

  return (
    <main className="relative">
      {/* ============ HERO ============ */}
      <section className="relative min-h-[calc(100vh-4rem)] flex items-center px-4 py-12">
        <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-12 items-center">
          {/* Left column */}
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
              <Link
                href="/projects"
                className="cyber-btn btn-primary px-8 py-4 font-display font-bold text-xs sm:text-sm tracking-[0.16em]"
              >
                <Sparkles className="w-4 h-4" />
                <span>{t('ctaProjects')}</span>
              </Link>
              <Link
                href="/blog"
                className="cyber-btn btn-ghost px-8 py-4 font-display font-semibold text-xs sm:text-sm tracking-[0.16em]"
              >
                <span>{t('ctaBlog')}</span>
                <ArrowUpRight className="w-4 h-4" />
              </Link>
            </div>

            <div className="flex items-center gap-3">
              <a
                href="https://github.com/Inna949Festchuk"
                target="_blank"
                rel="noopener noreferrer"
                className="cyber-btn btn-ghost !p-3"
                aria-label="GitHub"
                title="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
              <a
                href="mailto:contact@festchuk.dev"
                className="cyber-btn btn-ghost !p-3"
                aria-label="Email"
                title="Email"
              >
                <Mail className="w-5 h-5" />
              </a>
              <a
                href="https://t.me/festchuk"
                target="_blank"
                rel="noopener noreferrer"
                className="cyber-btn btn-ghost !p-3"
                aria-label="Telegram"
                title="Telegram"
              >
                <Send className="w-5 h-5" />
              </a>
              <span className="ml-2 font-mono text-[11px] tracking-[0.2em] text-zinc-400 hidden sm:inline">
                {t('uplink')}
              </span>
            </div>
          </motion.div>

          {/* Right column — hologram */}
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
              <h2
                className="glitch font-display font-black text-3xl sm:text-4xl inline-block"
                data-text={t('coreModules')}
              >
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

      {/* Футер — глобальный (components/Footer.tsx в layout), на каждой странице */}
    </main>
  );
}