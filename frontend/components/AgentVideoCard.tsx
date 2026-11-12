'use client';

import {useRef, useState, useEffect, useCallback} from 'react';
import Image from 'next/image';
import {Link} from '@/i18n/navigation';
import {useTranslations} from 'next-intl';

type CardState = 'idle' | 'loading' | 'playing' | 'glitch';

interface AgentVideoCardProps {
  name: string;
  image: string;
  video: string;
  slug: string;
  active: boolean;
  onComplete?: () => void;
  onActivate?: () => void;
}

/**
 * Agent "demo" card.
 *
 * idle    — continuous white-noise + "SIGNAL LOST" (image barely visible)
 * loading — cyberpunk progress bar 0→100% (only when it's this card's turn)
 * playing — muted video
 * glitch  — 0.8 s RGB-split + shake, then back to idle
 *
 * Triggers:
 *  – hover  → onActivate() tells the parent "I'm the current card"; the
 *             previously active card is interrupted (glitch → idle).
 *  – auto-cycle → parent sets `active` on the current card; `onComplete`
 *             fires on natural end so the parent can advance.
 */
export default function AgentVideoCard({
  name,
  image,
  video,
  slug,
  active,
  onComplete,
  onActivate,
}: AgentVideoCardProps) {
  const t = useTranslations('home');
  const [state, setState] = useState<CardState>('idle');
  const [progress, setProgress] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const isRunningRef = useRef(false);

  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  const onActivateRef = useRef(onActivate);
  useEffect(() => {
    onActivateRef.current = onActivate;
  }, [onActivate]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((tm) => clearTimeout(tm));
    timersRef.current = [];
  }, []);

  /**
   * Transition to glitch, then idle.
   * @param natural — true when the video ended naturally (call onComplete to
   *                  advance the cycle); false when interrupted (no advance).
   */
  const finishSequence = useCallback((natural: boolean) => {
    clearTimers();
    setState('glitch');
    timersRef.current.push(
      setTimeout(() => {
        setState('idle');
        setProgress(0);
        isRunningRef.current = false;
        if (natural) onCompleteRef.current?.();
      }, 800),
    );
  }, [clearTimers]);

  const startSequence = useCallback(() => {
    if (isRunningRef.current) return;
    isRunningRef.current = true;
    clearTimers();

    setState('loading');
    setProgress(0);

    let p = 0;
    const loadInterval = setInterval(() => {
      p += Math.floor(Math.random() * 15) + 8;
      if (p >= 100) {
        p = 100;
        clearInterval(loadInterval);
        setProgress(100);
        timersRef.current.push(
          setTimeout(() => {
            setState('playing');
            const v = videoRef.current;
            if (v) {
              v.currentTime = 0;
              v.play().catch(() => finishSequence(true));
            } else {
              finishSequence(true);
            }
          }, 300),
        );
      } else {
        setProgress(p);
      }
    }, 100);
    timersRef.current.push(loadInterval as unknown as ReturnType<typeof setTimeout>);
  }, [clearTimers, finishSequence]);

  const handleVideoEnd = useCallback(() => {
    finishSequence(true);
  }, [finishSequence]);

  const handleMouseEnter = () => {
    onActivateRef.current?.();
    if (state === 'idle' && !isRunningRef.current) {
      startSequence();
    }
  };

  // Auto-trigger: start when this card becomes the active one.
  useEffect(() => {
    if (active && state === 'idle' && !isRunningRef.current) {
      startSequence();
    }
  }, [active, state, startSequence]);

  // Interrupt: if this card is no longer active but is mid-sequence,
  // stop the video and show interference (glitch → idle) without advancing
  // the cycle.
  useEffect(() => {
    if (!active && isRunningRef.current && (state === 'loading' || state === 'playing')) {
      const v = videoRef.current;
      if (v) v.pause();
      finishSequence(false);
    }
  }, [active, state, finishSequence]);

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      clearTimers();
      const v = videoRef.current;
      if (v) v.pause();
    };
  }, [clearTimers]);

  // Image opacity: barely visible in idle, dimmed in loading, gone in play/glitch.
  const imgClass =
    state === 'playing' || state === 'glitch'
      ? 'opacity-0'
      : state === 'loading'
        ? 'opacity-25'
        : 'opacity-10';

  return (
    <>
      <Link href={`/modules/${slug}`} className="block" onMouseEnter={handleMouseEnter}>
        <div className="cyber-frame group relative" style={{aspectRatio: '1 / 1.33'}}>
        <div
          className={`cyber-frame-body relative overflow-hidden h-full w-full ${
            state === 'glitch' ? 'agent-glitch' : ''
          }`}
        >
          <span className="cb cb-tl" />
          <span className="cb cb-br" />

          {/* Base artwork — barely visible under the noise in idle */}
          {image && (
            <Image
              src={image}
              alt={name}
              fill
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
              className={`object-cover transition-opacity duration-500 ${imgClass}`}
            />
          )}

          {/* Video layer */}
          <video
            ref={videoRef}
            src={video}
            muted
            playsInline
            preload="auto"
            onEnded={handleVideoEnd}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${
              state === 'playing' || state === 'glitch' ? 'opacity-100' : 'opacity-0'
            }`}
          />

          {/* Idle — continuous white noise + SIGNAL LOST */}
          {state === 'idle' && (
            <div className="absolute inset-0 z-10 flex items-center justify-center">
              <div className="agent-static absolute inset-0" />
              <span className="relative z-20 font-mono text-[11px] tracking-[0.3em] text-white/70 animate-pulse">
                {t('signalLost')}
              </span>
            </div>
          )}

          {/* Loading — cyberpunk progress bar */}
          {state === 'loading' && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-black/70 backdrop-blur-[2px]">
              <div className="scanline-overlay absolute inset-0 opacity-30" />
              <div className="relative z-10 flex flex-col items-center gap-3 w-[80%]">
                <span className="font-mono text-[10px] tracking-[0.3em] text-neon-cyan uppercase animate-pulse">
                  {t('signalDecoding')}
                </span>
                <div className="w-full h-1.5 bg-zinc-800/80 border border-neon-cyan/30 overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-neon-cyan to-neon-purple transition-all duration-150"
                    style={{width: `${progress}%`}}
                  />
                </div>
                <span className="font-mono text-xs text-neon-cyan tabular-nums">{progress}%</span>
              </div>
            </div>
          )}

          {/* Glitch — RGB channel split flash (also used for interruptions) */}
          {state === 'glitch' && <div className="absolute inset-0 z-10 agent-glitch-overlay" />}
          </div>
        </div>
      </Link>
      {/* Name tag under the card */}
      <div className="mt-2 text-center font-mono text-[10px] tracking-[0.22em] text-zinc-500">
        {name} // module
      </div>
    </>
  );
}