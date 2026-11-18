import hashlib
import logging

from app import database, messaging
from app.object_store import create_object_store
from app.settings import Settings

logger = logging.getLogger("worker")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = Settings.from_env()
    object_store = create_object_store(settings)
    database.ensure_schema(settings.database_url)

    def handle_upload(message: dict) -> None:
        data = object_store.get(message["objectKey"])
        database.insert_file(
            settings.database_url,
            object_key=message["objectKey"],
            filename=message["filename"],
            size_bytes=len(data),
            sha256=hashlib.sha256(data).hexdigest(),
        )
        logger.info("Stored %s (%d bytes)", message["objectKey"], len(data))

    logger.info("Waiting for messages on %s", messaging.UPLOADS_QUEUE)
    messaging.consume_uploads(settings.rabbitmq_url, handle_upload)


if __name__ == "__main__":
    main()
