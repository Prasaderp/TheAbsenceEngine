from arq.connections import RedisSettings
from app.config import settings
from worker.tasks import run_analysis


class WorkerSettings:
    redis_settings = RedisSettings.from_dsn(settings.redis_url)
    max_jobs = 10
    job_timeout = 300
    max_tries = 3
    keep_result = 3600
    functions = [run_analysis]
