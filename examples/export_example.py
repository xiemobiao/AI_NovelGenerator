#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
导出示例：将已有小说导出为多种格式
"""

from export_manager import export_novel
from pathlib import Path
import logging

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def export_all_formats(
    novel_dir: str,
    title: str,
    author: str = "AI Novel Generator",
    num_chapters: int = None
):
    """
    导出所有支持的格式

    Args:
        novel_dir: 小说目录
        title: 小说标题
        author: 作者
        num_chapters: 导出章节数（None表示全部）
    """

    novel_path = Path(novel_dir)

    if not novel_path.exists():
        logger.error(f"目录不存在: {novel_dir}")
        return

    # 定义导出格式
    formats = {
        'txt': '纯文本',
        'epub': '电子书',
        'pdf': 'PDF文档',
        'docx': 'Word文档'
    }

    print(f"\n{'='*60}")
    print(f"📚 导出小说: {title}")
    print(f"{'='*60}\n")

    success_count = 0

    for fmt, desc in formats.items():
        output_file = novel_path / f"{title}.{fmt}"

        print(f"导出{desc}格式...")

        try:
            result = export_novel(
                novel_dir=novel_dir,
                output_file=str(output_file),
                format_type=fmt,
                title=title,
                author=author,
                num_chapters=num_chapters
            )

            if result:
                file_size = output_file.stat().st_size / 1024  # KB
                print(f"  ✅ 成功: {output_file} ({file_size:.1f} KB)")
                success_count += 1
            else:
                print(f"  ❌ 失败: {fmt}格式")

        except Exception as e:
            logger.error(f"导出{fmt}格式时出错: {e}")
            print(f"  ❌ 错误: {e}")

    print(f"\n{'='*60}")
    print(f"完成！成功导出 {success_count}/{len(formats)} 种格式")
    print(f"{'='*60}\n")


def main():
    """主函数"""

    # 示例1：导出指定目录的小说
    export_all_formats(
        novel_dir="./my_novel",
        title="我的第一部AI小说",
        author="张三",
        num_chapters=None  # 导出所有章节
    )

    # 示例2：只导出前10章
    # export_all_formats(
    #     novel_dir="./my_novel",
    #     title="我的小说（前10章）",
    #     author="张三",
    #     num_chapters=10
    # )


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        # 从命令行参数读取配置
        novel_dir = sys.argv[1]
        title = sys.argv[2] if len(sys.argv) > 2 else "未命名小说"
        author = sys.argv[3] if len(sys.argv) > 3 else "AI Novel Generator"

        export_all_formats(novel_dir, title, author)
    else:
        # 使用默认配置
        main()
