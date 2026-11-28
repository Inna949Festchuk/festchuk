// Нарезка ответа на куски TTS (чистые функции, без React/DOM — модуль
// тестируется в node вместе с ttsText.ts). Вынесено из ChatWidget.tsx, чтобы
// реальный код чанкера можно было прогнать в node при проверке density-cut.

import {findDenseLatinSpan, normalizeTtsLanguage, spellIdentifiers} from './ttsText';

// Strip markdown for voice synthesis: tables become comma-separated pauses,
// code blocks are dropped, emphasis markers removed.
export function stripMarkdownForTTS(text: string): string {
  const base = text
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
    .replace(/^[ \t]*(?:[^\n]*\t){2,}[^\n]*$/gm, ' ');
  // Identifiers must be spaced BEFORE the emphasis strip below: «_» is a
  // markdown marker for the stripper but part of a name for the voice
  // («search_fires» → «searchfires» without this). Done after fences, links
  // and table rows are dropped, so URLs are not touched.
  return spellIdentifiers(base)
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
export function createTTSChunker(onChunk: (chunk: string) => void, en = false) {
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
          // spellIdentifiers before the marker strip — the intro is voiced, and
          // «search_fires» in the first column must not collapse to «searchfires».
          const cell = spellIdentifiers(isPipe ? line.split('|')[1] || '' : line.split('\t')[0] || '')
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
    // Границы кусков (абсолютные позиции) — нужны density-cut'у ниже, чтобы
    // резать перед плотной латиницей только по концам предложений.
    const bounds: number[] = [];
    const bRe = /[.!?…](?=\s)|\n/g;
    let bm: RegExpExecArray | null;
    while ((bm = bRe.exec(region)) !== null) {
      const abs = consumed + bm.index + 1;
      if (inFence(abs)) continue;
      bounds.push(abs);
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
    // Density cut: синтезатор решает язык по всему куску, поэтому латинский
    // пробег в середине («FastMCP», «search_fires») утянет в английский и
    // кириллицу после него. Русское начало отправляем до пробега; если же
    // кусок уже начинается с плотной латиницы — режем сразу после пробега,
    // чтобы она ушла отдельным коротким запросом. Границы только те, что
    // нашлись в основном скане (концы предложений/переводы строк), и они не
    // должны попадать внутрь код-фенса.
    if (cut - consumed > MIN) {
      const span = findDenseLatinSpan(raw.slice(consumed, cut));
      if (span) {
        // Кандидаты: ближайший конец предложения ПЕРЕД пробегом (русское
        // начало уходит отдельно) или первый конец СРАЗУ ПОСЛЕ его начала
        // (пробег уходит коротким отдельным запросом).
        const before = span.start >= 120;
        const ordered = bounds
          .filter((b) =>
            before
              ? b - consumed >= 100 && b <= consumed + span.start
              : b >= consumed + span.start && b - consumed <= LIMIT,
          )
          .reverse(); // «перед пробегом» берём границу, ближайшую к пробегу
        let next = -1;
        for (const b of before ? ordered : ordered.slice().reverse()) {
          // Двухзначные куски — служебный шум (маркер списка «1.», «(DB0)»):
          // отдельный TTS-запрос на пару знаков, обрыв интонации и лишний
          // расход троттлинга tts. Берём следующую границу.
          if ((raw.slice(consumed, b).match(/[A-Za-zА-Яа-я]/g) || []).length < 20) continue;
          next = b;
          break;
        }
        if (next > consumed) {
          const f = fences.find(([a, z]) => next > a && next < z);
          if (f) next = f[0] > consumed ? f[0] : f[1];
          if (next > consumed && next - consumed <= LIMIT) cut = next;
        }
      }
    }
    if (cut <= consumed) return;
    const piece = raw.slice(consumed, cut);
    consumed = cut;
    const clean = withTableIntro(piece);
    // Language post-processing for the voice: move a leading English label
    // to the end of its sentence and swap known English connectives to
    // Russian, so the synthesizer keeps the utterance in Russian.
    if (clean) onChunk(normalizeTtsLanguage(clean, en));
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
export function feedAllToChunks(
  chunker: {feed: (raw: string, final?: boolean) => void; consumed: () => number},
  text: string,
) {
  let safety = 0;
  do {
    chunker.feed(text, true);
    safety += 1;
  } while (chunker.consumed() < text.length && safety < 50);
}
