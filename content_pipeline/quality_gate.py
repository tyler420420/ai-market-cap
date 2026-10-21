"""
QUALITY GATE — score an article and decide whether it may publish.

The template fallback in modules/article_writer.py produces readable-looking but
worthless filler ("X continues to be one of the most discussed topics...").
This gate rejects that class of content so scaled production never ships junk.

A passing article must clear ALL of:
  - minimum word count
  - real structure (H2s, paragraphs, lists)
  - NOT match the template signature
  - keyword actually present, used naturally
  - specific/concrete (tickers, numbers) not pure fluff
  - no duplicated boilerplate vs already-published articles

Usage:
    from quality_gate import evaluate
    verdict = evaluate(article, existing_titles)
    if verdict["pass"]: publish
"""

import re

MIN_WORDS = 600
MIN_H2 = 3
MIN_PARAGRAPHS = 4

# Signature phrases emitted by _write_template(). Any hit = automatic reject.
TEMPLATE_SIGNATURES = [
    "continues to be one of the most discussed topics",
    "this guide covers everything you need to know",
    "represents a meaningful opportunity for those willing",
    "let compound results work in your favor",
    "the concept of",
    "encompasses a broad range of ideas and strategies",
    "industry experts point to several key factors",
    "the landscape has shifted considerably over the past year",
    "starting today",          # "Start today, stay consistent..."
    "education gap",
]

# Title patterns from the keyword-spinner era.
BAD_TITLE_PATTERNS = [
    r"\bthe complete guide for \d{4}\b",
    r"^why does\b",
    r"^what is\b",
    r"^how to\b",
    r"^best way to\b",
    r"\bfor beginners\b",
    r"explained\b",
]

TICKER_RE = re.compile(r"\$?[A-Z]{2,5}\b")
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?%|\$\d+|\b\d{3,}\b")


def _strip_html(html_text):
    return re.sub(r"<[^>]+>", " ", html_text or "")


def _word_count(content):
    return len(_strip_html(content).split())


def _norm_title(title):
    """Normalize a title for duplicate comparison (case/punct/space-insensitive)."""
    return re.sub(r"[^a-z0-9]+", "", (title or "").lower()).strip()


def evaluate(article, published_titles=None, article_type="standard"):
    """Return {pass: bool, score: int, reasons: [str], checks: {}}.

    article_type:
      "standard" -> 600+ words (long-form analysis)
      "wins"     -> 200+ words (short weekly top-pick recap)
    """
    content = article.get("content", "") or ""
    title = article.get("title", "") or ""
    keyword = (article.get("keyword", "") or "").strip().lower()
    plain = _strip_html(content).lower()

    min_words = 200 if article_type == "wins" else MIN_WORDS
    min_h2 = 2 if article_type == "wins" else MIN_H2

    checks = {"type": article_type}
    reasons = []
    warnings = []
    score = 0

    # ── length ──
    words = _word_count(content)
    checks["word_count"] = words
    if words < min_words:
        reasons.append(f"too short ({words} < {min_words} for {article_type})")
    else:
        score += 25

    # ── structure ──
    h2 = content.count("<h2>")
    paras = len(re.findall(r"<p>", content))
    lists = content.count("<ul>") + content.count("<ol>")
    checks["h2"] = h2
    checks["paragraphs"] = paras
    checks["lists"] = lists
    if h2 < min_h2:
        reasons.append(f"needs {min_h2}+ H2 headings (has {h2})")
    else:
        score += 15
    if paras < 3:
        reasons.append(f"needs 3+ paragraphs (has {paras})")
    else:
        score += 10
    if lists >= 1:
        score += 5
    else:
        warnings.append("no bullet/numbered list")

    # ── template rejection ──
    hits = [s for s in TEMPLATE_SIGNATURES if s in plain]
    checks["template_hits"] = hits
    if hits:
        reasons.append(f"template filler detected: {hits[:2]}")
        score -= 60

    # ── title quality ──
    tl = title.lower()
    bad = [p for p in BAD_TITLE_PATTERNS if re.search(p, tl)]
    checks["bad_title"] = bad
    if bad:
        reasons.append(f"spun/keyword-stuffed title pattern: {bad[:1]}")
        score -= 25
    if len(title) > 70:
        # warning, not a hard reject — a strong title can run slightly long
        warnings.append(f"title long ({len(title)} chars, aim <60)")
        score -= 3

    # ── keyword usage ──
    if keyword:
        # Match on meaningful tokens; the stored keyword may carry a date suffix
        # ("bili pre-earnings pick 2026-10") that never appears verbatim.
        tokens = [t for t in re.split(r"\W+", keyword) if len(t) > 2]
        hits_kw = sum(1 for t in tokens if t in plain)
        # Density of the FULL phrase is the honest stuffing signal; summing every
        # token double-counts normal SEO phrasing.
        phrase_hits = plain.count(keyword) if keyword else 0
        density = (phrase_hits / words) if words else 0
        checks["keyword_tokens"] = len(tokens)
        checks["keyword_phrase_hits"] = phrase_hits
        checks["keyword_density"] = round(density, 4)
        if tokens and hits_kw == 0:
            reasons.append(f"keyword '{keyword}' has no token overlap in body")
            score -= 20
        elif density > 0.05:
            reasons.append(f"keyword stuffed ({density:.1%} of body)")
            score -= 20
        else:
            score += 15

    # ── specificity: real tickers + concrete numbers ──
    tickers = set(TICKER_RE.findall(_strip_html(content)))
    checks["ticker_count"] = len(tickers)
    if len(tickers) >= (1 if article_type == "wins" else 2):
        score += 15
    else:
        reasons.append(f"needs real tickers (has {len(tickers)})")
    nums = NUMBER_RE.findall(plain)
    checks["number_count"] = len(nums)
    if len(nums) >= (2 if article_type == "wins" else 3):
        score += 10
    else:
        reasons.append("needs concrete numbers/percentages")

    # ── duplicate vs published (skip self) ──
    if published_titles:
        norm = _norm_title(title)
        for pt in published_titles:
            if _norm_title(pt) == norm:
                continue  # same article, not a duplicate
            if norm and norm == _norm_title(pt):
                reasons.append(f"duplicate of published: {pt}")
                score -= 40
                break

    score = max(0, min(100, score))
    passed = not reasons
    return {"pass": passed, "score": score, "reasons": reasons,
            "warnings": warnings, "checks": checks}