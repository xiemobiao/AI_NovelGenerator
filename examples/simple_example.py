#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
简单示例：使用API生成一部短篇小说
"""

import requests
import time
import json
from pathlib import Path


def wait_for_task(api_base: str, task_id: str, check_interval: int = 5):
    """
    等待任务完成

    Args:
        api_base: API基础URL
        task_id: 任务ID
        check_interval: 检查间隔（秒）

    Returns:
        任务结果
    """
    print(f"任务ID: {task_id}")

    while True:
        response = requests.get(f"{api_base}/api/v1/task/{task_id}")

        if response.status_code != 200:
            raise Exception(f"查询任务失败: {response.text}")

        task = response.json()

        status_icon = {
            'pending': '⏳',
            'running': '🔄',
            'completed': '✅',
            'failed': '❌'
        }.get(task['status'], '❓')

        print(f"{status_icon} 状态: {task['status']}, "
              f"进度: {task['progress']:.1f}%, "
              f"消息: {task['message']}")

        if task['status'] == 'completed':
            return task.get('result')

        elif task['status'] == 'failed':
            raise Exception(f"任务失败: {task.get('error', '未知错误')}")

        time.sleep(check_interval)


def main():
    """主函数"""

    # API配置
    API_BASE = "http://localhost:8000"

    # 小说配置
    config = {
        "novel_config": {
            "topic": "一个AI学会了做梦，并在梦境中创造了一个虚拟世界",
            "genre": "科幻",
            "num_chapters": 5,
            "word_number": 2000,
            "content_guidance": "哲学思辨，探讨意识与现实的边界",
            "core_characters": "主角：ARIA（AI），科学家：陈博士",
            "key_items": "量子处理器，梦境记录仪",
            "scenes": "实验室，虚拟梦境世界",
            "time_constraints": "7天内完成实验"
        },
        "llm_config": {
            "interface_format": "OpenAI",
            "api_key": "your-api-key-here",  # 替换为你的API密钥
            "base_url": "https://api.openai.com/v1",
            "model_name": "gpt-4o-mini",
            "temperature": 0.8,
            "max_tokens": 8192,
            "timeout": 600
        },
        "embedding_config": {
            "interface_format": "OpenAI",
            "api_key": "your-api-key-here",  # 替换为你的API密钥
            "model_name": "text-embedding-ada-002",
            "retrieval_k": 4
        },
        "output_dir": "./ai_dream_novel",
        "project_name": "AI的梦境"
    }

    print("=" * 60)
    print("🚀 开始生成小说：AI的梦境")
    print("=" * 60)

    try:
        # Step 1: 生成小说架构
        print("\n📝 Step 1: 生成小说架构...")
        response = requests.post(
            f"{API_BASE}/api/v1/novel/architecture",
            json=config
        )

        if response.status_code != 200:
            raise Exception(f"请求失败: {response.text}")

        task_id = response.json()["task_id"]
        result = wait_for_task(API_BASE, task_id)

        print(f"\n✅ 架构生成完成！")
        print(f"   文件: {result.get('architecture_file', 'N/A')}")

        # 注意：以下步骤需要API完整实现后才能运行

        # Step 2: 生成章节目录
        # print("\n📚 Step 2: 生成章节目录...")
        # response = requests.post(f"{API_BASE}/api/v1/novel/blueprint", json=config)
        # task_id = response.json()["task_id"]
        # wait_for_task(API_BASE, task_id)

        # Step 3 & 4: 生成并定稿章节
        # for chapter_num in range(1, config["novel_config"]["num_chapters"] + 1):
        #     print(f"\n✍️  生成第{chapter_num}章...")
        #
        #     # 生成章节
        #     response = requests.post(f"{API_BASE}/api/v1/novel/chapter", json={
        #         "project_id": config["output_dir"],
        #         "chapter_number": chapter_num
        #     })
        #     task_id = response.json()["task_id"]
        #     wait_for_task(API_BASE, task_id)
        #
        #     # 定稿章节
        #     response = requests.post(f"{API_BASE}/api/v1/novel/finalize", json={
        #         "project_id": config["output_dir"],
        #         "chapter_number": chapter_num
        #     })
        #     task_id = response.json()["task_id"]
        #     wait_for_task(API_BASE, task_id)

        # 导出为EPUB
        print("\n📖 导出为EPUB格式...")
        response = requests.post(
            f"{API_BASE}/api/v1/novel/export",
            json={
                "project_id": config["output_dir"],
                "format": "epub",
                "title": "AI的梦境",
                "author": "AI Novel Generator"
            }
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 导出成功: {result['file']}")
        else:
            print(f"⚠️  导出失败: {response.text}")

        print("\n" + "=" * 60)
        print("🎉 所有操作完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    # 检查API服务器是否运行
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if response.status_code == 200:
            print("✅ API服务器运行正常")
            main()
        else:
            print("❌ API服务器响应异常")
    except requests.exceptions.RequestException:
        print("❌ 无法连接到API服务器")
        print("   请先启动API服务器: python api_server.py")
