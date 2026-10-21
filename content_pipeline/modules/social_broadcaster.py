"""
SOCIAL BROADCASTER - Multi-Platform Social Posting
Posts article announcements to LinkedIn and Reddit.
Handles auth, rate limits, and duplicate prevention.

X/Twitter was fully retired 2026-10-20 (Tyler). No X posting path remains.
"""

import os
import re
import json
import time
import random
import requests
from datetime import datetime
from pathlib import Path


class SocialBroadcaster:
    def __init__(self, global_config, client_config, logger):
        self.global_cfg = global_config
        self.client_cfg = client_config
        self.logger = logger
        
        self.state_file = "social_state.json"
        self.state = self._load_state()

        # Platform configs
        # NOTE: X/Twitter config intentionally removed 2026-10-20 — retired.

    def _load_state(self):
        if Path(self.state_file).exists():
            with open(self.state_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"posted_linkedin": {}, "posted_reddit": {}}
    
    def _save_state(self):
        with open(self.state_file, "w", encoding="utf-8") as f:
            json.dump(self.state, f, indent=2)
    
    def _already_posted(self, platform, article_url):
        """Check if we already posted this article to this platform."""
        return article_url in self.state.get(f"posted_{platform}", {})
    
    def _mark_posted(self, platform, article_url, post_id=""):
        """Record that we posted this article."""
        if f"posted_{platform}" not in self.state:
            self.state[f"posted_{platform}"] = {}
        self.state[f"posted_{platform}"][article_url] = {
            "date": datetime.now().isoformat(),
            "post_id": post_id
        }
        self._save_state()
    
    # ──────────────────────────────────────────────
    # LINKEDIN POSTING
    # ──────────────────────────────────────────────
    
    def _post_linkedin(self, article):
        """Post to LinkedIn."""
        token = self.global_cfg.get("linkedin_api_token")
        
        if not token:
            self.logger.info("  → LinkedIn token not configured, skipping.")
            return None
        
        if self._already_posted("linkedin", article["url"]):
            self.logger.info("  → Already posted to LinkedIn for this article.")
            return None
        
        try:
            headers = {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0"
            }
            
            post_data = {
                "author": "urn:li:person:ME",  # Replace with actual URN
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {
                            "text": f"📝 New article: {article['title']}\n\n{article['keyword']} — here's what you need to know. {article['url']}"
                        },
                        "shareMediaCategory": "ARTICLE",
                        "media": [{
                            "status": "READY",
                            "originalUrl": article["url"]
                        }]
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"
                }
            }
            
            r = requests.post(
                "https://api.linkedin.com/v2/ugcPosts",
                headers=headers,
                json=post_data,
                timeout=15
            )
            
            if r.status_code in [200, 201]:
                self._mark_posted("linkedin", article["url"])
                self.logger.info("  → LinkedIn: posted successfully")
                return {"platform": "linkedin"}
            else:
                self.logger.warning(f"  → LinkedIn error {r.status_code}: {r.text[:200]}")
                return None
                
        except Exception as e:
            self.logger.error(f"  → LinkedIn error: {e}")
            return None
    
    # ──────────────────────────────────────────────
    # REDDIT POSTING
    # ──────────────────────────────────────────────
    
    def _post_reddit(self, article):
        """Post article link to relevant subreddit."""
        reddit_config = self.client_cfg.get("reddit", {})
        subreddit = reddit_config.get("subreddit", "")
        
        if not subreddit:
            return None
        
        if self._already_posted("reddit", article["url"]):
            return None
        
        try:
            import praw
            
            reddit = praw.Reddit(
                client_id=os.getenv("REDDIT_CLIENT_ID"),
                client_secret=os.getenv("REDDIT_CLIENT_SECRET"),
                user_agent="TrafficMachine/1.0"
            )
            
            submission = reddit.subreddit(subreddit).submit(
                title=article["title"],
                url=article["url"],
                flair_id=reddit_config.get("flair_id")
            )
            
            self._mark_posted("reddit", article["url"], submission.id)
            self.logger.info(f"  → Reddit: posted to r/{subreddit}")
            return {"platform": "reddit", "post_id": submission.id}
            
        except ImportError:
            self.logger.warning("praw not installed. Run: pip install praw")
            return None
        except Exception as e:
            self.logger.error(f"  → Reddit error: {e}")
            return None
    
    # ──────────────────────────────────────────────
    # MASTER POST METHOD
    # ──────────────────────────────────────────────
    
    def broadcast(self, article):
        """
        Post article to all configured social platforms.
        Returns list of results.
        """
        results = []
        
        self.logger.info("  Broadcasting to social platforms...")

        # LinkedIn
        l_result = self._post_linkedin(article)
        if l_result:
            results.append(l_result)
        
        # Reddit
        r_result = self._post_reddit(article)
        if r_result:
            results.append(r_result)
        
        if not results:
            self.logger.info("  → No social posts made (credentials not configured or already posted)")
        
        return results
