from sqlmodel import select
from app.utils.geo_utils import haversine
from app.utils.text_utils import text_match_score, recency_boost
from app.services.llm_service import LLMService
from app.services.geo_service import GeoService
from app.database import get_session
from datetime import datetime, timedelta
from typing import List
from app.database import get_session
from app.models import Article, UserEvent

class NewsService:
    def __init__(self):
        self.llm = LLMService()
        self.geo = GeoService()

    def rank_category(self, category: str, limit=5):
        with get_session() as s:
            rows = s.exec(select(Article)).all()
        filtered = [a for a in rows if any(category.lower() == c.lower() for c in a.categories)]
        filtered.sort(key=lambda x: x.publication_date or datetime.min, reverse=True)
        return self._enrich(filtered[:limit])

    def rank_source(self, source: str, limit=5):
        with get_session() as s:
            rows = s.exec(select(Article)).all()
        filtered = [a for a in rows if a.source_name and a.source_name.lower() == source.lower()]
        filtered.sort(key=lambda x: x.publication_date or datetime.min, reverse=True)
        return self._enrich(filtered[:limit])

    def rank_score(self, threshold=0.7, limit=5):
        with get_session() as s:
            rows = s.exec(select(Article)).all()
        filtered = [a for a in rows if (a.relevance_score or 0) >= threshold]
        filtered.sort(key=lambda x: x.relevance_score or 0, reverse=True)
        return self._enrich(filtered[:limit])

    def rank_search(self, query: str, limit=5):
        with get_session() as s:
            rows = s.exec(select(Article)).all()
        scored = []
        for a in rows:
            tm = text_match_score(query, a.title, a.description)
            rs = a.relevance_score or 0
            final = (0.6 * tm + 0.4 * rs) * recency_boost(a.publication_date)
            if final > 0:
                scored.append((a, final))
        scored.sort(key=lambda t: t[1], reverse=True)
        return self._enrich([a for a, _ in scored[:limit]])

    def rank_nearby(self, lat, lon, radius=10.0, limit=5):
        with get_session() as s:
            rows = s.exec(select(Article)).all()
        filtered = [
            (a, haversine(lat, lon, a.latitude, a.longitude))
            for a in rows if a.latitude and a.longitude
        ]
        nearby = [a for a, d in filtered if d <= radius]
        nearby.sort(key=lambda x: haversine(lat, lon, x.latitude, x.longitude))
        return self._enrich(nearby[:limit])

    def _enrich(self, articles: List[Article]):
        return [
            {
                "title": a.title,
                "description": a.description,
                "url": a.url,
                "publication_date": a.publication_date.isoformat() if a.publication_date else None,
                "source_name": a.source_name,
                "category": a.categories,
                "relevance_score": a.relevance_score,
                "latitude": a.latitude,
                "longitude": a.longitude,
                "llm_summary": self.llm.summarize(a.title, a.description),
            }
            for a in articles
        ]
    
    def simulate_user_events(self, num_events=1000):
        """Simulate random user interactions with articles for testing trending feed."""
        from random import choice, uniform, randint
        from sqlalchemy import select
        

        with get_session() as s:
            articles = s.exec(select(Article)).scalars().all()

            if not articles:
                print("⚠️ No articles found in DB to simulate events.")
                return

            for _ in range(num_events):
                art = choice(articles)
                e = UserEvent(
                    article_id=art.id,
                    user_id=str(randint(1, 1000)),
                    event_type=choice(["view", "click", "share"]),
                    latitude=(art.latitude or 20.0) + uniform(-0.3, 0.3),
                    longitude=(art.longitude or 78.0) + uniform(-0.3, 0.3),
                    timestamp=datetime.utcnow() - timedelta(minutes=randint(0, 720))
                )
                s.add(e)
            s.commit()
        print(f"✅ Simulated {num_events} user events.")


    def compute_trending_feed(self, lat: float, lon: float, limit: int = 10):
        """
        Compute location-aware trending feed with realistic user-event weighting.
        Factors considered:
        - Engagement volume (views, clicks, shares)
        - Recency of interactions
        - Geographical proximity (boosts local relevance)
        """

        with get_session() as s:
            articles = s.exec(select(Article)).all()
            events = s.exec(select(UserEvent)).all()

            if not articles or not events:
                print("⚠️ Insufficient data to compute trending feed.")
                return {"count": 0, "articles": []}

            event_map = {}
            for e in events:
                stats = event_map.setdefault(
                    e.article_id, {"count": 0, "recent_score": 0.0, "distance_score": 0.0}
                )

                # Engagement weight by type
                weight = {"view": 1, "click": 2, "share": 3}.get(e.event_type, 1)
                stats["count"] += weight

                # Recency decay — newer interactions count more
                age_hours = max(1, (datetime.utcnow() - e.timestamp).total_seconds() / 3600)
                stats["recent_score"] += 1 / age_hours

                # Proximity bonus — sharp decay after ~2000 km
                distance = haversine(lat, lon, e.latitude, e.longitude)
                proximity_factor = max(0.0, 1 - min(distance / 2000, 1))
                stats["distance_score"] += proximity_factor * 10

            # --- Normalization across all articles ---
            def safe_max(v):
                return max(v) if v else 1

            max_count = safe_max([s["count"] for s in event_map.values()])
            max_recent = safe_max([s["recent_score"] for s in event_map.values()])
            max_distance = safe_max([s["distance_score"] for s in event_map.values()])

            # --- Compute composite trending score ---
            trending = []
            for art in articles:
                stats = event_map.get(art.id)
                if not stats:
                    continue
                score = (
                    (stats["count"] / max_count) * 0.4 +
                    (stats["recent_score"] / max_recent) * 0.2 +
                    (stats["distance_score"] / max_distance) * 0.4
                )
                trending.append((art, score))

            # --- Rank and enrich ---
            trending.sort(key=lambda x: x[1], reverse=True)
            top = trending[:limit]

            print(f"🔥 Trending Feed Generated ({len(top)} results):")
            for art, score in top:
                print(f"  - {art.title[:60]}... → score={round(score, 3)}")

            # Reuse enrich() + attach score
            enriched = self._enrich([a for a, _ in top])
            for i, (_, score) in enumerate(top):
                enriched[i]["trending_score"] = round(score, 3)

            return {"count": len(enriched), "articles": enriched}
        
    def filter_based_on_nearby_location_and_recency_subset(
        self,
        query: str,
        loc_name: str,
        base_articles: List[dict],
        radius_km: float = 500,
        limit: int = 5,
    ) -> List[dict]:
        """
        Re-rank a base set of already filtered articles by proximity + recency.
        `base_articles` is a list of dicts (the enriched articles) to re-score.
        """

        coords = self.geo.geocode(loc_name)
        if coords is None:
            # fallback to just return the base list (or rank_search over base)
            return base_articles[:limit]

        loc_lat, loc_lon = coords

        scored = []
        for a in base_articles:
            # We have enriched dict, so fields are direct
            title = a.get("title", "")
            desc = a.get("description", "")
            tm = text_match_score(query, title, desc)
            rs = a.get("relevance_score", 0) or 0
            base_score = (0.6 * tm + 0.4 * rs)
            # apply recency boost
            # You may need to convert publication_date string → datetime if needed,
            # or better store publication_date as datetime earlier
            # For simplicity, assume your a["publication_date"] is datetime or parse it
            # If it is string, parse to datetime
            # Here we skip recency in this subset version for brevity, or reuse recency_boost
            base_score *= recency_boost(
                datetime.fromisoformat(a["publication_date"])
                if isinstance(a.get("publication_date"), str)
                else a.get("publication_date")
            )

            dist = None
            lat = a.get("latitude")
            lon = a.get("longitude")
            if lat is not None and lon is not None:
                try:
                    dist = haversine(loc_lat, loc_lon, lat, lon)
                except Exception:
                    dist = None

            if dist is not None:
                if dist <= radius_km:
                    final = base_score + (1 / (1 + dist)) * 0.5
                else:
                    final = base_score * 0.5
            else:
                final = base_score

            scored.append((a, final))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = [a for a, _ in scored[:limit]]
        return top
