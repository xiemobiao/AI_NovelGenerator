# 开发文档

## 项目架构

### 目录结构

```
AI_NovelGenerator/
├── main.py                      # GUI入口
├── api_server.py               # API服务器
├── export_manager.py           # 导出管理器
├── logger_config.py            # 日志配置
├── config_manager.py           # 配置管理
├── llm_adapters.py            # LLM适配器
├── embedding_adapters.py      # Embedding适配器
├── prompt_definitions.py      # 提示词定义
├── consistency_checker.py     # 一致性检查
├── chapter_directory_parser.py # 目录解析
├── utils.py                   # 工具函数
├── tooltips.py               # UI提示
│
├── novel_generator/           # 核心生成引擎
│   ├── __init__.py
│   ├── architecture.py       # 架构生成
│   ├── blueprint.py          # 目录生成
│   ├── chapter.py           # 章节生成
│   ├── finalization.py      # 定稿处理
│   ├── knowledge.py         # 知识库管理
│   ├── vectorstore_utils.py # 向量库工具
│   └── common.py            # 通用工具
│
├── ui/                       # 用户界面
│   ├── __init__.py
│   ├── main_window.py       # 主窗口
│   ├── generation_handlers.py # 生成处理器
│   ├── config_tab.py        # 配置标签页
│   ├── main_tab.py          # 主标签页
│   ├── novel_params_tab.py  # 参数标签页
│   ├── setting_tab.py       # 架构标签页
│   ├── directory_tab.py     # 目录标签页
│   ├── chapters_tab.py      # 章节标签页
│   ├── character_tab.py     # 角色标签页
│   ├── summary_tab.py       # 摘要标签页
│   ├── role_library.py      # 角色库
│   ├── context_menu.py      # 右键菜单
│   └── helpers.py           # UI辅助
│
├── tests/                    # 测试套件
│   ├── __init__.py
│   ├── conftest.py          # pytest配置
│   ├── test_export_manager.py
│   ├── test_logger_config.py
│   └── test_api_server.py
│
├── docs/                     # 文档
│   ├── API_DOCUMENTATION.md
│   ├── DEVELOPMENT.md
│   └── TUTORIAL.md
│
├── logs/                     # 日志目录
├── vectorstore/             # 向量库存储
├── requirements.txt         # 依赖列表
├── pytest.ini              # pytest配置
└── README.md               # 项目说明
```

---

## 核心模块说明

### 1. 小说生成流程

#### 架构生成（Step 1）
- **模块**: `novel_generator/architecture.py`
- **功能**: 生成5个阶段的小说架构
  1. 核心种子（故事基础）
  2. 角色动力学（角色发展）
  3. 世界构建（世界观设定）
  4. 情节架构（三幕式结构）
  5. 初始角色状态

#### 目录生成（Step 2）
- **模块**: `novel_generator/blueprint.py`
- **功能**: 生成完整的章节目录
- **特色**: 分块生成，避免prompt过长

#### 章节生成（Step 3）
- **模块**: `novel_generator/chapter.py`
- **功能**: 生成章节草稿
- **上下文管理**:
  - 前N章摘要
  - 向量库检索
  - 角色状态跟踪
  - 用户指导整合

#### 定稿处理（Step 4）
- **模块**: `novel_generator/finalization.py`
- **功能**: 更新全局状态
  - 全局摘要
  - 角色状态表
  - 向量库

---

### 2. LLM适配器系统

**支持的LLM接口**:

```python
# OpenAI兼容
from llm_adapters import OpenAIAdapter
llm = OpenAIAdapter(
    api_key="sk-xxx",
    base_url="https://api.openai.com/v1",
    model_name="gpt-4o-mini",
    temperature=0.7
)

# DeepSeek
from llm_adapters import DeepSeekAdapter
llm = DeepSeekAdapter(
    api_key="sk-xxx",
    model_name="deepseek-chat"
)

# Google Gemini
from llm_adapters import GeminiAdapter
llm = GeminiAdapter(
    api_key="xxx",
    model_name="gemini-1.5-pro"
)

# Azure OpenAI
from llm_adapters import AzureOpenAIAdapter
llm = AzureOpenAIAdapter(
    api_key="xxx",
    azure_endpoint="https://xxx.openai.azure.com/",
    api_version="2024-02-15-preview",
    model_name="gpt-4"
)
```

**扩展新的LLM适配器**:

```python
from llm_adapters import BaseLLMAdapter

class MyCustomAdapter(BaseLLMAdapter):
    def __init__(self, api_key, **kwargs):
        super().__init__()
        # 初始化你的客户端
        self.client = MyLLMClient(api_key)

    def invoke(self, prompt: str) -> str:
        # 实现调用逻辑
        response = self.client.generate(prompt)
        return response.text
```

---

### 3. 向量库系统

**技术栈**: LangChain + Chroma + Sentence Transformers

**基本用法**:

```python
from novel_generator.vectorstore_utils import (
    initialize_vectorstore,
    update_vectorstore,
    retrieve_context
)

# 初始化向量库
vectorstore = initialize_vectorstore(
    embedding_llm=embedding_adapter,
    filepath="./my_novel"
)

# 更新向量库
update_vectorstore(
    vectorstore=vectorstore,
    new_text="章节内容...",
    chapter_id=1
)

# 检索上下文
context = retrieve_context(
    vectorstore=vectorstore,
    query="主角的能力",
    k=4
)
```

