from celery import Celery
from config import settings

app = Celery(
    'project',
    broker=settings.get_redis_url(),
    backend=settings.get_redis_url(),
    include=['services.tasks_service']
)

# конфиг для временной зоны
app.conf.timezone = 'Europe/Moscow'
app.conf.enable_utc = True

# дополнительные настройки для надежности
app.conf.broker_connection_retry_on_startup = True
app.conf.task_serializer = 'json'
app.conf.result_serializer = 'json'
app.conf.accept_content = ['json']

# настройки повторных попыток
app.conf.task_default_retry_delay = 300
app.conf.task_max_retries = 3
app.conf.task_acks_late = True
app.conf.worker_prefetch_multiplier = 1