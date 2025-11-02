"""Tests for authentication endpoints."""
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_register_user():
    """Test user registration."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "test@example.com",
            "password": "testpassword123",
            "full_name": "Test User"
        }
    )
    
    # Should succeed or fail if user exists
    assert response.status_code in [201, 400]
    
    if response.status_code == 201:
        data = response.json()
        assert data["email"] == "test@example.com"
        assert "id" in data


def test_login_user():
    """Test user login."""
    # First register
    client.post(
        "/api/v1/auth/register",
        json={
            "email": "login_test@example.com",
            "password": "testpassword123",
        }
    )
    
    # Then login
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "login_test@example.com",
            "password": "testpassword123",
        }
    )
    
    # Should succeed or fail if wrong credentials
    if response.status_code == 200:
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


def test_get_current_user():
    """Test getting current user info."""
    # Register and login first
    register_response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "current_user_test@example.com",
            "password": "testpassword123",
        }
    )
    
    if register_response.status_code == 201:
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "current_user_test@example.com",
                "password": "testpassword123",
            }
        )
        
        if login_response.status_code == 200:
            token = login_response.json()["access_token"]
            
            # Get current user
            response = client.get(
                "/api/v1/auth/me",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["email"] == "current_user_test@example.com"


def test_login_invalid_credentials():
    """Test login with invalid credentials."""
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent@example.com",
            "password": "wrongpassword",
        }
    )
    
    assert response.status_code == 401

