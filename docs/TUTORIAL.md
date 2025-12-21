# 使用教程

## 目录
1. [GUI模式使用教程](#gui模式)
2. [API模式使用教程](#api模式)
3. [命令行模式使用教程](#命令行模式)
4. [导出功能教程](#导出功能)
5. [高级功能](#高级功能)

---

## GUI模式

### 快速开始

#### 1. 启动应用

```bash
python main.py
```

#### 2. 配置LLM接口

在"LLM Model settings"标签页：

1. **选择接口类型**：OpenAI / DeepSeek / Gemini / Azure等
2. **填写API Key**：你的API密钥
3. **设置Base URL**（可选）：如使用本地Ollama，填写 `http://localhost:11434/v1`
4. **选择模型**：如 `gpt-4o-mini`、`deepseek-chat`
5. **调整参数**：
   - Temperature: 0.7（推荐）
   - Max Tokens: 8192（根据模型调整）
6. **点击"测试LLM连接"**：确认配置正确

#### 3. 配置Embedding接口

在"Embedding settings"标签页：

1. 配置Embedding模型（通常与LLM使用相同服务）
2. 设置检索数量（k=4推荐）
3. 测试连接

#### 4. 设置小说参数

在主界面右侧：

```
主题：一个程序员穿越到魔法世界的冒险故事
类型：玄幻
章节数：50
每章字数：3000
保存路径：D:/my_novels/magic_coder

【可选】高级参数：
内容指导：轻松幽默，带有科技与魔法碰撞的元素
核心人物：主角-李明（程序员），导师-梅林（大法师）
关键道具：魔法笔记本，时空之门
场景：现代都市，魔法学院，暗黑森林
时间约束：三个月内完成试炼
```

#### 5. 生成流程

**Step 1: 生成设定**
```
点击"Step1. 生成设定"按钮
等待5-10分钟
生成文件：
  - Novel_architecture.txt（小说架构）
  - character_state.txt（角色状态）
```

**Step 2: 生成目录**
```
点击"Step2. 生成目录"按钮
等待3-5分钟
生成文件：
  - Novel_directory.txt（完整章节目录）
```

**Step 3: 生成章节**
```
1. 设置"章节号"：1
2. （可选）填写"本章指导"：描述本章特殊要求
3. 点击"Step3. 生成章节"
4. 等待生成完成
5. 生成文件：
   - outline_1.txt（章节大纲）
   - chapter_1.txt（章节正文）
```

**Step 4: 定稿章节**
```
点击"Step4. 定稿当前章节"
系统将：
  - 更新global_summary.txt
  - 更新character_state.txt
  - 更新向量库（供后续章节使用）
```

**重复Step 3-4**，直到完成所有章节！

#### 6. 查看和编辑

- 在左侧文本框查看生成内容
- 在各标签页查看/编辑：
  - Novel Architecture：小说架构
  - Chapter Blueprint：章节目录
  - Chapters：章节列表
  - Character State：角色状态
  - Global Summary：全局摘要

---

## API模式

### 启动API服务器

```bash
# 方式1：直接运行
python api_server.py

# 方式2：使用uvicorn（生产环境推荐）
uvicorn api_server:app --host 0.0.0.0 --port 8000
```

### Python客户端示例

#### 完整生成流程

```python
import requests
import time
import json

API_BASE = "http://localhost:8000"

# 配置
config = {
    "novel_config": {
        "topic": "太空探险故事",
        "genre": "科幻",
        "num_chapters": 30,
        "word_number": 3000,
        "content_guidance": "硬科幻，注重科学细节"
    },
    "llm_config": {
        "interface_format": "OpenAI",
        "api_key": "your-api-key",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o-mini",
        "temperature": 0.7,
        "max_tokens": 8192,
        "timeout": 600
    },
    "embedding_config": {
        "interface_format": "OpenAI",
        "api_key": "your-api-key",
        "model_name": "text-embedding-ada-002",
        "retrieval_k": 4
    },
    "output_dir": "./space_adventure"
}

def wait_for_task(task_id):
    """等待任务完成"""
    while True:
        response = requests.get(f"{API_BASE}/api/v1/task/{task_id}")
        task = response.json()

        print(f"状态: {task['status']}, 进度: {task['progress']}%, 消息: {task['message']}")

        if task['status'] == 'completed':
            return task['result']
        elif task['status'] == 'failed':
            raise Exception(f"任务失败: {task['error']}")

        time.sleep(5)

# Step 1: 生成架构
print("Step 1: 生成小说架构...")
response = requests.post(f"{API_BASE}/api/v1/novel/architecture", json=config)
task_id = response.json()["task_id"]
result = wait_for_task(task_id)
print(f"架构文件: {result['architecture_file']}")

# Step 2: 生成目录
print("\nStep 2: 生成章节目录...")
response = requests.post(f"{API_BASE}/api/v1/novel/blueprint", json=config)
task_id = response.json()["task_id"]
wait_for_task(task_id)

# Step 3 & 4: 生成并定稿章节
for chapter_num in range(1, 31):
    print(f"\n生成第{chapter_num}章...")

    # 生成章节
    response = requests.post(f"{API_BASE}/api/v1/novel/chapter", json={
        "project_id": "./space_adventure",
        "chapter_number": chapter_num
    })
    task_id = response.json()["task_id"]
    wait_for_task(task_id)

    # 定稿章节
    response = requests.post(f"{API_BASE}/api/v1/novel/finalize", json={
        "project_id": "./space_adventure",
        "chapter_number": chapter_num
    })
    task_id = response.json()["task_id"]
    wait_for_task(task_id)

print("\n所有章节生成完成！")

# 导出为EPUB
print("\n导出为EPUB...")
response = requests.post(f"{API_BASE}/api/v1/novel/export", json={
    "project_id": "./space_adventure",
    "format": "epub",
    "title": "太空探险记",
    "author": "AI作者"
})
print(f"导出结果: {response.json()}")
```

---

## 命令行模式

### 使用Python脚本

创建 `generate_novel.py`:

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""命令行小说生成脚本"""

import argparse
from novel_generator import (
    Novel_architecture_generate,
    Chapter_blueprint_generate,
    generate_chapter_draft,
    finalize_chapter
)
from llm_adapters import create_llm_adapter
from embedding_adapters import create_embedding_adapter
from logger_config import setup_logger

def main():
    parser = argparse.ArgumentParser(description='AI小说生成器')
    parser.add_argument('--topic', required=True, help='小说主题')
    parser.add_argument('--genre', required=True, help='小说类型')
    parser.add_argument('--chapters', type=int, default=10, help='章节数')
    parser.add_argument('--words', type=int, default=3000, help='每章字数')
    parser.add_argument('--output', required=True, help='输出目录')
    parser.add_argument('--api-key', required=True, help='API密钥')
    parser.add_argument('--model', default='gpt-4o-mini', help='模型名称')

    args = parser.parse_args()

    # 设置日志
    logger = setup_logger()

    # 创建LLM适配器
    llm = create_llm_adapter(
        interface_format="OpenAI",
        api_key=args.api_key,
        model_name=args.model
    )

    # Step 1: 生成架构
    logger.info("Step 1: 生成小说架构...")
    Novel_architecture_generate(
        llm=llm,
        topic=args.topic,
        genre=args.genre,
        num_chapters=args.chapters,
        word_number=args.words,
        filepath=args.output
    )

    # Step 2: 生成目录
    logger.info("Step 2: 生成章节目录...")
    Chapter_blueprint_generate(
        llm=llm,
        filepath=args.output,
        num_chapters=args.chapters
    )

    # Step 3 & 4: 生成章节
    for i in range(1, args.chapters + 1):
        logger.info(f"生成第{i}章...")
        generate_chapter_draft(
            llm=llm,
            chapter_number=i,
            filepath=args.output
        )
        finalize_chapter(
            llm=llm,
            chapter_number=i,
            filepath=args.output
        )

    logger.info("完成！")

if __name__ == "__main__":
    main()
```

使用：

```bash
python generate_novel.py \
    --topic "末日求生" \
    --genre "科幻" \
    --chapters 20 \
    --words 3000 \
    --output ./my_novel \
    --api-key sk-xxx \
    --model gpt-4o-mini
```

---

## 导出功能

### GUI导出

待UI集成导出功能后更新...

### 命令行导出

```python
from export_manager import export_novel

# 导出为TXT
export_novel(
    novel_dir="./my_novel",
    output_file="./my_novel.txt",
    format_type="txt",
    title="我的小说",
    author="AI作者"
)

# 导出为EPUB
export_novel(
    novel_dir="./my_novel",
    output_file="./my_novel.epub",
    format_type="epub",
    title="我的小说",
    author="AI作者"
)

# 导出为PDF
export_novel(
    novel_dir="./my_novel",
    output_file="./my_novel.pdf",
    format_type="pdf",
    title="我的小说",
    author="AI作者"
)

# 导出为DOCX
export_novel(
    novel_dir="./my_novel",
    output_file="./my_novel.docx",
    format_type="docx",
    title="我的小说",
    author="AI作者"
)
```

### API导出

```bash
curl -X POST http://localhost:8000/api/v1/novel/export \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "./my_novel",
    "format": "epub",
    "title": "我的小说",
    "author": "AI作者"
  }'
```

---

## 高级功能

### 1. 使用知识库

导入参考资料：

```python
from novel_generator.knowledge import import_knowledge_to_vectorstore

# 导入知识文件
import_knowledge_to_vectorstore(
    knowledge_file="./reference.txt",
    embedding_llm=embedding_adapter,
    filepath="./my_novel",
    mode="append"  # 或 "new" 创建新库
)
```

在GUI中：
1. 点击"导入知识库"
2. 选择知识文件
3. 系统自动处理并添加到向量库

### 2. 一致性检查

```python
from consistency_checker import consistency_check

# 检查章节一致性
issues = consistency_check(
    llm=llm,
    chapter_number=5,
    filepath="./my_novel"
)

if issues:
    print(f"发现{len(issues)}个问题：")
    for issue in issues:
        print(f"- {issue}")
```

### 3. 角色库管理

在GUI中：
1. 打开"角色库"窗口
2. 导入角色模板
3. 使用AI辅助提取角色属性
4. 管理角色分类

### 4. 自定义提示词

编辑 `prompt_definitions.py`：

```python
# 自定义章节生成提示词
my_custom_prompt = """
根据以下信息生成章节：

主题：{topic}
类型：{genre}
章节号：{chapter_num}

【你的自定义指导】
...
"""
```

### 5. 批量生成

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

def generate_chapter(chapter_num):
    """生成单个章节"""
    generate_chapter_draft(llm, chapter_num, filepath)
    finalize_chapter(llm, chapter_num, filepath)

# 并发生成多个章节（注意API限流）
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(generate_chapter, i)
        for i in range(1, 11)
    ]
    for future in futures:
        future.result()
```

---

## 最佳实践

### 1. 主题设计

✅ **好的主题**：
```
一个失业程序员意外获得修改现实代码的能力，
在虚拟与现实交织的世界中寻找真相的故事
```

❌ **不好的主题**：
```
写一个小说
```

### 2. 内容指导

具体明确：
```
1. 主角性格：谨慎理性，但内心渴望冒险
2. 故事基调：前期轻松搞笑，中期悬疑紧张，后期热血战斗
3. 写作风格：第一人称叙述，注重心理描写
4. 禁止内容：避免过度暴力，不要狗血三角恋
```

### 3. 章节规划

- 每章3000-5000字为宜
- 总章节数建议20-100章
- 每5-10章设置一个小高潮

### 4. 向量库使用

- 每10章清理一次无关内容
- 重要情节手动添加到知识库
- 检索数量（k）建议4-8

### 5. 错误处理

- 生成失败时检查API额度
- 网络超时时增加timeout参数
- 定期备份生成的文件

---

## 故障排查

### 问题1：生成的内容质量不高

**解决方案**：
- 提高temperature（0.7-0.9）
- 使用更强大的模型（如GPT-4）
- 提供更详细的内容指导
- 增加参考知识库

### 问题2：生成速度慢

**解决方案**：
- 使用更快的模型
- 减少max_tokens
- 使用本地Ollama服务
- 开启并发生成

### 问题3：内容前后矛盾

**解决方案**：
- 定期运行一致性检查
- 手动审核并修正架构文件
- 增加向量库检索数量
- 维护详细的角色状态表

### 问题4：导出失败

**解决方案**：
```bash
# 安装所需的库
pip install ebooklib reportlab python-docx

# Linux下PDF导出需要中文字体
sudo apt-get install fonts-wqy-microhei
```

---

## 更多资源

- [API文档](./API_DOCUMENTATION.md)
- [开发文档](./DEVELOPMENT.md)
- [项目主页](https://github.com/YILING0013/AI_NovelGenerator)
- [问题反馈](https://github.com/YILING0013/AI_NovelGenerator/issues)
