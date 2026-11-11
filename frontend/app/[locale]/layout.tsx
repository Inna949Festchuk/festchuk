import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {Geologica, Inter, JetBrains_Mono} from 'next/font/google';
import {NextIntlClientProvider} from 'next-intl';
import {getMessages, getTranslations, setRequestLocale} from 'next-intl/server';
import '../globals.css';
import Header from '@/components/Header';
import ChatWidget from '@/components/ChatWidget';
import HudBottomGuard from '@/components/HudBottomGuard';
import Cityscape from '@/components/Cityscape';
import CyberMusicPlayer from '@/components/CyberMusicPlayer';
import Footer from '@/components/Footer';
import {locales} from '@/i18n/routing';

// Self-hosted fonts (next/font): downloaded at compile time inside the
// container and served from /_next/static/media — the browser no longer
// depends on fonts.googleapis.com at runtime (unstable DNS/network).
// Geologica covers both latin and cyrillic (variable 100–900), so RU/EN
// versions stay identical; bold weights (700–900) are the display look.
const geologica = Geologica({
  subsets: ['latin', 'cyrillic'],
  weight: ['500', '600', '700', '800', '900'],
  variable: '--font-display',
  display: 'swap',
});
const inter = Inter({
  subsets: ['latin', 'cyrillic'],
  variable: '--font-inter',
  display: 'swap',
});
const jbMono = JetBrains_Mono({
  subsets: ['latin', 'cyrillic'],
  variable: '--font-jbmono',
  display: 'swap',
});

export function generateStaticParams() {
  return locales.map((locale) => ({locale}));
}

export async function generateMetadata({
  params,
}: {
  params: {locale: string};
}): Promise<Metadata> {
  const t = await getTranslations({locale: params.locale, namespace: 'meta'});
  return {
    title: t('title'),
    description: t('description'),
    keywords: t.raw('keywords') as string[],
    alternates: {
      languages: {
        ru: '/ru',
        en: '/en',
      },
    },
  };
}

export default async function LocaleLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: {locale: string};
}) {
  const {locale} = params;
  if (!locales.includes(locale as (typeof locales)[number])) {
    notFound();
  }

  // Enable static rendering for this locale.
  setRequestLocale(locale);

  const messages = await getMessages();

  return (
    <html lang={locale} className={`dark ${geologica.variable} ${inter.variable} ${jbMono.variable}`}>
      <body className="antialiased flex min-h-screen flex-col">
        <NextIntlClientProvider locale={locale} messages={messages}>
          <div className="cyber-grid-bg" />
          <div className="bg-beams" />
          <div className="bg-horizon" />
          <Cityscape />
          <div className="scanline-overlay" />
          <Header />
          <div className="flex-1 pt-16 pb-24">{children}</div>
          <Footer />
          <CyberMusicPlayer />
          <ChatWidget />
          <HudBottomGuard />
        </NextIntlClientProvider>
      </body>
    </html>
  );
}