// Постобработка текста, уходящего в TTS (чистые функции, без React/DOM —
// модуль тестируется в node). Синтезатор (Gemini) выбирает язык по
// плотности английского в куске: насыщенные терминами фразы он читает
// по-английски, даже если они начинаются с кириллицы. Поэтому снижаем
// плотность английского и заменяем английские связки:
//   1. убираем английские скобки-глоссы («Nginx (reverse proxy, rate
//      limiting, static/media)» → «Nginx») — текст на экране не меняется;
//   2. известные английские связки заменяем русскими эквивалентами.
// Перенос лейблов («Label — описание» → «описание — это Label») удалён:
// он ломал грамматику в середине фразы («усилен pgvector» → «усилен Я
// перевожу… — это pgvector») и склеивал буллеты в монстр-предложение
// (инцидент 2026-11-20). Промт-правила (agent.py) сами снижают английские
// начала предложений.
// en=true (англоязычный UI) — pass-through: продукт русскоязычный.

// Фразы целиком, по \b, регистронезависимо; редкие в русской речи.
const ENGLISH_CONNECTIVES: Array<[RegExp, string]> = [
  [/\bas mentioned above\b/gi, 'как уже говорилось'],
  [/\bin summary\b/gi, 'в общем итоге'],
  [/\bin conclusion\b/gi, 'в итоге'],
  [/\bfor example\b/gi, 'например'],
  [/\bfor instance\b/gi, 'к примеру'],
  [/\bin particular\b/gi, 'в частности'],
  [/\bin addition\b/gi, 'кроме того'],
  [/\bfurthermore\b/gi, 'кроме того'],
  [/\bmoreover\b/gi, 'ещё'],
  [/\blet me explain\b/gi, 'поясню'],
  [/\bnote that\b/gi, 'обрати внимание'],
];

const applyConnectives = (s: string): string =>
  ENGLISH_CONNECTIVES.reduce((acc, [re, ru]) => acc.replace(re, ru), s);

// Доля кирилличных букв в латинице+кириллице строки (0..1).
const cyrillicShare = (s: string): number => {
  const letters = s.match(/[A-Za-zА-Яа-я]/g);
  if (!letters || letters.length < 4) return 0;
  return letters.filter((c) => /[А-Яа-я]/.test(c)).length / letters.length;
};

// Убираем скобки-глоссы, которые почти целиком английские — они главный
// источник плотности английского («(reverse proxy, rate limiting,
// static/media)»). Короткие теги (≤6 символов: «(DB0)», «(RAG)»,
// «(RU/EN)») и русские глоссы («(векторные представления)») оставляем.
// Скобки простые, без вложенности — глоссы в ответах именно такие.
const stripEnglishGlosses = (text: string): string => {
  let out = text.replace(/\(([^()]*)\)/g, (whole, inner: string) => {
    const content = inner.trim();
    if (content.length <= 6) return whole;
    return cyrillicShare(content) < 0.3 ? ' ' : whole;
  });
  // Осиротевшие скобки на границах чанка: кусок мог разрезаться посреди
  // глоссы — хвостовая незакрытая «(…» и ведущая «…)» (её начало в
  // предыдущем чанке). Тоже английские, убираем.
  out = out.replace(/\([^()]*$/, ' ');
  out = out.replace(/^[^()]*\)/, ' ');
  // Артефакты пунктуации после удаления: «Nginx , gunicorn» → «Nginx, gunicorn».
  out = out.replace(/\s+([,;:.])/g, '$1');
  out = out.replace(/^[,;:.]\s*/, '');
  out = out.replace(/\s{2,}/g, ' ');
  return out.trim();
};

export function normalizeTtsLanguage(text: string, en = false): string {
  if (en || !text) return text;
  return applyConnectives(stripEnglishGlosses(text));
}
