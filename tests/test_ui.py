import pytest
from playwright.sync_api import Page, expect
from datetime import datetime, timedelta

# Test data
TEST_USER = {
    "username": "uitestuser",
    "email": "uitest@example.com",
    "password": "testpass123"
}

TEST_BILL = {
    "biller_name": "UI Test Electric",
    "bill_type": "Electricity",
    "amount": "100.00",
    "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
    "reminder_frequency": "3"
}

@pytest.fixture(autouse=True)
def setup_teardown(page: Page):
    # Setup: Navigate to home page
    page.goto("http://localhost:8000")
    yield
    # Teardown: Clear cookies
    page.context.clear_cookies()

@pytest.fixture
def auth_page(page: Page, base_url):
    # Register a new user
    page.goto(f"{base_url}/register")
    page.fill("input[name='email']", TEST_USER["email"])
    page.fill("input[name='username']", TEST_USER["username"])
    page.fill("input[name='password']", TEST_USER["password"])
    page.fill("input[name='confirm_password']", TEST_USER["password"])
    
    with page.expect_response("**/register") as response_info:
        page.click("button[type='submit']")
    response = response_info.value
    
    # Login
    page.goto(f"{base_url}/login")
    page.fill("input[name='username']", TEST_USER["username"])
    page.fill("input[name='password']", TEST_USER["password"])
    page.click("button[type='submit']")
    
    return page

class TestAuthentication:
    def test_registration_flow(self, page: Page, base_url):
        # Go to register page
        page.goto(f"{base_url}/register")
        
        # Fill registration form
        page.fill("input[name='email']", TEST_USER["email"])
        page.fill("input[name='username']", TEST_USER["username"])
        page.fill("input[name='password']", TEST_USER["password"])
        page.fill("input[name='confirm_password']", TEST_USER["password"])
        
        # Submit form and wait for navigation
        with page.expect_response("**/register") as response_info:
            page.click("button[type='submit']")
        response = response_info.value
        
        # Verify success message
        expect(page.locator(".alert-success")).to_be_visible()
        expect(page.locator("text=Registration successful! Please login to continue.")).to_be_visible()
    
    def test_login_flow(self, page: Page, base_url):
        # Register first
        self.test_registration_flow(page, base_url)
        
        # Go to login page
        page.goto(f"{base_url}/login")
        
        # Fill login form
        page.fill("input[name='username']", TEST_USER["username"])
        page.fill("input[name='password']", TEST_USER["password"])
        
        # Submit form
        page.click("button[type='submit']")
        
        # Verify successful login
        expect(page.locator("text=Dashboard")).to_be_visible()

class TestBillManagement:
    def test_add_bill(self, auth_page: Page):
        auth_page.click("text=Add Bill")
        
        # Fill bill form
        auth_page.fill("input[name='biller_name']", "Test Biller")
        auth_page.fill("input[name='bill_type']", "Utility")
        auth_page.fill("input[name='amount']", "100")
        auth_page.fill("input[name='due_date']", "2024-12-31")
        auth_page.fill("input[name='reminder_frequency']", "7")
        
        # Submit form
        auth_page.click("button[type='submit']")
        
        # Verify bill added
        expect(auth_page.locator("text=Bill added successfully")).to_be_visible()
    
    def test_pay_bill(self, auth_page: Page):
        # Add a bill first
        self.test_add_bill(auth_page)
        
        # Click pay button
        auth_page.click("text=Pay")
        
        # Verify payment success
        expect(auth_page.locator("text=Payment successful")).to_be_visible()

class TestRewardsSystem:
    def test_view_rewards(self, auth_page: Page):
        auth_page.click("text=Rewards")
        expect(auth_page.locator("text=Available Rewards")).to_be_visible()
    
    def test_claim_reward(self, auth_page: Page):
        auth_page.click("text=Rewards")
        auth_page.click("text=Claim")
        expect(auth_page.locator("text=Reward claimed successfully")).to_be_visible()

class TestResponsiveDesign:
    @pytest.mark.parametrize("viewport", [
        {"width": 1920, "height": 1080},
        {"width": 768, "height": 1024},
        {"width": 375, "height": 812}
    ])
    def test_responsive_layout(self, auth_page: Page, viewport):
        auth_page.set_viewport_size(viewport)
        expect(auth_page.locator("nav")).to_be_visible()
        expect(auth_page.locator("footer")).to_be_visible()

class TestAccessibility:
    def test_keyboard_navigation(self, auth_page: Page):
        # Test tab navigation
        auth_page.keyboard.press("Tab")
        auth_page.keyboard.press("Enter")
        expect(auth_page.locator(":focus")).to_be_visible()
    
    def test_aria_labels(self, page: Page, base_url):
        page.goto(base_url)
        # Check important aria labels exist
        count = page.locator("[aria-label]").count()
        assert count > 0, "No aria labels found"

def test_homepage(page: Page, base_url):
    page.goto(base_url)
    expect(page.locator("text=Welcome to PayZen")).to_be_visible()

def test_register_flow(page: Page, base_url):
    page.goto(f"{base_url}/register")
    page.fill("input[name=email]", "test@example.com")
    page.fill("input[name=username]", "testuser")
    page.fill("input[name=password]", "testpass123")
    page.fill("input[name=confirm_password]", "testpass123")
    page.click("button[type=submit]")
    expect(page.locator(".alert-success")).to_be_visible()

def test_login_flow(page: Page, base_url):
    # Register first
    test_register_flow(page, base_url)
    
    # Login
    page.goto(f"{base_url}/login")
    page.fill("input[name=username]", "testuser")
    page.fill("input[name=password]", "testpass123")
    page.click("button[type=submit]")
    expect(page.locator("text=Dashboard")).to_be_visible()

def test_add_bill_flow(page: Page, base_url):
    # Login first
    test_login_flow(page, base_url)
    
    page.click("text=Add Bill")
    page.fill("input[name=biller_name]", "Test Biller")
    page.fill("input[name=bill_type]", "Utility")
    page.fill("input[name=amount]", "100")
    page.fill("input[name=due_date]", "2024-12-31")
    page.fill("input[name=reminder_frequency]", "7")
    page.click("button[type=submit]")
    expect(page.locator("text=Bill added successfully")).to_be_visible()

def test_redeem_reward_flow(page: Page, base_url):
    # Login first
    test_login_flow(page, base_url)
    
    page.click("text=Rewards")
    expect(page.locator("text=Available Rewards")).to_be_visible()
    page.click("text=Claim")
    expect(page.locator("text=Reward claimed successfully")).to_be_visible() 