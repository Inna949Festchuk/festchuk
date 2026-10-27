import Link from 'next/link';
import { Hexagon, Triangle, Circle } from 'lucide-react';

/**
 * Глобальный футер — рендерится в layout на каждой странице.
 * Прижат к самому низу (sticky footer), а нижняя зона pb-24
 * отведена под плавающий HUD (музыкальный плеер слева / чат справа),
 * чтобы они не перекрывали строку контента футера.
 */
export default function Footer() {
  return (
    <footer className="relative shrink-0 border-t border-cyber-border bg-[#050814]/85 backdrop-blur-md px-4 pt-6 pb-24">
      <div className="max-w-7xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4 md:gap-5">
        <div className="text-[11px] text-zinc-400 font-mono tracking-wider text-center md:text-left">
          © {new Date().getFullYear()} FESTCHUK CORP. ALL RIGHTS RESERVED.
        </div>
        <div className="flex gap-7 text-xs font-display font-bold text-zinc-300 tracking-[0.2em]">
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
          <Triangle className="w-4 h-4 text-neon-magenta" />
          <Circle className="w-4 h-4 text-acid-yellow" />
        </div>
      </div>
    </footer>
  );
}
