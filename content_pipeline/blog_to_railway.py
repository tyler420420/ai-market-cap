"""
BLOG_TO_RAILWAY — Process article queue and push blog articles to git
Run after traffic_engine.py --publish processes the queue.
Reads articles from article_queue/, generates blog HTML, pushes to ai-market-cap git repo.
"""

import os, re, sys, json, subprocess, shutil
from pathlib import Path
from datetime import datetime, date

# Paths
QUEUE_DIR = Path(__file__).parent / "article_queue"
PUBLISHED_DIR = QUEUE_DIR / "published"
BLOG_DIR = Path(r"C:\Users\Tyler_AI\ai-market-cap\blog")
INDEX_FILE = BLOG_DIR / "index.json"
GIT_DIR = Path(r"C:\Users\Tyler_AI\ai-market-cap")

# Make dirs
PUBLISHED_DIR.mkdir(exist_ok=True)
BLOG_DIR.mkdir(exist_ok=True)


def slugify(text):
    """Convert title to URL slug."""
    import re
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text).strip('-')
    return text[:60]


_TAG_RE = re.compile(r'<[^>]+>')
_WS_RE = re.compile(r'\s+')


def build_excerpt(html_content, limit=200):
    """Strip HTML down to plain text for the blog index card.

    The index stores PLAIN TEXT. scanner_web.py escapes at render time.
    Previously this pre-escaped to &lt;p&gt; AND the renderer emitted it raw,
    so users saw a literal "<p>" at the start of every card.
    """
    text = _TAG_RE.sub(" ", html_content or "")
    text = (text.replace("&nbsp;", " ").replace("&amp;", "&")
                .replace("&lt;", "<").replace("&gt;", ">")
                .replace("&quot;", '"').replace("&#39;", "'"))
    # Entity-encoded brackets decode back into real angle brackets. Strip them so
    # the stored excerpt is guaranteed inert no matter which consumer renders it.
    text = text.replace("<", " ").replace(">", " ")
    text = _WS_RE.sub(" ", text).strip()
    if len(text) > limit:
        cut = text[:limit].rsplit(" ", 1)[0]
        text = cut.rstrip(" ,;:-") + "..."
    return text


