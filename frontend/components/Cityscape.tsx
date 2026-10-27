'use client';

import { useEffect, useMemo, useRef } from 'react';

// Deterministic PRNG (no Math.random in render → no SSR/CSR hydration mismatch)
function makeRng(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0;
    return s / 4294967296;
  };
}

interface Building {
  x: number;
  w: number;
  h: number;
}

function makeSkyline(
  seed: number,
  minH: number,
  maxH: number,
  targetW: number,
): Building[] {
  const rand = makeRng(seed);
  const buildings: Building[] = [];
  let x = -10;
  while (x < targetW) {
    const w = 45 + Math.floor(rand() * 70);
    const h = minH + Math.floor(rand() * (maxH - minH));
    buildings.push({ x, w, h });
    x += w + 3 + Math.floor(rand() * 8);
  }
  return buildings;
}

function Skyline({
  back,
  seed,
  minH,
  maxH,
}: {
  back: boolean;
  seed: number;
  minH: number;
  maxH: number;
}) {
  const targetW = 1600;
  const buildings = useMemo(
    () => makeSkyline(seed, minH, maxH, targetW),
    [seed, minH, maxH],
  );
  const rand = useMemo(() => makeRng(seed * 7 + 3), [seed]);
  const VBH = 420;

  return (
    <svg
      viewBox={`0 0 ${targetW} ${VBH}`}
      preserveAspectRatio="xMinYMax slice"
      className="block w-full"
      style={{ height: back ? '42vh' : '34vh' }}
      aria-hidden
    >
      {buildings.map((b, i) => {
        const top = VBH - b.h;
        const windows = [];
        const cols = Math.max(1, Math.floor(b.w / 16));
        const rows = Math.max(1, Math.floor(b.h / 22));
        for (let r = 0; r < rows; r++) {
          for (let c = 0; c < cols; c++) {
            const lit = rand() > (back ? 0.86 : 0.8);
            const magenta = rand() > 0.82;
            if (lit) {
              windows.push(
                <rect
                  key={`${i}-${r}-${c}`}
                  x={b.x + 5 + c * 15}
                  y={top + 8 + r * 20}
                  width={5}
                  height={8}
                  fill={magenta ? '#BC13FE' : '#00F3FF'}
                  opacity={back ? 0.35 : 0.55}
                />,
              );
            }
          }
        }
        return (
          <g key={i}>
            <rect
              x={b.x}
              y={top}
              width={b.w}
              height={b.h}
              fill={back ? '#070b16' : '#05070f'}
            />
            {/* neon top edge */}
            <rect
              x={b.x}
              y={top}
              width={b.w}
              height={back ? 1.5 : 2.5}
              fill={back ? '#123' : '#00F3FF'}
              opacity={back ? 0.4 : 0.7}
            />
            {/* faint side edge */}
            <rect
              x={b.x}
              y={top}
              width={back ? 1 : 1.5}
              height={b.h}
              fill="#00F3FF"
              opacity={back ? 0.12 : 0.22}
            />
            {windows}
          </g>
        );
      })}
    </svg>
  );
}

function DataStreams() {
  const columns = useMemo(() => {
    const rand = makeRng(991);
    const hex = '0123456789ABCDEF#@$%&*<>/=+?';
    return Array.from({ length: 14 }).map((_, ci) => {
      const chars = Array.from({ length: 26 }).map(() =>
        hex[Math.floor(rand() * hex.length)],
      );
      const left = 3 + ci * 7 + rand() * 3;
      const dur = 6 + rand() * 8;
      const delay = -rand() * 10;
      const cyan = rand() > 0.5;
      return { chars, left, dur, delay, cyan, ci };
    });
  }, []);

  return (
    <div className="absolute inset-0 overflow-hidden" aria-hidden>
      {columns.map((c) => (
        <div
          key={c.ci}
          className="datastream"
          style={{
            left: `${c.left}%`,
            animationDuration: `${c.dur}s`,
            animationDelay: `${c.delay}s`,
            color: c.cyan ? 'rgba(0,243,255,0.5)' : 'rgba(188,19,254,0.45)',
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
  const backRef = useRef<HTMLDivElement>(null);
  const frontRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    let raf = 0;
    const onScroll = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const y = window.scrollY;
        if (backRef.current) backRef.current.style.transform = `translateY(${y * 0.05}px)`;
        if (frontRef.current) frontRef.current.style.transform = `translateY(${y * 0.12}px)`;
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
      {/* data streams */}
      <DataStreams />
      {/* orbital grid sweep */}
      <div className="orbit-grid" />
      {/* back skyline */}
      <div ref={backRef} className="absolute bottom-0 inset-x-0 will-change-transform">
        <Skyline back seed={1337} minH={120} maxH={300} />
      </div>
      {/* front skyline */}
      <div ref={frontRef} className="absolute bottom-0 inset-x-0 will-change-transform">
        <Skyline back={false} seed={777} minH={70} maxH={220} />
      </div>
      {/* light beams from the city */}
      <div className="city-beam city-beam-1" />
      <div className="city-beam city-beam-2" />
    </div>
  );
}
