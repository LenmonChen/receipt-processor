from celery import Celery

celery_app = Celery(
    __name__,
    broker_url="amqp://admin:admin@8.153.104.236:5672//",
    result_backend="redis://:redis@8.153.104.236:6379/0",
    include=["app.tasks.background_task", "app.tasks.split_images","app.db.session","app.utils.attach_process", "app.utils.file_processing"],
    broker_connection_retry_on_startup=True
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='Asia/Shanghai',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5分钟任务超时
    task_soft_time_limit=240,
)


if __name__ == '__main__':
    print("✅ 正在加载该 celery_app 实例", __file__)
    print("📦 当前 broker_url 配置:", celery_app.conf.broker_url)
    print("📦 当前 result_backend 配置:", celery_app.conf.result_backend)

