# ui/export_tab.py
# -*- coding: utf-8 -*-
"""
导出功能标签页
提供多格式导出功能的图形界面
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
import threading
from pathlib import Path
from typing import Callable
import os


class ExportTab:
    """导出功能标签页"""

    def __init__(self, parent_frame, log_callback: Callable[[str], None]):
        """
        初始化导出标签页

        Args:
            parent_frame: 父容器
            log_callback: 日志输出回调函数
        """
        self.frame = parent_frame
        self.log = log_callback

        self.setup_ui()

    def setup_ui(self):
        """设置UI布局"""
        # 主容器
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        # ==================== 顶部：说明区域 ====================
        info_frame = ctk.CTkFrame(self.frame)
        info_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")

        info_label = ctk.CTkLabel(
            info_frame,
            text="📚 导出功能：将生成的小说导出为多种格式",
            font=("Arial", 14, "bold")
        )
        info_label.pack(pady=10)

        info_text = ctk.CTkLabel(
            info_frame,
            text="支持格式：TXT（纯文本）、EPUB（电子书）、PDF（文档）、DOCX（Word）",
            font=("Arial", 12)
        )
        info_text.pack(pady=(0, 10))

        # ==================== 中部：配置区域 ====================
        config_frame = ctk.CTkFrame(self.frame)
        config_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        config_frame.grid_columnconfigure(1, weight=1)

        row = 0

        # 项目目录
        ctk.CTkLabel(config_frame, text="项目目录:").grid(
            row=row, column=0, padx=10, pady=10, sticky="w"
        )
        self.project_dir_entry = ctk.CTkEntry(
            config_frame,
            placeholder_text="选择包含小说章节的目录..."
        )
        self.project_dir_entry.grid(
            row=row, column=1, padx=10, pady=10, sticky="ew"
        )
        ctk.CTkButton(
            config_frame,
            text="浏览",
            width=80,
            command=self.browse_project_dir
        ).grid(row=row, column=2, padx=10, pady=10)
        row += 1

        # 导出格式
        ctk.CTkLabel(config_frame, text="导出格式:").grid(
            row=row, column=0, padx=10, pady=10, sticky="w"
        )
        self.format_var = ctk.StringVar(value="txt")
        format_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        format_frame.grid(row=row, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        formats = [
            ("TXT (纯文本)", "txt"),
            ("EPUB (电子书)", "epub"),
            ("PDF (文档)", "pdf"),
            ("DOCX (Word)", "docx")
        ]

        for i, (text, value) in enumerate(formats):
            ctk.CTkRadioButton(
                format_frame,
                text=text,
                variable=self.format_var,
                value=value
            ).grid(row=0, column=i, padx=10)
        row += 1

        # 小说标题
        ctk.CTkLabel(config_frame, text="小说标题:").grid(
            row=row, column=0, padx=10, pady=10, sticky="w"
        )
        self.title_entry = ctk.CTkEntry(
            config_frame,
            placeholder_text="输入小说标题（会用于文件名和元数据）"
        )
        self.title_entry.grid(
            row=row, column=1, columnspan=2, padx=10, pady=10, sticky="ew"
        )
        row += 1

        # 作者
        ctk.CTkLabel(config_frame, text="作者:").grid(
            row=row, column=0, padx=10, pady=10, sticky="w"
        )
        self.author_entry = ctk.CTkEntry(
            config_frame,
            placeholder_text="作者名称（可选）"
        )
        self.author_entry.insert(0, "AI Novel Generator")
        self.author_entry.grid(
            row=row, column=1, columnspan=2, padx=10, pady=10, sticky="ew"
        )
        row += 1

        # 小说类型
        ctk.CTkLabel(config_frame, text="类型:").grid(
            row=row, column=0, padx=10, pady=10, sticky="w"
        )
        self.genre_entry = ctk.CTkEntry(
            config_frame,
            placeholder_text="小说类型（如：玄幻、科幻等，可选）"
        )
        self.genre_entry.grid(
            row=row, column=1, columnspan=2, padx=10, pady=10, sticky="ew"
        )
        row += 1

        # 导出章节数
        ctk.CTkLabel(config_frame, text="导出章节:").grid(
            row=row, column=0, padx=10, pady=10, sticky="w"
        )
        chapters_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        chapters_frame.grid(row=row, column=1, columnspan=2, padx=10, pady=10, sticky="w")

        self.all_chapters_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(
            chapters_frame,
            text="全部章节",
            variable=self.all_chapters_var,
            command=self.toggle_chapter_limit
        ).grid(row=0, column=0, padx=(0, 20))

        ctk.CTkLabel(chapters_frame, text="或前").grid(row=0, column=1)
        self.chapter_limit_entry = ctk.CTkEntry(
            chapters_frame,
            width=80,
            state="disabled"
        )
        self.chapter_limit_entry.grid(row=0, column=2, padx=5)
        ctk.CTkLabel(chapters_frame, text="章").grid(row=0, column=3)
        row += 1

        # 输出文件
        ctk.CTkLabel(config_frame, text="输出文件:").grid(
            row=row, column=0, padx=10, pady=10, sticky="w"
        )
        self.output_file_entry = ctk.CTkEntry(
            config_frame,
            placeholder_text="输出文件路径（自动生成）"
        )
        self.output_file_entry.grid(
            row=row, column=1, padx=10, pady=10, sticky="ew"
        )
        ctk.CTkButton(
            config_frame,
            text="选择",
            width=80,
            command=self.browse_output_file
        ).grid(row=row, column=2, padx=10, pady=10)
        row += 1

        # 分隔线
        ctk.CTkFrame(config_frame, height=2).grid(
            row=row, column=0, columnspan=3, padx=10, pady=10, sticky="ew"
        )
        row += 1

        # ==================== 底部：操作区域 ====================
        action_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        action_frame.grid(row=row, column=0, columnspan=3, padx=10, pady=10)

        # 导出按钮
        self.export_button = ctk.CTkButton(
            action_frame,
            text="🚀 开始导出",
            command=self.start_export,
            width=200,
            height=40,
            font=("Arial", 14, "bold")
        )
        self.export_button.grid(row=0, column=0, padx=10)

        # 打开文件夹按钮
        self.open_folder_button = ctk.CTkButton(
            action_frame,
            text="📁 打开输出目录",
            command=self.open_output_folder,
            width=150,
            height=40,
            state="disabled"
        )
        self.open_folder_button.grid(row=0, column=1, padx=10)

        # 进度标签
        self.progress_label = ctk.CTkLabel(
            config_frame,
            text="",
            font=("Arial", 12)
        )
        self.progress_label.grid(
            row=row+1, column=0, columnspan=3, padx=10, pady=5
        )

    def toggle_chapter_limit(self):
        """切换章节数量限制"""
        if self.all_chapters_var.get():
            self.chapter_limit_entry.configure(state="disabled")
        else:
            self.chapter_limit_entry.configure(state="normal")

    def browse_project_dir(self):
        """浏览项目目录"""
        directory = filedialog.askdirectory(title="选择项目目录")
        if directory:
            self.project_dir_entry.delete(0, "end")
            self.project_dir_entry.insert(0, directory)

            # 自动设置输出文件名
            if self.title_entry.get():
                self.update_output_filename()

    def browse_output_file(self):
        """选择输出文件"""
        format_ext = self.format_var.get()
        filetypes = {
            "txt": [("文本文件", "*.txt")],
            "epub": [("EPUB文件", "*.epub")],
            "pdf": [("PDF文件", "*.pdf")],
            "docx": [("Word文档", "*.docx")]
        }

        filename = filedialog.asksaveasfilename(
            title="保存为",
            defaultextension=f".{format_ext}",
            filetypes=filetypes.get(format_ext, [("所有文件", "*.*")])
        )

        if filename:
            self.output_file_entry.delete(0, "end")
            self.output_file_entry.insert(0, filename)

    def update_output_filename(self):
        """自动更新输出文件名"""
        project_dir = self.project_dir_entry.get()
        title = self.title_entry.get()
        format_ext = self.format_var.get()

        if project_dir and title:
            output_file = Path(project_dir) / f"{title}.{format_ext}"
            self.output_file_entry.delete(0, "end")
            self.output_file_entry.insert(0, str(output_file))

    def validate_inputs(self) -> bool:
        """验证输入"""
        project_dir = self.project_dir_entry.get().strip()
        if not project_dir:
            messagebox.showerror("错误", "请选择项目目录")
            return False

        if not Path(project_dir).exists():
            messagebox.showerror("错误", "项目目录不存在")
            return False

        title = self.title_entry.get().strip()
        if not title:
            messagebox.showerror("错误", "请输入小说标题")
            return False

        # 检查是否有章节文件
        chapter_files = list(Path(project_dir).glob("chapter_*.txt"))
        if not chapter_files:
            messagebox.showerror("错误", "项目目录中没有找到章节文件")
            return False

        return True

    def start_export(self):
        """开始导出"""
        if not self.validate_inputs():
            return

        # 禁用导出按钮
        self.export_button.configure(state="disabled")
        self.progress_label.configure(text="正在导出...")

        # 在后台线程中执行导出
        thread = threading.Thread(target=self.export_thread)
        thread.daemon = True
        thread.start()

    def export_thread(self):
        """导出线程"""
        try:
            from export_manager import export_novel

            # 获取参数
            project_dir = self.project_dir_entry.get().strip()
            title = self.title_entry.get().strip()
            author = self.author_entry.get().strip() or "AI Novel Generator"
            genre = self.genre_entry.get().strip() or "未分类"
            format_type = self.format_var.get()

            # 导出章节数
            num_chapters = None
            if not self.all_chapters_var.get():
                try:
                    num_chapters = int(self.chapter_limit_entry.get())
                except:
                    pass

            # 输出文件
            output_file = self.output_file_entry.get().strip()
            if not output_file:
                output_file = str(Path(project_dir) / f"{title}.{format_type}")

            self.log(f"\n{'='*60}")
            self.log(f"开始导出小说")
            self.log(f"{'='*60}")
            self.log(f"项目目录: {project_dir}")
            self.log(f"标题: {title}")
            self.log(f"作者: {author}")
            self.log(f"类型: {genre}")
            self.log(f"格式: {format_type.upper()}")
            self.log(f"输出文件: {output_file}")
            if num_chapters:
                self.log(f"导出章节: 前{num_chapters}章")
            else:
                self.log(f"导出章节: 全部")
            self.log(f"{'-'*60}\n")

            # 执行导出
            success = export_novel(
                novel_dir=project_dir,
                output_file=output_file,
                format_type=format_type,
                title=title,
                author=author,
                genre=genre,
                num_chapters=num_chapters
            )

            if success:
                self.log(f"\n✅ 导出成功！")
                self.log(f"输出文件: {output_file}")

                # 计算文件大小
                file_size = Path(output_file).stat().st_size
                if file_size < 1024:
                    size_str = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    size_str = f"{file_size / 1024:.1f} KB"
                else:
                    size_str = f"{file_size / (1024 * 1024):.1f} MB"

                self.log(f"文件大小: {size_str}")
                self.log(f"{'='*60}\n")

                # 更新UI
                self.frame.after(0, lambda: self.progress_label.configure(
                    text=f"✅ 导出成功！文件: {Path(output_file).name}",
                    text_color="green"
                ))
                self.frame.after(0, lambda: self.open_folder_button.configure(state="normal"))

                messagebox.showinfo("成功", f"导出成功！\n文件: {output_file}")

            else:
                self.log(f"\n❌ 导出失败")
                self.log(f"{'='*60}\n")

                self.frame.after(0, lambda: self.progress_label.configure(
                    text="❌ 导出失败，请查看日志",
                    text_color="red"
                ))

                messagebox.showerror("失败", "导出失败，请查看日志了解详情")

        except Exception as e:
            error_msg = f"导出过程出错: {str(e)}"
            self.log(f"\n❌ {error_msg}")
            self.log(f"{'='*60}\n")

            self.frame.after(0, lambda: self.progress_label.configure(
                text=f"❌ {error_msg}",
                text_color="red"
            ))

            messagebox.showerror("错误", error_msg)

        finally:
            # 重新启用导出按钮
            self.frame.after(0, lambda: self.export_button.configure(state="normal"))

    def open_output_folder(self):
        """打开输出目录"""
        output_file = self.output_file_entry.get().strip()
        if output_file and Path(output_file).exists():
            output_dir = Path(output_file).parent

            # 根据操作系统打开文件夹
            import sys
            if sys.platform == "win32":
                os.startfile(output_dir)
            elif sys.platform == "darwin":  # macOS
                os.system(f'open "{output_dir}"')
            else:  # Linux
                os.system(f'xdg-open "{output_dir}"')
