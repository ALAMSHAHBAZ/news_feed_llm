from fastapi import APIRouter, Query
from app.services.news_service import NewsService
from app.services.intent_service import IntentService
import logging

router = APIRouter(prefix="/api/news", tags=["News"])
service = NewsService()
intent_service = IntentService()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

@router.get("/category")
def by_category(category: str = Query(...)):
    return {"articles": service.rank_category(category), "count": 5}

@router.get("/source")
def by_source(source: str = Query(...)):
    return {"articles": service.rank_source(source), "count": 5}

@router.get("/score")
def by_score(threshold: float = 0.7):
    return {"articles": service.rank_score(threshold), "count": 5}

@router.get("/search")
def search(query: str = Query(...)):
    return {"articles": service.rank_search(query), "count": 5}

@router.get("/nearby")
def nearby(lat: float, lon: float, radius: float = 10.0):
    return {"articles": service.rank_nearby(lat, lon, radius), "count": 5}

@router.post("/query")
async def smart_query(req: dict):
    user_query = req.get("query")
    if not user_query or not isinstance(user_query, str):
        return {"error": "Query text is required (string)"}

    intent_info = intent_service.extract_intent(user_query)
    intents = intent_info.get("intent", [])
    entities = intent_info.get("entities", [])
    location = intent_info.get("location")
    source = intent_info.get("source")

    logging.info(f"User Query: {user_query}")
    logging.info(f"Detected Intent(s): {intents}")
    logging.info(f"Detected Entities: {entities}")
    logging.info(f"Detected Location: {location}")
    logging.info(f"Detected Source: {source}")

    logic_used = []
    # Step 1: start with search
    base = service.rank_search(user_query)
    logic_used.append("Search")

    # Step 2: filter by category if present
    category = entities[0] if entities else None
    if "category" in intents and category:
        base = [a for a in base if any(category.lower() == c.lower() for c in a.get("category", []))]
        logic_used.append(f"Category({category})")

    # Step 3: filter by source if present (liberal filter)
    source = next((e for e in entities if "news" in e.lower() or "times" in e.lower()), None)
    if "source" in intents and source:
        filtered_by_source = [a for a in base if a.get("source_name") and source.lower() in a["source_name"].lower()]
        if filtered_by_source:
            base = filtered_by_source
            logic_used.append(f"Source({source})")
        else:
            # if no match by source, skip this filtering
            logic_used.append(f"Source({source}) filter skipped (no match)")

    # Step 4: if location asked, re-rank by nearby + recency using subset
    if "nearby" in intents and location:
        base = service.filter_based_on_nearby_location_and_recency_subset(
            user_query, location, base_articles=base
        )
        logic_used.append(f"Nearby({location})")

    # Build logic_used string
    logic_str = " + ".join(logic_used)

    logging.info(f"✅ Retrieval Logic Used: {logic_str}")

    return {
        "query": user_query,
        "intent": intents,
        "logic_used": logic_str,
        "count": len(base),
        "articles": base
    }



@router.get("/trending")
async def get_trending_news(
    lat: float = Query(..., description="User latitude"),
    lon: float = Query(..., description="User longitude"),
    limit: int = Query(5, description="Max number of articles to return"),
    simulate: bool = Query(False, description="Simulate events if no data")
):
    """
    Returns location-based trending news feed.
    If `simulate=true`, auto-generates sample user events when no data exists.
    """
    # 🧩 Optional simulation for first-time setup / dev
    from app.database import get_session
    from app.models import UserEvent
    with get_session() as s:
        total_events = s.query(UserEvent).count()

    if simulate and total_events == 0:
        service.simulate_user_events(num_events=500)

    articles = service.compute_trending_feed(lat, lon, limit)
    return {"count": len(articles), "articles": articles}