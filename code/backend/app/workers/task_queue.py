# from celery import Celery # Removed due to dependency issues
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure Celery
# celery_app = Celery( # Removed due to dependency issues
#     "quantumnest_workers",
#     broker=os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0"),
#     backend=os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
# )

# Configure Celery settings
# celery_app.conf.update( # Removed due to dependency issues
#     task_serializer="json",
#     accept_content=["json"],
#     result_serializer="json",
#     timezone="UTC",
#     enable_utc=True,
#     task_track_started=True,
#     task_time_limit=3600,  # 1 hour timeout for tasks
#     worker_prefetch_multiplier=1,  # Prevent worker from prefetching too many tasks
#     task_acks_late=True,  # Acknowledge tasks after they are executed
# )

# Mock celery_app to satisfy imports
class MockCeleryApp:
    def task(self, **kwargs):
        def decorator(func):
            return func
        return decorator

celery_app = MockCeleryApp()
