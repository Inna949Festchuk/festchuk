'use client';

import { motion } from 'framer-motion';

/**
 * Holographic cube inside a rotating HUD ring with data readouts.
 * Pure CSS 3D + SVG — no external assets.
 */
export default function Hologram() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.9 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.9, delay: 0.3 }}
      className="holo-scene select-none"
      aria-hidden
    >
      {/* Outer HUD ring */}
      <svg className="holo-ring" viewBox="0 0 200 200" fill="none">
        <circle cx="100" cy="100" r="96" stroke="rgba(0,243,255,0.35)" strokeWidth="0.8" strokeDasharray="4 6" />
        <circle cx="100" cy="100" r="86" stroke="rgba(0,243,255,0.2)" strokeWidth="0.6" />
        <circle cx="100" cy="100" r="92" stroke="rgba(188,19,254,0.3)" strokeWidth="1" strokeDasharray="30 200" strokeLinecap="round" />
        {/* tick marks */}
        {Array.from({ length: 60 }).map((_, i) => {
          const a = (i / 60) * Math.PI * 2;
          const r1 = 90, r2 = i % 5 === 0 ? 82 : 86;
          const x1 = 100 + r1 * Math.cos(a);
          const y1 = 100 + r1 * Math.sin(a);
          const x2 = 100 + r2 * Math.cos(a);
          const y2 = 100 + r2 * Math.sin(a);
          return (
            <line key={i} x1={x1} y1={y1} x2={x2} y2={y2}
              stroke={i % 5 === 0 ? 'rgba(0,243,255,0.7)' : 'rgba(0,243,255,0.25)'} strokeWidth="0.8" />
          );
        })}
      </svg>

      {/* Inner counter-rotating ring */}
      <svg className="holo-ring holo-ring--inner" viewBox="0 0 200 200" fill="none">
        <circle cx="100" cy="100" r="60" stroke="rgba(188,19,254,0.4)" strokeWidth="0.8" strokeDasharray="8 10" />
        <circle cx="100" cy="100" r="52" stroke="rgba(0,243,255,0.3)" strokeWidth="0.6" strokeDasharray="2 6" />
        {/* crosshair */}
        <line x1="100" y1="30" x2="100" y2="44" stroke="rgba(0,243,255,0.6)" strokeWidth="1" />
        <line x1="100" y1="156" x2="100" y2="170" stroke="rgba(0,243,255,0.6)" strokeWidth="1" />
        <line x1="30" y1="100" x2="44" y2="100" stroke="rgba(0,243,255,0.6)" strokeWidth="1" />
        <line x1="156" y1="100" x2="170" y2="100" stroke="rgba(0,243,255,0.6)" strokeWidth="1" />
      </svg>

      {/* 3D wireframe cube */}
      <div className="holo-cube-wrap">
        <div className="holo-cube">
          <div className="face face-front" />
          <div className="face face-back" />
          <div className="face face-right" />
          <div className="face face-left" />
          <div className="face face-top" />
          <div className="face face-bottom" />
        </div>
        <div className="holo-core" />
      </div>

      {/* Data readouts */}
      <div className="data-readout" style={{ top: '6%', left: '2%' }}>
        LATENCY&nbsp;<span className="text-white">0.02ms</span>
      </div>
      <div className="data-readout" style={{ top: '20%', right: '0' }}>
        UPLINK&nbsp;<span className="text-white">STABLE</span>
      </div>
      <div className="data-readout" style={{ bottom: '18%', left: '0' }}>
        NODE&nbsp;<span className="text-white">44-A</span>
      </div>
      <div className="data-readout" style={{ bottom: '4%', right: '4%' }}>
        <span style={{ color: '#22c55e' }}>●</span>&nbsp;ONLINE
      </div>
    </motion.div>
  );
}
