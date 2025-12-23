from typing import Any
from dotenv import load_dotenv

load_dotenv()


class MockCeleryApp:

    def task(self, **kwargs) -> Any:

        def decorator(func):
            return func

        return decorator


celery_app = MockCeleryApp()
