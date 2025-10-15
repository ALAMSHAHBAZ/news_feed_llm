# Contextual News Retrieval API

A backend service providing context-aware news retrieval over a local dataset, with support for:
- filtering by **category**, **source**, **score**, **text search**, or **proximity / nearby**
- a **smart query** endpoint that uses an LLM to determine intent
- a **smart trending** endpoint returns location-based, user activity(like, view, share) and recency based trending news feed.
- enriching articles with LLM-generated summaries (with caching)
- optional geocoding of location names into latitude/longitude

---

## 🛠 Setup & Running Instructions

### Prerequisites

- Python 3.10 or above  
- (Optional) OpenAI / LLM API key as environment variable  
- (Optional) Geocoding API key, if using external geocoder  

### Install & Ingest Data

1. Clone or copy the repository into a folder  
2. Create a virtual environment and install dependencies:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
3. Ingest your news_data.json (or folder of JSON files) into the database:
   ```python ingest.py --input ./news_data.json```

4. Run the Application
```uvicorn app.main:app --reload --port 8000```
Server runs at http://127.0.0.1:8000


## API Endpoints & Examples
 All endpoints return JSON with fields: count and articles. Each article includes keys like title, description, url, publication_date, source_name, category, relevance_score, latitude, longitude, llm_summary.

 1. Category

```Request

GET /api/news/category?category=Technology


Example Response

{
  "count": 5,
  "articles": [
    {
      "title": "New AI breakthrough announced",
      "description": "...",
      "url": "...",
      "publication_date": "2025-04-10T12:00:00",
      "source_name": "TechCrunch",
      "category": ["Technology"],
      "relevance_score": 0.87,
      "latitude": 37.77,
      "longitude": -122.42,
      "llm_summary": "A new AI model that improves inference speed was launched..."
    },
    ...
  ]
}
```

2. Source

```Request

GET /api/news/source?source=Reuters


Example Response

{
  "count": 5,
  "articles": [
    {
      "title": "Markets rally after central bank pivot",
      "description": "...",
      "url": "...",
      "publication_date": "2025-05-05T09:30:00",
      "source_name": "Reuters",
      "category": ["Markets", "Business"],
      "relevance_score": 0.92,
      "latitude": 51.51,
      "longitude": -0.13,
      "llm_summary": "Stocks worldwide rallied following hints of easing interest rates..."
    },
    ...
  ]
}
```

3. Score

```Request

GET /api/news/score?threshold=0.7


Example Response

{
  "count": 5,
  "articles": [
    {
      "title": "Breakthrough in battery technology",
      "description": "...",
      "url": "...",
      "publication_date": "2025-06-15T08:00:00",
      "source_name": "Wired",
      "category": ["Technology"],
      "relevance_score": 0.89,
      "latitude": 40.71,
      "longitude": -74.01,
      "llm_summary": "Researchers unveiled a battery that doubles energy density..."
    },
    ...
  ]
}
```

4. Search

```Request

GET /api/news/search?query=Elon+Musk+Starlink


Example Response

{
  "count": 5,
  "articles": [
    {
      "title": "Pakistan grants Starlink permission",
      "description": "...",
      "url": "...",
      "publication_date": "2025-03-23T05:26:46",
      "source_name": "Hindustan Times",
      "category": ["World", "Technology"],
      "relevance_score": 0.69,
      "latitude": 17.87,
      "longitude": 73.43,
      "llm_summary": "Pakistan has provided temporary approval for Elon Musk’s Starlink service..."
    },
    ...
  ]
}
```

5. Nearby

```Request

GET /api/news/nearby?lat=28.6139&lon=77.2090&radius=50


Example Response

{
  "count": 5,
  "articles": [
    {
      "title": "Delhi air quality drops sharply",
      "description": "...",
      "url": "...",
      "publication_date": "2025-05-20T07:30:00",
      "source_name": "DelhiTimes",
      "category": ["Local", "Environment"],
      "relevance_score": 0.74,
      "latitude": 28.70,
      "longitude": 77.10,
      "llm_summary": "Delhi’s air quality index soared past safe levels..."
    },
    ...
  ]
}
```

6. Smart Query

```Request

POST /api/news/query
{
  "query": "Technology trends coverage by Times Now in India"
}


Example Response

```{
  "query": "Technology trends coverage by Times Now in India",
  "intent": ["category","source"],
  "logic_used": "Search + Category(Technology) + Source(Times Now)",
  "count": 5,
  "articles": [
    {
      "title": "AI innovation report by Times Now",
      "description": "...",
      "url": "...",
      "publication_date": "2025-07-01T11:00:00",
      "source_name": "Times Now",
      "category": ["Technology","Innovation"],
      "relevance_score": 0.85,
      "latitude": 28.70,
      "longitude": 77.10,
      "llm_summary": "Times Now features an in-depth AI innovation report..."
    },
    ...
  ]
}
```

7. Trending

Provides location-based trending articles, using simulated or real user interaction data.

```Request

GET /api/news/trending?lat=28.6139&lon=77.2090&limit=5&simulate=true


Response Example

{
  "count": 5,
  "articles": [
    {
      "title": "Local startup funding roundup in Delhi",
      "description": "...",
      "url": "...",
      "publication_date": "2025-08-12T10:20:00",
      "source_name": "Delhi Business News",
      "category": ["Business","Technology"],
      "latitude": 28.70,
      "longitude": 77.10,
      "trending_score": 0.95,
      "llm_summary": "Several startups in the Delhi region recently secured funding in August, highlighting increased investor interest locally."
    },
    {
      "title": "Delhi pollution alert intensifies",
      "description": "...",
      "url": "...",
      "publication_date": "2025-08-12T08:00:00",
      "source_name": "Delhi Times",
      "category": ["Local","Environment"],
      "latitude": 28.70,
      "longitude": 77.10,
      "trending_score": 0.88,
      "llm_summary": "Air quality in New Delhi worsened sharply today, prompting health advisories and alerts across the city."
    }
    // … up to 5 articles
  ]
}
