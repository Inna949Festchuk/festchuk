'use client';

import {useEffect, useRef, useState} from 'react';
import {useTranslations, useLocale} from 'next-intl';
import {useParams} from 'next/navigation';
import {Link} from '@/i18n/navigation';
import {Radio} from 'lucide-react';

interface ModuleData {
  id: number;
  slug: string;
  code_name: string;
  name: string;
  description: string;
  video_url: string;
  skills_text: string;
  greeting: string;
  init_text: string;
  shutdown_text: string;
  is_active: boolean;
}

// Per-module presentation: accent color (cyan/purple, matching the home
// page hex icons) + short label for the "next module" buttons.
const MODULES: Record<string, {name: string; color: 'cyan' | 'purple'; label: string}> = {
  'neural-sync': {name: 'NEURAL SYNC', color: 'cyan', label: 'NEURAL SYNC (Разум системы)'},
  'quantum-shield': {name: 'QUANTUM SHIELD', color: 'purple', label: 'QUANTUM SHIELD (Защита)'},
  'omni-vision': {name: 'OMNI VISION', color: 'cyan', label: 'OMNI VISION (Голографический интерфейс)'},
  'hyper-drive': {name: 'HYPER DRIVE', color: 'purple', label: 'HYPER DRIVE (Бэкенд-архитектура)'},
};

// Full literal class strings per accent so Tailwind sees them (no runtime
// concatenation). Each module page is tinted by its own color.
const ACCENTS = {
  cyan: {
    eyebrow: 'text-neon-cyan',
    border: 'border-neon-cyan/20',
    h1accent: 'text-neon-cyan text-glow-cyan',
    frame: 'border-neon-cyan/40',
    shadow: 'shadow-[0_0_24px_rgba(0,243,255,0.15)]',
  },
  purple: {
    eyebrow: 'text-neon-purple',
    border: 'border-neon-purple/20',
    h1accent: 'text-neon-purple text-glow-purple',
    frame: 'border-neon-purple/40',
    shadow: 'shadow-[0_0_24px_rgba(188,19,254,0.15)]',
  },
};

function isVideoFile(url: string): boolean {
  return /\.(mp4|webm|ogg|ogv|mov|m4v)(\?|$)/i.test(url);
}

