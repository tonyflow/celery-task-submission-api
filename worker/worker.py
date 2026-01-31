import time
import logging
from celery import Celery

celery_app = Celery("worker", broker="amqp://guest:guest@rabbitmq:5672//", backend="redis://redis:6379/0")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
_logger = logging.getLogger(__name__)


class Worker(object):
    def __init__(self):
        _logger.info("Initializing worker")
        time.sleep(10)
        _logger.info("Initialized worker")

    def __call__(self, x, y):
        _logger.info("Worker doing important work")
        time.sleep(2)
        z = x + y
        _logger.info("Worker done.")
        return z


@celery_app.task
def add(x: int, y: int) -> int:
    worker = Worker()
    return worker(x, y)