def build_article_html(article, slug):
    """Build a full HTML article page matching the site's design."""
    title = article.get("title", "")
    meta_desc = article.get("meta_description", "")
    content = article.get("content", "")
    keyword = article.get("keyword", "")
    author = article.get("author", "AI Market Cap")
    article_date = article.get("date", date.today().isoformat())

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<link rel="icon" type="image/png" href="/static/logo.png">
<title>{title} — AI Market Cap</title>
<meta name="description" content="{meta_desc}">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{meta_desc}">
<meta property="og:type" content="article">
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{
    font-family: 'Segoe UI', Arial, sans-serif;
    background: #0d1117;
    color: #c9d1d9;
    min-height: 100vh;
    line-height: 1.7;
}}
a {{ text-decoration: none; color: #58a6ff; }}
a:hover {{ color: #79b8ff; }}
.w {{
    background: linear-gradient(135deg, #1a1f2e, #161b22);
    padding: 20px 30px;
    border-bottom: 1px solid #30363d;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 12px;
}}
.w h1 a {{ color: #58a6ff; font-size: 1.5em; text-decoration: none; }}
.w .nav a {{ margin-left: 16px; color: #58a6ff; font-size: 0.9em; }}
.w .nav a.active {{ color: #ffd700; font-weight: bold; }}
.article-wrap {{
    max-width: 720px;
    margin: 0 auto;
    padding: 48px 20px 80px;
}}
.article-header {{ margin-bottom: 32px; padding-bottom: 24px; border-bottom: 1px solid #30363d; }}
.article-header .tag {{
    display: inline-block;
    background: #1a3a5c;
    color: #58a6ff;
    padding: 4px 12px;
    border-radius: 4px;
    font-size: 0.75em;
    font-weight: bold;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}}
.article-header h1 {{
    color: #fff;
    font-size: 2em;
    line-height: 1.25;
    margin-bottom: 16px;
}}
.article-header .meta {{
    color: #888;
    font-size: 0.85em;
}}
.article-header .meta span {{ margin-right: 16px; }}
.article-header .keyword-tag {{
    display: inline-block;
    background: #1a2a1a;
    color: #00ff88;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.75em;
    margin-left: 8px;
}}
.article-body {{ color: #c9d1d9; font-size: 1.05em; }}
.article-body p {{ margin-bottom: 20px; }}
.article-body h2 {{
    color: #fff;
    font-size: 1.4em;
    margin: 36px 0 14px;
    padding-bottom: 8px;
    border-bottom: 1px solid #21262d;
}}
.article-body h3 {{ color: #e6edf3; font-size: 1.15em; margin: 24px 0 10px; }}
.article-body ul, .article-body ol {{
    margin: 0 0 20px 24px;
}}
.article-body li {{ margin-bottom: 8px; }}
.article-body strong {{ color: #fff; }}
.article-body blockquote {{
    border-left: 3px solid #ffd700;
    padding: 12px 20px;
    margin: 24px 0;
    background: #161b22;
    border-radius: 0 8px 8px 0;
    color: #c9d1d9;
    font-style: italic;
}}
.article-body a {{ color: #58a6ff; text-decoration: underline; }}
.back-link {{
    display: inline-block;
    margin-bottom: 24px;
    color: #58a6ff;
    font-size: 0.9em;
}}
.cta-box {{
    background: linear-gradient(135deg, #0d2b1a, #0a1a12);
    border: 2px solid #00ff88;
    border-radius: 12px;
    padding: 28px;
    text-align: center;
    margin-top: 48px;
    box-shadow: 0 0 20px rgba(0,255,136,0.15);
}}
.cta-box h2 {{ color: #2ea043; font-size: 1.3em; margin-bottom: 10px; }}
.cta-box p {{ color: #c9d1d9; font-size: 0.9em; margin-bottom: 20px; }}
.btn {{
    background: #ffd700;
    border: 2px solid #000;
    color: #000;
    padding: 12px 28px;
    border-radius: 6px;
    font-size: 0.95em;
    cursor: pointer;
    font-weight: bold;
    display: inline-block;
}}
.btn:hover {{ background: #2ea043; border-color: #2ea043; color: #fff; }}
</style>
</head>
<body>

<div class=w>
  <h1><a href="/">AI Market Cap</a></h1>
  <div class=nav>
    <a href="/">Scanner</a>
    <a href="/wins">Wins</a>
    <a href="/blog" class=active>Blog</a>
    <a href="/about">About</a>
  </div>
</div>

<article class=article-wrap>
  <a href="/blog" class=back-link>← Back to Articles</a>

  <div class=article-header>
    <div class=tag>📝 Analysis</div>
    <h1>{title}</h1>
    <div class=meta>
      <span>By {author}</span>
      <span>{article_date}</span>
      <span class=keyword-tag>#{keyword}</span>
    </div>
  </div>

  <div class=article-body>
    {content}
  </div>

  <div class=cta-box>
    <h2>Find pre-earnings setups before they move</h2>
    <p>AI Market Cap runs a free daily scan on AI stocks before earnings. See what's scoring highest this week.</p>
    <a href="/" class=btn>Open Free Scanner →</a>
  </div>
</article>

</body>
</html>"""


def process_queue():
    """Process queued articles, generate HTML, push to git."""
    today_str = date.today().isoformat()
    
    # Find ALL articles in queue (including published dir - re-process any that haven't been blogged)
    queue_files = list(QUEUE_DIR.glob("aismarketcap_*.json"))
    
    # Load existing index
    index = []
    if INDEX_FILE.exists():
        index = json.loads(INDEX_FILE.read_text(encoding="utf-8"))
    
    processed = 0
    pushed = False
    
    for qf in sorted(queue_files):
        try:
            article = json.loads(qf.read_text(encoding="utf-8"))
            
            slug = slugify(article.get("title", qf.stem))
            article["slug"] = slug
            
            # Check if already in index
            if any(a.get("slug") == slug for a in index):
                # Move to published
                dest = PUBLISHED_DIR / qf.name
                shutil.move(str(qf), str(dest))
                continue
            
            # Build article HTML
            html = build_article_html(article, slug)
            html_path = BLOG_DIR / f"{slug}.html"
            html_path.write_text(html, encoding="utf-8")
            print(f"  [OK] Created: blog/{slug}.html")
            
            # Add to index (newest first)
            index.insert(0, {
                "slug": slug,
                "title": article.get("title", ""),
                "keyword": article.get("keyword", ""),
                "date": article.get("date", today_str),
                "meta_description": article.get("meta_description", ""),
                "excerpt": build_excerpt(article.get("content", ""), 200)
            })
            
            # Move to published
            dest = PUBLISHED_DIR / qf.name
            shutil.move(str(qf), str(dest))
            processed += 1
            pushed = True
            
        except Exception as e:
            print(f"  [FAIL] Failed: {qf.name}: {e}")
    
    # Save updated index
    if pushed:
        INDEX_FILE.write_text(json.dumps(index, indent=2), encoding="utf-8")
        print(f"  [OK] Updated index.json ({len(index)} articles)")
        
        # Ping Google to crawl the updated sitemap
        # ── Search engine indexing ──
        # Google retired the public sitemap ping endpoint in 2023 (it 404s), so
        # Google's path is: sitemap.xml (regenerated from index.json below) +
        # the robots.txt Sitemap declaration. Bing/IndexNow gets a real push.
        print("  [INDEX] Notifying search engines...")
        try:
            r = subprocess.run(
                ["python", str(GIT_DIR / "indexnow_submit.py"), "--all"],
                capture_output=True, text=True, timeout=180, cwd=str(GIT_DIR)
            )
            out = (r.stdout or "").strip().splitlines()
            for line in out[-3:]:
                print(f"  [INDEX] {line.strip()}")
        except Exception as e:
            print(f"  [WARN] IndexNow submission failed: {e}")

        print("  [INDEX] Google: sitemap.xml regenerated from index.json "
              "and declared in robots.txt — no ping endpoint exists anymore.")

        # Git push — add files one at a time so one bad path doesn't kill the whole thing
        try:
            git_opts = {"capture_output": True, "text": True, "cwd": str(GIT_DIR)}
            add_failed = False
            r = subprocess.run(["git", "add", "blog/"], **git_opts)
            if r.returncode != 0:
                print(f"  [FAIL] Git add blog/ failed: {r.stderr.strip()}")
                add_failed = True
            # index.json lives inside blog/ — add it with the correct path
            blog_index = BLOG_DIR / "index.json"
            if blog_index.exists():
                r2 = subprocess.run(["git", "add", "blog/index.json"], **git_opts)
                if r2.returncode != 0:
                    print(f"  [FAIL] Git add blog/index.json failed: {r2.stderr.strip()}")
                    add_failed = True
            if add_failed:
                print(f"  [FAIL] Skipping commit — git add stage had errors")
            else:
                result = subprocess.run(
                    ["git", "commit", "-m", f"Blog: {processed} new article(s) ({today_str})"],
                    **git_opts
                )
                if result.returncode == 0:
                    print(f"  [OK] Committed: {result.stdout.strip()}")
                    push_result = subprocess.run(
                        ["git", "push", "origin", "master"],
                        **git_opts
                    )
                    if push_result.returncode == 0:
                        print(f"  [OK] Pushed to GitHub! Railway will redeploy shortly.")
                    else:
                        print(f"  [FAIL] Push failed: {push_result.stderr.strip()}")
                else:
                    print(f"  [WARN] Nothing to commit: {result.stderr.strip()}")
        except Exception as e:
            print(f"  [FAIL] Git error: {e}")
    else:
        print("  No new articles to publish.")
        # Still ping the search engines. A quiet day is exactly when a stale
        # index is least likely to be noticed, and IndexNow is idempotent.
        try:
            r = subprocess.run(
                ["python", str(GIT_DIR / "indexnow_submit.py"), "--all"],
                capture_output=True, text=True, timeout=180, cwd=str(GIT_DIR)
            )
            for line in (r.stdout or "").strip().splitlines()[-2:]:
                print(f"  [INDEX] {line.strip()}")
        except Exception as e:
            print(f"  [WARN] IndexNow submission failed: {e}")

    print(f"\n  Total articles in blog: {len(index)}")
    return processed


if __name__ == "__main__":
    print("=" * 50)
    print("  BLOG TO RAILWAY PUBLISHER")
    print(f"  {date.today().isoformat()}")
    print("=" * 50)
    processed = process_queue()
    print(f"\n[OK] Done. {processed} article(s) published to blog.")
