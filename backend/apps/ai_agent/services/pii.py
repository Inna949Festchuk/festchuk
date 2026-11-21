"""
PII masking for chat input (152-FZ, data minimization).

Pure functions, no Django imports — unit-testable in isolation.
`mask_pii` is applied in the chat views BEFORE the text is stored and
before it reaches the LLM/embeddings provider: personal data never
leaves the server perimeter and never rests in storage.

Detected types and placeholders:
    EMAIL    -> [EMAIL]
    CARD     -> [CARD]      (13-19 digits, Luhn check)
    PASSPORT -> [PASSPORT]  (RF: 4-digit series + 6-digit number)
    SNILS    -> [SNILS]     (XXX-XX-XXX YY, checksum of the control digit)
    INN      -> [INN]       (10 or 12 digits, control-digit checksums)
    PHONE    -> [PHONE]     (RU mobile: +7/8/7 followed by 10 digits,
                             third digit 9; toll-free 8-800 etc. are kept)

Deliberate limitations (documented for the privacy policy):
- Version strings ("14.2.0"), ports ("8000") and short numbers never match.
- Numbers inside code samples can be masked when they look like PII;
  this is the price of a deterministic, zero-latency guard.
"""
import re

__all__ = ['mask_pii', 'luhn_valid']


# ------------------------------------------------------------ validators

def luhn_valid(digits: str) -> bool:
    """Luhn check for a raw digit string (card numbers)."""
    total = 0
    for i, ch in enumerate(reversed(digits)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0


def _snils_valid(digits: str) -> bool:
    """Control-digit check for a 10-digit SNILS registry number.

    Weights 3..11 over the first 9 digits; remainder mod 100, x10 if < 10;
    the last digit of the result must equal the 10th digit.
    """
    if len(digits) != 10:
        return False
    s = sum(int(d) * w for d, w in zip(digits, range(3, 12)))
    r = s % 100
    if r < 10:
        r *= 10
    return r % 10 == int(digits[9])


def _inn_valid(digits: str) -> bool:
    """Control-digit checks for Russian INN (10 digits individual, 12 legal)."""
    def check(body: str, weights, control: int) -> bool:
        s = sum(int(d) * w for d, w in zip(body, weights))
        return s % 11 % 10 == control

    if len(digits) == 10:
        return check(digits[:9], (2, 4, 10, 3, 5, 9, 4, 6, 8), int(digits[9]))
    if len(digits) == 12:
        return (check(digits[:10], (7, 2, 4, 10, 3, 5, 9, 4, 6, 8), int(digits[10]))
                and check(digits[:10], (3, 5, 9, 4, 6, 8, 10, 7, 2, 4), int(digits[11])))
    return False


# ------------------------------------------------------------ patterns
# Candidate regexes are intentionally slightly over-matching; each match
# is validated (digit length / Luhn / checksum / mobile flag) before the
# replacement. Order matters: longest/most specific first.

_CARD_RE = re.compile(r'(?<!\d)(?:\d[\s\-]?){12,18}\d(?!\d)')
_PASSPORT_CONTEXT_RE = re.compile(
    r'(?i)(?:серия|series)\s*(\d{4})\s*(?:номер|number)?\s*(\d{6})(?!\d)'
)
_PASSPORT_BARE_RE = re.compile(r'(?<!\d)(\d{4})[\s\-](\d{6})(?!\d)')
_SNILS_RE = re.compile(r'(?<!\d)(\d{3})[\s\-](\d{3})[\s\-](\d{3})[\s\-](\d{2})(?!\d)')
_INN_RE = re.compile(r'(?<!\d)\d{10,12}(?!\d)')
_PHONE_RE = re.compile(r'(?<!\d)(?:\+7|8|7)[\s\-()]*(?:\d[\s\-()]{0,2}){9}\d(?!\d)')
_EMAIL_RE = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')


def _digits(text: str) -> str:
    return re.sub(r'\D', '', text)


def _mask_card(text: str, found: list) -> str:
    def repl(m):
        digits = _digits(m.group(0))
        if 13 <= len(digits) <= 19 and luhn_valid(digits):
            found.append('card')
            return '[CARD]'
        return m.group(0)
    return _CARD_RE.sub(repl, text)


def _mask_phone(text: str, found: list) -> str:
    def repl(m):
        digits = _digits(m.group(0))
        # Exactly 11 digits starting 7/8, third digit 9 (RU mobile).
        # Toll-free (8-800), landline codes and random 11-digit runs
        # pass the pattern but fail this check and stay untouched.
        if len(digits) == 11 and digits[0] in '78' and digits[2] == '9':
            found.append('phone')
            return '[PHONE]'
        return m.group(0)
    return _PHONE_RE.sub(repl, text)


def _mask_passport(text: str, found: list) -> str:
    for regex in (_PASSPORT_CONTEXT_RE, _PASSPORT_BARE_RE):
        def repl(m):
            found.append('passport')
            return '[PASSPORT]'
        text = regex.sub(repl, text)
    return text


def _mask_snils(text: str, found: list) -> str:
    def repl(m):
        digits = ''.join(m.groups())
        if _snils_valid(digits[:10]):
            found.append('snils')
            return '[SNILS]'
        return m.group(0)
    return _SNILS_RE.sub(repl, text)


def _mask_inn(text: str, found: list) -> str:
    def repl(m):
        digits = m.group(0)
        if _inn_valid(digits):
            found.append('inn')
            return '[INN]'
        return m.group(0)
    return _INN_RE.sub(repl, text)


def _mask_email(text: str, found: list) -> str:
    def repl(m):
        found.append('email')
        return '[EMAIL]'
    return _EMAIL_RE.sub(repl, text)


def mask_pii(text: str) -> tuple:
    """Mask personal data in user text.

    Returns ``(masked_text, found_types)`` where ``found_types`` is a list
    of type names in order of first appearance (used for anonymous
    counters). A masked placeholder never matches a later pattern.
    """
    if not text:
        return text, []
    found: list = []
    text = _mask_email(text, found)
    text = _mask_card(text, found)
    text = _mask_passport(text, found)
    text = _mask_snils(text, found)
    text = _mask_inn(text, found)
    text = _mask_phone(text, found)
    return text, found
