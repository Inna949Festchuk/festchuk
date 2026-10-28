'use client';

import {useTranslations} from 'next-intl';
import {Link} from '@/i18n/navigation';
import {Radio, ArrowLeft} from 'lucide-react';

export default function NotFound() {
  const t = useTranslations('notFound');

  return (
    <main className="min-h-screen flex flex-col items-center justify-center gap-6 px-4 text-center">
      <div className="inline-flex items-center gap-2 font-mono text-xs tracking-[0.28em] text-neon-magenta mb-2">
        <Radio className="w-3.5 h-3.5 animate-pulse" />
        <span>{t('code')}</span>
      </div>
      <h1 className="text-5xl sm:text-6xl font-display font-black tracking-wide">
        <span className="text-white">{t('title')}</span>
      </h1>
      <p className="text-zinc-300 font-mono text-xs sm:text-sm max-w-md">{t('desc')}</p>
      <Link
        href="/"
        className="cyber-btn btn-primary px-6 py-3 text-xs font-bold mt-2"
      >
        <ArrowLeft className="w-4 h-4" />
        <span>{t('home')}</span>
      </Link>
    </main>
  );
}