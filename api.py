import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from supabase import Client, create_client

from features import extract_features, fingerprint_similarity, generate_fingerprint

load_dotenv()

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("terraceid")

supabase: Client = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))

app = FastAPI(title="TerraceID API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/identify")
async def identify_chant(audio: UploadFile = File(...)):
    audio_bytes = await audio.read()
    if not audio_bytes:
        raise HTTPException(status_code=400, detail="Empty audio file")

    log.info("Received %d bytes, content-type=%s", len(audio_bytes), audio.content_type)

    try:
        features = extract_features(audio_bytes)
    except Exception as e:
        log.exception("Feature extraction failed")
        raise HTTPException(status_code=422, detail=f"Could not process audio: {e}")

    # Step 1: pgvector — fast coarse filter, get top 50 candidates
    candidates = supabase.rpc(
        "match_chant",
        {
            "query_embedding": features.tolist(),
            "match_threshold": 0.0,
            "match_count":     50,
        },
    ).execute()

    if not candidates.data:
        return {"match": None, "message": "No match found — try a longer or clearer recording"}

    # Step 2: chromaprint — precise re-ranking of those 50
    try:
        query_fp = generate_fingerprint(audio_bytes)
    except Exception as e:
        log.warning("Fingerprint generation failed, falling back to vector match: %s", e)
        query_fp = None

    ids = [m["id"] for m in candidates.data]
    fp_rows = (
        supabase.table("chants")
        .select("id, team, chant_name, audio_url, fingerprint")
        .in_("id", ids)
        .execute()
    )

    best = None
    best_score = -1.0

    for row in fp_rows.data:
        if query_fp and row.get("fingerprint"):
            score = fingerprint_similarity(query_fp, row["fingerprint"])
        else:
            # fall back to vector similarity position for rows without a fingerprint yet
            score = next(
                (1 - i * 0.01 for i, c in enumerate(candidates.data) if c["id"] == row["id"]),
                0.0,
            )

        if score > best_score:
            best_score = score
            best = row

    if best is None or best_score < 0.1:
        return {"match": None, "message": "No match found — try a longer or clearer recording"}

    return {
        "match": {
            "team":       best["team"],
            "chant_name": best["chant_name"],
            "audio_url":  best["audio_url"],
            "confidence": round(best_score * 100, 1),
        }
    }


# Serve the web frontend at /
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
