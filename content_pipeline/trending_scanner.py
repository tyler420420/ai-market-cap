"""
TRENDING SCANNER — find what people are actually searching about today.

Keyless data sources (verified reachable from this box):
  - Yahoo Finance /v1/finance/trending/US   -> 25 most-trending US symbols
  - Nasdaq api screener                     -> full US universe for movers

Output: ranked trending tickers with real price action, saved to
trending_scan.json so the article writer can target live demand.

No Reddit: returns HTTP 403 from this host.
No AlphaVantage demo key: returns rows with null symbols.
"""

import json
import re
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
OUT = Path(__file__).parent / "trending_scan.json"

# AI/semiconductor complex we actually cover, plus high-interest names that
# show up in Yahoo trending regardless of sector.
AI_RELEVANT = {
    "NVDA", "AMD", "AVGO", "TSM", "MU", "SMCI", "INTC", "ARM", "MRVL", "CRDO",
    "VRT", "ANET", "DELL", "HPE", "LITE", "COHR", "APH", "GLW", "ONTO", "AMAT",
    "LRCX", "KLAC", "TER", "ENTG", "WDC", "STX", "SNPS", "CDNS", "MRVL", "PLTR",
    "AI", "SNOW", "DDOG", "MDB", "NET", "CRWV", "NBIS", "IREN", "RIOT", "MARA",
    "GOOG", "GOOGL", "MSFT", "META", "AMZN", "AAPL", "TSLA", "ORCL", "CRM",
    "IBM", "QCOM", "TXN", "ADI", "NXPI", "MPWR", "ON", "SWKS", "QRVO", "LSCC",
}


def _get_json(url, timeout=20):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8", "replace"))


def yahoo_trending():
    """Top trending US symbols as ranked by Yahoo Finance.

    Yahoo frequently omits shortName in this endpoint; fall back to a quote
    lookup so articles carry real company names, not bare tickers.
    """
    try:
        data = _get_json("https://query1.finance.yahoo.com/v1/finance/trending/US?count=25")
        results = data.get("finance", {}).get("result", [])
        if not results:
            return []
        out = []
        for idx, q in enumerate(results[0].get("quotes", [])):
            sym = (q.get("symbol") or "").upper()
            if not sym or not re.fullmatch(r"[A-Z.\-]{1,6}", sym):
                continue
            out.append({
                "symbol": sym,
                "name": q.get("shortName") or q.get("longName") or "",
                "yahoo_rank": idx + 1,
                "source": "yahoo_trending",
            })
        _fill_names(out)
        return out
    except Exception as e:
        print(f"  [WARN] yahoo_trending failed: {e}")
        return []


_NAME_CACHE = {}


def _fill_names(entries):
    """Resolve company name + live % change via Yahoo v8 chart.

    Yahoo's v7 /v7/finance/quote returns 401 without a crumb, but v8/chart is
    keyless and carries regularMarketPrice + chartPreviousClose.
    """
    cache_file = Path(__file__).parent / "ticker_names.json"
    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
    except Exception:
        cache = {}

    for e in entries:
        sym = e["symbol"]
        if cache.get(sym, {}).get("name"):
            e["name"] = cache[sym]["name"]
            if cache[sym].get("pct") is not None:
                e["pct_change"] = cache[sym]["pct"]
            if cache[sym].get("price"):
                e["price"] = cache[sym]["price"]
            continue

        try:
            d = _get_json(
                f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
                "?range=5d&interval=1d", timeout=20)
            meta = (d.get("chart", {}).get("result") or [{}])[0].get("meta", {})
            name = meta.get("shortName") or meta.get("longName") or ""
            price = meta.get("regularMarketPrice")
            prev = meta.get("chartPreviousClose") or meta.get("previousClose")
            pct = None
            if price and prev:
                pct = round((price - prev) / prev * 100, 2)

            if name:
                e["name"] = name
                cache[sym] = {"name": name, "price": price, "pct": pct}
            if pct is not None and e.get("pct_change") is None:
                e["pct_change"] = pct
            if price and not e.get("price"):
                e["price"] = price
        except Exception:
            pass

        if not e.get("name"):
            e["name"] = sym

    try:
        cache_file.write_text(json.dumps(cache, indent=2), encoding="utf-8")
    except Exception:
        pass


# Penny stocks, warrants, units, rights and SPAC tickers poison the list.
JUNK_SUFFIX = re.compile(r"(W|WT|WARR?|U|UNITS?|R|RIGHTS?|A|B|C)$")
MIN_PRICE = 5.0


