from celery import Celery

celery_app = Celery(
    "library",
    broker="redis://localhost:6379/0",
    backend="redis://localhost:6379/0"
)

celery_app.conf.timezone = 'Asia/Tashkent'
celery_app.conf.enable_utc = True
