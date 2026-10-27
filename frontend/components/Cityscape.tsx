'use client';

import { useEffect, useMemo, useRef } from 'react';

function makeRng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

function DataStreams() {
  const columns = useMemo(() => {
    const rand = makeRng(991);
    const hex = '0123456789ABCDEF#@$%&*<>/=+?';
    return Array.from({ length: 12 }).map((_, ci) => {
      const chars = Array.from({ length: 24 }).map(() =>
        hex[Math.floor(rand() * hex.length)],
      );
      const left = 4 + ci * 8 + rand() * 2.5;
      const dur = 8 + rand() * 9;
      const delay = -rand() * 12;
      const cyan = rand() > 0.45;
      return { chars, left, dur, delay, cyan, ci };
    });
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden opacity-55" aria-hidden>
      {columns.map((c) => (
        <div
          key={c.ci}
          className="datastream"
          style={{
            left: `${c.left}%`,
            animationDuration: `${c.dur}s`,
            animationDelay: `${c.delay}s`,
            color: c.cyan ? 'rgba(0,243,255,0.42)' : 'rgba(255,43,214,0.38)',
          }}
        >
          {c.chars.map((ch, i) => (
            <span key={i}>{ch}</span>
          ))}
        </div>
      ))}
    </div>
  );
}

export default function Cityscape() {
  const bgRef = useRef<HTMLDivElement>(null);
  const glowRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const y = window.scrollY;
        if (bgRef.current) {
          bgRef.current.style.transform = `scale(1.06) translate3d(0, ${y * -0.04}px, 0)`;
        }
        if (glowRef.current) {
          glowRef.current.style.transform = `translate3d(0, ${y * 0.03}px, 0)`;
        }
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => {
      window.removeEventListener('scroll', onScroll);
      cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <div className="cityscape fixed inset-0 z-[-1] overflow-hidden pointer-events-none" aria-hidden>
      {/* High-res Cyberpunk City Artwork Layer */}
      <div
        ref={bgRef}
        className="cyber-city-artwork"
        style={{ backgroundImage: "url('/assets/cyber-city-bg.png')" }}
      />

      {/* Atmospheric multi-stop vignette for crisp foreground legibility */}
      <div className="cyber-city-vignette" />

      {/* Ambient neon bloom */}
      <div ref={glowRef} className="cyber-city-bloom" />

      {/* Subtle perspective grid & data rain */}
      <div className="orbit-grid" />
      <DataStreams />

      {/* Light beams */}
      <div className="city-beam city-beam-1" />
      <div className="city-beam city-beam-2" />
    </div>
  );
}
