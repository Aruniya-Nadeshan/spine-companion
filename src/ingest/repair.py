"""Repair words that were glued together in the source text ("experienceand" -> "experience and").

Some publisher XML is missing spaces between words. Fixing it by hand is not
possible at this size, and a general spell-checker could change medical terms,
so the repair is deliberately conservative:

- It never touches a word that is in an English dictionary (so "thereby" and
  "sometimes" are safe), and never touches all-capital acronyms.
- It only splits a word into parts that the document itself uses elsewhere,
  at least 5 times each (or common short words such as "and", "is", "the").
- The glued word must be rare compared with its parts: it can appear at most
  10 times and at most half as often as its rarest part. A word the document
  uses constantly is real vocabulary, not a typo.
- Words under 7 letters are only split into two common short words ("ofthe").
- It never splits after a common prefix such as "non" or "anti".
- It never touches parts of web addresses or e-mail addresses.

A second rule handles glue that has a capital letter at the join ("dysfunctionTo",
"theCobb"). It splits only where a lower-case letter meets a capital, both sides are
real words (dictionary words, or words the document uses often), and the token is not
a known name such as "PubMed" or "ScoliScore".
- Every change is recorded, so the list can be reviewed before it is trusted.
"""
import re
from collections import Counter

WORD = re.compile(r"[A-Za-z]{5,}")
ANY_WORD = re.compile(r"[A-Za-z]+")

MIN_PART_FREQ = 5     # each part must appear this often in the document
MAX_WHOLE_FREQ = 10   # a glued word appears at most this often in the document
RARITY_RATIO = 2      # ...and at most 1/RARITY_RATIO as often as its rarest part
SHORT_WORD = 7        # words shorter than this are only split into function words
MIN_LONG_PART = 4     # parts shorter than this must be a common function word

FUNCTION_WORDS = {"is", "of", "to", "in", "on", "or", "as", "by", "at", "an", "it", "be",
                  "we", "and", "the", "for", "are", "was", "with", "that", "this", "from",
                  "not", "can", "may", "has", "have", "its", "but", "all", "per", "who"}
PREFIXES = {"non", "anti", "pre", "post", "sub", "inter", "intra", "para", "semi", "over",
            "under", "hyper", "hypo", "micro", "macro", "multi", "poly", "retro", "trans",
            "pseudo", "extra", "infra", "meta", "peri"}


# Product, database and method names that legitimately contain a lower-to-upper transition.
CAMEL_KEEP = {"PubMed", "MedLine", "ScienceDirect", "SpineCor", "ScoliScore", "SPORTDiscus",
              "EndNote", "YouTube", "JAMA", "PowerPoint", "WordPress", "ResearchGate",
              "GoogleScholar", "CINAHL", "ClinicalTrials", "DeKorvin", "McMaster", "McKenzie"}

_speller = None


def default_is_known(word):
    """True if `word` is an ordinary English word (uses the pyspellchecker dictionary)."""
    global _speller
    if _speller is None:
        from spellchecker import SpellChecker  # imported lazily so tests can avoid it
        _speller = SpellChecker()
    return bool(_speller.known([word]))


def build_vocab(sections):
    """Count how often each word appears in the document (lower case)."""
    counts = Counter()
    for sec in sections:
        for text in [sec["heading"], *sec["paragraphs"]]:
            counts.update(w.lower() for w in ANY_WORD.findall(text))
    return counts


def _is_word(part, vocab):
    if vocab[part] < MIN_PART_FREQ:
        return False
    return len(part) >= MIN_LONG_PART or part in FUNCTION_WORDS


def _segment(word, vocab, depth):
    """Best way to cut `word` (lower case) into known words: (parts, score) or None."""
    best = None
    for i in range(2, len(word) - 1):
        left, right = word[:i], word[i:]
        if left in PREFIXES or not _is_word(left, vocab):
            continue
        if _is_word(right, vocab):
            candidate = ([left, right], min(vocab[left], vocab[right]))
        elif depth > 1:
            sub = _segment(right, vocab, depth - 1)
            if sub is None:
                continue
            candidate = ([left] + sub[0], min(vocab[left], sub[1]))
        else:
            continue
        if best is None or candidate[1] > best[1]:
            best = candidate
    return best


