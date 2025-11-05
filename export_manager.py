# export_manager.py
# -*- coding: utf-8 -*-
"""
小说导出管理器
支持导出为 TXT, EPUB, PDF, DOCX 格式
"""

import os
from typing import List, Optional, Dict
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class NovelExporter:
    """小说导出器，支持多种格式"""

    def __init__(self, novel_dir: str):
        """
        初始化导出器

        Args:
            novel_dir: 小说文件所在目录
        """
        self.novel_dir = Path(novel_dir)
        self.chapters_data = []
        self.metadata = {
            'title': '未命名小说',
            'author': 'AI Novel Generator',
            'language': 'zh-CN',
            'genre': '未分类'
        }

    def load_chapters(self, num_chapters: Optional[int] = None) -> List[Dict[str, str]]:
        """
        从目录加载所有章节

        Args:
            num_chapters: 要加载的章节数量，None表示全部

        Returns:
            章节列表，每个章节包含title和content
        """
        self.chapters_data = []

        # 读取章节文件
        chapter_files = sorted(
            self.novel_dir.glob("chapter_*.txt"),
            key=lambda x: int(x.stem.split('_')[1])
        )

        if num_chapters:
            chapter_files = chapter_files[:num_chapters]

        for chapter_file in chapter_files:
            try:
                with open(chapter_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()

                chapter_num = int(chapter_file.stem.split('_')[1])
                title = f"第{chapter_num}章"

                # 尝试从目录文件获取章节标题
                directory_file = self.novel_dir / "Novel_directory.txt"
                if directory_file.exists():
                    title = self._extract_chapter_title(directory_file, chapter_num) or title

                self.chapters_data.append({
                    'number': chapter_num,
                    'title': title,
                    'content': content
                })

            except Exception as e:
                logger.error(f"加载章节 {chapter_file} 失败: {e}")

        logger.info(f"成功加载 {len(self.chapters_data)} 个章节")
        return self.chapters_data

    def _extract_chapter_title(self, directory_file: Path, chapter_num: int) -> Optional[str]:
        """从目录文件中提取章节标题"""
        try:
            with open(directory_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # 查找章节标题（格式：第X章：标题）
            for line in content.split('\n'):
                if f"第{chapter_num}章" in line or f"第 {chapter_num} 章" in line:
                    # 提取标题部分
                    if '：' in line or ':' in line:
                        parts = line.split('：' if '：' in line else ':', 1)
                        if len(parts) > 1:
                            return parts[0].strip()
                    return line.strip()
        except Exception as e:
            logger.warning(f"提取章节标题失败: {e}")

        return None

    def set_metadata(self, title: str = None, author: str = None,
                     genre: str = None, language: str = None):
        """设置小说元数据"""
        if title:
            self.metadata['title'] = title
        if author:
            self.metadata['author'] = author
        if genre:
            self.metadata['genre'] = genre
        if language:
            self.metadata['language'] = language

    def export_txt(self, output_path: str) -> bool:
        """
        导出为TXT格式

        Args:
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                # 写入标题
                f.write(f"{self.metadata['title']}\n")
                f.write(f"作者: {self.metadata['author']}\n")
                f.write(f"类型: {self.metadata['genre']}\n")
                f.write("=" * 50 + "\n\n")

                # 写入章节
                for chapter in self.chapters_data:
                    f.write(f"\n\n{chapter['title']}\n")
                    f.write("-" * 40 + "\n\n")
                    f.write(chapter['content'])
                    f.write("\n")

            logger.info(f"成功导出TXT: {output_path}")
            return True

        except Exception as e:
            logger.error(f"导出TXT失败: {e}")
            return False

    def export_epub(self, output_path: str) -> bool:
        """
        导出为EPUB格式

        Args:
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            from ebooklib import epub

            book = epub.EpubBook()

            # 设置元数据
            book.set_identifier(f'novel_{hash(self.metadata["title"])}')
            book.set_title(self.metadata['title'])
            book.set_language(self.metadata['language'])
            book.add_author(self.metadata['author'])

            # 创建章节
            epub_chapters = []
            spine = ['nav']

            for chapter in self.chapters_data:
                # 创建EPUB章节
                c = epub.EpubHtml(
                    title=chapter['title'],
                    file_name=f'chapter_{chapter["number"]}.xhtml',
                    lang=self.metadata['language']
                )

                # 设置章节内容（添加HTML格式）
                content_html = f'<h1>{chapter["title"]}</h1>'
                # 将文本按段落分割
                paragraphs = chapter['content'].split('\n')
                for para in paragraphs:
                    if para.strip():
                        content_html += f'<p>{para.strip()}</p>'

                c.content = content_html

                book.add_item(c)
                epub_chapters.append(c)
                spine.append(c)

            # 添加目录
            book.toc = epub_chapters

            # 添加导航文件
            book.add_item(epub.EpubNcx())
            book.add_item(epub.EpubNav())

            # 设置spine
            book.spine = spine

            # 写入文件
            epub.write_epub(output_path, book, {})

            logger.info(f"成功导出EPUB: {output_path}")
            return True

        except ImportError:
            logger.error("请安装ebooklib库: pip install ebooklib")
            return False
        except Exception as e:
            logger.error(f"导出EPUB失败: {e}")
            return False

    def export_pdf(self, output_path: str) -> bool:
        """
        导出为PDF格式

        Args:
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY

            # 注册中文字体（使用系统字体）
            try:
                # Linux字体路径
                font_paths = [
                    '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                    '/usr/share/fonts/truetype/droid/DroidSansFallbackFull.ttf',
                    '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc',
                ]

                font_registered = False
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        pdfmetrics.registerFont(TTFont('Chinese', font_path))
                        font_registered = True
                        break

                if not font_registered:
                    logger.warning("未找到中文字体，PDF可能无法正确显示中文")
                    return False

            except Exception as e:
                logger.error(f"注册中文字体失败: {e}")
                return False

            # 创建PDF
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=2*cm,
                leftMargin=2*cm,
                topMargin=2*cm,
                bottomMargin=2*cm
            )

            # 定义样式
            styles = getSampleStyleSheet()

            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontName='Chinese',
                fontSize=24,
                alignment=TA_CENTER,
                spaceAfter=30,
            )

            chapter_title_style = ParagraphStyle(
                'ChapterTitle',
                parent=styles['Heading2'],
                fontName='Chinese',
                fontSize=18,
                spaceAfter=20,
                spaceBefore=20,
            )

            body_style = ParagraphStyle(
                'CustomBody',
                parent=styles['BodyText'],
                fontName='Chinese',
                fontSize=12,
                alignment=TA_JUSTIFY,
                leading=20,
                firstLineIndent=24,
            )

            # 构建内容
            story = []

            # 标题页
            story.append(Paragraph(self.metadata['title'], title_style))
            story.append(Spacer(1, 0.5*cm))
            story.append(Paragraph(f"作者: {self.metadata['author']}", body_style))
            story.append(Paragraph(f"类型: {self.metadata['genre']}", body_style))
            story.append(PageBreak())

            # 章节内容
            for chapter in self.chapters_data:
                # 章节标题
                story.append(Paragraph(chapter['title'], chapter_title_style))

                # 章节内容（按段落分割）
                paragraphs = chapter['content'].split('\n')
                for para in paragraphs:
                    if para.strip():
                        story.append(Paragraph(para.strip(), body_style))
                        story.append(Spacer(1, 0.3*cm))

                story.append(PageBreak())

            # 生成PDF
            doc.build(story)

            logger.info(f"成功导出PDF: {output_path}")
            return True

        except ImportError:
            logger.error("请安装reportlab库: pip install reportlab")
            return False
        except Exception as e:
            logger.error(f"导出PDF失败: {e}")
            return False

    def export_docx(self, output_path: str) -> bool:
        """
        导出为DOCX格式

        Args:
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        try:
            from docx import Document
            from docx.shared import Pt, Cm
            from docx.enum.text import WD_ALIGN_PARAGRAPH

            doc = Document()

            # 设置页边距
            sections = doc.sections
            for section in sections:
                section.top_margin = Cm(2.54)
                section.bottom_margin = Cm(2.54)
                section.left_margin = Cm(3.18)
                section.right_margin = Cm(3.18)

            # 添加标题
            title = doc.add_heading(self.metadata['title'], 0)
            title.alignment = WD_ALIGN_PARAGRAPH.CENTER

            # 添加元数据
            doc.add_paragraph(f"作者: {self.metadata['author']}")
            doc.add_paragraph(f"类型: {self.metadata['genre']}")
            doc.add_paragraph("")  # 空行

            # 添加分隔线
            doc.add_paragraph("=" * 50)
            doc.add_page_break()

            # 添加章节
            for chapter in self.chapters_data:
                # 章节标题
                chapter_heading = doc.add_heading(chapter['title'], 1)

                # 章节内容
                paragraphs = chapter['content'].split('\n')
                for para in paragraphs:
                    if para.strip():
                        p = doc.add_paragraph(para.strip())
                        # 设置段落格式
                        p_format = p.paragraph_format
                        p_format.first_line_indent = Cm(0.74)  # 首行缩进
                        p_format.line_spacing = 1.5  # 行距

                doc.add_page_break()

            # 保存文档
            doc.save(output_path)

            logger.info(f"成功导出DOCX: {output_path}")
            return True

        except ImportError:
            logger.error("请安装python-docx库: pip install python-docx")
            return False
        except Exception as e:
            logger.error(f"导出DOCX失败: {e}")
            return False

    def export(self, format_type: str, output_path: str) -> bool:
        """
        统一导出接口

        Args:
            format_type: 导出格式 ('txt', 'epub', 'pdf', 'docx')
            output_path: 输出文件路径

        Returns:
            是否成功
        """
        format_type = format_type.lower()

        if format_type == 'txt':
            return self.export_txt(output_path)
        elif format_type == 'epub':
            return self.export_epub(output_path)
        elif format_type == 'pdf':
            return self.export_pdf(output_path)
        elif format_type == 'docx':
            return self.export_docx(output_path)
        else:
            logger.error(f"不支持的格式: {format_type}")
            return False


def export_novel(novel_dir: str, output_file: str,
                 format_type: str = 'txt',
                 title: str = None,
                 author: str = "AI Novel Generator",
                 genre: str = "未分类",
                 num_chapters: int = None) -> bool:
    """
    便捷导出函数

    Args:
        novel_dir: 小说目录
        output_file: 输出文件路径
        format_type: 导出格式
        title: 小说标题
        author: 作者
        genre: 类型
        num_chapters: 导出章节数

    Returns:
        是否成功
    """
    exporter = NovelExporter(novel_dir)

    # 加载章节
    chapters = exporter.load_chapters(num_chapters)
    if not chapters:
        logger.error("没有找到可导出的章节")
        return False

    # 设置元数据
    if not title:
        title = f"小说作品_{len(chapters)}章"

    exporter.set_metadata(title=title, author=author, genre=genre)

    # 导出
    return exporter.export(format_type, output_file)


if __name__ == "__main__":
    # 测试导出功能
    logging.basicConfig(level=logging.INFO)

    # 示例用法
    novel_dir = "./my_novel"

    if os.path.exists(novel_dir):
        # 导出为不同格式
        export_novel(novel_dir, "output.txt", "txt", title="我的小说")
        export_novel(novel_dir, "output.epub", "epub", title="我的小说")
        export_novel(novel_dir, "output.pdf", "pdf", title="我的小说")
        export_novel(novel_dir, "output.docx", "docx", title="我的小说")
