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
} from 'lucide-react';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

export default function ChatWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [speaking, setSpeaking] = useState(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // Initialize session
  useEffect(() => {
    fetch('/api/chat/session/')
      .then(r => r.json())
      .then(data => setSessionId(data.session_id))
      .catch(() => {});

    return () => {
      if (audioRef.current) audioRef.current.pause();
    };
  }, []);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const stopSpeaking = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    setSpeaking(false);
  }, []);

  const playResponse = useCallback((text: string) => {
    // Use TTS endpoint to get audio
    stopSpeaking();
    fetch(`/api/chat/tts/?text=${encodeURIComponent(text.slice(0, 500))}`)
      .then(r => r.ok ? r.blob() : null)
      .then(blob => {
        if (!blob) return;
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => {
          setSpeaking(false);
          URL.revokeObjectURL(url);
        };
        audio.play().then(() => setSpeaking(true)).catch(() => setSpeaking(false));
      })
      .catch(() => setSpeaking(false));
  }, [stopSpeaking]);

  const sendMessage = useCallback(async (text?: string) => {
    const message = text ?? input.trim();
    if (!message || loading || !sessionId) return;

    stopSpeaking();

    const userMsg: Message = {
      id: crypto.randomUUID(),
      role: 'user',
      content: message,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
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
      setMessages(prev => [...prev, assistantMsg]);
      playResponse(assistantMsg.content);
    } catch {
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: '⚠️ AI-сервис временно недоступен. Попробуйте позже.',
          timestamp: new Date(),
        },
      ]);
    } finally {
      setLoading(false);
    }
  }, [input, loading, sessionId, playResponse, stopSpeaking]);

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
        stream.getTracks().forEach(t => t.stop());
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
              // Show recognized text and send it
              const userMsg: Message = {
                id: crypto.randomUUID(),
                role: 'user',
                content: `🎤 ${data.text}`,
                timestamp: new Date(),
              };
              setMessages(prev => [...prev, userMsg]);
              sendMessage(data.text);
              return;
            }
          }
          setMessages(prev => [
            ...prev,
            {
              id: crypto.randomUUID(),
              role: 'assistant',
              content: '⚠️ Не удалось распознать речь. Попробуйте ещё раз.',
              timestamp: new Date(),
            },
          ]);
        } catch {
          setMessages(prev => [
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
      setMessages(prev => [
        ...prev,
        {
          id: crypto.randomUUID(),
          role: 'assistant',
          content: '⚠️ Нет доступа к микрофону.',
          timestamp: new Date(),
        },
      ]);
    }
  }, [sessionId, sendMessage]);

  const stopRecording = useCallback(() => {
    mediaRecorderRef.current?.stop();
  }, []);

  return (
    <>
      {/* Floating button */}
      <motion.button
        initial={{ scale: 0 }}
        animate={{ scale: 1 }}
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.95 }}
        onClick={() => setIsOpen(!isOpen)}
        className="fixed bottom-6 right-6 z-50 w-14 h-14 rounded-full flex items-center justify-center
                   bg-cyber-card border-2 border-neon-cyan/50 shadow-neon-cyan
                   hover:shadow-neon-cyan-lg hover:border-neon-cyan transition-all"
        aria-label="AI-ассистент"
      >
        {isOpen ? (
          <X className="w-6 h-6 text-neon-cyan" />
        ) : (
          <Bot className="w-6 h-6 text-neon-cyan" />
        )}
        {!isOpen && (
          <span className="absolute -top-1 -right-1 w-3 h-3 rounded-full bg-neon-cyan animate-neon-pulse" />
        )}
      </motion.button>

      {/* Chat panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, y: 20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: 20, scale: 0.95 }}
            className="fixed bottom-24 right-6 z-50 w-[calc(100vw-3rem)] max-w-md h-[500px] max-h-[70vh]
                       rounded-xl overflow-hidden bg-cyber-card/95 backdrop-blur-md
                       border border-neon-cyan/30 shadow-[0_0_40px_rgba(0,243,255,0.15)]"
          >
            {/* Header */}
            <div className="px-4 py-3 border-b border-cyber-border bg-cyber-black/50 flex items-center gap-3">
              <div className="relative">
                <Bot className="w-5 h-5 text-neon-cyan" />
                <span className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-green-400" />
              </div>
              <div className="flex-1">
                <div className="text-sm font-semibold text-foreground">AI-ассистент</div>
                <div className="text-xs text-zinc-500">
                  {isRecording ? '🎙 Запись...' : speaking ? '🔊 Озвучка...' : 'Онлайн'}
                </div>
              </div>
              {speaking && (
                <button onClick={stopSpeaking} className="p-1.5 text-zinc-400 hover:text-neon-cyan">
                  <VolumeX className="w-4 h-4" />
                </button>
              )}
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {messages.length === 0 && (
                <div className="text-center py-8">
                  <Bot className="w-10 h-10 text-zinc-600 mx-auto mb-3" />
                  <p className="text-sm text-zinc-500">
                    Спросите о моих проектах или статьях.
                    <br />
                    Например: «Какие технологии ты используешь?»
                  </p>
                </div>
              )}

              {messages.map(msg => (
                <motion.div
                  key={msg.id}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div
                    className={`max-w-[85%] px-3 py-2 rounded-xl text-sm ${
                      msg.role === 'user'
                        ? 'bg-neon-cyan/10 border border-neon-cyan/20 text-foreground'
                        : 'bg-zinc-800/50 border border-zinc-700 text-zinc-300'
                    }`}
                  >
                    {msg.content}
                  </div>
                </motion.div>
              ))}

              {loading && (
                <div className="flex justify-start">
                  <div className="px-3 py-2 rounded-xl bg-zinc-800/50 border border-zinc-700">
                    <Loader2 className="w-4 h-4 text-neon-cyan animate-spin" />
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            {/* Input */}
            <div className="p-3 border-t border-cyber-border bg-cyber-black/30">
              <div className="flex items-center gap-2">
                <button
                  onClick={isRecording ? stopRecording : startRecording}
                  disabled={loading}
                  className={`p-2 rounded-lg border transition-colors ${
                    isRecording
                      ? 'border-red-500 text-red-400 bg-red-500/10 animate-pulse'
                      : 'border-zinc-700 text-zinc-400 hover:border-zinc-500 disabled:opacity-50'
                  }`}
                  title={isRecording ? 'Остановить запись' : 'Голосовой ввод'}
                >
                  {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                </button>

                <input
                  type="text"
                  value={input}
                  onChange={e => setInput(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && sendMessage()}
                  placeholder="Спросите о проектах..."
                  disabled={loading}
                  className="flex-1 px-3 py-2 bg-zinc-900 border border-zinc-700 rounded-lg text-sm text-foreground
                             placeholder-zinc-600 focus:outline-none focus:border-neon-cyan/50 disabled:opacity-50"
                />

                <button
                  onClick={() => sendMessage()}
                  disabled={loading || !input.trim()}
                  className="p-2 rounded-lg bg-neon-cyan/10 border border-neon-cyan/30 text-neon-cyan
                             hover:bg-neon-cyan/20 disabled:opacity-30 disabled:cursor-not-allowed"
                  title="Отправить"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
