'use client';

import {useEffect, useState} from 'react';
import {useTranslations} from 'next-intl';
import {Radio, Mail, Send, ShieldCheck, Database, Eraser, Globe} from 'lucide-react';

/**
 * Политика приватности (152-ФЗ). Статическая страница: весь контент —
 * в messages (privacy namespace), срок хранения берётся из API
 * (retention_hours из конфига бэкенда), чтобы текст не дрифтнул от TTL.
 * Без появляющихся анимаций (UI-инвариант проекта).
 */
export default function PrivacyPage() {
  const t = useTranslations('privacy');
  const [retentionHours, setRetentionHours] = useState<number | null>(null);

  useEffect(() => {
    fetch('/api/chat/session/')
      .then((r) => (r.ok ? r.json() : null))
      .then((data) => {
        if (data && typeof data.retention_hours === 'number') {
          setRetentionHours(data.retention_hours);
        }
      })
      .catch(() => {});
  }, []);

  const hours = retentionHours ?? 4;

  const sections = [
    {
      icon: ShieldCheck,
      hex: 'hex-cyan',
      code: t('sOperator'),
      body: <p className="text-sm text-zinc-300">{t('operatorText')}</p>,
    },
    {
      icon: Globe,
      hex: 'hex-purple',
      code: t('sProcessing'),
      body: (
        <ul className="space-y-2.5 text-sm text-zinc-300 list-disc pl-5">
          <li>{t('processing1')}</li>
          <li>{t('processing2')}</li>
          <li>{t('processing3')}</li>
        </ul>
      ),
    },
    {
      icon: Database,
      hex: 'hex-cyan',
      code: t('sStorage'),
      body: <p className="text-sm text-zinc-300">{t('storageText', {hours})}</p>,
    },
    {
      icon: ShieldCheck,
      hex: 'hex-purple',
      code: t('sPii'),
      body: <p className="text-sm text-zinc-300">{t('piiText')}</p>,
    },
    {
      icon: Radio,
      hex: 'hex-cyan',
      code: t('sExternal'),
      body: <p className="text-sm text-zinc-300">{t('externalText')}</p>,
    },
    {
      icon: Eraser,
      hex: 'hex-purple',
      code: t('sDeletion'),
      body: <p className="text-sm text-zinc-300">{t('deletionText')}</p>,
    },
    {
      icon: Mail,
      hex: 'hex-cyan',
      code: t('sContacts'),
      body: (
        <div className="space-y-2.5 text-sm">
          <a
            href="mailto:festchuk@yandex.ru"
            className="flex items-center gap-2 text-zinc-300 hover:text-neon-cyan transition-colors"
          >
            <Mail className="w-4 h-4 shrink-0" />
            <span>{t('contactEmail')}</span>
          </a>
          <a
            href="https://t.me/Dilmah949"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-zinc-300 hover:text-neon-cyan transition-colors"
          >
            <Send className="w-4 h-4 shrink-0" />
            <span>{t('contactTelegram')}</span>
          </a>
        </div>
      ),
    },
  ];

  return (
    <main className="min-h-screen px-4 py-12">
      <div className="max-w-5xl mx-auto">
        <div className="mb-10 border-b border-neon-cyan/20 pb-6">
          <div className="inline-flex items-center gap-2 font-mono text-xs tracking-[0.25em] text-neon-cyan mb-2">
            <Radio className="w-3.5 h-3.5" />
            <span>{t('headerCode')}</span>
          </div>
          <div className="flex flex-col md:flex-row md:items-end justify-between gap-6">
            <div>
              <h1 className="text-4xl sm:text-5xl font-display font-black tracking-wide">
                <span className="text-white">{t('title1')}</span>{' '}
                <span className="text-neon-cyan text-glow-cyan">{t('title2')}</span>
              </h1>
            </div>
            <p className="text-zinc-300 font-mono text-xs sm:text-sm max-w-md md:text-right">
              {t('headerDesc')}
            </p>
          </div>
        </div>

        <div className="space-y-4">
          {sections.map((section) => (
            <div key={section.code} className="cyber-frame">
              <div className="cyber-frame-body p-6 flex items-start gap-5 relative">
                <span className="cb cb-tl" />
                <span className="cb cb-br" />
                <div className={`hex-icon ${section.hex} shrink-0`}>
                  <section.icon className="w-5 h-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <div className="font-mono text-[10px] tracking-[0.22em] text-neon-cyan mb-2">
                    {section.code}
                  </div>
                  {section.body}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
