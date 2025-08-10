# Se Python introduktion video ift. syntax. fx. Python for Java coders or Python for JS coders
# Løs fejl i .py filer 
# Implementer Amazon Bedrock AI signals
# DONE
# Set debugging op i Python (Et virtual environment til at teste i)
# Debug scoring metode og hvordan man kan sætte det op
import os
import logging
from typing import Any, Dict, List
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger("app.analyzer")

AWS_REGION = os.getenv("AWS_REGION", "eu-central-1")
comprehend = boto3.client("comprehend", region_name=AWS_REGION)



def _preview(text: str, max_len: int = 80) -> str:
    t = (text or "").replace("\n", " ")
    return t[:max_len] + ("..." if len(t) > max_len else "")

def analyze_text(text: str) -> Dict[str, Any]:
    FAKE_ANALYZER = os.getenv("FAKE_ANALYZER", "0") == "1"
    if FAKE_ANALYZER:
        return {
        "labels": ["DRUG"],
        "entities": [
            {"value": "Ibuprofen", "type": "DRUG", "start_index": 0, "end_index": 9}
        ],
        "score": 0.9,
        "sentiment": "POSITIVE",
        "summary": ""
    }
    if not text:
        logger.info("analyze_text: tom tekst modtaget")
        return {"labels": [], "entities": [], "score": 0.0, "sentiment": "UNKNOWN", "summary": ""}

    logger.info("analyze_text: len=%d preview='%s'", len(text), _preview(text))

    sentiment = "UNKNOWN"
    score = 0.0

    try:
        s = comprehend.detect_sentiment(Text=text, LanguageCode="en")
        sentiment = s.get("Sentiment", "UNKNOWN")
        scores = s.get("SentimentScore", {}) or {}
        if scores:
            score = float(max(scores.values()))
        logger.info("detect_sentiment ok: sentiment=%s score=%.3f", sentiment, score)
    except ClientError as e:
        logger.exception("detect_sentiment fejlede: %s", e)

    try:
        resp = comprehend.detect_entities(Text=text, LanguageCode="en")
        raw = resp.get("Entities", []) or []
        entities = [{
            "value": it.get("Text", ""),
            "type": it.get("Type", "OTHER"),
            "start_index": int(it["BeginOffset"]) if it.get("BeginOffset") is not None else None,
            "end_index": int(it["EndOffset"]) if it.get("EndOffset") is not None else None,
        } for it in raw]
        labels = sorted({e["type"] for e in entities if e.get("type")})
        logger.info("detect_entities ok: entities=%d labels=%d", len(entities), len(labels))
    except ClientError:
        logger.exception("detect_entities fejlede")
        entities, labels = [], []

    return {"labels": labels, "entities": entities, "score": score, "sentiment": sentiment, "summary": ""}

