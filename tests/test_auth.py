# tests/test_auth.py
# -*- coding: utf-8 -*-
"""
认证相关测试
"""

import pytest
from fastapi import status


@pytest.mark.auth
class TestUserRegistration:
    """用户注册测试"""

    def test_register_success(self, client):
        """测试成功注册"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["username"] == "newuser"
        assert data["user"]["email"] == "new@example.com"

    def test_register_duplicate_username(self, client, test_user):
        """测试重复用户名"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": test_user.username,
                "email": "different@example.com",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "用户名已被注册" in response.json()["detail"]

    def test_register_duplicate_email(self, client, test_user):
        """测试重复邮箱"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "differentuser",
                "email": test_user.email,
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "邮箱已被注册" in response.json()["detail"]

    def test_register_invalid_email(self, client):
        """测试无效邮箱"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "invalid-email",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_register_short_password(self, client):
        """测试密码太短"""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "username": "newuser",
                "email": "new@example.com",
                "password": "123"
            }
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.auth
class TestUserLogin:
    """用户登录测试"""

    def test_login_success(self, client, test_user):
        """测试成功登录"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "user" in data
        assert "token" in data
        assert data["user"]["username"] == "testuser"

    def test_login_wrong_password(self, client, test_user):
        """测试错误密码"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "wrongpassword"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "用户名或密码错误" in response.json()["detail"]

    def test_login_nonexistent_user(self, client):
        """测试不存在的用户"""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "nonexistent",
                "password": "password123"
            }
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.auth
class TestUserProfile:
    """用户信息测试"""

    def test_get_current_user(self, client, auth_headers):
        """测试获取当前用户信息"""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["username"] == "testuser"
        assert data["email"] == "test@example.com"

    def test_get_current_user_unauthorized(self, client):
        """测试未认证访问"""
        response = client.get("/api/v1/auth/me")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_update_user_info(self, client, auth_headers):
        """测试更新用户信息"""
        response = client.put(
            "/api/v1/auth/me",
            headers=auth_headers,
            json={
                "email": "updated@example.com"
            }
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["email"] == "updated@example.com"

    def test_change_password(self, client, auth_headers):
        """测试修改密码"""
        response = client.post(
            "/api/v1/auth/password",
            headers=auth_headers,
            json={
                "old_password": "password123",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == status.HTTP_200_OK

        # 验证新密码可以登录
        login_response = client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "newpassword123"
            }
        )
        assert login_response.status_code == status.HTTP_200_OK

    def test_change_password_wrong_old(self, client, auth_headers):
        """测试旧密码错误"""
        response = client.post(
            "/api/v1/auth/password",
            headers=auth_headers,
            json={
                "old_password": "wrongpassword",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
