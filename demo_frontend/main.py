import os
from typing import Annotated

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from google.cloud import storage

app = FastAPI(
    title="Tenant Bucket API",
    description="Self-service GCS bucket interface. List, upload, download and delete objects.",
    version="1.0.0",
)

BUCKET_NAME = os.environ["BUCKET_NAME"]

def get_client() -> storage.Client:
    # Picks up GOOGLE_APPLICATION_CREDENTIALS automatically
    return storage.Client()


# ── LIST ──────────────────────────────────────────────────────────────────────

@app.get(
    "/files",
    summary="List all objects in the bucket",
    response_description="A list of object names",
)
def list_files() -> list[dict]:
    client = get_client()
    bucket = client.bucket(BUCKET_NAME)
    blobs = client.list_blobs(bucket)
    return [
        {
            "name": blob.name,
            "size_bytes": blob.size,
            "updated": blob.updated.isoformat() if blob.updated else None,
            "content_type": blob.content_type,
        }
        for blob in blobs
    ]


# ── UPLOAD ────────────────────────────────────────────────────────────────────

@app.post(
    "/files/{filename}",
    summary="Upload a file to the bucket",
    status_code=201,
)
async def upload_file(
    filename: str,
    file: Annotated[UploadFile, File(description="The file to upload")],
) -> dict:
    client = get_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    contents = await file.read()
    blob.upload_from_string(
        contents,
        content_type=file.content_type or "application/octet-stream",
    )
    return {"uploaded": filename, "size_bytes": len(contents)}


# ── DOWNLOAD ──────────────────────────────────────────────────────────────────

@app.get(
    "/files/{filename}",
    summary="Download a file from the bucket",
)
def download_file(filename: str) -> StreamingResponse:
    client = get_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    if not blob.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found")

    def _stream():
        with blob.open("rb") as f:
            while chunk := f.read(1024 * 256):
                yield chunk

    return StreamingResponse(
        _stream(),
        media_type=blob.content_type or "application/octet-stream",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── DELETE ────────────────────────────────────────────────────────────────────

@app.delete(
    "/files/{filename}",
    summary="Delete a file from the bucket",
)
def delete_file(filename: str) -> dict:
    client = get_client()
    bucket = client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    if not blob.exists():
        raise HTTPException(status_code=404, detail=f"{filename} not found")

    blob.delete()
    return {"deleted": filename}


# ── HEALTH ────────────────────────────────────────────────────────────────────

@app.get("/healthz", summary="Health check", include_in_schema=False)
def health() -> dict:
    return {"status": "ok"}