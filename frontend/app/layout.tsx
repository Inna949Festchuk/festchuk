import type { Metadata } from 'next';
import './globals.css';
import Header from '@/components/Header';
import ChatWidget from '@/components/ChatWidget';
import Cityscape from '@/components/Cityscape';
import CyberMusicPlayer from '@/components/CyberMusicPlayer';
import Footer from '@/components/Footer';

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
      <body className="antialiased flex min-h-screen flex-col">
        <div className="cyber-grid-bg" />
        <div className="bg-beams" />
        <div className="bg-horizon" />
        <Cityscape />
        <div className="scanline-overlay" />
        <Header />
        <div className="flex-1 pt-16">{children}</div>
        <Footer />
        <CyberMusicPlayer />
        <ChatWidget />
      </body>
    </html>
  );
}
