import json

from aiokafka import AIOKafkaProducer
from loguru import logger

from config import settings


class KafkaEventProducer:
    def __init__(self) -> None:
        self._producer: AIOKafkaProducer | None = None

    async def start(self) -> None:
        if self._producer is not None:
            return
        self._producer = AIOKafkaProducer(
            bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda value: json.dumps(value, ensure_ascii=False).encode("utf-8"),
            key_serializer=lambda value: str(value).encode("utf-8") if value is not None else None,
            acks="all",
            enable_idempotence=True,
        )
        await self._producer.start()
        logger.info("[KAFKA-PRODUCER] started bootstrap_servers={}", settings.KAFKA_BOOTSTRAP_SERVERS)

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None
            logger.info("[KAFKA-PRODUCER] stopped")

    async def send(self, *, topic: str, key: str, value: dict) -> None:
        if self._producer is None:
            await self.start()
        assert self._producer is not None
        metadata = await self._producer.send_and_wait(topic=topic, key=key, value=value)
        logger.debug(
            "[KAFKA-PRODUCER] sent topic={} partition={} offset={} key={}",
            metadata.topic,
            metadata.partition,
            metadata.offset,
            key,
        )
