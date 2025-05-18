import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db
from app import models
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import json

# Test data
TEST_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "testpass123"
}

TEST_BILL = {
    "biller_name": "Test Electric",
    "bill_type": "Electricity",
    "amount": 100.00,
    "due_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
    "reminder_frequency": 3
}

@pytest.fixture(scope="function")
def test_db():
    # Create a new engine and session for each test
    SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # Create all tables
    models.Base.metadata.create_all(bind=engine)
    
    def override_get_db():
        try:
            db = TestingSessionLocal()
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    
    db = TestingSessionLocal()
    yield db
    db.close()
    
    # Drop tables after test
    models.Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_client():
    return TestClient(app)

@pytest.fixture
def auth_headers(test_db, test_client):
    # Register user
    response = test_client.post("/auth/register", json=TEST_USER)
    assert response.status_code == 200
    
    # Login user
    response = test_client.post("/auth/login", data={
        "username": TEST_USER["email"],
        "password": TEST_USER["password"]
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestAuth:
    def test_register(self, test_db, test_client):
        response = test_client.post("/auth/register", json=TEST_USER)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["email"] == TEST_USER["email"]

    def test_login(self, test_db, test_client):
        # Register first
        test_client.post("/auth/register", json=TEST_USER)
        
        # Try login
        response = test_client.post("/auth/login", data={
            "username": TEST_USER["email"],
            "password": TEST_USER["password"]
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_invalid_login(self, test_db, test_client):
        response = test_client.post("/auth/login", data={
            "username": "wrong",
            "password": "wrong"
        })
        assert response.status_code == 401

class TestBills:
    def test_create_bill(self, test_db, test_client, auth_headers):
        response = test_client.post("/bills/", json=TEST_BILL, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["biller_name"] == TEST_BILL["biller_name"]
        assert data["amount"] == TEST_BILL["amount"]

    def test_get_bills(self, test_db, test_client, auth_headers):
        # Create a bill first
        test_client.post("/bills/", json=TEST_BILL, headers=auth_headers)
        
        # Get all bills
        response = test_client.get("/bills/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        assert data[0]["biller_name"] == TEST_BILL["biller_name"]

class TestRewards:
    def test_get_points(self, test_db, test_client, auth_headers):
        response = test_client.get("/rewards/points", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "points" in data

    def test_redeem_reward(self, test_db, test_client, auth_headers):
        # Create a reward first
        reward = models.Reward(
            name="Test Reward",
            description="Test Description",
            points_required=500,
            is_active=True
        )
        test_db.add(reward)
        test_db.commit()
        test_db.refresh(reward)

        # Add points first
        test_client.post("/rewards/add-points", json={"points": 1000}, headers=auth_headers)
        
        # Try to redeem
        response = test_client.post("/rewards/redeem", json={
            "reward_id": reward.id,
            "points_cost": reward.points_required
        }, headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "success" in data
        assert data["success"] == True
        assert "remaining_points" in data
        assert data["remaining_points"] == 500  # 1000 - 500

class TestEmailNotifications:
    def test_bill_reminder(self, test_db, test_client, auth_headers):
        # Add a bill with near due date
        soon_bill = TEST_BILL.copy()
        soon_bill["due_date"] = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        test_client.post("/bills/", json=soon_bill, headers=auth_headers)
        
        # Trigger reminder check
        response = test_client.get("/test-reminder", headers=auth_headers)
        assert response.status_code == 200

    def test_payment_confirmation(self, test_db, test_client, auth_headers):
        # Add and pay a bill
        response = test_client.post("/bills/", json=TEST_BILL, headers=auth_headers)
        bill_id = response.json()["id"]
        response = test_client.post(f"/bills/{bill_id}/pay", headers=auth_headers)
        assert response.status_code == 200

class TestAdminDashboard:
    @pytest.mark.skip(reason="Admin dashboard not implemented yet")
    def test_admin_access(self, test_db, test_client, auth_headers):
        response = test_client.get("/admin", headers=auth_headers)
        assert response.status_code in [200, 403]  # 403 if not admin

    @pytest.mark.skip(reason="Admin dashboard not implemented yet")
    def test_view_statistics(self, test_db, test_client, auth_headers):
        response = test_client.get("/admin/stats", headers=auth_headers)
        assert response.status_code in [200, 403]  # 403 if not admin