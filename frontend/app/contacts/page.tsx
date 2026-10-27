'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import {
  Mail,
  Send,
  Github,
  Copy,
  Check,
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
      title: 'Email',
      value: EMAIL,
      href: `mailto:${EMAIL}`,
      action: 'copy',
      color: 'neon-cyan',
    },
    {
      icon: Send,
      title: 'Telegram',
      value: '@festchuk',
      href: TELEGRAM,
      action: 'link',
      color: 'neon-purple',
    },
    {
      icon: Github,
      title: 'GitHub',
      value: 'Inna949Festchuk',
      href: GITHUB,
      action: 'link',
      color: 'acid-yellow',
    },
  ];

  return (
    <main className="min-h-screen px-4 py-12">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-display font-bold mb-4">
          <span className="text-foreground">Связаться</span>{' '}
          <span className="text-neon-cyan text-glow-cyan">со мной</span>
        </h1>
        <p className="text-zinc-500 mb-12">
          Открыт к интересным проектам, консультациям и сотрудничеству
        </p>

        <div className="space-y-4">
          {contactCards.map((card, i) => (
            <motion.div
              key={card.title}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
              className={`glass-card rounded-xl p-6 flex items-center gap-4 group ${
                card.action === 'copy' ? 'cursor-pointer' : ''
              }`}
              onClick={card.action === 'copy' ? copyEmail : undefined}
            >
              <div className={`p-3 rounded-lg bg-${card.color}/10 border border-${card.color}/20`}>
                <card.icon className={`w-6 h-6 text-${card.color}`} />
              </div>

              <div className="flex-1 min-w-0">
                <div className="text-sm text-zinc-500">{card.title}</div>
                <div className="text-lg font-medium text-foreground truncate">
                  {card.value}
                </div>
              </div>

              <div className="flex gap-2">
                {card.action === 'copy' && (
                  <button
                    className={`p-2 rounded-lg border transition-colors ${
                      copied
                        ? 'border-neon-cyan text-neon-cyan'
                        : 'border-zinc-700 text-zinc-500 hover:border-zinc-500'
                    }`}
                    title="Копировать email"
                  >
                    {copied ? (
                      <Check className="w-4 h-4" />
                    ) : (
                      <Copy className="w-4 h-4" />
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
                  className="p-2 rounded-lg border border-zinc-700 text-zinc-500 hover:border-zinc-500 hover:text-zinc-300 transition-colors"
                  title={card.action === 'link' ? 'Открыть' : 'Написать'}
                >
                  {card.action === 'copy' ? (
                    <Mail className="w-4 h-4" />
                  ) : (
                    <Send className="w-4 h-4" />
                  )}
                </a>
              </div>
            </motion.div>
          ))}
        </div>

        <div className="mt-16 glass-card rounded-xl p-8">
          <h2 className="text-xl font-display font-semibold text-foreground mb-4">
            Как быстро связаться
          </h2>
          <ul className="space-y-3 text-zinc-400">
            <li className="flex items-start gap-3">
              <span className="text-neon-cyan font-mono">01</span>
              Для сотрудничества и проектов — Email или Telegram
            </li>
            <li className="flex items-start gap-3">
              <span className="text-neon-purple font-mono">02</span>
              Для технических вопросов — GitHub Issues
            </li>
            <li className="flex items-start gap-3">
              <span className="text-acid-yellow font-mono">03</span>
              Отвечаю в течение 24 часов
            </li>
          </ul>
        </div>
      </div>
    </main>
  );
}