def _is_tradeable(entry):
    """Filter out warrants/units/penny stocks — no article value."""
    sym = entry["symbol"]
    if JUNK_SUFFIX.search(sym) and not sym.endswith(("UW",)):
        # allow known real names that happen to end in these letters
        if sym not in AI_RELEVANT:
            return False
    price = entry.get("price")
    if price is not None and price < MIN_PRICE:
        return False
    name = (entry.get("name") or "").lower()
    bad_words = ("warrant", "unit", "right", "depositary", "acquisition corp",
                 "blank check", "shell")
    if any(w in name for w in bad_words):
        return False
    return True


def nasdaq_movers():
    """Biggest % movers today across the US universe."""
    try:
        url = ("https://api.nasdaq.com/api/screener/stocks"
               "?tableonly=true&limit=8000&download=true")
        data = _get_json(url, timeout=35)
        rows = (data.get("data") or {}).get("rows") or []
        parsed = []
        for r in rows:
            sym = (r.get("symbol") or "").upper()
            pct = _to_float(r.get("pctchange"))
            if not sym or pct is None or abs(pct) < 5:
                continue
            parsed.append({
                "symbol": sym,
                "name": (r.get("name") or sym)[:70],
                "pct_change": pct,
                "price": _to_float(r.get("lastsale")),
                "source": "nasdaq_movers",
            })
        parsed.sort(key=lambda x: abs(x["pct_change"]), reverse=True)
        parsed = parsed[:60]
        _fill_names(parsed)
        return parsed
    except Exception as e:
        print(f"  [WARN] nasdaq_movers failed: {e}")
        return []


def _to_float(v):
    if v is None:
        return None
    s = str(v).replace("$", "").replace(",", "").replace("%", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def merge(trend, movers):
    """Combine sources; score by trend rank + move magnitude, AI names boosted."""
    by_sym = {}

    for t in trend:
        by_sym[t["symbol"]] = {**t, "pct_change": None, "price": None}

    mover_map = {m["symbol"]: m for m in movers}
    # Enrich every trending symbol that also moved today.
    for sym, t in by_sym.items():
        if sym in mover_map:
            t["pct_change"] = mover_map[sym]["pct_change"]
            t["price"] = mover_map[sym]["price"]

    # Movers with no Yahoo trending rank still matter (biggest % moves of the day),
    # but only surface them if they are in our coverage or moved hard.
    for m in movers:
        if m["symbol"] in by_sym:
            continue
        if m["symbol"] in AI_RELEVANT or abs(m["pct_change"]) >= 10:
            by_sym[m["symbol"]] = {
                "symbol": m["symbol"], "name": m["name"],
                "yahoo_rank": None, "pct_change": m["pct_change"],
                "price": m.get("price"), "source": "nasdaq_movers",
            }

    scored = []
    for sym, t in by_sym.items():
        if not _is_tradeable(t):
            continue
        score = 0.0
        if t.get("yahoo_rank"):
            score += max(0, 26 - t["yahoo_rank"])          # 25 -> +1 ... 1 -> +25
        if t.get("pct_change") is not None:
            score += min(abs(t["pct_change"]), 40) * 0.5   # big movers matter
        if sym in AI_RELEVANT:
            score += 15
        if t.get("source") == "yahoo_trending":
            score += 5
        scored.append({**t, "score": round(score, 2)})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


def scan(top_n=25):
    print("=" * 58)
    print(f"  TRENDING SCAN — {datetime.now():%Y-%m-%d %H:%M}")
    print("=" * 58)

    trend = yahoo_trending()
    print(f"  yahoo_trending : {len(trend)} symbols")
    movers = nasdaq_movers()
    print(f"  nasdaq_movers  : {len(movers)} movers (|move| >= 5%)")

    merged = merge(trend, movers)
    top = merged[:top_n]

    OUT.write_text(json.dumps({
        "scanned_at": datetime.now().isoformat(),
        "count": len(top),
        "trending": top,
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"\n  TOP {len(top)} (scored by rank + move + AI relevance):\n")
    for t in top:
        pct = f"{t['pct_change']:+.2f}%" if t.get("pct_change") is not None else "     —"
        rk = f"#{t['yahoo_rank']}" if t.get("yahoo_rank") else "  —"
        print(f"   {t['score']:6.2f}  {t['symbol']:<6} {rk:<5} {pct:>9}  {t['name'][:38]}")
    print(f"\n  [OK] saved -> {OUT}")
    return top


if __name__ == "__main__":
    scan()