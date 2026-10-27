import re
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional
import httpx
from sqlalchemy.orm import Session
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

from backend.app.config import settings
from backend.app.models import SocialDocument
from backend.app.logging_config import record_log

vader_analyzer = SentimentIntensityAnalyzer()

STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
    "could", "did", "do", "does", "doing", "down", "during", "each", "few", "for", "from", "further",
    "had", "has", "have", "having", "he", "her", "here", "hers", "herself", "him", "himself", "his",
    "how", "i", "if", "in", "into", "is", "it", "its", "itself", "just", "me", "more", "most", "my",
    "myself", "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our",
    "ours", "ourselves", "out", "over", "own", "same", "she", "should", "so", "some", "such", "than",
    "that", "the", "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this",
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what",
    "when", "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your", "yours",
    "yourself", "yourselves", "music", "album", "song", "track", "new", "released", "announced", "tour"
}

class TwsmaService:
    @staticmethod
    def clean_text(raw_html: str) -> str:
        # Strip HTML tags
        clean_re = re.compile(r'<.*?>')
        text = re.sub(clean_re, ' ', raw_html)
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def tokenize(text: str) -> List[str]:
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        return [w for w in words if w not in STOPWORDS]

    @classmethod
    def sync_news_feed(cls, db: Session) -> Dict[str, Any]:
        """Fetches real articles from permitted music RSS feeds and saves to database."""
        feed_urls = [u.strip() for u in settings.MUSIC_RSS_FEEDS.split(",") if u.strip()]
        if not feed_urls:
            return {"status": "NO_FEEDS_CONFIGURED", "articles_added": 0}

        total_added = 0
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TWSMAMusicAnalytics/1.0"}

        for feed_url in feed_urls:
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.get(feed_url, headers=headers)
                    if resp.status_code != 200:
                        record_log("WARNING", f"RSS feed HTTP {resp.status_code} from {feed_url}")
                        continue
                    
                    root = ET.fromstring(resp.content)
                    channel = root.find("channel")
                    items = channel.findall("item") if channel is not None else root.findall(".//item")
                    
                    for item in items:
                        title_elem = item.find("title")
                        link_elem = item.find("link")
                        desc_elem = item.find("description")
                        pub_date_elem = item.find("pubDate")

                        title = title_elem.text if title_elem is not None and title_elem.text else ""
                        link = link_elem.text if link_elem is not None and link_elem.text else ""
                        raw_desc = desc_elem.text if desc_elem is not None and desc_elem.text else ""
                        clean_desc = cls.clean_text(raw_desc)

                        if not link or not title:
                            continue

                        # Check if already present
                        exists = db.query(SocialDocument).filter(SocialDocument.source_url == link).first()
                        if exists:
                            continue

                        # Text analytics on title + summary
                        combined_text = f"{title}. {clean_desc}"
                        tokens = cls.tokenize(combined_text)
                        
                        # VADER Sentiment
                        vs = vader_analyzer.polarity_scores(combined_text)
                        compound = vs.get("compound", 0.0)
                        if compound >= 0.05:
                            s_label = "positive"
                        elif compound <= -0.05:
                            s_label = "negative"
                        else:
                            s_label = "neutral"

                        import json
                        doc = SocialDocument(
                            source_name="Pitchfork News",
                            source_url=link,
                            title=title,
                            summary=clean_desc[:500],
                            tokens_json=json.dumps(tokens),
                            sentiment_compound=compound,
                            sentiment_label=s_label,
                            published_at=datetime.now(timezone.utc),
                            retrieved_at=datetime.now(timezone.utc)
                        )
                        db.add(doc)
                        total_added += 1

                db.commit()
                record_log("INFO", f"TWSMA synced {total_added} articles from {feed_url}")
            except Exception as e:
                record_log("ERROR", f"TWSMA feed sync exception for {feed_url}: {str(e)}")

        return {"status": "SUCCESS", "articles_added": total_added}

    @classmethod
    def get_summary(cls, db: Session) -> Dict[str, Any]:
        """Returns analytics summary over retrieved music articles."""
        docs = db.query(SocialDocument).order_by(SocialDocument.retrieved_at.desc()).limit(100).all()
        if not docs:
            # Try to auto-sync once if empty
            cls.sync_news_feed(db)
            docs = db.query(SocialDocument).order_by(SocialDocument.retrieved_at.desc()).limit(100).all()

        import json
        all_tokens = []
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}

        article_list = []
        for d in docs:
            sentiment_counts[d.sentiment_label] = sentiment_counts.get(d.sentiment_label, 0) + 1
            toks = json.loads(d.tokens_json) if d.tokens_json else []
            all_tokens.extend(toks)
            
            top_toks = [w for w, _ in Counter(toks).most_common(5)]
            article_list.append({
                "id": d.id,
                "source_name": d.source_name,
                "source_url": d.source_url,
                "title": d.title,
                "summary": d.summary,
                "sentiment_compound": round(d.sentiment_compound, 3),
                "sentiment_label": d.sentiment_label,
                "top_terms": top_toks,
                "published_at": d.published_at.isoformat() if d.published_at else None
            })

        token_counts = Counter(all_tokens).most_common(20)
        top_keywords = [{"term": term, "count": count} for term, count in token_counts]

        return {
            "status": "ACTIVE" if docs else "EMPTY",
            "articles_count": len(docs),
            "unique_sources_count": len(set(d.source_name for d in docs)),
            "latest_retrieval": docs[0].retrieved_at.isoformat() if docs else None,
            "sentiment_distribution": sentiment_counts,
            "top_keywords": top_keywords,
            "methodology": {
                "text_preprocessing": "HTML stripping, Lowercasing, Regex tokenization, Custom stopword filtration",
                "sentiment_model": "VADER (Valence Aware Dictionary and sEntiment Reasoner) Lexicon Engine",
                "term_frequency": "Normalized token frequency over real music news documents",
                "social_signal_derivation": "Normalized artist/title co-occurrence in retrieved news articles blended with sentiment valence"
            },
            "articles": article_list[:20]
        }

    @classmethod
    def calculate_text_signal_for_artist(cls, db: Session, artist_name: str, track_title: str) -> Dict[str, Any]:
        """
        Calculates real text/social signal for a given track based on actual news mentions.
        Returns score in [0.0, 1.0], evidence, and availability status.
        """
        artist_lower = artist_name.lower()
        title_lower = track_title.lower()

        docs = db.query(SocialDocument).all()
        if not docs:
            return {
                "available": False,
                "score": None,
                "reason": "No real text documents in database. Run TWSMA feed sync.",
                "evidence": []
            }

        matching_docs = []
        for d in docs:
            t_lower = d.title.lower()
            s_lower = d.summary.lower()
            if artist_lower in t_lower or artist_lower in s_lower or title_lower in t_lower:
                matching_docs.append(d)

        if not matching_docs:
            return {
                "available": False,
                "score": None,
                "reason": f"No recent mentions of '{artist_name}' found in current news feeds",
                "evidence": []
            }

        # Calculate sentiment and mention density
        avg_sentiment = sum(d.sentiment_compound for d in matching_docs) / len(matching_docs)
        # Normalize compound (-1 to 1) to (0 to 1)
        sentiment_norm = (avg_sentiment + 1.0) / 2.0
        # Mention frequency bonus (saturating at 5 mentions)
        mention_factor = min(1.0, len(matching_docs) / 5.0)

        raw_score = 0.5 * mention_factor + 0.5 * sentiment_norm
        final_score = round(min(1.0, max(0.0, raw_score)), 4)

        evidence = [
            {
                "article_title": d.title,
                "source_url": d.source_url,
                "sentiment_label": d.sentiment_label,
                "sentiment_score": round(d.sentiment_compound, 3)
            }
            for d in matching_docs[:3]
        ]

        return {
            "available": True,
            "score": final_score,
            "reason": f"Found {len(matching_docs)} recent music news mention(s) with sentiment: {round(avg_sentiment, 2)}",
            "evidence": evidence
        }
