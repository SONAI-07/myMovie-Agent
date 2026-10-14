import base64
import json
import logging
import re
from typing import Any, Dict, List, Optional, Union
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from agent.infra_agent import run_pipeline
from app.config import get_settings
from app.database import delete_recommendation, get_all_recommendations, save_recommendation
from app.dependencies import verify_webhook_token
from app.services.gmail_watcher import extract_movie_from_bms_email, gmail_watcher

logger = logging.getLogger("bingeWatch.router")

router = APIRouter()


class DirectMovieRequest(BaseModel):
    movie_watched: str = Field(
        ...,
        description="Name of the movie watched (e.g., 'Shutter Island', 'Interstellar')",
        examples=["Shutter Island"]
    )
    region: Optional[str] = Field(
        default="US",
        description="Target streaming region code (e.g., 'US', 'IN', 'GB', 'CA')",
        examples=["US"]
    )


class PubSubMessage(BaseModel):
    data: Optional[str] = Field(
        default=None,
        description="Base64-encoded payload from Pub/Sub topic"
    )
    attributes: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional metadata key-value pairs"
    )
    messageId: Optional[str] = Field(
        default=None,
        description="Pub/Sub message identifier"
    )
    publishTime: Optional[str] = Field(
        default=None,
        description="Timestamp when published"
    )


class PubSubPushPayload(BaseModel):
    message: PubSubMessage
    subscription: Optional[str] = None


class MovieItem(BaseModel):
    title: str
    release_year: Optional[Union[int, str]] = None
    thematic_connection: Optional[str] = None
    spark_reason: Optional[str] = None
    streaming_link: Optional[str] = None


class RecommendationResponse(BaseModel):
    id: Optional[str] = None
    status: str = "success"
    movie_watched: str
    source: str = "web"
    primary_theme: Optional[str] = None
    dominant_emotion: Optional[str] = None
    cinematic_style: Optional[str] = None
    recommendations: List[MovieItem] = []


class SimulateTicketRequest(BaseModel):
    movie_name: str = Field(..., examples=["Kalki 2898 AD", "Shutter Island"])


def parse_pubsub_data(b64_data: str) -> str:
    """
    Decodes base64 data from a Pub/Sub message and returns the identified movie title.
    """
    try:
        decoded_bytes = base64.b64decode(b64_data)
        decoded_str = decoded_bytes.decode("utf-8").strip()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to decode base64 Pub/Sub data: {e}"
        )

    # Try parsing as JSON first
    try:
        parsed_json = json.loads(decoded_str)
        if isinstance(parsed_json, dict):
            for key in ["movie_watched", "movie", "movie_title", "title", "film"]:
                if key in parsed_json and parsed_json[key]:
                    return str(parsed_json[key]).strip()
            # If payload contains email body or subject
            content = parsed_json.get("body") or parsed_json.get("subject") or parsed_json.get("text")
            if content:
                extracted = extract_movie_from_bms_email(parsed_json.get("subject", ""), str(content))
                if extracted:
                    return extracted
    except json.JSONDecodeError:
        pass

    # Fallback to BookMyShow text extraction
    extracted = extract_movie_from_bms_email("", decoded_str)
    if extracted:
        return extracted

    if len(decoded_str.splitlines()) == 1 and len(decoded_str) < 100:
        return decoded_str

    raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        detail="Could not extract movie title from Pub/Sub payload"
    )


@router.post(
    "/recommend",
    response_model=RecommendationResponse,
    summary="Direct movie recommendation",
    dependencies=[Depends(verify_webhook_token)]
)
async def direct_recommendation(payload: DirectMovieRequest) -> RecommendationResponse:
    """
    Direct endpoint to trigger the recommendation pipeline with a movie name.
    Automatically saves the recommendation to the database for persistence.
    """
    movie = payload.movie_watched.strip()
    if not movie:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Movie title cannot be empty"
        )

    logger.info("Direct recommendation triggered for movie: %s (Region: %s)", movie, payload.region)
    pipeline_result = await run_pipeline(movie, region=payload.region or "US")

    # Save to SQLite database so it stays permanently stored in the UI
    saved = save_recommendation(movie, pipeline_result, source="web")

    raw_recs = pipeline_result.get("final_streaming_links") or pipeline_result.get("curated_movies") or []
    items = [
        MovieItem(
            title=item.get("title", "Unknown"),
            release_year=item.get("release_year"),
            thematic_connection=item.get("thematic_connection"),
            spark_reason=item.get("spark_reason"),
            streaming_link=item.get("streaming_link")
        )
        for item in raw_recs if isinstance(item, dict)
    ]

    return RecommendationResponse(
        id=saved["id"],
        movie_watched=movie,
        source="web",
        primary_theme=pipeline_result.get("primary_theme"),
        dominant_emotion=pipeline_result.get("dominant_emotion"),
        cinematic_style=pipeline_result.get("cinematic_style"),
        recommendations=items
    )


