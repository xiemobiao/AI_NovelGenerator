# tests/test_api_server.py
# -*- coding: utf-8 -*-
"""
API服务器测试
"""

import pytest
from fastapi.testclient import TestClient
from api_server import app


@pytest.fixture
def client():
    """创建测试客户端"""
    return TestClient(app)


class TestBasicEndpoints:
    """测试基础端点"""

    def test_root(self, client):
        """测试根路径"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "version" in data

    def test_health_check(self, client):
        """测试健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestTaskEndpoints:
    """测试任务相关端点"""

    def test_list_tasks(self, client):
        """测试列出任务"""
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200
        data = response.json()
        assert "total" in data
        assert "tasks" in data

    def test_get_nonexistent_task(self, client):
        """测试获取不存在的任务"""
        response = client.get("/api/v1/task/nonexistent-id")
        assert response.status_code == 404


class TestExportEndpoint:
    """测试导出端点"""

    def test_export_invalid_project(self, client):
        """测试导出不存在的项目"""
        response = client.post(
            "/api/v1/novel/export",
            json={
                "project_id": "/nonexistent/project",
                "format": "txt",
                "title": "测试"
            }
        )
        assert response.status_code == 404
