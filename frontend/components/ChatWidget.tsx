'use client';

import {useState, useRef, useEffect, useCallback} from 'react';
import {useTranslations, useLocale} from 'next-intl';
import {motion, AnimatePresence} from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import rehypeHighlight from 'rehype-highlight';
import {
  Bot,
  X,
  Send,
  Mic,
  MicOff,
  Loader2,
  Volume2,
  VolumeX,
  Sparkles,
  Trash2,
  Maximize2,
  Minimize2,
  Terminal,
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

// Strip markdown for voice synthesis: tables become comma-separated pauses,
// code blocks are dropped, emphasis markers removed.
function stripMarkdownForTTS(text: string): string {
  return text
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/```[\s\S]*$/g, ' ')
    .replace(/`([^`]*)`/g, '$1')
    .replace(/!\[[^\]]*\]\([^)]*\)/g, ' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/^\s{0,3}#{1,6}\s+/gm, '')
    .replace(/^\s*[-*+]\s+/gm, '')
    .replace(/^\s*\d+\.\s+/gm, '')
    // Tables are never voiced cell by cell: the model writes a one-sentence
    // intro before each table (prompt rule), the voice reads that instead.
    // Drop whole pipe-lines, including partial rows mid-stream.
    .replace(/^[ \t]*\|.*$/gm, ' ')
    // Tab-separated "tables" (model occasionally emits them): lines with
    // several tabs are table rows, not prose.
    .replace(/^[ \t]*(?:[^\n]*\t){2,}[^\n]*$/gm, ' ')
    .replace(/[*_~]{1,3}/g, '')
    .replace(/^\s*[-=]{3,}\s*$/gm, ' ')
    .replace(/\n{2,}/g, '. ')
    .replace(/(?:\.\s*){2,}/g, '. ')
    .replace(/\n/g, ' ')
    .replace(/\s{2,}/g, ' ')
    .replace(/^[\s.!?…\-–—]+/, '')
    .trim();
}

// Incremental chunker for live TTS: as the answer streams in, completed
// sentences (≥150 chars, ≤450 — the backend caps one synthesis at 500) are
// cut out and sent to synthesis immediately, so voice follows the text
// instead of waiting for the full reply. Never cuts inside an open code fence.
function createTTSChunker(onChunk: (chunk: string) => void, en = false) {
  let consumed = 0;
  const LIMIT = 450;
  const MIN = 150;
  // Table-voicing state: the voice must not read a bare table title and must
  // not read cells. The model writes a content intro (prompt rule); if it
  // doesn't, a mechanical one built from the real first-column values is
  // prepended. A small state machine (not text heuristics on previous
  // chunks) tracks which table is covered:
  //   inTable — the previous piece contained table rows;
  //   introDone — the current table already has a voiced intro;
  //   pendingValues — rows collected while waiting for text to attach to.
  let inTable = false;
  let introDone = false;
  let pendingValues: string[] = [];
  let pendingRows = 0;
  let prevClean = '';
  const lastTableSentence = (s: string): number => {
    // Length of the sentence containing the LAST «таблица/table» mention:
    // a real intro is a content sentence (>45 chars), a bare heading is not.
    let idx = -1;
    const re = /таблиц|table/gi;
    let m: RegExpExecArray | null;
    while ((m = re.exec(s)) !== null) idx = m.index;
    if (idx < 0) return 0;
    const prefix = s.slice(0, idx);
    const bounds = prefix.match(/[.!?…]\s/g);
    const start = bounds ? prefix.length - bounds[bounds.length - 1].length : 0;
    const rest = s.slice(idx + 1);
    const endMatch = rest.match(/[.!?…]/);
    const end = endMatch ? idx + 1 + (endMatch.index ?? 0) + 1 : s.length;
    return end - start;
  };
  const buildIntro = (): string => {
    const shown = pendingValues.slice(0, 4).join(', ');
    const more = pendingRows > 4 ? (en ? ' and more' : ' и другие') : '';
    return en
      ? `Details are presented in the following table${shown ? `: ${shown}${more}` : ''}. `
      : `Детали представлены в следующей таблице${shown ? `: ${shown}${more}` : ''}. `;
  };
  const withTableIntro = (piece: string): string => {
    const pipeStart = piece.search(/^[ \t]*\|/m);
    const tabStart = piece.search(/^[ \t]*(?:[^\n]*\t){2,}[^\n]*$/m);
    const tableStart =
      pipeStart >= 0 && tabStart >= 0 ? Math.min(pipeStart, tabStart) : pipeStart >= 0 ? pipeStart : tabStart;
    let clean = stripMarkdownForTTS(piece);
    if (tableStart >= 0) {
      // Prose before this piece's table while the previous piece was still
      // inside a table ⇒ a NEW table begins: reset the state.
      const proseBefore = stripMarkdownForTTS(piece.slice(0, tableStart));
      if (inTable && proseBefore.length > 0) {
        inTable = false;
        introDone = false;
        pendingValues = [];
        pendingRows = 0;
      }
      if (!introDone) {
        // Only the FIRST contiguous table block in this piece (rows stop at
        // the first non-table line) — otherwise values from a later table
        // in the same piece would leak into this intro.
        const lines: string[] = [];
        for (const l of piece.slice(tableStart).split('\n')) {
          if (!(/^[ \t]*\|/.test(l) || (l.match(/\t/g) || []).length >= 2)) break;
          lines.push(l);
        }
        // The first table line of the FIRST piece is the header row; in
        // continuation pieces every line is data.
        lines.slice(inTable ? 0 : 1).forEach((line) => {
          const isPipe = /^[ \t]*\|/.test(line);
          const cell = (isPipe ? line.split('|')[1] || '' : line.split('\t')[0] || '')
            .replace(/[*_~`]/g, '')
            .trim();
          if (!cell) return;
          if (isPipe && /^[\s:|-]*$/.test(cell)) return; // separator row
          pendingRows += 1;
          if (pendingValues.length < 4) {
            pendingValues.push(cell.length > 42 ? `${cell.slice(0, 42)}…` : cell);
          }
        });
        const modelIntro =
          !inTable && (lastTableSentence(proseBefore) > 45 || lastTableSentence(prevClean) > 45);
        if (modelIntro) {
          introDone = true;
          pendingValues = [];
          pendingRows = 0;
        } else if (clean) {
          clean = buildIntro() + clean;
          introDone = true;
          pendingValues = [];
          pendingRows = 0;
        }
        // rows-only piece (clean === ''): wait for a piece with text to
        // attach the intro to.
      }
      inTable = true;
    } else {
      if (clean && pendingValues.length > 0) {
        clean = buildIntro() + clean;
      }
      pendingValues = [];
      pendingRows = 0;
      introDone = false;
      inTable = false;
    }
    if (clean) prevClean = clean;
    return clean;
  };
  const feed = (raw: string, final = false) => {
    // Code fences are atomic: never cut inside a block and never leave an
    // orphan ``` marker at the start of the remainder — the stripper would
    // treat it as an unclosed fence and eat the rest of the answer.
    const fences: Array<[number, number]> = [];
    let open = -1;
    const fenceRe = /```/g;
    let fm: RegExpExecArray | null;
    while ((fm = fenceRe.exec(raw)) !== null) {
      if (open < 0) open = fm.index;
      else {
        fences.push([open, fm.index + 3]);
        open = -1;
      }
    }
    const inFence = (abs: number) =>
      fences.some(([a, b]) => abs > a && abs < b) || (open >= 0 && abs > open);
    const region = raw.slice(consumed);
    let cut = -1;
    const bRe = /[.!?…](?=\s)|\n/g;
    let bm: RegExpExecArray | null;
    while ((bm = bRe.exec(region)) !== null) {
      const abs = consumed + bm.index + 1;
      if (inFence(abs)) continue;
      if (abs - consumed <= LIMIT) cut = abs;
      else break;
    }
    if (final) {
      if (raw.length - consumed > LIMIT) {
        // Long tail: emit one full chunk now, the rest on the next final
        // pass — a single piece above the backend's 500-char cap would be
        // truncated there and lose its tail in the voice.
        if (cut <= consumed) {
          const sp = region.lastIndexOf(' ', LIMIT);
          cut = consumed + (sp > MIN ? sp : LIMIT);
          const f = fences.find(([a, b]) => cut > a && cut < b);
          if (f) cut = f[0] > consumed ? f[0] : f[1];
          if (open >= 0 && cut > open && open > consumed) cut = open;
        }
      } else {
        cut = raw.length;
      }
    } else if (cut - consumed < MIN) {
      if (region.length <= LIMIT) return; // wait for more text
      const sp = region.lastIndexOf(' ', LIMIT);
      cut = consumed + (sp > MIN ? sp : LIMIT);
      // Snap a forced cut out of any code block (whole block goes to the
      // next chunk; if it starts at consumed, take it whole and strip it).
      const f = fences.find(([a, b]) => cut > a && cut < b);
      if (f) cut = f[0] > consumed ? f[0] : f[1];
      if (open >= 0 && cut > open) {
        // Unclosed fence: cut before it, or wait at its start — consuming
        // raw code lines without the ``` marker would voice them later.
        if (open > consumed) cut = open;
        else return;
      }
    }
    if (cut <= consumed) return;
    // Language guard: TTS picks the language per chunk — a chunk opening with
    // an English term ("RAG (Retrieval-Augmented Generation): …") drags the
    // whole chunk into English. If the remainder would start in Latin, first
    // defer the cut to the next feed (more text becomes visible), then pull
    // the cut to just past the leading Latin run.
    if (!final && cut > consumed) {
      const rest0 = raw.slice(cut);
      if (/^[A-Za-z]/.test(rest0.replace(/^\s+/, ''))) {
        let k = cut;
        while (k < raw.length && /\s/.test(raw[k])) k++;
        const leadStart = k;
        while (
          k < raw.length &&
          k - leadStart < 120 &&
          /[A-Za-z0-9(),.;:'"&/ \u2019\u2013\u2014-]/.test(raw[k])
        ) {
          k++;
        }
        // The lead must end at a terminator (space/colon/punctuation). If the
        // next char continues a word ("AI-агенты"), defer the cut — otherwise
        // a Latin fragment would leak into the voiced text.
        const prev = k > leadStart ? raw[k - 1] : ' ';
        if (!/[\s:.,!?…)"'’—–]/.test(prev)) {
          return;
        }
        // Never split a tab-table row: pull the cut to the end of the line,
        // so the whole row stays in one piece and the stripper drops it.
        let kEnd = k;
        const nl = raw.indexOf('\n', kEnd);
        if (nl >= 0 && raw.slice(kEnd, nl).includes('\t') && nl - kEnd < 200) kEnd = nl + 1;
        if (
          k > leadStart &&
          kEnd - consumed <= LIMIT &&
          /[А-Яа-я]/.test(raw.slice(kEnd, kEnd + 3))
        ) {
          cut = kEnd;
        } else {
          return; // wait for the next feed to see past the Latin lead
        }
      }
    }
    const piece = raw.slice(consumed, cut);
    consumed = cut;
    const clean = withTableIntro(piece);
    if (clean) onChunk(clean);
    // Last resort: the table ended the reply and its intro stayed deferred —
    // voice it anyway, after the table.
    if (final && !clean && pendingValues.length > 0 && !introDone) {
      const intro = buildIntro();
      pendingValues = [];
      pendingRows = 0;
      introDone = true;
      onChunk(intro);
    }
  };
  return {feed, consumed: () => consumed};
}

// Emit every chunk of a full text (a long tail needs several final passes).
function feedAllToChunks(
  chunker: {feed: (raw: string, final?: boolean) => void; consumed: () => number},
  text: string,
) {
  let safety = 0;
  do {
    chunker.feed(text, true);
    safety += 1;
  } while (chunker.consumed() < text.length && safety < 50);
}

export default function ChatWidget() {
  const t = useTranslations('chat');
  const locale = useLocale();

  const [isOpen, setIsOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);
  const [sessionError, setSessionError] = useState(false);
  const [activeModuleSlug, setActiveModuleSlug] = useState<string | null>(null);
  // Id of the assistant message currently being streamed (null when idle).
  const [streamingId, setStreamingId] = useState<string | null>(null);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const ttsAbortRef = useRef<AbortController | null>(null);
  // Live TTS queue: chunks arrive while the answer is still streaming.
  const ttsQueueRef = useRef<string[]>([]);
  const ttsClosedRef = useRef(false);
  const ttsWakeRef = useRef<(() => void) | null>(null);
  const ttsSlugRef = useRef('');
  const ttsEnabledRef = useRef(true);

  const quickPrompts = [t('q1'), t('q2'), t('q3'), t('q4')];
  const timeLocale = locale === 'ru' ? 'ru-RU' : 'en-US';

  // Initialize session. Extracted so it can be retried on failure.
  const initSession = useCallback(async () => {
    try {
      const res = await fetch('/api/chat/session/');
      if (!res.ok) throw new Error('session failed');
      const data = await res.json();
      setSessionId(data.session_id);
      setSessionError(false);
    } catch {
      setSessionError(true);
    }
  }, []);

  // Initialize session
  useEffect(() => {
    initSession();

    return () => {
      if (audioRef.current) audioRef.current.pause();
      abortRef.current?.abort();
      ttsAbortRef.current?.abort();
      ttsQueueRef.current = [];
      ttsClosedRef.current = true;
      ttsWakeRef.current?.();
    };
  }, [initSession]);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({behavior: 'smooth'});
  }, [messages, loading]);

  const stopSpeaking = useCallback(() => {
    ttsAbortRef.current?.abort();
    ttsAbortRef.current = null;
    ttsQueueRef.current = [];
    ttsClosedRef.current = true;
    ttsWakeRef.current?.();
    ttsWakeRef.current = null;
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setSpeaking(false);
  }, []);

  useEffect(() => {
    ttsEnabledRef.current = ttsEnabled;
    if (!ttsEnabled) stopSpeaking();
  }, [ttsEnabled, stopSpeaking]);

  // Queue player: consumes chunks as they arrive (live during the text
  // stream), prefetching the next synthesis while the current audio plays.
  const startTTSPlayer = useCallback(() => {
    const controller = new AbortController();
    ttsAbortRef.current = controller;

    const fetchChunk = async (chunk: string): Promise<string | null> => {
      const params = new URLSearchParams({text: chunk, lang: locale});
      if (ttsSlugRef.current) params.set('module_slug', ttsSlugRef.current);
      try {
        const r = await fetch(`/api/chat/tts/?${params.toString()}`, {
          signal: controller.signal,
        });
        if (!r.ok) return null;
        return URL.createObjectURL(await r.blob());
      } catch {
        return null;
      }
    };

    const run = async () => {
      setSpeaking(true);
      let url: string | null = null;
      let prefetch: Promise<string | null> | null = null;
      while (!controller.signal.aborted) {
        if (!url) {
          if (ttsQueueRef.current.length === 0) {
            if (ttsClosedRef.current) break;
            await new Promise<void>((res) => {
              ttsWakeRef.current = res;
            });
            ttsWakeRef.current = null;
            continue;
          }
          const chunk = ttsQueueRef.current.shift()!;
          url = prefetch ? await prefetch : await fetchChunk(chunk);
          prefetch = null;
        }
        if (!prefetch && ttsQueueRef.current.length > 0) {
          prefetch = fetchChunk(ttsQueueRef.current[0]);
        }
        if (url) {
          const currentUrl = url;
          url = null;
          await new Promise<void>((resolve) => {
            const audio = new Audio(currentUrl);
            audioRef.current = audio;
            const finish = () => {
              URL.revokeObjectURL(currentUrl);
              if (audioRef.current === audio) audioRef.current = null;
              resolve();
            };
            audio.onended = finish;
            audio.onerror = finish;
            // pause() from stopSpeaking must also unblock the queue loop
            audio.onpause = finish;
            audio.play().catch(finish);
          });
        }
      }
      if (url) URL.revokeObjectURL(url);
      prefetch?.then((u) => {
        if (u) URL.revokeObjectURL(u);
      });
      if (!controller.signal.aborted) setSpeaking(false);
    };
    run();
  }, [locale]);

  const enqueueTTS = useCallback((chunk: string) => {
    if (!ttsEnabledRef.current) return;
    ttsQueueRef.current.push(chunk);
    ttsWakeRef.current?.();
  }, []);

  const closeTTS = useCallback(() => {
    ttsClosedRef.current = true;
    ttsWakeRef.current?.();
  }, []);

  const initTTS = useCallback(
    (slug: string) => {
      stopSpeaking();
      ttsClosedRef.current = false;
      ttsSlugRef.current = slug;
      startTTSPlayer();
    },
    [stopSpeaking, startTTSPlayer],
  );

  // Full-text path (module greetings): feed everything at once and close.
  const playResponse = useCallback(
    (text: string, moduleSlug?: string | null) => {
      if (!ttsEnabled) return;
      initTTS(moduleSlug ?? activeModuleSlug ?? '');
      const chunker = createTTSChunker(enqueueTTS, locale === 'en');
      feedAllToChunks(chunker, text);
      closeTTS();
    },
    [ttsEnabled, initTTS, enqueueTTS, closeTTS, activeModuleSlug],
  );

  // Listen for module-specific chat activation from module pages
  useEffect(() => {
    const handleModuleChatOpen = (e: Event) => {
      const { slug, greeting } = (e as CustomEvent).detail || {};
      if (slug) {
        setActiveModuleSlug(slug);
        setIsOpen(true);

        if (greeting) {
          const greetMsg: Message = {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: greeting,
            timestamp: new Date(),
          };
          setMessages(prev => [...prev, greetMsg]);
          playResponse(greeting, slug);
        }
      }
    };

    window.addEventListener('openModuleChat', handleModuleChatOpen);
    return () => {
      window.removeEventListener('openModuleChat', handleModuleChatOpen);
    };
  }, [playResponse]);

  const sendMessage = useCallback(
    async (text?: string) => {
      const message = (text ?? input).trim();
      if (!message || loading) return;

      // Session not established (e.g. the initial /api/chat/session/ call failed):
      // surface it visibly and try again, instead of dropping the input silently.
      if (!sessionId) {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'user',
            content: message,
            timestamp: new Date(),
          },
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: t('errSession'),
            timestamp: new Date(),
          },
        ]);
        if (!text) setInput('');
        initSession();
        return;
      }

      stopSpeaking();
      // Voice follows the text: completed sentences go to synthesis while
      // the answer is still streaming (queue player consumes them live).
      if (ttsEnabled) initTTS(activeModuleSlug ?? '');
      const ttsChunker = createTTSChunker(enqueueTTS, locale === 'en');

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: message,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      if (!text) setInput('');
      setLoading(true);

      const controller = new AbortController();
      abortRef.current = controller;

      // Streaming reply state lives in locals/refs: React state is flushed in
      // ~60ms batches so ReactMarkdown is not re-parsed on every token.
      let msgId: string | null = null;
      let fullText = '';
      let finalSlug = activeModuleSlug ?? '';
      let flushTimer: ReturnType<typeof setInterval> | null = null;

      const flush = () => {
        if (!msgId) return;
        const id = msgId;
        const snapshot = fullText;
        setMessages((prev) =>
          prev.map((m) => (m.id === id ? {...m, content: snapshot} : m)),
        );
        ttsChunker.feed(snapshot);
      };
      const stopFlush = () => {
        if (flushTimer) {
          clearInterval(flushTimer);
          flushTimer = null;
        }
      };

      try {
        const res = await fetch('/api/chat/message/stream/', {
          method: 'POST',
          headers: {'Content-Type': 'application/json', Accept: 'text/event-stream'},
          body: JSON.stringify({
            session_id: sessionId,
            message,
            lang: locale,
            module_slug: activeModuleSlug || '',
          }),
          signal: controller.signal,
        });
        if (!res.ok || !res.body) throw new Error('Failed');

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';
        let finished = false;

        while (!finished) {
          const {done, value} = await reader.read();
          if (done) break;
          buffer += decoder.decode(value, {stream: true});

          let sep: number;
          while ((sep = buffer.indexOf('\n\n')) >= 0) {
            const rawEvent = buffer.slice(0, sep);
            buffer = buffer.slice(sep + 2);
            let eventName = 'message';
            const dataLines: string[] = [];
            for (const line of rawEvent.split('\n')) {
              if (line.startsWith('event:')) eventName = line.slice(6).trim();
              else if (line.startsWith('data:')) dataLines.push(line.slice(5).trim());
            }
            if (dataLines.length === 0) continue;
            let data: {text?: string; module_slug?: string; error?: string};
            try {
              data = JSON.parse(dataLines.join('\n'));
            } catch {
              continue;
            }

            if (eventName === 'meta') {
              // The backend may switch the persona mid-reply (activate_module)
              // or hand back to the coordinator — sync the slug both ways so
              // the next TTS chunks use the effective voice.
              finalSlug = data.module_slug || '';
              setActiveModuleSlug(finalSlug || null);
              ttsSlugRef.current = finalSlug;
            } else if (eventName === 'delta') {
              fullText += data.text || '';
              if (!msgId) {
                msgId = crypto.randomUUID();
                const id = msgId;
                setMessages((prev) => [
                  ...prev,
                  {id, role: 'assistant', content: '', timestamp: new Date()},
                ]);
                setStreamingId(id);
                flushTimer = setInterval(flush, 60);
              }
            } else if (eventName === 'done') {
              finished = true;
              stopFlush();
              // done.text is authoritative (reconciles any lost deltas)
              const text = data.text || fullText || t('errNoResponse');
              const slug = data.module_slug ?? finalSlug;
              if (msgId) {
                const id = msgId;
                setMessages((prev) =>
                  prev.map((m) => (m.id === id ? {...m, content: text} : m)),
                );
              } else {
                setMessages((prev) => [
                  ...prev,
                  {id: crypto.randomUUID(), role: 'assistant', content: text, timestamp: new Date()},
                ]);
              }
              setActiveModuleSlug(slug || null);
              ttsSlugRef.current = slug;
              feedAllToChunks(ttsChunker, text);
              closeTTS();
              reader.cancel();
            } else if (eventName === 'error') {
              throw new Error(data.error || 'stream error');
            }
          }
        }
        // Connection ended without a done event: keep whatever was streamed
        if (!finished) {
          stopFlush();
          flush();
          feedAllToChunks(ttsChunker, fullText);
          closeTTS();
        }
      } catch {
        stopFlush();
        if (msgId && fullText) {
          flush();
        } else if (!controller.signal.aborted) {
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: t('errAi'),
              timestamp: new Date(),
            },
          ]);
        }
        if (!controller.signal.aborted) {
          feedAllToChunks(ttsChunker, fullText);
          closeTTS();
        }
      } finally {
        stopFlush();
        abortRef.current = null;
        setStreamingId(null);
        setLoading(false);
      }
    },
    [input, loading, sessionId, ttsEnabled, initTTS, enqueueTTS, closeTTS, stopSpeaking, locale, t, initSession, activeModuleSlug],
  );

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({audio: true});
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((tr) => tr.stop());
        setIsRecording(false);

        const audioBlob = new Blob(audioChunksRef.current, {type: 'audio/webm'});
        if (!sessionId) return;

        setLoading(true);
        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');

          const res = await fetch(`/api/chat/voice/stt/?session_id=${sessionId}&lang=${locale}`, {
            method: 'POST',
            body: formData,
          });

          if (res.ok) {
            const data = await res.json();
            if (data.text) {
              sendMessage(data.text);
              return;
            }
          }
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: t('errStt'),
              timestamp: new Date(),
            },
          ]);
        } catch {
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: t('errStt2'),
              timestamp: new Date(),
            },
          ]);
        } finally {
          setLoading(false);
        }
      };

      recorder.start();
      setIsRecording(true);
    } catch {
      setMessages((prev) => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: t('errMic'),
          timestamp: new Date(),
        },
      ]);
    }
  }, [sessionId, sendMessage, locale, t]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
  }, []);

  const clearHistory = () => {
    stopSpeaking();
    abortRef.current?.abort();
    setStreamingId(null);
    setMessages([]);
  };

  return (
    <>
      {/* Floating HUD launcher button */}
      <motion.button
        initial={{scale: 0}}
        animate={{scale: 1}}
        whileHover={{scale: 1.06}}
        whileTap={{scale: 0.96}}
        onClick={() => setIsOpen(!isOpen)}
        className="h-[62px] fixed right-5 bottom-[var(--hud-bottom,0.75rem)] sm:bottom-[var(--hud-bottom,1.25rem)] z-50 group flex items-center gap-3 px-4 py-3
                   bg-[#090e20]/95 backdrop-blur-md border border-neon-cyan/70
                   shadow-[0_0_24px_rgba(0,243,255,0.35)] hover:shadow-[0_0_34px_rgba(255,43,214,0.55)]
                   hover:border-neon-magenta transition-all"
        style={{
          clipPath:
            'polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)',
        }}
        aria-label={t('launcherAria')}
      >
        <span className="relative flex items-center justify-center w-8 h-8 hex-icon hex-cyan !w-8 !h-8">
          {isOpen ? (
            <X className="w-4 h-4 text-neon-cyan" />
          ) : (
            <Bot className="w-4 h-4 text-neon-cyan" />
          )}
        </span>
        <div className="hidden sm:flex flex-col items-start text-left pr-1">
          <span className="font-mono text-[9px] tracking-[0.2em] text-neon-cyan flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-[#22c55e] animate-ping" />
            {t('coreOnline')}
          </span>
          <span className="font-display font-bold text-xs tracking-wider text-white">
            {isOpen ? t('closeLabel') : t('openLabel')}
          </span>
        </div>
      </motion.button>

      {/* Holographic AI Assistant Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{opacity: 0, y: 24, scale: 0.96}}
            animate={{opacity: 1, y: 0, scale: 1}}
            exit={{opacity: 0, y: 24, scale: 0.96}}
            transition={{duration: 0.22}}
            className={`fixed right-5 top-[76px] bottom-[calc(var(--hud-bottom,0.75rem)+66px)] sm:bottom-[calc(var(--hud-bottom,1.25rem)+66px)] z-50 drop-shadow-[0_0_24px_rgba(0,243,255,0.22)] ${
              expanded ? 'w-[calc(100vw-2.5rem)] max-w-2xl' : 'w-[calc(100vw-2.5rem)] max-w-[430px]'
            }`}
          >
            <div className="cyber-frame h-full w-full">
              <div className="cyber-frame-body flex flex-col h-full relative overflow-hidden">
              <span className="cb cb-tl" />
              <span className="cb cb-br" />

              {/* Top HUD Header */}
              <div className="px-4 py-3.5 border-b border-neon-cyan/25 bg-[#060a18]/70 flex items-center justify-between gap-2">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="hex-icon hex-cyan !w-10 !h-10 shrink-0">
                    <Bot className="w-5 h-5 text-neon-cyan" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-display font-bold text-xs tracking-wider text-white truncate">
                        NEURAL LINK // QWEN-RAG
                      </span>
                    </div>
                    <div className="font-mono text-[10px] tracking-widest text-zinc-400 flex items-center gap-1.5 mt-0.5">
                      <span
                        className={`w-1.5 h-1.5 rounded-full ${
                          isRecording
                            ? 'bg-red-500 animate-ping'
                            : loading
                              ? 'bg-acid-yellow animate-pulse'
                              : 'bg-[#22c55e]'
                        }`}
                      />
                      {isRecording
                        ? 'VOICE CAPTURE ACTIVE...'
                        : speaking
                          ? 'SYNTH VOICE OUTPUT...'
                          : loading
                            ? streamingId
                              ? 'LIVE TRANSMISSION...'
                              : 'QUERYING VECTOR MATRIX...'
                            : 'UPLINK STABLE • NODE 44-A'}
                    </div>
                  </div>
                </div>

                {/* Action buttons */}
                <div className="flex items-center gap-1 shrink-0">
                  <button
                    type="button"
                    onClick={() => {
                      if (speaking) stopSpeaking();
                      setTtsEnabled((v) => !v);
                    }}
                    className={`p-1.5 border transition-colors ${
                      ttsEnabled
                        ? 'border-neon-cyan/40 text-neon-cyan bg-neon-cyan/10'
                        : 'border-cyber-border text-zinc-500 hover:text-zinc-300'
                    }`}
                    title={ttsEnabled ? t('ttsOn') : t('ttsOff')}
                  >
                    {ttsEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                  </button>
                  {messages.length > 0 && (
                    <button
                      type="button"
                      onClick={clearHistory}
                      className="p-1.5 border border-cyber-border text-zinc-400 hover:text-neon-magenta hover:border-neon-magenta/50 transition-colors"
                      title={t('clear')}
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setExpanded((v) => !v)}
                    className="hidden sm:inline-flex p-1.5 border border-cyber-border text-zinc-400 hover:text-neon-cyan hover:border-neon-cyan/50 transition-colors"
                    title={expanded ? t('collapse') : t('expand')}
                  >
                    {expanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 border border-cyber-border text-zinc-400 hover:text-neon-magenta hover:border-neon-magenta/50 transition-colors"
                    title={t('close')}
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Messages Feed */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-gradient-to-b from-[#070b18]/45 to-[#050813]/65">
                {messages.length === 0 && (
                  <div className="py-4 px-2">
                    <div className="p-4 border border-neon-cyan/25 bg-neon-cyan/5 mb-4 relative">
                      <div className="flex items-center gap-2 text-neon-cyan font-mono text-[10px] tracking-[0.2em] mb-1.5">
                        <Terminal className="w-3.5 h-3.5" />
                        {t('sysInit')}
                      </div>
                      <p className="text-xs font-mono text-zinc-300 leading-relaxed">
                        {t('greeting')}
                      </p>
                    </div>

                    <div className="font-mono text-[10px] tracking-[0.18em] text-zinc-400 mb-2.5 flex items-center gap-1.5">
                      <Sparkles className="w-3 h-3 text-neon-magenta" />
                      {t('quickLabel')}
                    </div>
                    <div className="grid grid-cols-1 gap-2">
                      {quickPrompts.map((prompt) => (
                        <button
                          key={prompt}
                          type="button"
                          onClick={() => sendMessage(prompt)}
                          className="text-left px-3 py-2 text-xs font-mono text-zinc-200 bg-[#0d1428]/90
                                     border border-neon-cyan/30 hover:border-neon-cyan hover:text-neon-cyan
                                     hover:bg-neon-cyan/10 transition-all flex items-center justify-between group"
                        >
                          <span className="truncate">{prompt}</span>
                          <span className="text-neon-cyan opacity-60 group-hover:opacity-100 group-hover:translate-x-0.5 transition-all">
                            →
                          </span>
                        </button>
                      ))}
                    </div>
                  </div>
                )}

                {messages.map((msg) => (
                  <motion.div
                    key={msg.id}
                    initial={{opacity: 0, y: 8}}
                    animate={{opacity: 1, y: 0}}
                    className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <span className="font-mono text-[9px] tracking-[0.16em] text-zinc-500 mb-1 px-1">
                      {msg.role === 'user' ? t('userTag') : t('aiTag')} •{' '}
                      {msg.timestamp.toLocaleTimeString(timeLocale, {
                        hour: '2-digit',
                        minute: '2-digit',
                      })}
                    </span>
                    <div
                      className={`max-w-[88%] px-3.5 py-2.5 text-xs sm:text-sm leading-relaxed ${
                        msg.role === 'user'
                          ? 'bg-gradient-to-r from-neon-magenta/25 to-neon-purple/25 border border-neon-magenta/60 text-white shadow-[0_0_16px_rgba(255,43,214,0.18)]'
                          : 'bg-[#0e162d]/95 border border-neon-cyan/40 text-zinc-100 shadow-[0_0_16px_rgba(0,243,255,0.1)]'
                      }`}
                      style={{
                        clipPath:
                          'polygon(8px 0, 100% 0, 100% calc(100% - 8px), calc(100% - 8px) 100%, 0 100%, 0 8px)',
                      }}
                    >
                      {msg.role === 'assistant' ? (
                        <div className="chat-md">
                          <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            rehypePlugins={[rehypeHighlight]}
                          >
                            {msg.content}
                          </ReactMarkdown>
                        </div>
                      ) : (
                        <span className="whitespace-pre-wrap break-words">{msg.content}</span>
                      )}
                    </div>
                  </motion.div>
                ))}

                {loading && !streamingId && (
                  <div className="flex items-start gap-2">
                    <div className="px-3.5 py-2.5 bg-[#0e162d]/95 border border-neon-cyan/40 flex items-center gap-2.5">
                      <Loader2 className="w-4 h-4 text-neon-cyan animate-spin" />
                      <span className="font-mono text-xs text-neon-cyan tracking-wider">
                        {t('synth')}
                      </span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Bar */}
              <div className="p-3 border-t border-neon-cyan/25 bg-[#060a18]/80">
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={isRecording ? stopRecording : startRecording}
                    disabled={loading}
                    className={`p-2.5 border transition-all shrink-0 ${
                      isRecording
                        ? 'border-red-500 text-red-400 bg-red-500/20 animate-pulse shadow-[0_0_14px_rgba(239,68,68,0.5)]'
                        : 'border-neon-purple/50 text-neon-purple bg-neon-purple/10 hover:border-neon-magenta hover:text-neon-magenta disabled:opacity-40'
                    }`}
                    style={{
                      clipPath:
                        'polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px)',
                    }}
                    title={isRecording ? t('micOn') : t('micOff')}
                  >
                    {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  </button>

                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder={t('placeholder')}
                    disabled={loading}
                    className="flex-1 min-w-0 px-3.5 py-2.5 bg-[#0b1224] border border-neon-cyan/35 text-xs sm:text-sm text-white
                               placeholder-zinc-500 font-mono focus:outline-none focus:border-neon-cyan
                               focus:shadow-[0_0_14px_rgba(0,243,255,0.25)] disabled:opacity-50"
                  />

                  <button
                    type="button"
                    onClick={() => sendMessage()}
                    disabled={loading || !input.trim()}
                    className="cyber-btn btn-primary p-2.5 shrink-0 flex items-center justify-center disabled:opacity-35 disabled:pointer-events-none"
                    style={{
                      clipPath:
                        'polygon(6px 0, 100% 0, 100% calc(100% - 6px), calc(100% - 6px) 100%, 0 100%, 0 6px)',
                    }}
                    title={t('send')}
                  >
                    <Send className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}