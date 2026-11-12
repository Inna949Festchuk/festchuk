'use client';

import { useRef, useState, useEffect, useCallback } from 'react';
import Image from 'next/image';
import {Link} from '@/i18n/navigation';
import {useTranslations} from 'next-intl';

type CardState = 'idle' | 'loading' | 'playing' | 'glitch' | 'static';

interface AgentVideoCardProps {
  name: string;
  image: string;
  video: string;
  slug: string;
  active: boolean;
  onComplete?: () => void;
}

/**
 * A single agent "demo" card. Lifecycle:
 *   idle  -> loading (cyberpunk progress bar 0..100%)
 *        -> playing (muted video)
 *        -> glitch  (RGB-split + shake)
 *        -> static  (white-noise + "SIGNAL LOST")
 *        -> idle
 * Triggered either by hover, or when this card is the active one in the
 * auto-cycle. `onComplete` fires when a sequence finishes so the parent can
 * advance to the next card.
 */
export default function AgentVideoCard({name, image, video, slug, active, onComplete}: AgentVideoCardProps) {
  const t = useTranslations('home');
  const [state, setState] = useState<CardState>('idle');
  const [progress, setProgress] = useState(0);
  const videoRef = useRef<HTMLVideoElement>(null);
  const timersRef = useRef<ReturnType<typeof setTimeout>[]>([]);
  const isRunningRef = useRef(false);

  // Keep a stable ref to the latest onComplete so the timer callbacks never
  // capture a stale closure.
  const onCompleteRef = useRef(onComplete);
  useEffect(() => {
    onCompleteRef.current = onComplete;
  }, [onComplete]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach((tm) => clearTimeout(tm));
    timersRef.current = [];
  }, []);

  const finishSequence = useCallback(() => {
    setState('glitch');
    timersRef.current.push(
      setTimeout(() => {
        setState('static');
        timersRef.current.push(
          setTimeout(() => {
            setState('idle');
            setProgress(0);
            isRunningRef.current = false;
            onCompleteRef.current?.();
          }, 1200),
        );
      }, 800),
    );
  }, []);

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
              v.play().catch(() => finishSequence());
            } else {
              finishSequence();
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
    finishSequence();
  }, [finishSequence]);

  const handleMouseEnter = () => {
    if (state === 'idle') startSequence();
  };

  // Auto-cycle trigger: run the sequence when this card becomes the active one.
  useEffect(() => {
    if (active && state === 'idle' && !isRunningRef.current) {
      startSequence();
    }
  }, [active, state, startSequence]);

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      clearTimers();
      const v = videoRef.current;
      if (v) v.pause();
    };
  }, [clearTimers]);

  return (
    <Link href={`/modules/${slug}`} className="block">
      <div className="cyber-frame group relative" style={{aspectRatio: '1 / 1.33'}}>
        <div
          className={`cyber-frame-body relative overflow-hidden h-full w-full ${
            state === 'glitch' ? 'agent-glitch' : ''
          }`}
        >
          <span className="cb cb-tl" />
          <span className="cb cb-br" />

          {/* Base artwork — always present, fades out while the video plays */}
          {image && (
            <Image
              src={image}
              alt={name}
              fill
              sizes="(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 25vw"
              className={`object-cover transition-all duration-500 ${
                state === 'playing' ? 'opacity-0 scale-105' : 'opacity-100 group-hover:scale-[1.04]'
              }`}
            />
          )}

          {/* Video layer — visible only during the playing phase */}
          <video
            ref={videoRef}
            src={video}
            muted
            playsInline
            preload="metadata"
            onEnded={handleVideoEnd}
            className={`absolute inset-0 w-full h-full object-cover transition-opacity duration-300 ${
              state === 'playing' ? 'opacity-100' : 'opacity-0'
            }`}
          />

          {/* Loading overlay — cyberpunk progress bar with percentage */}
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

          {/* Glitch overlay — RGB channel split flash */}
          {state === 'glitch' && <div className="absolute inset-0 z-10 agent-glitch-overlay" />}

          {/* Static / white noise — SVG turbulence + "SIGNAL LOST" */}
          {state === 'static' && (
            <div className="absolute inset-0 z-20 flex items-center justify-center">
              <div className="agent-noise absolute inset-0" />
              <span className="relative z-30 font-mono text-xs tracking-[0.3em] text-white/80 animate-pulse">
                {t('signalLost')}
              </span>
            </div>
          )}
        </div>
      </div>
      <div className="mt-2 text-center font-mono text-[10px] tracking-[0.22em] text-zinc-500">
        {name} // module
      </div>
    </Link>
  );
}