'use client';

import {useLocale} from 'next-intl';
import {usePathname, useRouter} from '@/i18n/navigation';
import {locales} from '@/i18n/routing';

export default function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const pathname = usePathname();

  const switchLocale = (next: string) => {
    if (next === locale) return;
    router.replace(pathname, {locale: next});
  };

  return (
    <div
      className="flex items-center gap-1 p-1 border border-cyber-border bg-[#070c1c]/70"
      role="group"
      aria-label="Language"
    >
      {locales.map((l) => {
        const active = l === locale;
        return (
          <button
            key={l}
            type="button"
            onClick={() => switchLocale(l)}
            aria-pressed={active}
            className={`px-2 py-1 font-mono text-[10px] tracking-[0.18em] transition-all ${
              active
                ? 'text-neon-cyan bg-neon-cyan/15 border border-neon-cyan/50 shadow-[0_0_10px_rgba(0,243,255,0.25)]'
                : 'text-zinc-400 border border-transparent hover:text-white hover:bg-white/5'
            }`}
          >
            {l.toUpperCase()}
          </button>
        );
      })}
    </div>
  );
}