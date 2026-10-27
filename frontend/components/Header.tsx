'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { Menu, X, User } from 'lucide-react';

const navLinks = [
  { href: '/', label: 'HOME' },
  { href: '/projects', label: 'PROJECTS' },
  { href: '/blog', label: 'BLOG' },
  { href: '/contacts', label: 'CONTACT' },
];

export default function Header() {
  const [scrolled, setScrolled] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const pathname = usePathname();
  // Normalize trailing slashes (site uses trailingSlash: true)
  const norm = (p: string) => p.replace(/\/+$/, '') || '/';

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 20);
    window.addEventListener('scroll', onScroll);
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        scrolled
          ? 'bg-[#060912]/85 backdrop-blur-md border-b border-cyber-border'
          : 'bg-transparent'
      }`}
    >
      <nav className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-3 group">
          <span className="relative w-9 h-9 grid place-items-center">
            <span className="absolute inset-0 hex-icon !w-9 !h-9 hex-cyan" />
            <span className="relative font-display font-black text-neon-cyan text-sm">
              F
            </span>
          </span>
          <span className="font-display font-black text-foreground text-xl tracking-widest">
            FESTCHUK
            <span className="text-neon-cyan">.DEV</span>
          </span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden md:flex items-center gap-8">
          {navLinks.map(link => {
            const active = norm(pathname) === norm(link.href);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`flex items-center gap-2 text-xs font-semibold tracking-[0.2em] transition-colors ${
                  active ? 'text-neon-cyan' : 'text-zinc-400 hover:text-foreground'
                }`}
              >
                <span
                  className={`w-1.5 h-1.5 rounded-full ${
                    active ? 'bg-neon-cyan shadow-[0_0_8px_#00F3FF]' : 'bg-[#22c55e]'
                  }`}
                />
                {link.label}
              </Link>
            );
          })}
        </div>

        {/* Right: user + JACK IN */}
        <div className="hidden md:flex items-center gap-3">
          <span className="p-2 text-zinc-500">
            <User className="w-5 h-5" />
          </span>
          <Link
            href="/contacts"
            className="cyber-btn btn-primary px-6 py-2.5 font-display font-bold text-xs tracking-[0.2em]"
          >
            JACK IN
          </Link>
        </div>

        {/* Mobile toggle */}
        <button
          className="md:hidden p-2 text-zinc-400 hover:text-foreground"
          onClick={() => setMobileOpen(!mobileOpen)}
          aria-label="Меню"
        >
          {mobileOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6" />}
        </button>
      </nav>

      {/* Mobile menu */}
      <AnimatePresence>
        {mobileOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="md:hidden bg-[#060912]/95 backdrop-blur-md border-b border-cyber-border overflow-hidden"
          >
            <div className="px-4 py-4 space-y-1">
              {navLinks.map(link => {
                const active = norm(pathname) === norm(link.href);
                return (
                  <Link
                    key={link.href}
                    href={link.href}
                    onClick={() => setMobileOpen(false)}
                    className={`flex items-center gap-3 px-4 py-3 text-sm font-semibold tracking-[0.15em] transition-colors ${
                      active
                        ? 'bg-neon-cyan/10 text-neon-cyan'
                        : 'text-zinc-400 hover:text-foreground hover:bg-white/5'
                    }`}
                  >
                    <span
                      className={`w-1.5 h-1.5 rounded-full ${
                        active ? 'bg-neon-cyan' : 'bg-[#22c55e]'
                      }`}
                    />
                    {link.label}
                  </Link>
                );
              })}
              <Link
                href="/contacts"
                onClick={() => setMobileOpen(false)}
                className="cyber-btn btn-primary px-6 py-3 mt-3 text-center font-display font-bold text-xs tracking-[0.2em]"
              >
                JACK IN
              </Link>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
}