@router.get("/history", summary="List Stored Movie Recommendations")
async def list_history(limit: int = 50) -> Dict[str, Any]:
    """
    Returns all stored recommendations from BookMyShow, Gmail, or Web searches.
    """
    records = get_all_recommendations(limit=limit)
    return {
        "status": "success",
        "count": len(records),
        "history": records
    }


@router.delete("/history/{rec_id}", summary="Delete a Stored Recommendation")
async def remove_history(rec_id: str) -> Dict[str, Any]:
    """Deletes a recommendation by its ID."""
    deleted = delete_recommendation(rec_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Recommendation record not found")
    return {"status": "success", "deleted_id": rec_id}


@router.get("/gmail/status", summary="Check Gmail Watcher Status")
async def gmail_status() -> Dict[str, Any]:
    """Returns the operational status of the Gmail BookMyShow autonomous listener."""
    settings = get_settings()
    configured = gmail_watcher.is_configured
    masked_user = (
        settings.gmail_user[:3] + "***@" + settings.gmail_user.split("@")[-1]
        if settings.gmail_user and "@" in settings.gmail_user
        else None
    )
    return {
        "configured": configured,
        "account": masked_user,
        "server": settings.gmail_imap_server,
        "check_interval_seconds": settings.gmail_check_interval
    }


@router.post("/gmail/sync", summary="Trigger Immediate Gmail Check")
async def gmail_sync() -> Dict[str, Any]:
    """
    Manually triggers an immediate poll of Gmail for unread BookMyShow confirmation tickets.
    """
    if not gmail_watcher.is_configured:
        return {
            "status": "idle",
            "message": "Gmail credentials (GMAIL_USER and GMAIL_APP_PASSWORD) not configured in .env",
            "processed": []
        }

    processed = await gmail_watcher.check_and_process_emails()
    return {
        "status": "completed",
        "processed_count": len(processed),
        "processed": processed
    }


@router.post("/gmail/simulate", summary="Simulate BookMyShow Confirmation Email")
async def simulate_bms_email(payload: SimulateTicketRequest) -> Dict[str, Any]:
    """
    Simulates receipt of an email from 'orders@bookmyshow.com'.
    Extracts the movie, triggers the agent, and persists it to history.
    """
    saved = await gmail_watcher.simulate_incoming_ticket(payload.movie_name)
    return {
        "status": "success",
        "message": f"Simulated BookMyShow ticket for '{payload.movie_name}' processed and saved.",
        "record": saved
    }


@router.post(
    "/webhook/pubsub",
    summary="GCP Pub/Sub Push Webhook",
    dependencies=[Depends(verify_webhook_token)]
)
async def pubsub_webhook(payload: PubSubPushPayload) -> Dict[str, Any]:
    """
    Dedicated endpoint for Google Cloud Pub/Sub push subscriptions.
    Awaits and processes the event, saving the result to SQLite.
    """
    if not payload.message.data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing 'data' in Pub/Sub message"
        )

    movie = parse_pubsub_data(payload.message.data)
    logger.info("Pub/Sub webhook received movie: %s", movie)

    pipeline_result = await run_pipeline(movie)
    saved = save_recommendation(movie, pipeline_result, source="pubsub")

    return {
        "status": "acknowledged",
        "movie_watched": movie,
        "record_id": saved["id"],
        "results": pipeline_result
    }


@router.post(
    "/webhook",
    summary="Unified Webhook Endpoint",
    dependencies=[Depends(verify_webhook_token)]
)
async def unified_webhook(request: Request) -> Dict[str, Any]:
    """
    Flexible webhook endpoint that auto-detects Pub/Sub or direct JSON,
    executing the workflow and saving the outcome.
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON payload"
        )

    if isinstance(body, dict) and "message" in body and isinstance(body["message"], dict):
        b64_data = body["message"].get("data")
        if not b64_data:
            raise HTTPException(status_code=400, detail="Missing Pub/Sub message data")
        movie = parse_pubsub_data(b64_data)
        source = "pubsub"
    elif isinstance(body, dict):
        movie = body.get("movie_watched") or body.get("movie") or body.get("title")
        if not movie:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="JSON payload must specify 'movie_watched' or 'movie'"
            )
        movie = str(movie).strip()
        source = "webhook"
    else:
        raise HTTPException(status_code=400, detail="Unsupported payload structure")

    logger.info("Executing pipeline for webhook movie: %s", movie)
    pipeline_result = await run_pipeline(movie)
    saved = save_recommendation(movie, pipeline_result, source=source)

    return {
        "status": "success",
        "movie_watched": movie,
        "record_id": saved["id"],
        "pipeline_result": pipeline_result
    }