def _in_web_address(text, start, end):
    """True if the word at text[start:end] looks like part of a URL, domain or e-mail address."""
    before = text[start - 1] if start else ""
    after = text[end:end + 2]
    if before in ("/", "@", "_"):
        return True
    if before == "." and start >= 2 and text[start - 2].isalnum():
        return True
    return len(after) == 2 and after[0] in "./@_" and after[1].isalnum()


CAMEL_TOKEN = re.compile(r"[A-Za-z]{5,}")


def _known_word(word, vocab, is_known):
    """An ordinary English word, or a word this document uses often (names, terms)."""
    return is_known(word) or vocab[word] >= MIN_PART_FREQ


def _split_camel_token(token, vocab, is_known):
    """Split `token` where a lower-case letter meets a capital and both sides are real words."""
    if token in CAMEL_KEEP or token.isupper() or is_known(token.lower()):
        return None
    cuts, last = [], 0
    for i in range(1, len(token)):
        if not (token[i - 1].islower() and token[i].isupper()):
            continue
        left = token[last:i].lower()
        # the right piece runs to the next transition (or the end of the token)
        nxt = next((j for j in range(i + 1, len(token))
                    if token[j - 1].islower() and token[j].isupper()), len(token))
        right = token[i:nxt].lower()
        left_ok = left in FUNCTION_WORDS or (len(left) >= 4 and _known_word(left, vocab, is_known))
        right_ok = right in FUNCTION_WORDS or (len(right) >= 4 and _known_word(right, vocab, is_known))
        if left_ok and right_ok:
            cuts.append(i)
            last = i
    if not cuts:
        return None
    pieces, start = [], 0
    for cut in cuts + [len(token)]:
        pieces.append(token[start:cut])
        start = cut
    return " ".join(pieces)


def split_camel_glue(text, vocab, found, is_known=default_is_known):
    """Fix glue with a capital at the join, e.g. "dysfunctionTo" -> "dysfunction To"."""
    def fix(match):
        token = match.group(0)
        if _in_web_address(match.string, match.start(), match.end()):
            return token
        fixed = _split_camel_token(token, vocab, is_known)
        if fixed is None:
            return token
        found[(token, fixed)] += 1
        return fixed

    return CAMEL_TOKEN.sub(fix, text)


def repair_text(text, vocab, found, is_known=default_is_known):
    """Fix glued words in one string. `found` (a Counter) records each repair."""
    def fix(match):
        original = match.group(0)
        lower = original.lower()
        if original.isupper() or vocab[lower] > MAX_WHOLE_FREQ or is_known(lower):
            return original
        if _in_web_address(match.string, match.start(), match.end()):
            return original
        segmented = _segment(lower, vocab, depth=2)
        if segmented is None:
            return original
        parts, rarest_part = segmented
        if vocab[lower] * RARITY_RATIO > rarest_part:
            return original  # used about as often as its parts, so it is real vocabulary
        if len(original) < SHORT_WORD and not all(p in FUNCTION_WORDS for p in parts):
            return original
        pieces, position = [], 0
        for part in parts:
            pieces.append(original[position:position + len(part)])  # keeps the original capitals
            position += len(part)
        repaired = " ".join(pieces)
        found[(original, repaired)] += 1
        return repaired

    text = split_camel_glue(text, vocab, found, is_known)
    return WORD.sub(fix, text)


def repair_sections(sections, is_known=default_is_known):
    """Return (repaired_sections, repairs). Each repair is {"from", "to", "count"}."""
    vocab = build_vocab(sections)
    found = Counter()
    repaired = [
        {"heading": repair_text(sec["heading"], vocab, found, is_known),
         "paragraphs": [repair_text(p, vocab, found, is_known) for p in sec["paragraphs"]]}
        for sec in sections
    ]
    repairs = [{"from": a, "to": b, "count": n} for (a, b), n in sorted(found.items())]
    return repaired, repairs
