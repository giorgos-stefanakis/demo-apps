import json
from collections.abc import Callable

import pika

UPLOADS_QUEUE = "uploads"


def _connect(rabbitmq_url: str) -> pika.BlockingConnection:
    return pika.BlockingConnection(pika.URLParameters(rabbitmq_url))


def declare_queue(rabbitmq_url: str) -> None:
    connection = _connect(rabbitmq_url)
    try:
        connection.channel().queue_declare(queue=UPLOADS_QUEUE, durable=True)
    finally:
        connection.close()


def publish_upload(rabbitmq_url: str, message: dict) -> None:
    connection = _connect(rabbitmq_url)
    try:
        connection.channel().basic_publish(
            exchange="",
            routing_key=UPLOADS_QUEUE,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                content_type="application/json", delivery_mode=pika.DeliveryMode.Persistent
            ),
        )
    finally:
        connection.close()


def consume_uploads(rabbitmq_url: str, handle: Callable[[dict], None]) -> None:
    """Calls handle for each message and acknowledges it after handle returns. Blocks forever."""
    connection = _connect(rabbitmq_url)
    channel = connection.channel()
    channel.queue_declare(queue=UPLOADS_QUEUE, durable=True)
    channel.basic_qos(prefetch_count=1)

    def on_message(channel, method, properties, body):
        handle(json.loads(body))
        channel.basic_ack(delivery_tag=method.delivery_tag)

    channel.basic_consume(queue=UPLOADS_QUEUE, on_message_callback=on_message)
    channel.start_consuming()
