import type {Metadata} from 'next';
import {notFound} from 'next/navigation';
import {NextIntlClientProvider} from 'next-intl';
import {getMessages, getTranslations, setRequestLocale} from 'next-intl/server';
import '../globals.css';
import Header from '@/components/Header';
import ChatWidget from '@/components/ChatWidget';
import Cityscape from '@/components/Cityscape';
import CyberMusicPlayer from '@/components/CyberMusicPlayer';
import Footer from '@/components/Footer';
import {locales} from '@/i18n/routing';

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
    <html lang={locale} className="dark">
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
        </NextIntlClientProvider>
      </body>
    </html>
  );
}