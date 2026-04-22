import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field


DB_PATH = Path(__file__).parent / "cars_demo.db"


SAMPLE_CARS = [
    ("Maruti Suzuki", "Alto K10",       "VXI",        4.0,  25.0,  67,  "Commercial,Personal Use",           "Hatchback"),
    ("Maruti Suzuki", "Swift",          "ZXI",        6.5,  23.0,  89,  "Family Use,Personal Use",           "Hatchback"),
    ("Tata",          "Tiago",          "XZ Plus",    5.5,  20.0,  85,  "Personal Use,Commercial",           "Hatchback"),
    ("Hyundai",       "i20",            "Asta",       7.5,  20.0,  83,  "Personal Use,Family Use",           "Hatchback"),
    ("Tata",          "Altroz",         "XZ Plus",    7.0,  19.0,  88,  "Personal Use,Family Use",           "Hatchback"),
    ("Maruti Suzuki", "Dzire",          "ZXI",        7.0,  22.0,  89,  "Commercial,Family Use,Personal Use", "Sedan"),
    ("Honda",         "City",           "VX MT",     12.0,  18.0, 119,  "Family Use,Personal Use",           "Sedan"),
    ("Maruti Suzuki", "Ertiga",         "ZXI",       10.0,  20.0, 101,  "Family Use,Commercial",             "MPV"),
    ("Toyota",        "Innova Crysta",  "GX",        20.0,  12.0, 148,  "Family Use,Commercial",             "MPV"),
    ("Mahindra",      "Bolero",         "B6",         9.0,  16.0,  75,  "Commercial,Family Use",             "SUV"),
    ("Tata",          "Nexon",          "XZ Plus",    9.0,  22.0, 118,  "Family Use,Personal Use",           "SUV"),
    ("Kia",           "Seltos",         "HTX",       11.0,  17.0, 140,  "Family Use,Personal Use",           "SUV"),
    ("Hyundai",       "Creta",          "SX",        12.0,  17.0, 113,  "Family Use,Personal Use",           "SUV"),
    ("Mahindra",      "XUV700",         "AX7",       16.0,  16.0, 197,  "Family Use",                        "SUV"),
    ("Toyota",        "Fortuner",       "4x2 AT",    35.0,  12.0, 201,  "Family Use",                        "SUV"),
    ("BMW",           "3 Series",       "330Li",     52.0,  14.0, 255,  "Personal Use",                      "Sedan"),
    ("Mercedes-Benz", "C-Class",        "C 200",     62.0,  14.0, 204,  "Personal Use",                      "Sedan"),
    ("Audi",          "Q5",             "45 TFSI",   72.0,  13.0, 258,  "Personal Use,Family Use",           "SUV"),
]


def init_db() -> None:
    with sqlite3.connect(DB_PATH) as conn:
        conn.executescript(
            """
            DROP TABLE IF EXISTS cars;
            CREATE TABLE cars (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                brand        TEXT NOT NULL,
                model        TEXT NOT NULL,
                variant      TEXT NOT NULL,
                price_lakh   REAL NOT NULL,
                mileage_kmpl REAL NOT NULL,
                power_bhp    INTEGER NOT NULL,
                usage        TEXT NOT NULL,
                body_type    TEXT NOT NULL
            );
            """
        )
        conn.executemany(
            """
            INSERT INTO cars (brand, model, variant, price_lakh, mileage_kmpl, power_bhp, usage, body_type)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            SAMPLE_CARS,
        )
        conn.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Car Buying Assistant — Backend", lifespan=lifespan)


class SearchRequest(BaseModel):
    budget_lakh: float = Field(..., gt=0, description="Maximum budget in Lakhs ₹")
    preferences: List[str] = Field(..., min_length=1, description="Usage preferences")
    priority: str = Field(..., description="'Mileage' or 'Performance'")


class CarResult(BaseModel):
    id: int
    brand: str
    model: str
    variant: str
    price_lakh: float
    mileage_kmpl: float
    power_bhp: int
    usage: str
    body_type: str


class SearchResponse(BaseModel):
    count: int
    query: str
    params: list
    results: List[CarResult]


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/search-cars", response_model=SearchResponse)
def search_cars(req: SearchRequest):
    if req.priority == "Mileage":
        order_col = "mileage_kmpl"
    elif req.priority == "Performance":
        order_col = "power_bhp"
    else:
        raise HTTPException(status_code=400, detail="priority must be 'Mileage' or 'Performance'")

    usage_clause = " OR ".join(["usage LIKE ?"] * len(req.preferences))
    usage_params = [f"%{p}%" for p in req.preferences]

    sql = f"""
        SELECT id, brand, model, variant, price_lakh, mileage_kmpl, power_bhp, usage, body_type
        FROM cars
        WHERE price_lakh <= ?
          AND ({usage_clause})
        ORDER BY {order_col} DESC
        LIMIT 10
    """
    params = [req.budget_lakh, *usage_params]

    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(sql, params).fetchall()

    results = [CarResult(**dict(row)) for row in rows]
    return SearchResponse(
        count=len(results),
        query=" ".join(sql.split()),
        params=params,
        results=results,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend:app", host="0.0.0.0", port=8000, reload=True)