export default function ModulePage() {
  const locale = useLocale();
  const params = useParams();
  const slug = params.slug as string;
  const t = useTranslations('modules');
  const [module, setModule] = useState<ModuleData | null>(null);
  const [loaded, setLoaded] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const replayTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const meta = MODULES[slug] || {name: slug.toUpperCase(), color: 'cyan' as const, label: slug};
  const c = ACCENTS[meta.color];

  useEffect(() => {
    fetch(`/api/modules/${slug}/?lang=${locale}`)
      .then(r => (r.ok ? r.json() : null))
      .then(data => {
        setModule(data);
        setLoaded(true);
      })
      .catch(() => setLoaded(true));
  }, [slug, locale]);

  const otherModules = Object.entries(MODULES)
    .filter(([s]) => s !== slug)
    .map(([, m]) => m);

  const handleTalkToMe = () => {
    if (module) {
      window.dispatchEvent(new CustomEvent('openModuleChat', {
        detail: {slug: module.slug, greeting: module.greeting},
      }));
    }
  };

  // Autoplay muted; when it ends, wait 15s and play again (cyclic).
  const handleVideoEnd = () => {
    if (replayTimer.current) clearTimeout(replayTimer.current);
    replayTimer.current = setTimeout(() => {
      const v = videoRef.current;
      if (v) {
        v.currentTime = 0;
        v.play().catch(() => {});
      }
    }, 15000);
  };

  useEffect(() => () => {
    if (replayTimer.current) clearTimeout(replayTimer.current);
  }, []);

  if (!loaded) {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="cyber-frame">
          <div className={`cyber-frame-body px-8 py-5 font-mono tracking-[0.2em] animate-pulse ${c.eyebrow}`}>
            {t('loading')}
          </div>
        </div>
      </main>
    );
  }

  if (!module) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] gap-4">
        <p className="font-mono text-zinc-400">{t('notFound')}</p>
        <Link href="/" className="cyber-btn btn-ghost px-6 py-3 text-sm font-bold">
          {t('backHome')}
        </Link>
      </div>
    );
  }

  // Split the terminal intro: first line = title, rest = narrative description.
  const initParts = (module.init_text || '').split(/\n\s*\n/);
  const initTitle = initParts[0] || '';
  const initDesc = initParts.slice(1).join('\n') || module.description || '';

  // Module name in two tones: first word white, the rest in the module color.
  const nameParts = meta.name.split(' ');
  const nameFirst = nameParts[0];
  const nameRest = nameParts.slice(1).join(' ');

  return (
    <main className="relative">
      {/* ============ HEADER (contacts style, tinted by module color) ============ */}
      <section className="px-4 pt-8 pb-6">
        <div className="max-w-7xl mx-auto">
          <div className={`mb-12 border-b ${c.border} pb-6`}>
            <div className={`inline-flex items-center gap-2 font-mono text-xs leading-none tracking-[0.25em] ${c.eyebrow}`}>
              <Radio className="w-3.5 h-3.5 animate-pulse" />
              <span>{t('terminalAccess')}</span>
            </div>
            <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
              <div>
                <h1 className="-mt-1.5 text-4xl sm:text-5xl font-display font-black tracking-wide">
                  <span className="text-white">{nameFirst}</span>
                  {nameRest && <>{' '}<span className={c.h1accent}>{nameRest}</span></>}
                </h1>
              </div>
              <p className="text-zinc-300 font-mono text-xs sm:text-sm max-w-md md:text-right leading-relaxed">
                {initDesc}
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ============ VIDEO + COMPETENCIES ============ */}
      <section className="px-4 py-8">
        <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-[auto_1fr] gap-10 lg:gap-12 items-start lg:items-stretch lg:h-[604px]">
          {/* Video card — 9:16, beveled (cut) corners, flush left, autoplay
              muted, 15s cyclic replay; competencies card matches its height */}
          <div className="flex flex-col items-start">
            <div
              className={`w-full max-w-[340px] lg:w-[340px] bg-[#0a0f1f] border ${c.frame} ${c.shadow}`}
              style={{
                aspectRatio: '9 / 16',
                clipPath: 'polygon(16px 0, 100% 0, 100% calc(100% - 16px), calc(100% - 16px) 100%, 0 100%, 0 16px)',
              }}
            >
              {module.video_url ? (
                isVideoFile(module.video_url) ? (
                  <video
                    ref={videoRef}
                    src={module.video_url}
                    autoPlay
                    muted
                    controls
                    playsInline
                    onEnded={handleVideoEnd}
                    className="w-full h-full object-cover bg-black"
                  />
                ) : (
                  <iframe
                    src={module.video_url}
                    className="w-full h-full border-0"
                    allow="autoplay; encrypted-media"
                    title={`${meta.name} — video`}
                  />
                )
              ) : (
                <div className="w-full h-full flex items-center justify-center">
                  <span className="font-mono text-xs text-zinc-600 tracking-widest">
                    {t('noVideo')}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Competencies card — wider than the video, no internal scroll,
              same height as the video on desktop */}
          <div className="cyber-frame w-full lg:h-full">
            <div className="cyber-frame-body p-6 h-full">
              <span className="cb cb-tl" />
              <span className="cb cb-br" />
              <div className={`font-mono text-sm sm:text-base tracking-[0.2em] ${c.eyebrow} mb-4 font-bold`}>
                {meta.name} // {t('competencies')}
              </div>
              <div className="text-zinc-300 font-mono text-xs sm:text-sm leading-relaxed whitespace-pre-wrap">
                {module.skills_text}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ============ SHUTDOWN + TALK + NEXT MODULE ============ */}
      <section className="px-4 pb-16">
        <div className="max-w-4xl mx-auto flex flex-col items-center gap-8">
          <div className="font-mono text-sm text-zinc-400 text-center leading-relaxed whitespace-pre-wrap max-w-2xl">
            {module.shutdown_text}
          </div>

          <button
            onClick={handleTalkToMe}
            className="cyber-btn btn-primary px-10 py-4 font-display font-bold text-sm tracking-[0.16em] cursor-pointer"
          >
            {t('talkToMe')}
          </button>

          <div className="flex flex-col items-center gap-3">
            <span className="font-mono text-xs text-zinc-500 tracking-[0.2em]">
              {t('chooseNext')}
            </span>
            <div className="flex flex-wrap justify-center gap-3">
              {otherModules.map(m => (
                <Link
                  key={m.name}
                  href={`/modules/${Object.keys(MODULES).find(k => MODULES[k] === m)}`}
                  className="cyber-btn btn-ghost px-5 py-2.5 text-xs font-mono tracking-wider"
                >
                  {m.label}
                </Link>
              ))}
            </div>
          </div>
        </div>
      </section>
    </main>
  );
}