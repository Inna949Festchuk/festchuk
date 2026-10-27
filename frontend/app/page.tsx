'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import {
  Github,
  Mail,
  Send,
  Brain,
  Shield,
  Eye,
  Cpu,
  Hexagon,
  Triangle,
  Circle,
} from 'lucide-react';
import Hologram from '@/components/Hologram';
import Odometer from '@/components/Odometer';

const modules = [
  {
    icon: Brain,
    code: 'AI / LLM / RAG',
    name: 'NEURAL SYNC',
    desc: 'Ретривал по проектам и статьям, Function Calling, голос (STT/TTS).',
    hex: 'hex-cyan',
  },
  {
    icon: Shield,
    code: 'SECURITY',
    name: 'QUANTUM SHIELD',
    desc: 'Rate limiting, анонимные аналитики, compliance 152-ФЗ без ПДн.',
    hex: 'hex-purple',
  },
  {
    icon: Eye,
    code: 'FRONTEND / UX',
    name: 'OMNI VISION',
    desc: 'Next.js 14, Framer Motion, киберпанк-UI, полная адаптивность.',
    hex: 'hex-cyan',
  },
  {
    icon: Cpu,
    code: 'BACKEND / DATA',
    name: 'HYPER DRIVE',
    desc: 'Django 5, DRF, Celery, PostgreSQL + pgvector, Redis.',
    hex: 'hex-purple',
  },
];

const stats = [
  { n: 15, suffix: '+', label: 'PROJECTS' },
  { n: 5, suffix: '+', label: 'YEARS EXP' },
  { n: 10, suffix: '+', label: 'ARTICLES' },
  { n: 24, suffix: '/7', label: 'AI ONLINE' },
];

