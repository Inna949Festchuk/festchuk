import type { Metadata } from 'next';
import './globals.css';
import Header from '@/components/Header';
import ChatWidget from '@/components/ChatWidget';
import Cityscape from '@/components/Cityscape';
import CyberMusicPlayer from '@/components/CyberMusicPlayer';

export const metadata: Metadata = {
  title: 'Константин Фестчук — AI-Driven Fullstack Developer',
  description: 'Персональный сайт-портфолио: проекты, блог, AI-ассистент. Киберпанк-стиль.',
  keywords: ['portfolio', 'fullstack', 'django', 'nextjs', 'ai', 'cyberpunk'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="ru" className="dark">
      <body className="antialiased">
        <div className="cyber-grid-bg" />
        <div className="bg-beams" />
        <div className="bg-horizon" />
        <Cityscape />
        <div className="scanline-overlay" />
        <Header />
        <div className="pt-16 pb-24">{children}</div>
        <CyberMusicPlayer />
        <ChatWidget />
      </body>
    </html>
  );
}
