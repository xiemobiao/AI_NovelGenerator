# 示例代码

本目录包含各种使用示例，帮助你快速上手AI Novel Generator。

## 📁 文件说明

### 1. simple_example.py
完整的小说生成示例，使用API模式。

**功能**：
- 配置LLM和Embedding
- 生成5章短篇小说
- 导出为EPUB格式

**使用方法**：
```bash
# 1. 启动API服务器
python api_server.py

# 2. 运行示例（在新终端）
python examples/simple_example.py
```

**注意**：需要先编辑文件，填入你的API密钥。

---

### 2. export_example.py
导出功能示例，将已有小说导出为多种格式。

**功能**：
- 导出TXT、EPUB、PDF、DOCX格式
- 支持导出部分章节
- 自动显示文件大小

**使用方法**：
```bash
# 方式1：使用默认配置
python examples/export_example.py

# 方式2：指定参数
python examples/export_example.py ./my_novel "我的小说" "作者名"
```

---

## 🚀 快速开始

### 准备工作

1. **安装依赖**
```bash
pip install -r requirements.txt
```

2. **准备API密钥**
- OpenAI: https://platform.openai.com/api-keys
- DeepSeek: https://platform.deepseek.com/
- 或使用本地Ollama

3. **（可选）安装导出依赖**
```bash
pip install ebooklib reportlab python-docx
```

### 方式1：GUI模式（推荐新手）

```bash
python main.py
```

按照界面提示操作即可。

### 方式2：API模式（适合程序化调用）

```bash
# 启动API服务器
python api_server.py

# 运行示例
python examples/simple_example.py
```

### 方式3：纯代码模式

```python
from novel_generator import Novel_architecture_generate
from llm_adapters import create_llm_adapter

# 创建LLM适配器
llm = create_llm_adapter(
    interface_format="OpenAI",
    api_key="your-key",
    model_name="gpt-4o-mini"
)

# 生成架构
Novel_architecture_generate(
    llm=llm,
    topic="你的主题",
    genre="类型",
    num_chapters=10,
    word_number=3000,
    filepath="./output"
)
```

---

## 📚 更多示例

### 示例3：批量生成章节

```python
from novel_generator import generate_chapter_draft, finalize_chapter
from llm_adapters import create_llm_adapter

llm = create_llm_adapter(
    interface_format="OpenAI",
    api_key="your-key",
    model_name="gpt-4o-mini"
)

# 批量生成第1-10章
for i in range(1, 11):
    print(f"生成第{i}章...")

    # 生成草稿
    generate_chapter_draft(
        llm=llm,
        chapter_number=i,
        filepath="./my_novel"
    )

    # 定稿
    finalize_chapter(
        llm=llm,
        chapter_number=i,
        filepath="./my_novel"
    )

    print(f"第{i}章完成！")
```

### 示例4：使用知识库

```python
from novel_generator.knowledge import import_knowledge_to_vectorstore
from embedding_adapters import create_embedding_adapter

# 创建Embedding适配器
embedding = create_embedding_adapter(
    interface_format="OpenAI",
    api_key="your-key",
    model_name="text-embedding-ada-002"
)

# 导入知识文件
import_knowledge_to_vectorstore(
    knowledge_file="./reference_material.txt",
    embedding_llm=embedding,
    filepath="./my_novel",
    mode="append"  # 追加模式
)

print("知识库导入完成！")
```

### 示例5：一致性检查

```python
from consistency_checker import consistency_check
from llm_adapters import create_llm_adapter

llm = create_llm_adapter(
    interface_format="OpenAI",
    api_key="your-key",
    model_name="gpt-4o-mini"
)

# 检查第5章的一致性
issues = consistency_check(
    llm=llm,
    chapter_number=5,
    filepath="./my_novel"
)

if issues:
    print("发现以下问题：")
    for issue in issues:
        print(f"- {issue}")
else:
    print("未发现一致性问题")
```

---

## ⚙️ 配置示例

### 使用本地Ollama

```python
config = {
    "llm_config": {
        "interface_format": "OpenAI",  # Ollama兼容OpenAI接口
        "api_key": "ollama",  # 任意值
        "base_url": "http://localhost:11434/v1",
        "model_name": "qwen2.5:14b",
        "temperature": 0.7,
        "max_tokens": 4096
    },
    "embedding_config": {
        "interface_format": "Ollama",
        "api_key": "ollama",
        "base_url": "http://localhost:11434",
        "model_name": "nomic-embed-text"
    }
}
```

### 使用DeepSeek

```python
config = {
    "llm_config": {
        "interface_format": "DeepSeek",
        "api_key": "sk-xxx",
        "model_name": "deepseek-chat",
        "temperature": 0.8
    }
}
```

---

## 🐛 故障排查

### 问题1：API连接失败

**检查**：
- API密钥是否正确
- base_url是否正确
- 网络连接是否正常

**测试连接**：
```bash
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer your-api-key"
```

### 问题2：导出失败

**安装依赖**：
```bash
# EPUB导出
pip install ebooklib

# PDF导出
pip install reportlab

# DOCX导出
pip install python-docx
```

### 问题3：向量库错误

**解决方案**：
- 检查Embedding配置
- 清空vectorstore目录后重试
- 确认chromadb版本兼容

---

## 📖 相关文档

- [完整教程](../docs/TUTORIAL.md)
- [API文档](../docs/API_DOCUMENTATION.md)
- [开发文档](../docs/DEVELOPMENT.md)

---

## 💡 贡献示例

如果你有好的示例代码，欢迎贡献！

1. Fork项目
2. 在 `examples/` 目录添加你的示例
3. 更新本README
4. 提交PR

---

## 📞 获取帮助

- 提交Issue: https://github.com/YILING0013/AI_NovelGenerator/issues
- 查看FAQ: [README.md](../README.md#疑难解答)
