# backend/app/main.py

from decimal import Decimal
import os, time, uuid 
from typing import List
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from boto3.dynamodb.conditions import Key

# Henter klasser og funktioner fra de andre .py filer
from .schemas import AnalyzeIn, ReportOut
from .services.analyzer import analyze_text  # must return dict with keys: labels, entities, score, optional sentiment, summary

# --- logging tilføjet ---
import logging
from logging.config import dictConfig
from contextvars import ContextVar
from botocore.exceptions import ClientError
# --- slut logging imports ---

# Load .env locally; on AWS EB you set env vars in the console
load_dotenv()


TABLE_NAME = os.getenv("DDB_TABLE_NAME", "Reports")
AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
DEMO_USER = os.getenv("DEMO_USER", "demo")
CORS_ORIGIN = os.getenv("CORS_ORIGIN", "http://localhost:5173")

AWS_DDB_ENDPOINT = os.getenv("AWS_DDB_ENDPOINT")  # fx "http://dynamodb:8000" i docker

# Opretter forbindelse til vores database 
ddb = boto3.resource("dynamodb", region_name=AWS_REGION)
table = ddb.Table(TABLE_NAME)

# --- logging konfiguration ---
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

dictConfig({
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s %(levelname)s %(name)s [rid=%(request_id)s]: %(message)s"
        }
    },
    "handlers": {
        "default": {"class": "logging.StreamHandler", "formatter": "default"}
    },
    "root": {"level": LOG_LEVEL, "handlers": ["default"]},
})

logger = logging.getLogger("app.main")
request_id_ctx = ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id_ctx.get()
        return True

for h in logging.getLogger().handlers:
    h.addFilter(RequestIdFilter())
# --- slut logging konfiguration ---
logger.info("program start")

app = FastAPI(title="Reports API")

app.add_middleware( # kommunikation mellem frontend og backend
    CORSMiddleware,
    allow_origins=[CORS_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- request logging middleware (bevarer dine egne kommentarer uændret) ---
@app.middleware("http")
async def log_requests(request, call_next):
    rid = request.headers.get("x-request-id", str(uuid.uuid4()))
    token = request_id_ctx.set(rid)
    start = time.perf_counter()
    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start) * 1000
        response.headers["x-request-id"] = rid
        logger.info("HTTP %s %s status=%s dur=%.1fms", request.method, request.url.path, response.status_code, duration_ms)
        return response
    finally:
        request_id_ctx.reset(token)
# --- slut middleware ---

@app.get("/health") # Tjek om API kører
def health():
    logger.debug("health check")
    return {"ok": True}

@app.post("/analyze", response_model=ReportOut) # 
def analyze(input: AnalyzeIn): # Definer funktion og AnalyzeIn er input
    """
    Analyze text, store in DynamoDB, return the stored item.
    analyzer.analyze_text must return:
      {
        "labels": List[str],
        "entities": List[dict],
        "score": float,
        "sentiment": Optional[str],
        "summary": Optional[str]
      }
    """
    result = analyze_text(input.text) # Modtager tekst fra analyzer.py funktionen

    score_raw = result.get("score", 0.0)
    try:
     score_db = Decimal(str(score_raw))
    except Exception:
     score_db = Decimal("0")

    now = int(time.time())
    item = { # Udfylder felter i din database ud fra input og analyse resultat
        "userId": DEMO_USER,
        "createdAt": now,
        "id": str(uuid.uuid4()),
        "text": input.text,
        "labels": result.get("labels", []),
        "entities": result.get("entities", []),
        "score": score_db,
        "sentiment": result.get("sentiment", "UNKNOWN"),
        "summary": result.get("summary", ""),
        "source": "manual",
    }

    
    
    try:
        table.put_item(Item=item) # Gemmer hele item i tabellen
        logger.info(
            "saved report id=%s labels=%d entities=%d sentiment=%s score=%s",
            item["id"], len(item["labels"]), len(item["entities"]), item["sentiment"], item["score"]
        )
    except ClientError as e:
        logger.exception("dynamodb put_item failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to store item")
    response_item = dict(item)
    try:
        response_item["score"] = float(response_item["score"])
    except Exception:
        response_item["score"] = 0.0
    return response_item

# Funktion henter seneste 10 items for en bruger ID
@app.get("/reports", response_model=List[ReportOut])
def list_reports(limit: int = 10):
    """
    Return latest items for the demo user.
    Requires table with PK userId (S) and SK createdAt (N).
    """
    try:
        resp = table.query(
            KeyConditionExpression=Key("userId").eq(DEMO_USER),
            ScanIndexForward=False,  # newest first
            Limit=limit,
        )
    except ClientError as e:
        logger.exception("dynamodb query failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to query reports")

    items = resp.get("Items", [])
    logger.info("list_reports returned=%d", len(items))
    return items

# Funktion der slår en enkel item op ved at bruge en ID
@app.get("/reports/{report_id}", response_model=ReportOut) 
def get_report_by_id(report_id: str):
    """
    Optional convenience lookup by id using GSI 'byId'.
    Your DynamoDB template must define a GSI with Partition Key 'id'.
    """
    try:
        resp = table.query(
            IndexName="byId",
            KeyConditionExpression=Key("id").eq(report_id),
            Limit=1,
        )
    except ClientError as e:
        logger.exception("dynamodb query by id failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to query by id")

    items = resp.get("Items", [])
    if not items:
        logger.info("report not found id=%s", report_id)
        raise HTTPException(status_code=404, detail="Not found")
    return items[0]
