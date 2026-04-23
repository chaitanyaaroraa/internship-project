"""
FastAPI backend - CarDekho Recommendation Engine
=================================================
Loads the car dataset CSV into an in-memory SQLite database on startup.
Exposes a POST /recommend endpoint that builds a dynamic SQL query using
the user's filter parameters and returns scored, ranked results.

Run:  python app.py
"""

import csv
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# ──────────────────────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────────────────────
CSV_PATH = Path(__file__).resolve().parent.parent.parent / "cars_dataset.csv"
if not CSV_PATH.exists():
    CSV_PATH = Path(__file__).resolve().parent.parent / "cars_dataset.csv"
if not CSV_PATH.exists():
    CSV_PATH = Path(__file__).resolve().parent / "cars_dataset.csv"

DB_PATH = ":memory:"

# ──────────────────────────────────────────────────────────────
# Database helpers
# ──────────────────────────────────────────────────────────────
_connection: Optional[sqlite3.Connection] = None


def _get_db() -> sqlite3.Connection:
    assert _connection is not None, "Database not initialised"
    return _connection


def _init_db():
    global _connection
    _connection = sqlite3.connect(DB_PATH, check_same_thread=False)
    _connection.row_factory = sqlite3.Row

    cur = _connection.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS cars (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            model_variant   TEXT,
            model           TEXT,
            variant         TEXT,
            features        TEXT,
            specs           TEXT,
            mileage_kmpl    REAL,
            safety_rating   INTEGER,
            city            TEXT,
            ex_showroom_price INTEGER,
            on_road_price   INTEGER
        )
    """)
    _connection.commit()

    if not CSV_PATH.exists():
        print(f"[WARN] CSV not found at {CSV_PATH} - starting with empty table")
        return

    with open(CSV_PATH, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = []
        for row in reader:
            rows.append((
                row.get("model+variant", "").strip(),
                row.get("model", "").strip(),
                row.get("variant", "").strip(),
                row.get("features", "").strip(),
                row.get("specs", "").strip(),
                float(row.get("mileage_kmpl", 0)),
                int(row.get("safety_rating", 0)),
                row.get("city", "").strip(),
                int(row.get("ex_showroom_price", 0)),
                int(row.get("on_road_price", 0)),
            ))

        cur.executemany("""
            INSERT INTO cars
                (model_variant, model, variant, features, specs,
                 mileage_kmpl, safety_rating, city, ex_showroom_price, on_road_price)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)
        _connection.commit()

    print(f"[OK] Loaded {len(rows)} rows from {CSV_PATH}")


# ──────────────────────────────────────────────────────────────
# FastAPI app
# ──────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    _init_db()
    yield
    if _connection:
        _connection.close()


