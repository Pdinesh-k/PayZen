import pytest
from playwright.sync_api import sync_playwright

@pytest.fixture(scope="session")
def browser_type_launch_args():
    return {"headless": True}

@pytest.fixture(scope="session")
def browser_context_args():
    return {
        "viewport": {
            "width": 1920,
            "height": 1080,
        },
        "ignore_https_errors": True,
    } 