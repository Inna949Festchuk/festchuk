'use client';

import { useCallback, useEffect, useRef, useState } from 'react';
import { Volume2, VolumeX, Shuffle, Radio } from 'lucide-react';

interface TrackComposition {
  id: string;
  title: string;
  subtitle: string;
  bpm: number;
  accent: 'cyan' | 'magenta' | 'purple' | 'yellow';
  bassRoot: number[];
  arpNotes: number[][];
  leadNotes: (number | null)[][];
  padChord: number[][];
  cutoffBase: number;
}

const mtof = (midi: number) => 440 * Math.pow(2, (midi - 69) / 12);

const TRACKS: TrackComposition[] = [
  {
    id: 'neon-rain-district',
    title: 'NEON RAIN // SECTOR 09',
    subtitle: 'SYNTHWAVE • 114 BPM',
    bpm: 114,
    accent: 'cyan',
    bassRoot: [38, 41, 45, 43], // D2, F2, A2, G2
    arpNotes: [
      [50, 53, 57, 62, 65, 62, 57, 53],
      [53, 57, 60, 65, 69, 65, 60, 57],
      [57, 60, 64, 69, 72, 69, 64, 60],
      [55, 58, 62, 67, 70, 67, 62, 58],
    ],
    leadNotes: [
      [74, null, 72, 69, null, 65, 67, null],
      [72, null, 69, 65, null, 69, 72, null],
      [76, null, 74, 72, null, 69, 67, null],
      [70, null, 69, 67, 65, null, 62, null],
    ],
    padChord: [
      [62, 65, 69],
      [60, 65, 69],
      [60, 64, 69],
      [58, 62, 67],
    ],
    cutoffBase: 1450,
  },
  {
    id: 'quantum-overdrive',
    title: 'QUANTUM OVERDRIVE',
    subtitle: 'DARKSYNTH • 126 BPM',
    bpm: 126,
    accent: 'magenta',
    bassRoot: [36, 39, 34, 31], // C2, D#2, A#1, G1
    arpNotes: [
      [48, 51, 55, 60, 63, 60, 55, 51],
      [51, 55, 58, 63, 67, 63, 58, 55],
      [46, 50, 53, 58, 62, 58, 53, 50],
      [43, 47, 50, 55, 59, 55, 50, 47],
    ],
    leadNotes: [
      [72, 75, null, 70, 72, null, 67, null],
      [75, 79, null, 74, 75, null, 70, null],
      [70, 74, null, 69, 70, null, 65, null],
      [67, null, 70, 67, 65, 63, 62, null],
    ],
    padChord: [
      [60, 63, 67],
      [58, 63, 67],
      [58, 62, 65],
      [55, 59, 62],
    ],
    cutoffBase: 1850,
  },
  {
    id: 'chrome-horizon',
    title: 'CHROME HORIZON 2089',
    subtitle: 'OUTRUN • 108 BPM',
    bpm: 108,
    accent: 'purple',
    bassRoot: [45, 41, 36, 43], // A2, F2, C2, G2
    arpNotes: [
      [57, 60, 64, 69, 71, 69, 64, 60],
      [53, 57, 60, 65, 67, 65, 60, 57],
      [48, 52, 55, 60, 64, 60, 55, 52],
      [55, 59, 62, 67, 69, 67, 62, 59],
    ],
    leadNotes: [
      [76, null, 72, null, 69, 71, 72, null],
      [77, null, 72, null, 69, 67, 65, null],
      [72, null, 67, null, 64, 67, 72, null],
      [74, null, 71, 67, null, 69, 71, null],
    ],
    padChord: [
      [60, 64, 69],
      [60, 65, 69],
      [60, 64, 67],
      [59, 62, 67],
    ],
    cutoffBase: 1320,
  },
  {
    id: 'neural-black-ice',
    title: 'NEURAL BLACK ICE',
    subtitle: 'CYBER INDUSTRIAL • 132 BPM',
    bpm: 132,
    accent: 'yellow',
    bassRoot: [40, 40, 43, 38], // E2, E2, G2, D2
    arpNotes: [
      [52, 55, 59, 64, 59, 55, 64, 59],
      [52, 58, 59, 64, 66, 64, 59, 55],
      [55, 59, 62, 67, 62, 59, 67, 62],
      [50, 54, 57, 62, 57, 54, 62, 57],
    ],
    leadNotes: [
      [76, 76, null, 79, 76, null, 71, null],
      [78, 76, null, 74, 71, null, 69, null],
      [79, null, 76, 74, null, 71, 74, null],
      [74, null, 71, 69, 67, null, 64, null],
    ],
    padChord: [
      [59, 64, 67],
      [58, 64, 66],
      [59, 62, 67],
      [57, 62, 66],
    ],
    cutoffBase: 2100,
  },
  {
    id: 'void-uplink',
    title: 'VOID UPLINK // DRIFT',
    subtitle: 'CYBER AMBIENT • 98 BPM',
    bpm: 98,
    accent: 'cyan',
    bassRoot: [37, 44, 42, 40], // C#2, G#2, F#2, E2
    arpNotes: [
      [49, 56, 61, 64, 68, 64, 61, 56],
      [56, 60, 63, 68, 72, 68, 63, 60],
      [54, 57, 61, 66, 69, 66, 61, 57],
      [52, 56, 59, 64, 68, 64, 59, 56],
    ],
    leadNotes: [
      [73, null, null, 68, 71, null, 64, null],
      [72, null, null, 68, 63, null, 68, null],
      [69, null, 73, null, 66, null, 64, null],
      [68, null, 64, null, 59, null, null, null],
    ],
    padChord: [
      [61, 64, 68],
      [60, 63, 68],
      [57, 61, 66],
      [56, 59, 64],
    ],
    cutoffBase: 1100,
  },
];

