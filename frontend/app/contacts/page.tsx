'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Mail,
  Send,
  Github,
  Copy,
  Check,
  Radio,
  ArrowUpRight,
} from 'lucide-react';

const EMAIL = 'contact@festchuk.dev';
const TELEGRAM = 'https://t.me/festchuk';
const GITHUB = 'https://github.com/Inna949Festchuk';

export default function ContactsPage() {
  const [copied, setCopied] = useState(false);

  const copyEmail = async () => {
    try {
      await navigator.clipboard.writeText(EMAIL);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {}
  };

  const contactCards = [
    {
      icon: Mail,
      code: 'CHANNEL 01 // DIRECT MAIL',
      title: 'Email',
      value: EMAIL,
      href: `mailto:${EMAIL}`,
      action: 'copy',
      hex: 'hex-cyan',
    },
    {
      icon: Send,
      code: 'CHANNEL 02 // ENCRYPTED CHAT',
      title: 'Telegram',
      value: '@festchuk',
      href: TELEGRAM,
      action: 'link',
      hex: 'hex-purple',
    },
    {
      icon: Github,
      code: 'CHANNEL 03 // CODE REPOSITORIES',
      title: 'GitHub',
      value: 'Inna949Festchuk',
      href: GITHUB,
      action: 'link',
      hex: 'hex-cyan',
    },
  ];

  return (
    <main className="min-h-screen px-4 py-12">
      <div className="max-w-4xl mx-auto">
        <div className="mb-10 border-b border-neon-cyan/20 pb-6">
          <div className="inline-flex items-center gap-2 font-mono text-xs tracking-[0.25em] text-neon-cyan mb-2">
            <Radio className="w-3.5 h-3.5 animate-pulse" />
            <span>UPLINK // COMMUNICATION TERMINALS</span>
          </div>
          <h1 className="text-4xl sm:text-5xl font-display font-black tracking-wide mb-3">
            <span className="text-white">СВЯЗАТЬСЯ</span>{' '}
            <span className="text-neon-cyan text-glow-cyan">СО МНОЙ</span>
          </h1>
          <p className="text-zinc-300 font-mono text-xs sm:text-sm max-w-xl">
            Открыт к сложным инженерным задачам, разработке AI-систем, архитектуре и техническому консалтингу.
          </p>
        </div>

        <div className="space-y-4">
          {contactCards.map((card, i) => (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`cyber-frame group ${card.action === 'copy' ? 'cursor-pointer' : ''}`}
              onClick={card.action === 'copy' ? copyEmail : undefined}
            >
              <div className="cyber-frame-body p-6 flex flex-col sm:flex-row sm:items-center gap-5 relative">
                <span className="cb cb-tl" />
                <span className="cb cb-br" />

                <div className={`hex-icon ${card.hex} shrink-0`}>
                  <card.icon className="w-6 h-6" />
                </div>

                <div className="flex-1 min-w-0">
                  <div className="font-mono text-[10px] tracking-[0.22em] text-neon-cyan mb-1">
                    {card.code}
                  </div>
                  <div className="text-xs text-zinc-400">{card.title}</div>
                  <div className="text-lg sm:text-xl font-display font-bold text-white truncate group-hover:text-neon-cyan transition-colors">
                    {card.value}
                  </div>
                </div>

                <div className="flex flex-wrap gap-2.5 shrink-0">
                  {card.action === 'copy' && (
                    <button
                      type="button"
                      className={`cyber-btn px-4 py-2.5 text-xs font-bold ${
                        copied ? 'btn-primary' : 'btn-ghost'
                      }`}
                      title="Скопировать email"
                    >
                      {copied ? (
                        <>
                          <Check className="w-4 h-4" />
                          <span>СКОПИРОВАНО</span>
                        </>
                      ) : (
                        <>
                          <Copy className="w-4 h-4" />
                          <span>КОПИРОВАТЬ</span>
                        </>
                      )}
                    </button>
                  )}
                  <a
                    href={card.href}
                    target={card.action === 'link' ? '_blank' : undefined}
                    rel={card.action === 'link' ? 'noopener noreferrer' : undefined}
                    onClick={(e) => {
                      if (card.action === 'copy') e.stopPropagation();
                    }}
                    className="cyber-btn btn-primary px-5 py-2.5 text-xs font-bold"
                    title={card.action === 'link' ? 'Открыть канал' : 'Написать письмо'}
                  >
                    <span>{card.action === 'copy' ? 'НАПИСАТЬ' : 'ОТКРЫТЬ'}</span>
                    <ArrowUpRight className="w-4 h-4" />
                  </a>
                </div>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="mt-10 cyber-frame">
          <div className="cyber-frame-body p-6 md:p-8 relative">
            <span className="cb cb-tl" />
            <span className="cb cb-br" />
            <div className="font-mono text-xs tracking-[0.24em] text-neon-magenta mb-2">
              // PROTOCOL GUIDELINES
            </div>
            <h2 className="text-xl font-display font-bold text-white mb-5">
              РЕГЛАМЕНТ СВЯЗИ
            </h2>
            <ul className="space-y-3.5 text-sm text-zinc-300">
              <li className="flex items-start gap-3">
                <span className="px-2 py-0.5 text-xs font-mono bg-neon-cyan/15 text-neon-cyan border border-neon-cyan/40">
                  01
                </span>
                <span>Для коммерческих проектов и архитектуры — Telegram или Email.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="px-2 py-0.5 text-xs font-mono bg-neon-purple/15 text-neon-purple border border-neon-purple/40">
                  02
                </span>
                <span>Для вопросов по коду и open-source — GitHub Issues / Pull Requests.</span>
              </li>
              <li className="flex items-start gap-3">
                <span className="px-2 py-0.5 text-xs font-mono bg-acid-yellow/15 text-acid-yellow border border-acid-yellow/40">
                  03
                </span>
                <span>Среднее время отклика по прямым каналам — менее 24 часов.</span>
              </li>
            </ul>
          </div>
        </div>
      </div>
    </main>
  );
}
