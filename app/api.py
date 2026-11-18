import asyncio
import hashlib
import json
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

from fastapi import Depends, FastAPI, Header, UploadFile, status
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

from app import database, messaging
from app.auth import TokenValidator
from app.object_store import create_object_store
from app.settings import Settings

settings = Settings.from_env()
object_store = create_object_store(settings)
token_validator = TokenValidator(settings.auth_tenant_id, settings.auth_client_id, settings.auth_api_audience)

CHAT_REPLY = (
    "This reply is streamed one token at a time through the cluster's routing. "
    "If the words appear one by one, nothing between the browser and the api buffers the stream."
)
CHAT_TOKEN_DELAY_SECONDS = 0.15


@asynccontextmanager
async def lifespan(app: FastAPI):
    database.ensure_schema(settings.database_url)
    messaging.declare_queue(settings.rabbitmq_url)
    yield


app = FastAPI(title="demo-app api", lifespan=lifespan)


def require_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    return token_validator.validate(authorization)


User = Annotated[dict, Depends(require_user)]


@app.get("/healthz")
def healthz() -> dict:
    # A fingerprint shows that the secret arrived without exposing it.
    fingerprint = hashlib.sha256(settings.demo_api_key.encode()).hexdigest()[:12]
    return {"status": "ok", "demoApiKeySha256": fingerprint}


@app.get("/config.json")
def config() -> dict:
    return {
        "tenantId": settings.auth_tenant_id,
        "clientId": settings.auth_client_id,
        "apiAudience": settings.auth_api_audience,
    }


@app.post("/upload", status_code=status.HTTP_202_ACCEPTED)
def upload(file: UploadFile, user: User) -> dict:
    filename = Path(file.filename or "upload").name
    object_key = f"{uuid.uuid4()}/{filename}"
    object_store.put(object_key, file.file.read())
    messaging.publish_upload(settings.rabbitmq_url, {"objectKey": object_key, "filename": filename})
    return {"objectKey": object_key}


@app.get("/files")
def files(user: User) -> list[dict]:
    return database.list_files(settings.database_url)


async def chat_events() -> AsyncIterator[str]:
    for token in CHAT_REPLY.split(" "):
        yield f"data: {json.dumps({'token': token + ' '})}\n\n"
        await asyncio.sleep(CHAT_TOKEN_DELAY_SECONDS)
    yield "event: done\ndata: {}\n\n"


@app.get("/chat")
def chat(user: User) -> StreamingResponse:
    return StreamingResponse(
        chat_events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app.mount("/", StaticFiles(directory=Path(__file__).parent / "static", html=True), name="static")
