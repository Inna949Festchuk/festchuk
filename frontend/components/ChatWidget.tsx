'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
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

const QUICK_PROMPTS = [
  'Расскажи про проекты',
  'Какой стек технологий?',
  'О чём статьи в блоге?',
  'Как связаться с Константином?',
];

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(true);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Initialize session
  useEffect(() => {
    fetch('/api/chat/session/')
      .then((r) => r.json())
      .then((data) => setSessionId(data.session_id))
      .catch(() => {});

    return () => {
      if (audioRef.current) audioRef.current.pause();
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, loading]);

  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setSpeaking(false);
  }, []);

  const playResponse = useCallback(
    (text: string) => {
      if (!ttsEnabled) return;
      stopSpeaking();
      fetch(`/api/chat/tts/?text=${encodeURIComponent(text.slice(0, 500))}`)
        .then((r) => (r.ok ? r.blob() : null))
        .then((blob) => {
          if (!blob) return;
          const url = URL.createObjectURL(blob);
          const audio = new Audio(url);
          audioRef.current = audio;
          audio.onended = () => {
            setSpeaking(false);
            URL.revokeObjectURL(url);
          };
          audio
            .play()
            .then(() => setSpeaking(true))
            .catch(() => setSpeaking(false));
        })
        .catch(() => setSpeaking(false));
    },
    [stopSpeaking, ttsEnabled],
  );

  const sendMessage = useCallback(
    async (text?: string) => {
      const message = (text ?? input).trim();
      if (!message || loading || !sessionId) return;

      stopSpeaking();

      const userMsg: Message = {
        id: crypto.randomUUID(),
        role: 'user',
        content: message,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, userMsg]);
      if (!text) setInput('');
      setLoading(true);

      try {
        const res = await fetch('/api/chat/message/', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            session_id: sessionId,
            message,
          }),
        });

        if (!res.ok) throw new Error('Failed');
        const data = await res.json();

        const assistantMsg: Message = {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: data.message?.content || 'Не удалось получить ответ',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMsg]);
        playResponse(assistantMsg.content);
      } catch {
        setMessages((prev) => [
          ...prev,
          {
            id: crypto.randomUUID(),
            role: 'assistant',
            content: '⚠️ AI-сервис временно недоступен. Проверьте подключение или попробуйте позже.',
            timestamp: new Date(),
          },
        ]);
      } finally {
        setLoading(false);
      }
    },
    [input, loading, sessionId, playResponse, stopSpeaking],
  );

  const startRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;
      audioChunksRef.current = [];

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((t) => t.stop());
        setIsRecording(false);

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (!sessionId) return;

        setLoading(true);
        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');

          const res = await fetch(`/api/chat/voice/stt/?session_id=${sessionId}`, {
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
              content: '⚠️ Не удалось распознать речь. Попробуйте ещё раз.',
              timestamp: new Date(),
            },
          ]);
        } catch {
          setMessages((prev) => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: '⚠️ Ошибка распознавания речи.',
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
          content: '⚠️ Нет доступа к микрофону в браузере.',
          timestamp: new Date(),
        },
      ]);
    }
  }, [sessionId, sendMessage]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
  }, []);

  const clearHistory = () => {
    stopSpeaking();
    setMessages([]);
  };

  return (
    <>
      {/* Floating HUD launcher button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.06 }}
        whileTap={{ scale: 0.96 }}
        onClick={() => setIsOpen(!isOpen)}
        className="fixed right-5 bottom-[132px] sm:bottom-[72px] z-50 group flex items-center gap-3 px-4 py-3
                   bg-[#090e20]/95 backdrop-blur-md border border-neon-cyan/70
                   shadow-[0_0_24px_rgba(0,243,255,0.35)] hover:shadow-[0_0_34px_rgba(255,43,214,0.55)]
                   hover:border-neon-magenta transition-all"
        style={{
          clipPath:
            'polygon(10px 0, 100% 0, 100% calc(100% - 10px), calc(100% - 10px) 100%, 0 100%, 0 10px)',
        }}
        aria-label="Открыть нейро-ассистента"
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
            AI CORE // ONLINE
          </span>
          <span className="font-display font-bold text-xs tracking-wider text-white">
            {isOpen ? 'CLOSE TERMINAL' : 'NEURAL ASSIST'}
          </span>
        </div>
      </motion.button>

      {/* Holographic AI Assistant Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 24, scale: 0.96 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 24, scale: 0.96 }}
            transition={{ duration: 0.22 }}
            className={`fixed right-5 top-[76px] bottom-[198px] sm:bottom-[138px] z-50 drop-shadow-[0_0_24px_rgba(0,243,255,0.22)] ${
              expanded ? 'w-[calc(100vw-2.5rem)] max-w-2xl' : 'w-[calc(100vw-2.5rem)] max-w-[430px]'
            }`}
          >
            <div className="cyber-frame h-full w-full">
              <div className="cyber-frame-body flex flex-col h-full relative overflow-hidden">
              <span className="cb cb-tl" />
              <span className="cb cb-br" />

              {/* Top HUD Header */}
              <div className="px-4 py-3.5 border-b border-neon-cyan/25 bg-[#060a18]/90 flex items-center justify-between gap-2">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="hex-icon hex-cyan !w-10 !h-10 shrink-0">
                    <Bot className="w-5 h-5 text-neon-cyan" />
                  </div>
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-display font-bold text-xs tracking-wider text-white truncate">
                        NEURAL LINK // QWEN-RAG
                      </span>
                      <span className="px-1.5 py-0.5 text-[9px] font-mono bg-neon-cyan/15 text-neon-cyan border border-neon-cyan/40">
                        v3.5
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
                            ? 'QUERYING VECTOR MATRIX...'
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
                    title={ttsEnabled ? 'Автоозвучка включена' : 'Автоозвучка выключена'}
                  >
                    {ttsEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
                  </button>
                  {messages.length > 0 && (
                    <button
                      type="button"
                      onClick={clearHistory}
                      className="p-1.5 border border-cyber-border text-zinc-400 hover:text-neon-magenta hover:border-neon-magenta/50 transition-colors"
                      title="Очистить диалог"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  )}
                  <button
                    type="button"
                    onClick={() => setExpanded((v) => !v)}
                    className="hidden sm:inline-flex p-1.5 border border-cyber-border text-zinc-400 hover:text-neon-cyan hover:border-neon-cyan/50 transition-colors"
                    title={expanded ? 'Свернуть окно' : 'Развернуть окно'}
                  >
                    {expanded ? <Minimize2 className="w-3.5 h-3.5" /> : <Maximize2 className="w-3.5 h-3.5" />}
                  </button>
                  <button
                    type="button"
                    onClick={() => setIsOpen(false)}
                    className="p-1.5 border border-cyber-border text-zinc-400 hover:text-neon-magenta hover:border-neon-magenta/50 transition-colors"
                    title="Закрыть"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>

              {/* Messages Feed */}
              <div className="flex-1 overflow-y-auto p-4 space-y-3.5 bg-gradient-to-b from-[#070b18]/80 to-[#050813]/95">
                {messages.length === 0 && (
                  <div className="py-4 px-2">
                    <div className="p-4 border border-neon-cyan/25 bg-neon-cyan/5 mb-4 relative">
                      <div className="flex items-center gap-2 text-neon-cyan font-mono text-[10px] tracking-[0.2em] mb-1.5">
                        <Terminal className="w-3.5 h-3.5" />
                        SYSTEM INITIALIZED
                      </div>
                      <p className="text-xs text-zinc-300 leading-relaxed">
                        Привет! Я нейросетевой ассистент Константина Фестчука с доступом к базе
                        проектов, GitHub README и статьям блога через RAG.
                      </p>
                    </div>

                    <div className="font-mono text-[10px] tracking-[0.18em] text-zinc-400 mb-2.5 flex items-center gap-1.5">
                      <Sparkles className="w-3 h-3 text-neon-magenta" />
                      БЫСТРЫЕ КОМАНДЫ:
                    </div>
                    <div className="grid grid-cols-1 gap-2">
                      {QUICK_PROMPTS.map((prompt) => (
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
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}
                  >
                    <span className="font-mono text-[9px] tracking-[0.16em] text-zinc-500 mb-1 px-1">
                      {msg.role === 'user' ? 'USER // INPUT' : 'AI CORE // RESPONSE'} •{' '}
                      {msg.timestamp.toLocaleTimeString('ru-RU', {
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
                      {msg.content}
                    </div>
                  </motion.div>
                ))}

                {loading && (
                  <div className="flex items-start gap-2">
                    <div className="px-3.5 py-2.5 bg-[#0e162d]/95 border border-neon-cyan/40 flex items-center gap-2.5">
                      <Loader2 className="w-4 h-4 text-neon-cyan animate-spin" />
                      <span className="font-mono text-xs text-neon-cyan tracking-wider">
                        СИНТЕЗ ОТВЕТА...
                      </span>
                    </div>
                  </div>
                )}
                <div ref={messagesEndRef} />
              </div>

              {/* Input Bar */}
              <div className="p-3 border-t border-neon-cyan/25 bg-[#060a18]/95">
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
                    title={isRecording ? 'Остановить запись' : 'Голосовой ввод (STT)'}
                  >
                    {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                  </button>

                  <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
                    placeholder="Введите запрос в нейросеть..."
                    disabled={loading}
                    className="flex-1 min-w-0 px-3.5 py-2.5 bg-[#0b1224] border border-neon-cyan/35 text-xs sm:text-sm text-white
                               placeholder-zinc-500 font-mono focus:outline-none focus:border-neon-cyan
                               focus:shadow-[0_0_14px_rgba(0,243,255,0.25)] disabled:opacity-50"
                  />

                  <button
                    type="button"
                    onClick={() => sendMessage()}
                    disabled={loading || !input.trim()}
                    className="cyber-btn btn-primary px-4 py-2.5 text-xs font-bold shrink-0 disabled:opacity-35 disabled:pointer-events-none"
                    title="Отправить запрос"
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