---

### 4. 导出系统

**支持格式**: TXT, EPUB, PDF, DOCX

**基本用法**:

```python
from export_manager import export_novel

# 导出为EPUB
export_novel(
    novel_dir="./my_novel",
    output_file="./output.epub",
    format_type="epub",
    title="我的小说",
    author="作者名",
    num_chapters=10
)
```

**添加新导出格式**:

```python
class NovelExporter:
    def export_my_format(self, output_path: str) -> bool:
        """导出为自定义格式"""
        try:
            # 实现导出逻辑
            return True
        except Exception as e:
            logger.error(f"导出失败: {e}")
            return False
```

---

### 5. 日志系统

**基本用法**:

```python
from logger_config import setup_logger, get_logger

# 设置日志（只需在主程序调用一次）
logger = setup_logger(
    name="MyModule",
    log_dir="./logs",
    log_level=logging.INFO
)

# 在其他模块中获取日志器
logger = get_logger("SubModule")
logger.info("信息日志")
logger.error("错误日志")
```

**日志配置**:

```python
import logging
from logger_config import set_log_level

# 动态调整日志级别
set_log_level(logging.DEBUG)
```

---

## 开发环境设置

### 1. 克隆项目

```bash
git clone https://github.com/YILING0013/AI_NovelGenerator.git
cd AI_NovelGenerator
```

### 2. 创建虚拟环境（推荐）

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. 安装依赖

```bash
# 基础依赖
pip install -r requirements.txt

# 开发依赖（包含测试工具）
pip install pytest pytest-cov pytest-asyncio
pip install black flake8 mypy  # 代码格式化和检查工具
```

### 4. 配置pre-commit（可选）

```bash
pip install pre-commit
pre-commit install
```

---

## 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/test_export_manager.py

# 运行特定测试用例
pytest tests/test_export_manager.py::TestNovelExporter::test_export_txt

# 生成覆盖率报告
pytest --cov=. --cov-report=html
```

### 编写测试

```python
# tests/test_my_module.py
import pytest
from my_module import my_function

def test_my_function():
    """测试我的函数"""
    result = my_function(input_data)
    assert result == expected_output
```

---

## 代码规范

### Python风格指南

遵循 PEP 8 规范：

```bash
# 代码格式化
black .

# 代码检查
flake8 .

# 类型检查
mypy .
```

### 提交规范

提交消息格式：

```
<type>(<scope>): <subject>

<body>

<footer>
```

类型（type）:
- feat: 新功能
- fix: 修复bug
- docs: 文档更新
- style: 代码格式
- refactor: 重构
- test: 测试相关
- chore: 构建/工具变更

示例：
```
feat(export): 添加PDF导出功能

- 实现PDF生成逻辑
- 支持中文字体
- 添加单元测试

Closes #123
```

---

## 性能优化

### 1. 向量库优化

```python
# 批量添加文档（更高效）
vectorstore.add_texts(
    texts=[chapter1, chapter2, chapter3],
    metadatas=[meta1, meta2, meta3]
)
```

### 2. LLM调用优化

```python
# 使用缓存减少重复调用
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_llm_call(prompt: str) -> str:
    return llm.invoke(prompt)
```

### 3. 并发处理

```python
import asyncio

async def generate_multiple_chapters(chapter_numbers):
    tasks = [
        generate_chapter_async(num)
        for num in chapter_numbers
    ]
    results = await asyncio.gather(*tasks)
    return results
```

---

## 故障排查

### 常见问题

1. **向量库初始化失败**
   - 检查Embedding模型配置
   - 确认网络连接
   - 查看日志文件

2. **LLM调用超时**
   - 增加timeout参数
   - 检查API服务状态
   - 使用更快的模型

3. **内存不足**
   - 减少向量库检索数量
   - 使用分块处理
   - 清理不需要的数据

### 调试技巧

```python
# 启用详细日志
import logging
logging.basicConfig(level=logging.DEBUG)

# 使用pdb调试
import pdb
pdb.set_trace()
```

---

## 贡献指南

### 提交PR流程

1. Fork项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 代码审查标准

- [ ] 代码符合PEP 8规范
- [ ] 添加了适当的测试
- [ ] 文档已更新
- [ ] 所有测试通过
- [ ] 没有引入新的依赖（或已在requirements.txt中声明）

---

## 发布流程

### 版本号规范

使用语义化版本：`MAJOR.MINOR.PATCH`

- MAJOR: 不兼容的API变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的bug修复

### 发布步骤

1. 更新版本号
2. 更新CHANGELOG
3. 运行完整测试
4. 创建Git标签
5. 推送到仓库
6. 生成发布包

```bash
# 创建标签
git tag -a v1.5.0 -m "Release version 1.5.0"
git push origin v1.5.0

# 打包
python setup.py sdist bdist_wheel
```

---

## 更多资源

- [LangChain文档](https://python.langchain.com/)
- [FastAPI文档](https://fastapi.tiangolo.com/)
- [ChromaDB文档](https://docs.trychroma.com/)
- [CustomTkinter文档](https://customtkinter.tomschimansky.com/)
