'use client';

/**
 * Cyberpunk AI Robot visual for the Hero section.
 * Upper body fits harmoniously into the first screen while the lower body
 * extends downward and gradually dissolves without disappearing completely.
 */
export default function Hologram() {
  return (
    <div className="hero-robot-stage select-none pointer-events-none" aria-hidden="true">
      <div className="hero-robot-glow" />
      <img
        src="/assets/cyber-robot.webp"
        alt=""
        width={611}
        height={1379}
        decoding="async"
        fetchPriority="high"
        className="hero-robot-img"
      />
      <img
        src="/assets/cyber-robot-neon.webp"
        alt=""
        width={611}
        height={1379}
        decoding="async"
        className="hero-robot-img hero-robot-img--neon"
      />
    </div>
  );
}