app = FastAPI(
    title="CarDekho Recommendation API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────────────────────
# Request / Response schemas
# ──────────────────────────────────────────────────────────────
class RecommendRequest(BaseModel):
    budget: float                          # max budget in lakhs
    car_type: str = "Any"                  # "Any" | "SUV" | "Sedan" | "Hatchback"
    usage: str = "Mixed"                   # "City" | "Highway" | "Mixed"
    preferred_brands: List[str] = []       # e.g. ["Maruti", "Hyundai"]


class CarResult(BaseModel):
    model: str
    variant: str
    features: str
    specs: str
    mileage_kmpl: float
    safety_rating: int
    city: str
    ex_showroom_price: int
    on_road_price: int
    price_lakh: float
    score: float
    reason: str


class RecommendResponse(BaseModel):
    count: int
    cars: List[CarResult]


# ──────────────────────────────────────────────────────────────
# Car-type mapping (model name -> body type)
# ──────────────────────────────────────────────────────────────
CAR_TYPE_MAP = {
    "Maruti Swift": "Hatchback",
    "Maruti Baleno": "Hatchback",
    "Maruti Alto K10": "Hatchback",
    "Maruti WagonR": "Hatchback",
    "Hyundai i20": "Hatchback",
    "Tata Altroz": "Hatchback",
    "Tata Punch": "SUV",
    "Tata Nexon": "SUV",
    "Hyundai Venue": "SUV",
    "Hyundai Creta": "SUV",
    "Kia Sonet": "SUV",
    "Mahindra XUV300": "SUV",
    "Mahindra XUV700": "SUV",
    "Honda City": "Sedan",
    "Honda Amaze": "Sedan",
    "Hyundai Aura": "Sedan",
}

# Brand extraction from model name
BRANDS = ["Maruti", "Hyundai", "Tata", "Honda", "Kia", "Mahindra"]


def _get_brand(model: str) -> str:
    for b in BRANDS:
        if model.startswith(b):
            return b
    return ""


# ──────────────────────────────────────────────────────────────
# Build reason text
# ──────────────────────────────────────────────────────────────
def _build_reason(row: dict, usage: str, is_preferred_brand: bool) -> str:
    parts = []

    if is_preferred_brand:
        parts.append("from a brand you prefer")

    if row["safety_rating"] >= 5:
        parts.append("top-rated 5-star safety")
    elif row["safety_rating"] >= 4:
        parts.append("strong safety rating")

    if row["mileage_kmpl"] >= 20:
        parts.append(f"excellent mileage ({row['mileage_kmpl']} km/l)")
    elif row["mileage_kmpl"] >= 17:
        parts.append(f"good mileage ({row['mileage_kmpl']} km/l)")

    price_lakh = row["ex_showroom_price"] / 100000
    if price_lakh < 7:
        parts.append("very budget-friendly")

    specs = row.get("specs", "")
    if "Automatic" in specs or "CVT" in specs or "AMT" in specs:
        parts.append("automatic transmission")

    if "Sunroof" in row.get("features", ""):
        parts.append("comes with sunroof")

    if not parts:
        parts.append("solid all-round choice in your budget")

    reason = ", ".join(parts)
    return reason[0].upper() + reason[1:] + "."


# ──────────────────────────────────────────────────────────────
# /recommend endpoint
# ──────────────────────────────────────────────────────────────
@app.post("/recommend", response_model=RecommendResponse)
async def recommend(req: RecommendRequest):
    db = _get_db()

    budget_paise = int(req.budget * 100000)

    where_clauses = ["ex_showroom_price <= ?"]
    params: list = [budget_paise]

    # Car type filter
    if req.car_type and req.car_type != "Any":
        matching_models = [m for m, t in CAR_TYPE_MAP.items() if t == req.car_type]
        if matching_models:
            placeholders = ", ".join("?" for _ in matching_models)
            where_clauses.append(f"model IN ({placeholders})")
            params.extend(matching_models)

    # Brand filter
    if req.preferred_brands:
        brand_conditions = " OR ".join("model LIKE ?" for _ in req.preferred_brands)
        where_clauses.append(f"({brand_conditions})")
        params.extend(f"{b}%" for b in req.preferred_brands)

    sql = f"""
        SELECT model_variant, model, variant, features, specs,
               mileage_kmpl, safety_rating, city,
               ex_showroom_price, on_road_price
        FROM cars
        WHERE {' AND '.join(where_clauses)}
        ORDER BY ex_showroom_price ASC
    """

    print(f"\n[QUERY] {sql}")
    print(f"[PARAMS] {params}")

    cur = db.execute(sql, params)
    rows = [dict(r) for r in cur.fetchall()]

    # Score and rank
    scored = []
    for row in rows:
        score = 0.0
        brand = _get_brand(row["model"])
        is_preferred_brand = brand in req.preferred_brands

        if is_preferred_brand:
            score += 25

        score += row["mileage_kmpl"] * 0.5
        score += row["safety_rating"] * 4

        price_lakh = row["ex_showroom_price"] / 100000
        score += max(0, (req.budget - price_lakh) * 1.5)

        if req.usage.lower() == "city" and row["mileage_kmpl"] >= 20:
            score += 10
        elif req.usage.lower() == "highway":
            if "Turbo" in row.get("specs", ""):
                score += 10
            if "Automatic" in row.get("specs", "") or "CVT" in row.get("specs", ""):
                score += 5
        elif req.usage.lower() == "mixed":
            score += 5

        reason = _build_reason(row, req.usage, is_preferred_brand)
        scored.append((row, round(score, 1), reason))

    scored.sort(key=lambda x: x[1], reverse=True)
    top = scored[:5]

    results = []
    for row, score, reason in top:
        results.append(CarResult(
            model=row["model"],
            variant=row["variant"],
            features=row["features"],
            specs=row["specs"],
            mileage_kmpl=row["mileage_kmpl"],
            safety_rating=row["safety_rating"],
            city=row["city"],
            ex_showroom_price=row["ex_showroom_price"],
            on_road_price=row["on_road_price"],
            price_lakh=round(row["ex_showroom_price"] / 100000, 2),
            score=score,
            reason=reason,
        ))

    return RecommendResponse(count=len(results), cars=results)


@app.get("/health")
async def health():
    db = _get_db()
    count = db.execute("SELECT COUNT(*) FROM cars").fetchone()[0]
    return {"status": "ok", "car_count": count}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=True)