export default function HomePage() {
  return (
    <main className="relative">
      {/* ============ HERO ============ */}
      <section className="relative min-h-[calc(100vh-4rem)] flex items-center px-4 py-12">
        <div className="max-w-7xl mx-auto w-full grid lg:grid-cols-2 gap-10 items-center">
          {/* Left column */}
          <motion.div
            initial={{ opacity: 0, x: -30 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.7 }}
          >
            <div className="mb-7 inline-flex items-center gap-2 px-4 py-2 border border-neon-cyan/40 bg-neon-cyan/5">
              <span className="w-2 h-2 rounded-full bg-[#22c55e] animate-neon-pulse" />
              <span className="text-xs text-neon-cyan font-mono tracking-[0.25em]">
                AI-DRIVEN FULLSTACK DEVELOPER
              </span>
            </div>

            <h1 className="font-display font-black leading-[0.92] mb-6 text-6xl sm:text-7xl lg:text-8xl">
              <span className="glitch block" data-text="FESTCHUK">
                FESTCHUK
              </span>
            </h1>

            <p className="font-display text-xl sm:text-2xl text-zinc-300 tracking-wide mb-5">
              Константин <span className="text-neon-cyan">Фестчук</span>
            </p>

            <p className="text-base md:text-lg text-zinc-400 mb-9 max-w-lg leading-relaxed">
              Строю интеллектуальные приложения на стыке{' '}
              <span className="text-neon-purple text-glow-purple">Python</span>,{' '}
              <span className="text-neon-cyan text-glow-cyan">React</span> и{' '}
              <span className="text-acid-yellow">AI</span> — от бэкенда до голосового ассистента.
            </p>

            <div className="flex flex-wrap gap-4 mb-9">
              <Link
                href="/projects"
                className="cyber-btn btn-primary px-8 py-3.5 font-display font-bold text-sm tracking-widest"
              >
                INITIALIZE SYSTEM
              </Link>
              <Link
                href="/blog"
                className="cyber-btn btn-ghost px-8 py-3.5 font-display font-semibold text-sm tracking-widest"
              >
                VIEW DEMO
              </Link>
            </div>

            <div className="flex gap-4">
              <a
                href="https://github.com/Inna949Festchuk"
                target="_blank"
                rel="noopener noreferrer"
                className="p-3 border border-cyber-border text-zinc-400 hover:text-neon-cyan hover:border-neon-cyan/60 transition-colors"
                aria-label="GitHub"
              >
                <Github className="w-5 h-5" />
              </a>
              <a
                href="mailto:contact@festchuk.dev"
                className="p-3 border border-cyber-border text-zinc-400 hover:text-neon-cyan hover:border-neon-cyan/60 transition-colors"
                aria-label="Email"
              >
                <Mail className="w-5 h-5" />
              </a>
              <a
                href="https://t.me/festchuk"
                target="_blank"
                rel="noopener noreferrer"
                className="p-3 border border-cyber-border text-zinc-400 hover:text-neon-cyan hover:border-neon-cyan/60 transition-colors"
                aria-label="Telegram"
              >
                <Send className="w-5 h-5" />
              </a>
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
          <h2
            className="glitch font-display font-black text-3xl sm:text-4xl mb-3 inline-block"
            data-text="CORE MODULES"
          >
            CORE MODULES
          </h2>
          <div className="h-0.5 w-28 bg-neon-cyan mb-12 shadow-[0_0_12px_#00F3FF]" />

          <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-5">
            {modules.map((m, i) => (
              <motion.div
                key={m.name}
                initial={{ opacity: 0, y: 30 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: i * 0.1 }}
                className="cyber-frame"
              >
                <div className="cyber-frame-body p-6 h-full">
                  <span className="cb cb-tl" />
                  <span className="cb cb-tr" />
                  <span className="cb cb-bl" />
                  <span className="cb cb-br" />
                  <div className={`hex-icon ${m.hex} mb-5`}>
                    <m.icon className="w-6 h-6" />
                  </div>
                  <div className="module-eyebrow mb-2">{m.code}</div>
                  <h3 className="font-display font-bold text-lg text-foreground mb-2">
                    {m.name}
                  </h3>
                  <p className="text-sm text-zinc-400 leading-relaxed">{m.desc}</p>
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
            <div className="grid grid-cols-2 md:grid-cols-4 gap-y-8">
              {stats.map((s, i) => (
                <motion.div
                  key={s.label}
                  initial={{ opacity: 0 }}
                  whileInView={{ opacity: 1 }}
                  viewport={{ once: true }}
                  transition={{ delay: i * 0.1 }}
                  className={`flex flex-col items-center justify-center px-4 ${
                    i < stats.length - 1 ? 'md:border-r md:border-cyber-border' : ''
                  }`}
                >
                  <div className="stat-num text-4xl md:text-5xl">
                    <Odometer value={s.n} suffix={s.suffix} />
                  </div>
                  <div className="text-[11px] text-zinc-500 tracking-[0.25em] mt-3">
                    {s.label}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ============ FOOTER ============ */}
      <footer className="relative px-4 py-8 mt-6 border-t border-cyber-border">
        <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-5">
          <div className="text-[11px] text-zinc-600 font-mono tracking-wider">
            © {new Date().getFullYear()} FESTCHUK CORP. ALL RIGHTS RESERVED.
          </div>
          <div className="flex gap-7 text-[11px] text-zinc-500 tracking-wider">
            <Link href="/projects" className="hover:text-neon-cyan transition-colors">
              PROJECTS
            </Link>
            <Link href="/blog" className="hover:text-neon-cyan transition-colors">
              BLOG
            </Link>
            <Link href="/contacts" className="hover:text-neon-cyan transition-colors">
              CONTACT
            </Link>
          </div>
          <div className="flex gap-3 items-center">
            <Hexagon className="w-4 h-4 text-neon-cyan" />
            <Triangle className="w-4 h-4 text-neon-purple" />
            <Circle className="w-4 h-4 text-acid-yellow" />
          </div>
        </div>
      </footer>
    </main>
  );
}
