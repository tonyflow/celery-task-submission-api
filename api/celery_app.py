from celery import Celery


instance = Celery("worker", broker="amqp://guest:guest@rabbitmq:5672//", backend="redis://redis:6379/0")