const BAR_COUNT = 12;

export default function CyberMusicPlayer() {
  const [isPlaying, setIsPlaying] = useState(false);
  const [trackIndex, setTrackIndex] = useState(0);
  const [bars, setBars] = useState<number[]>(() => Array(BAR_COUNT).fill(18));

  const ctxRef = useRef<AudioContext | null>(null);
  const masterRef = useRef<GainNode | null>(null);
  const analyserRef = useRef<AnalyserNode | null>(null);
  const timerRef = useRef<number | null>(null);
  const rafRef = useRef<number | null>(null);
  const stepRef = useRef<number>(0);
  const trackIndexRef = useRef<number>(0);

  useEffect(() => {
    trackIndexRef.current = trackIndex;
  }, [trackIndex]);

  const createNoiseBuffer = (ctx: AudioContext) => {
    const bufferSize = ctx.sampleRate * 0.25;
    const buffer = ctx.createBuffer(1, bufferSize, ctx.sampleRate);
    const output = buffer.getChannelData(0);
    for (let i = 0; i < bufferSize; i++) {
      output[i] = Math.random() * 2 - 1;
    }
    return buffer;
  };

  const triggerStep = useCallback(
    (ctx: AudioContext, dest: AudioNode, noiseBuffer: AudioBuffer, step: number, track: TrackComposition) => {
      const now = ctx.currentTime + 0.02;
      const stepDur = 60 / track.bpm / 4; // 16th note
      const bar = Math.floor(step / 16) % 4;
      const stepInBar = step % 16;

      // 1. Kick on 0, 4, 8, 12 (+ occasional syncopation on 14)
      if (stepInBar % 4 === 0 || (stepInBar === 14 && bar % 2 === 1)) {
        const osc = ctx.createOscillator();
        const gain = ctx.createGain();
        osc.type = 'sine';
        osc.frequency.setValueAtTime(135, now);
        osc.frequency.exponentialRampToValueAtTime(34, now + 0.16);
        gain.gain.setValueAtTime(0.42, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.2);
        osc.connect(gain);
        gain.connect(dest);
        osc.start(now);
        osc.stop(now + 0.21);
      }

      // 2. Snare / cyber clap on 4 and 12
      if (stepInBar === 4 || stepInBar === 12) {
        const noise = ctx.createBufferSource();
        noise.buffer = noiseBuffer;
        const filter = ctx.createBiquadFilter();
        filter.type = 'bandpass';
        filter.frequency.setValueAtTime(1400, now);
        filter.Q.setValueAtTime(1.2, now);
        const gain = ctx.createGain();
        gain.gain.setValueAtTime(0.22, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.16);
        noise.connect(filter);
        filter.connect(gain);
        gain.connect(dest);
        noise.start(now);
        noise.stop(now + 0.17);
      }

      // 3. Hi-hat on every 2nd 16th + offbeat shimmer
      if (stepInBar % 2 === 0 || stepInBar === 15) {
        const hat = ctx.createBufferSource();
        hat.buffer = noiseBuffer;
        const hp = ctx.createBiquadFilter();
        hp.type = 'highpass';
        hp.frequency.setValueAtTime(6800, now);
        const gain = ctx.createGain();
        const amp = stepInBar % 4 === 2 ? 0.085 : 0.045;
        gain.gain.setValueAtTime(amp, now);
        gain.gain.exponentialRampToValueAtTime(0.001, now + 0.05);
        hat.connect(hp);
        hp.connect(gain);
        gain.connect(dest);
        hat.start(now);
        hat.stop(now + 0.055);
      }

      // 4. Driving offbeat / rolling cyber bass (sawtooth + lowpass envelope)
      const bassMidi = track.bassRoot[bar] + (stepInBar % 2 === 1 ? 12 : 0);
      const bassOsc = ctx.createOscillator();
      const bassSub = ctx.createOscillator();
      const bassFilter = ctx.createBiquadFilter();
      const bassGain = ctx.createGain();

      bassOsc.type = 'sawtooth';
      bassSub.type = 'square';
      const bassFreq = mtof(bassMidi);
      bassOsc.frequency.setValueAtTime(bassFreq, now);
      bassSub.frequency.setValueAtTime(bassFreq * 0.5, now);

      bassFilter.type = 'lowpass';
      bassFilter.Q.setValueAtTime(4.5, now);
      bassFilter.frequency.setValueAtTime(track.cutoffBase * 0.65, now);
      bassFilter.frequency.exponentialRampToValueAtTime(180, now + stepDur * 0.9);

      bassGain.gain.setValueAtTime(0.18, now);
      bassGain.gain.exponentialRampToValueAtTime(0.001, now + stepDur * 0.92);

      bassOsc.connect(bassFilter);
      bassSub.connect(bassFilter);
      bassFilter.connect(bassGain);
      bassGain.connect(dest);
      bassOsc.start(now);
      bassSub.start(now);
      bassOsc.stop(now + stepDur);
      bassSub.stop(now + stepDur);

      // 5. Arpeggiator (16th notes)
      const arpSeq = track.arpNotes[bar];
      const arpMidi = arpSeq[stepInBar % arpSeq.length];
      const arpOsc = ctx.createOscillator();
      const arpFilter = ctx.createBiquadFilter();
      const arpGain = ctx.createGain();

      arpOsc.type = 'sawtooth';
      arpOsc.frequency.setValueAtTime(mtof(arpMidi), now);
      arpFilter.type = 'lowpass';
      const lfo = Math.sin(step * 0.25) * 450;
      arpFilter.frequency.setValueAtTime(track.cutoffBase + lfo, now);
      arpFilter.Q.setValueAtTime(2.4, now);

      arpGain.gain.setValueAtTime(0.075, now);
      arpGain.gain.exponentialRampToValueAtTime(0.001, now + stepDur * 0.88);

      arpOsc.connect(arpFilter);
      arpFilter.connect(arpGain);
      arpGain.connect(dest);
      arpOsc.start(now);
      arpOsc.stop(now + stepDur * 0.92);

      // 6. Warm Pad chord at start of every bar
      if (stepInBar === 0) {
        const chord = track.padChord[bar];
        const barDur = stepDur * 16;
        chord.forEach((noteMidi, idx) => {
          const padOsc = ctx.createOscillator();
          const padFilter = ctx.createBiquadFilter();
          const padGain = ctx.createGain();
          padOsc.type = idx % 2 === 0 ? 'sawtooth' : 'triangle';
          padOsc.detune.setValueAtTime((idx - 1) * 9, now);
          padOsc.frequency.setValueAtTime(mtof(noteMidi), now);

          padFilter.type = 'lowpass';
          padFilter.frequency.setValueAtTime(920, now);

          padGain.gain.setValueAtTime(0.001, now);
          padGain.gain.linearRampToValueAtTime(0.04, now + 0.25);
          padGain.gain.exponentialRampToValueAtTime(0.001, now + barDur * 0.98);

          padOsc.connect(padFilter);
          padFilter.connect(padGain);
          padGain.connect(dest);
          padOsc.start(now);
          padOsc.stop(now + barDur);
        });
      }

      // 7. Cyber Lead melody on 8th notes
      if (stepInBar % 2 === 0) {
        const leadSeq = track.leadNotes[bar];
        const leadMidi = leadSeq[Math.floor(stepInBar / 2) % leadSeq.length];
        if (leadMidi !== null) {
          const leadOsc = ctx.createOscillator();
          const leadGain = ctx.createGain();
          const leadFilter = ctx.createBiquadFilter();
          leadOsc.type = 'square';
          leadOsc.detune.setValueAtTime(6, now);
          leadOsc.frequency.setValueAtTime(mtof(leadMidi), now);

          leadFilter.type = 'lowpass';
          leadFilter.frequency.setValueAtTime(2400, now);

          const noteDur = stepDur * 1.85;
          leadGain.gain.setValueAtTime(0.06, now);
          leadGain.gain.exponentialRampToValueAtTime(0.001, now + noteDur);

          leadOsc.connect(leadFilter);
          leadFilter.connect(leadGain);
          leadGain.connect(dest);
          leadOsc.start(now);
          leadOsc.stop(now + noteDur + 0.02);
        }
      }
    },
    [],
  );

  const stopScheduler = useCallback(() => {
    if (timerRef.current !== null) {
      window.clearInterval(timerRef.current);
      timerRef.current = null;
    }
    if (rafRef.current !== null) {
      window.cancelAnimationFrame(rafRef.current);
      rafRef.current = null;
    }
  }, []);

  const startEngine = useCallback(
    async (targetTrackIndex: number) => {
      stopScheduler();

      const AudioCtx = window.AudioContext || (window as unknown as { webkitAudioContext: typeof AudioContext }).webkitAudioContext;
      if (!ctxRef.current) {
        const ctx = new AudioCtx();
        const master = ctx.createGain();
        master.gain.value = 0.75;
        const analyser = ctx.createAnalyser();
        analyser.fftSize = 64;
        analyser.smoothingTimeConstant = 0.76;

        master.connect(analyser);
        analyser.connect(ctx.destination);

        ctxRef.current = ctx;
        masterRef.current = master;
        analyserRef.current = analyser;
      }

      const ctx = ctxRef.current;
      const master = masterRef.current!;
      const analyser = analyserRef.current!;

      if (ctx.state === 'suspended') {
        await ctx.resume();
      }

      const noiseBuffer = createNoiseBuffer(ctx);
      const track = TRACKS[targetTrackIndex];
      const stepMs = (60 / track.bpm / 4) * 1000;

      triggerStep(ctx, master, noiseBuffer, stepRef.current++, track);
      timerRef.current = window.setInterval(() => {
        const activeTrack = TRACKS[trackIndexRef.current];
        triggerStep(ctx, master, noiseBuffer, stepRef.current++, activeTrack);
      }, stepMs);

      const freqData = new Uint8Array(analyser.frequencyBinCount);
      const updateBars = () => {
        analyser.getByteFrequencyData(freqData);
        const next: number[] = [];
        for (let i = 0; i < BAR_COUNT; i++) {
          const bin = freqData[i + 1] ?? 0;
          const pct = Math.max(16, Math.min(100, Math.round((bin / 255) * 100)));
          next.push(pct);
        }
        setBars(next);
        rafRef.current = window.requestAnimationFrame(updateBars);
      };
      rafRef.current = window.requestAnimationFrame(updateBars);
    },
    [stopScheduler, triggerStep],
  );

  const togglePlay = async () => {
    if (isPlaying) {
      stopScheduler();
      if (ctxRef.current && ctxRef.current.state === 'running') {
        await ctxRef.current.suspend();
      }
      setIsPlaying(false);
      setBars(Array(BAR_COUNT).fill(18));
      return;
    }

    setIsPlaying(true);
    await startEngine(trackIndex);
  };

  const playRandomTrack = async () => {
    const candidates = TRACKS.map((_, idx) => idx).filter((idx) => idx !== trackIndex);
    const randomIdx = candidates[Math.floor(Math.random() * candidates.length)] ?? 0;
    stepRef.current = 0;
    setTrackIndex(randomIdx);
    trackIndexRef.current = randomIdx;
    setIsPlaying(true);
    await startEngine(randomIdx);
  };

  useEffect(() => {
    return () => {
      stopScheduler();
      if (ctxRef.current) {
        ctxRef.current.close().catch(() => {});
      }
    };
  }, [stopScheduler]);

  const currentTrack = TRACKS[trackIndex];

  return (
    <div className="cyber-audio-dock" role="region" aria-label="Фоновый киберпанк-плеер">
      <div className={`cyber-audio-panel ${isPlaying ? 'is-playing' : ''}`}>
        <span className="cb cb-tl" />
        <span className="cb cb-br" />

        {/* Equalizer visualizer */}
        <div className="cyber-eq" aria-hidden="true">
          {bars.map((height, idx) => (
            <span
              key={idx}
              className={`cyber-eq-bar accent-${currentTrack.accent}`}
              style={{
                height: `${isPlaying ? height : 18}%`,
              }}
            />
          ))}
        </div>

        {/* Track info */}
        <div className="cyber-audio-meta">
          <div className="cyber-audio-status">
            <Radio className={`w-3 h-3 ${isPlaying ? 'text-neon-cyan animate-pulse' : 'text-zinc-500'}`} />
            <span>{isPlaying ? 'SYNTH STREAM // LIVE' : 'SYNTH STREAM // STANDBY'}</span>
          </div>
          <div className="cyber-audio-title" title={currentTrack.title}>
            {currentTrack.title}
          </div>
          <div className="cyber-audio-sub">{currentTrack.subtitle}</div>
        </div>

        {/* Controls */}
        <div className="cyber-audio-Actions">
          <button
            type="button"
            onClick={togglePlay}
            className={`cyber-audio-btn ${isPlaying ? 'active' : ''}`}
            aria-label={isPlaying ? 'Отключить фоновую музыку' : 'Включить фоновую музыку'}
            title={isPlaying ? 'Отключить музыку' : 'Включить музыку'}
          >
            {isPlaying ? <Volume2 className="w-4 h-4" /> : <VolumeX className="w-4 h-4" />}
            <span>{isPlaying ? 'MUTE' : 'PLAY'}</span>
          </button>

          <button
            type="button"
            onClick={playRandomTrack}
            className="cyber-audio-btn cyber-audio-btn-shuffle"
            aria-label="Случайная киберпанк-композиция"
            title="Переключить на случайную композицию"
          >
            <Shuffle className="w-4 h-4" />
            <span>RANDOM</span>
          </button>
        </div>
      </div>
    </div>
  );
}
