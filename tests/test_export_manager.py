# tests/test_export_manager.py
# -*- coding: utf-8 -*-
"""
导出管理器测试
"""

import pytest
from pathlib import Path
from export_manager import NovelExporter, export_novel


class TestNovelExporter:
    """测试NovelExporter类"""

    def test_initialization(self, sample_novel_dir):
        """测试初始化"""
        exporter = NovelExporter(str(sample_novel_dir))
        assert exporter.novel_dir == sample_novel_dir
        assert exporter.metadata['title'] == '未命名小说'
        assert exporter.metadata['author'] == 'AI Novel Generator'

    def test_load_chapters(self, sample_novel_dir):
        """测试加载章节"""
        exporter = NovelExporter(str(sample_novel_dir))
        chapters = exporter.load_chapters()

        assert len(chapters) == 3
        assert chapters[0]['number'] == 1
        assert '内容' in chapters[0]['content']

    def test_load_limited_chapters(self, sample_novel_dir):
        """测试加载限定数量的章节"""
        exporter = NovelExporter(str(sample_novel_dir))
        chapters = exporter.load_chapters(num_chapters=2)

        assert len(chapters) == 2

    def test_set_metadata(self, sample_novel_dir):
        """测试设置元数据"""
        exporter = NovelExporter(str(sample_novel_dir))
        exporter.set_metadata(
            title="测试小说",
            author="测试作者",
            genre="科幻"
        )

        assert exporter.metadata['title'] == "测试小说"
        assert exporter.metadata['author'] == "测试作者"
        assert exporter.metadata['genre'] == "科幻"

    def test_export_txt(self, sample_novel_dir, temp_dir):
        """测试TXT导出"""
        exporter = NovelExporter(str(sample_novel_dir))
        exporter.load_chapters()

        output_file = temp_dir / "output.txt"
        result = exporter.export_txt(str(output_file))

        assert result is True
        assert output_file.exists()

        content = output_file.read_text(encoding='utf-8')
        assert '未命名小说' in content
        assert '第1章' in content or 'chapter_1' in content

    def test_export_function(self, sample_novel_dir, temp_dir):
        """测试便捷导出函数"""
        output_file = temp_dir / "novel.txt"

        result = export_novel(
            novel_dir=str(sample_novel_dir),
            output_file=str(output_file),
            format_type='txt',
            title="测试小说",
            author="测试作者"
        )

        assert result is True
        assert output_file.exists()


class TestExportFormats:
    """测试不同导出格式（可选，需要安装相应库）"""

    @pytest.mark.skipif(
        not pytest.importorskip("ebooklib", minversion=None),
        reason="需要安装ebooklib"
    )
    def test_export_epub(self, sample_novel_dir, temp_dir):
        """测试EPUB导出"""
        exporter = NovelExporter(str(sample_novel_dir))
        exporter.load_chapters()
        exporter.set_metadata(title="测试EPUB")

        output_file = temp_dir / "output.epub"
        result = exporter.export_epub(str(output_file))

        assert result is True
        assert output_file.exists()

    @pytest.mark.skipif(
        not pytest.importorskip("docx", minversion=None),
        reason="需要安装python-docx"
    )
    def test_export_docx(self, sample_novel_dir, temp_dir):
        """测试DOCX导出"""
        exporter = NovelExporter(str(sample_novel_dir))
        exporter.load_chapters()
        exporter.set_metadata(title="测试DOCX")

        output_file = temp_dir / "output.docx"
        result = exporter.export_docx(str(output_file))

        assert result is True
        assert output_file.exists()
