'use client';

import {useTranslations} from 'next-intl';
import {Link} from '@/i18n/navigation';
import {Hexagon, Triangle, Circle} from 'lucide-react';

/**
 * Глобальный футер — рендерится в layout на каждой странице.
 * Тонкая полоса, прижатая к самому низу (sticky footer).
 * Плеер и чат плавают ВЫШЕ футера (в отступе pb-24 обёртки
 * контента в layout), не перекрывая ни футер, ни контент.
 */
export default function Footer() {
  const t = useTranslations('footer');

  return (
    <footer className="relative shrink-0 border-t border-cyber-border bg-[#050814]/85 backdrop-blur-md px-4 py-4">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 md:gap-5">
        <div className="text-[11px] text-zinc-400 font-mono tracking-wider text-center md:text-left">
          {t('rights', {year: new Date().getFullYear()})}
        </div>
        <div className="flex gap-7 text-xs font-display font-bold text-zinc-300 tracking-[0.2em]">
          <Link href="/projects" className="hover:text-neon-cyan transition-colors">
            {t('projects')}
          </Link>
          <Link href="/blog" className="hover:text-neon-cyan transition-colors">
            {t('blog')}
          </Link>
          <Link href="/contacts" className="hover:text-neon-cyan transition-colors">
            {t('contact')}
          </Link>
        </div>
        <div className="flex gap-3 items-center">
          <Hexagon className="w-4 h-4 text-neon-cyan" />
          <Triangle className="w-4 h-4 text-neon-magenta" />
          <Circle className="w-4 h-4 text-acid-yellow" />
        </div>
      </div>
    </footer>
  );
}