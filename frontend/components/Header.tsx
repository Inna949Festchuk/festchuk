'use client';

import {useState, useEffect} from 'react';
import {useTranslations} from 'next-intl';
import {usePathname, Link} from '@/i18n/navigation';
import {motion, AnimatePresence} from 'framer-motion';
import {Menu, X} from 'lucide-react';
import LanguageSwitcher from '@/components/LanguageSwitcher';

const navLinks = [
  {href: '/', key: 'home'},
  {href: '/projects', key: 'projects'},
  {href: '/blog', key: 'blog'},
  {href: '/contacts', key: 'contacts'},
] as const;

export default function Header() {
  const t = useTranslations('nav');
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  // Normalize trailing slashes (site uses trailingSlash: true)
  const norm = (p: string) => p.replace(/\/+$/, '') || '/';

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 12);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-[#050814]/90 backdrop-blur-lg border-b border-neon-cyan/30 shadow-[0_4px_30px_rgba(0,0,0,0.65)]'
          : 'bg-[#050814]/65 backdrop-blur-md border-b border-cyber-border/70'
      }`}
    >
      <nav className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <span className="relative w-9 h-9 grid place-items-center">
            <span className="absolute inset-0 hex-icon !w-9 !h-9 hex-cyan group-hover:scale-105 transition-transform" />
            <span className="relative font-display font-black text-neon-cyan text-sm">
              F
            </span>
          </span>
          <div className="flex flex-col">
            <span className="font-display font-black text-white text-lg tracking-widest leading-none">
              FESTCHUK
              <span className="text-neon-cyan">.DEV</span>
            </span>
            <span className="font-mono text-[9px] tracking-[0.24em] text-zinc-400 mt-0.5">
              NEURAL GRID // v2.6
            </span>
          </div>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-2">
          {navLinks.map((link) => {
            const active =
              norm(link.href) === '/'
                ? norm(pathname) === '/'
                : norm(pathname).startsWith(norm(link.href));
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`relative px-4 py-2 flex items-center gap-2 font-display text-xs font-bold tracking-[0.18em] transition-all ${
                  active
                    ? 'text-neon-cyan bg-neon-cyan/10 border border-neon-cyan/40 shadow-[0_0_16px_rgba(0,243,255,0.2)]'
                    : 'text-zinc-300 hover:text-white border border-transparent hover:border-neon-cyan/25 hover:bg-white/5'
                }`}
                style={{
                  clipPath:
                    'polygon(7px 0, 100% 0, 100% calc(100% - 7px), calc(100% - 7px) 100%, 0 100%, 0 7px)',
                }}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    active ? 'bg-neon-cyan shadow-[0_0_8px_#00F3FF]' : 'bg-[#22c55e]'
                  }`}
                />
                <span>{t(link.key)}</span>
              </Link>
            );
          })}
        </div>

        {/* Right: language */}
        <div className="hidden md:flex items-center gap-3">
          <LanguageSwitcher />
        </div>

        {/* Mobile toggle */}
        <button
          type="button"
          className="md:hidden p-2 text-zinc-300 hover:text-neon-cyan border border-cyber-border"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label={t('menu')}
        >
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{opacity: 0, height: 0}}
            animate={{opacity: 1, height: 'auto'}}
            exit={{opacity: 0, height: 0}}
            className="md:hidden bg-[#060912]/95 backdrop-blur-lg border-b border-neon-cyan/30 overflow-hidden"
          >
            <div className="px-4 py-4 space-y-1.5">
              <div className="flex justify-end mb-1">
                <LanguageSwitcher />
              </div>
              {navLinks.map((link) => {
                const active =
                  norm(link.href) === '/'
                    ? norm(pathname) === '/'
                    : norm(pathname).startsWith(norm(link.href));
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center justify-between px-4 py-3 text-xs font-display font-bold tracking-[0.18em] transition-colors ${
                      active
                        ? 'bg-neon-cyan/15 text-neon-cyan border border-neon-cyan/40'
                        : 'text-zinc-300 hover:text-white hover:bg-white/5 border border-transparent'
                    }`}
                  >
                    <span className="flex items-center gap-3">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          active ? 'bg-neon-cyan' : 'bg-[#22c55e]'
                        }`}
                      />
                      {t(link.key)}
                    </span>
                    <span className="font-mono text-[10px] text-zinc-500">
                      {link.href === '/'
                        ? 'HOME'
                        : link.href.replace(/^\//, '').toUpperCase()}
                    </span>
                  </Link>
                );
              })}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}