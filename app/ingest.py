#!/usr/bin/env python3
"""
Ingest news JSON files into the local DB (SQLite by default; Postgres supported).
Usage:
    python ingest.py --input ./news_data.json
"""
import argparse, json, glob, os, gzip
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Iterable, List, Dict, Any


from app.database import init_db, get_session
from models import Article

ISO_FORMATS = [
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%d %H:%M:%S",
]

def iter_files(input_path: str) -> Iterable[str]:
    if os.path.isdir(input_path):
        for p in glob.glob(os.path.join(input_path, "**", "*.json"), recursive=True):
            yield p
        for p in glob.glob(os.path.join(input_path, "**", "*.json.gz"), recursive=True):
            yield p
    else:
        yield input_path

def load_json_array(path: str) -> List[Dict[str, Any]]:
    opener = gzip.open if path.endswith(".gz") else open
    with opener(path, "rt", encoding="utf-8") as f:
        data = json.load(f)
        if not isinstance(data, list):
            raise ValueError(f"File {path} does not contain a JSON array")
        return data

def parse_dt(val) -> datetime | None:
    if not val:
        return None
    s = str(val).replace("Z", "+00:00").strip()
    for fmt in ISO_FORMATS:
        try:
            return datetime.strptime(s, fmt)
        except Exception:
            continue
    try:
        return datetime.fromisoformat(s.replace("Z", ""))
    except Exception:
        return None

def normalize_article(obj: Dict[str, Any]) -> Article:
    art = Article(
        id=str(obj.get("id")),
        title=str(obj.get("title") or "").strip(),
        description=(obj.get("description") or None),
        url=(obj.get("url") or None),
        publication_date=parse_dt(obj.get("publication_date")),
        source_name=(obj.get("source_name") or None),
        relevance_score=(float(obj.get("relevance_score")) if obj.get("relevance_score") is not None else None),
        latitude=(float(obj.get("latitude")) if obj.get("latitude") is not None else None),
        longitude=(float(obj.get("longitude")) if obj.get("longitude") is not None else None),
    )
    cats = obj.get("category")
    if isinstance(cats, list):
        art.categories = [str(c).strip() for c in cats if str(c).strip()]
    elif isinstance(cats, str) and cats.strip():
        art.categories = [c.strip() for c in cats.split(",") if c.strip()]
    else:
        art.categories = []
    return art

def ingest_files(paths: List[str], batch_size: int = 1000) -> tuple[int, int]:
    total_rows = 0
    files_done = 0
    with get_session() as s:
        buf: List[Article] = []
        for p in paths:
            try:
                arr = load_json_array(p)
            except Exception as e:
                print(f"[WARN] Skipping {p}: {e}")
                continue
            for obj in arr:
                try:
                    a = normalize_article(obj)
                    if not a.id:
                        continue
                    buf.append(a)
                    if len(buf) >= batch_size:
                        for rec in buf:
                            s.merge(rec)
                        s.commit()
                        total_rows += len(buf)
                        buf.clear()
                except Exception as e:
                    print(f"[WARN] Bad record in {p}: {e}")
            files_done += 1
        if buf:
            for rec in buf:
                s.merge(rec)
            s.commit()
            total_rows += len(buf)
    return total_rows, files_done

def main():
    ap = argparse.ArgumentParser(description="Ingest news JSON into DB")
    ap.add_argument("--input", required=True, help="Path to directory OR .json file")
    ap.add_argument("--batch-size", type=int, default=1000)
    ap.add_argument("--workers", type=int, default=1)
    args = ap.parse_args()

    init_db()

    paths = list(iter_files(args.input))
    total, files_done = ingest_files(paths, batch_size=args.batch_size)
    print(f"✅ Done. Upserted {total} records from {files_done} file(s).")

if __name__ == "__main__":
    main()
