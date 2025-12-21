# ui/longnovel_tab.py
# -*- coding: utf-8 -*-
"""
长篇小说项目管理标签页
提供卷管理、情节线管理、质量检查等功能
"""

import customtkinter as ctk
from tkinter import messagebox
from typing import Callable, Optional
from pathlib import Path
import json


class LongNovelTab:
    """长篇小说项目管理标签页"""

    def __init__(self, parent_frame, log_callback: Callable[[str], None], filepath_var):
        """
        初始化长篇项目管理标签页

        Args:
            parent_frame: 父容器
            log_callback: 日志输出回调函数
            filepath_var: 项目路径变量
        """
        self.frame = parent_frame
        self.log = log_callback
        self.filepath_var = filepath_var

        self.context_manager = None
        self.plot_tracker = None

        self.setup_ui()

    def setup_ui(self):
        """设置UI布局"""
        # 主容器布局
        self.frame.grid_columnconfigure(0, weight=1)
        self.frame.grid_rowconfigure(1, weight=1)

        # ==================== 顶部：项目状态 ====================
        status_frame = ctk.CTkFrame(self.frame)
        status_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        status_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            status_frame,
            text="📊 长篇项目管理",
            font=("Arial", 14, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)

        # 项目路径
        ctk.CTkLabel(status_frame, text="当前项目:").grid(
            row=1, column=0, padx=10, pady=5, sticky="w"
        )
        self.current_project_label = ctk.CTkLabel(
            status_frame,
            text="未选择",
            fg_color=("gray90", "gray20"),
            corner_radius=5
        )
        self.current_project_label.grid(
            row=1, column=1, padx=10, pady=5, sticky="ew"
        )

        # 初始化按钮
        self.init_button = ctk.CTkButton(
            status_frame,
            text="🔧 初始化项目管理",
            command=self.initialize_project,
            width=200
        )
        self.init_button.grid(row=2, column=0, columnspan=2, pady=10)

        # ==================== 中部：标签页 ====================
        self.sub_tabview = ctk.CTkTabview(self.frame)
        self.sub_tabview.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")

        # 子标签页
        self.sub_tabview.add("卷管理")
        self.sub_tabview.add("情节线")
        self.sub_tabview.add("质量报告")
        self.sub_tabview.add("Visualizations")

        # 构建各子页面
        self.build_volumes_page()
        self.build_plotlines_page()
        self.build_quality_page()
        self.build_visualizations_page()

    # ==================== 初始化 ====================

    def initialize_project(self):
        """初始化项目管理系统"""
        filepath = self.filepath_var.get().strip()
        if not filepath:
            messagebox.showerror("错误", "请先在主界面设置保存路径")
            return

        if not Path(filepath).exists():
            messagebox.showerror("错误", "项目目录不存在")
            return

        try:
            from context_manager import create_context_manager
            from plot_tracker import create_plot_tracker

            self.context_manager = create_context_manager(filepath)
            self.plot_tracker = create_plot_tracker(filepath)

            self.current_project_label.configure(text=filepath)
            self.init_button.configure(
                text="✅ 已初始化",
                state="disabled"
            )

            self.log(f"✅ 项目管理系统已初始化: {filepath}")
            self.log("   - 上下文管理器已加载")
            self.log("   - 情节追踪器已加载\n")

            # 刷新显示
            self.refresh_volumes_list()
            self.refresh_plotlines_list()
            self.refresh_quality_report()

            messagebox.showinfo("成功", "项目管理系统初始化成功！")

        except Exception as e:
            error_msg = f"初始化失败: {str(e)}"
            self.log(f"❌ {error_msg}\n")
            messagebox.showerror("错误", error_msg)

    # ==================== 卷管理页面 ====================

    def build_volumes_page(self):
        """构建卷管理页面"""
        volumes_frame = self.sub_tabview.tab("卷管理")
        volumes_frame.grid_columnconfigure(0, weight=1)
        volumes_frame.grid_columnconfigure(1, weight=2)
        volumes_frame.grid_rowconfigure(1, weight=1)

        # 左侧：卷列表
        left_frame = ctk.CTkFrame(volumes_frame)
        left_frame.grid(row=0, column=0, rowspan=2, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(left_frame, text="卷列表", font=("Arial", 12, "bold")).pack(
            pady=5
        )

        self.volumes_listbox = ctk.CTkTextbox(left_frame, height=400)
        self.volumes_listbox.pack(fill="both", expand=True, padx=5, pady=5)

        # 右侧：卷详情和编辑
        right_frame = ctk.CTkFrame(volumes_frame)
        right_frame.grid(row=0, column=1, padx=5, pady=5, sticky="nsew")
        right_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(
            right_frame,
            text="创建/编辑卷",
            font=("Arial", 12, "bold")
        ).grid(row=0, column=0, columnspan=2, pady=10)

        row = 1

        # 卷ID
        ctk.CTkLabel(right_frame, text="卷ID:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.volume_id_entry = ctk.CTkEntry(
            right_frame,
            placeholder_text="如: vol_1"
        )
        self.volume_id_entry.grid(
            row=row, column=1, padx=10, pady=5, sticky="ew"
        )
        row += 1

        # 卷标题
        ctk.CTkLabel(right_frame, text="标题:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        self.volume_title_entry = ctk.CTkEntry(
            right_frame,
            placeholder_text="如: 入门篇"
        )
        self.volume_title_entry.grid(
            row=row, column=1, padx=10, pady=5, sticky="ew"
        )
        row += 1

        # 章节范围
        ctk.CTkLabel(right_frame, text="章节范围:").grid(
            row=row, column=0, padx=10, pady=5, sticky="w"
        )
        range_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        range_frame.grid(row=row, column=1, padx=10, pady=5, sticky="ew")

        self.volume_start_entry = ctk.CTkEntry(range_frame, width=80)
        self.volume_start_entry.grid(row=0, column=0)
        ctk.CTkLabel(range_frame, text=" - ").grid(row=0, column=1)
        self.volume_end_entry = ctk.CTkEntry(range_frame, width=80)
        self.volume_end_entry.grid(row=0, column=2)
        row += 1

        # 摘要
        ctk.CTkLabel(right_frame, text="摘要:").grid(
            row=row, column=0, padx=10, pady=5, sticky="nw"
        )
        self.volume_summary_text = ctk.CTkTextbox(right_frame, height=80)
        self.volume_summary_text.grid(
            row=row, column=1, padx=10, pady=5, sticky="ew"
        )
        row += 1

        # 主要情节
        ctk.CTkLabel(right_frame, text="主要情节:").grid(
            row=row, column=0, padx=10, pady=5, sticky="nw"
        )
        self.volume_plot_text = ctk.CTkTextbox(right_frame, height=80)
        self.volume_plot_text.grid(
            row=row, column=1, padx=10, pady=5, sticky="ew"
        )
        row += 1

        # 按钮
        buttons_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        buttons_frame.grid(row=row, column=0, columnspan=2, pady=10)

        ctk.CTkButton(
            buttons_frame,
            text="创建卷",
            command=self.create_volume,
            width=100
        ).grid(row=0, column=0, padx=5)

        ctk.CTkButton(
            buttons_frame,
            text="刷新列表",
            command=self.refresh_volumes_list,
            width=100
        ).grid(row=0, column=1, padx=5)

    def create_volume(self):
        """创建卷"""
        if not self.context_manager:
            messagebox.showerror("错误", "请先初始化项目管理")
            return

        try:
            volume_id = self.volume_id_entry.get().strip()
            title = self.volume_title_entry.get().strip()
            start = int(self.volume_start_entry.get().strip())
            end = int(self.volume_end_entry.get().strip())
            summary = self.volume_summary_text.get("1.0", "end").strip()
            main_plot = self.volume_plot_text.get("1.0", "end").strip()

            if not all([volume_id, title, summary, main_plot]):
                messagebox.showerror("错误", "请填写所有必填字段")
                return

            self.context_manager.create_volume(
                volume_id,
                title,
                summary,
                (start, end),
                main_plot
            )

            self.log(f"✅ 创建卷: {volume_id} - {title}")
            self.log(f"   章节范围: {start}-{end}\n")

            self.refresh_volumes_list()
            messagebox.showinfo("成功", f"卷 '{title}' 创建成功")

            # 清空输入
            self.volume_id_entry.delete(0, "end")
            self.volume_title_entry.delete(0, "end")
            self.volume_start_entry.delete(0, "end")
            self.volume_end_entry.delete(0, "end")
            self.volume_summary_text.delete("1.0", "end")
            self.volume_plot_text.delete("1.0", "end")

        except Exception as e:
            error_msg = f"创建卷失败: {str(e)}"
            self.log(f"❌ {error_msg}\n")
            messagebox.showerror("错误", error_msg)

    def refresh_volumes_list(self):
        """刷新卷列表"""
        if not self.context_manager:
            return

        self.volumes_listbox.delete("1.0", "end")

        try:
            volumes = self.context_manager.volume_contexts

            if not volumes:
                self.volumes_listbox.insert("1.0", "暂无卷信息")
                return

            text = "卷列表:\n\n"
            for vol_id, vol_data in volumes.items():
                text += f"【{vol_data['title']}】\n"
                text += f"  ID: {vol_id}\n"
                text += f"  章节: {vol_data['chapters_range'][0]}-{vol_data['chapters_range'][1]}\n"
                text += f"  摘要: {vol_data['summary']}\n"
                text += f"\n"

            self.volumes_listbox.insert("1.0", text)

        except Exception as e:
            self.log(f"刷新卷列表失败: {e}\n")

    # ==================== 情节线页面 ====================

    def build_plotlines_page(self):
        """构建情节线管理页面"""
        plot_frame = self.sub_tabview.tab("情节线")
        plot_frame.grid_columnconfigure(0, weight=1)
        plot_frame.grid_rowconfigure(0, weight=1)

        # 情节线列表
        list_frame = ctk.CTkFrame(plot_frame)
        list_frame.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        ctk.CTkLabel(
            list_frame,
            text="情节线列表",
            font=("Arial", 12, "bold")
        ).pack(pady=5)

        self.plotlines_text = ctk.CTkTextbox(list_frame)
        self.plotlines_text.pack(fill="both", expand=True, padx=5, pady=5)

        # 按钮
        button_frame = ctk.CTkFrame(plot_frame, fg_color="transparent")
        button_frame.grid(row=1, column=0, pady=10)

        ctk.CTkButton(
            button_frame,
            text="刷新列表",
            command=self.refresh_plotlines_list,
            width=120
        ).grid(row=0, column=0, padx=5)

        ctk.CTkButton(
            button_frame,
            text="生成报告",
            command=self.generate_plot_report,
            width=120
        ).grid(row=0, column=1, padx=5)

    def refresh_plotlines_list(self):
        """刷新情节线列表"""
        if not self.plot_tracker:
            self.plotlines_text.delete("1.0", "end")
            self.plotlines_text.insert("1.0", "请先初始化项目管理")
            return

        self.plotlines_text.delete("1.0", "end")

        try:
            plotlines = self.plot_tracker.plotlines

            if not plotlines:
                self.plotlines_text.insert("1.0", "暂无情节线\n\n请在代码中使用plot_tracker创建情节线")
                return

            text = "情节线列表:\n\n"

            for plot_id, plot_data in plotlines.items():
                text += f"【{plot_data['title']}】\n"
                text += f"  ID: {plot_id}\n"
                text += f"  重要性: {plot_data['importance']}\n"
                text += f"  状态: {plot_data['status']}\n"
                text += f"  章节: {plot_data['start_chapter']}-{plot_data['expected_end_chapter']}\n"
                text += f"  描述: {plot_data['description']}\n"

                if plot_data.get('chapters'):
                    text += f"  涉及章节: {len(plot_data['chapters'])}章\n"

                text += f"\n"

            self.plotlines_text.insert("1.0", text)

        except Exception as e:
            self.log(f"刷新情节线列表失败: {e}\n")

    def generate_plot_report(self):
        """生成情节线报告"""
        if not self.plot_tracker:
            messagebox.showerror("错误", "请先初始化项目管理")
            return

        try:
            report = self.plot_tracker.generate_plot_report()

            report_text = f"""
{'='*50}
情节线报告
{'='*50}

总情节线数: {report['total_plotlines']}

状态统计:
"""
            for status, count in report['status_summary'].items():
                report_text += f"  {status}: {count}条\n"

            report_text += f"\n活跃冲突: {report['active_conflicts']}个"
            report_text += f"\n未回应伏笔: {report['unresolved_foreshadowing']}个\n"

            if report['main_plots']:
                report_text += f"\n主线情节:\n"
                for plot in report['main_plots']:
                    report_text += f"  - {plot['title']}: {plot['status']} ({plot['progress']})\n"

            report_text += f"\n{'='*50}\n"

            self.log(report_text)
            messagebox.showinfo("情节线报告", "报告已生成，请查看日志")

        except Exception as e:
            error_msg = f"生成报告失败: {str(e)}"
            self.log(f"❌ {error_msg}\n")
            messagebox.showerror("错误", error_msg)

    # ==================== 质量报告页面 ====================

    def build_quality_page(self):
        """构建质量报告页面"""
        quality_frame = self.sub_tabview.tab("质量报告")
        quality_frame.grid_columnconfigure(0, weight=1)
        quality_frame.grid_rowconfigure(0, weight=1)

        # 报告显示
        self.quality_text = ctk.CTkTextbox(quality_frame)
        self.quality_text.grid(row=0, column=0, padx=5, pady=5, sticky="nsew")

        # 刷新按钮
        ctk.CTkButton(
            quality_frame,
            text="🔍 生成质量报告",
            command=self.refresh_quality_report,
            width=200,
            height=40
        ).grid(row=1, column=0, pady=10)

    def refresh_quality_report(self):
        """刷新质量报告"""
        if not self.context_manager or not self.plot_tracker:
            self.quality_text.delete("1.0", "end")
            self.quality_text.insert("1.0", "请先初始化项目管理")
            return

        self.quality_text.delete("1.0", "end")

        try:
            # 生成一致性报告
            consistency_report = self.context_manager.generate_consistency_report()

            # 生成情节线报告
            plot_report = self.plot_tracker.generate_plot_report()

            report_text = f"""
{'='*60}
项目质量报告
{'='*60}

【一致性检查】
  总章节数: {consistency_report['total_chapters']}
  总角色数: {consistency_report['total_characters']}
  总地点数: {consistency_report['total_locations']}
  总物品数: {consistency_report['total_items']}
  未回应伏笔: {consistency_report['unresolved_foreshadowing']}

【主要角色】
"""

            for char in consistency_report['main_characters'][:10]:
                report_text += f"  - {char['name']}: 出场{char['appearances']}次 "
                report_text += f"(第{char['first_chapter']}-{char['last_chapter']}章)\n"

            if consistency_report['missing_information']:
                report_text += f"\n⚠️  缺失信息:\n"
                for info in consistency_report['missing_information'][:10]:
                    report_text += f"  - {info}\n"

            report_text += f"\n{'='*60}\n"
            report_text += f"【情节线统计】\n"
            report_text += f"  总情节线: {plot_report['total_plotlines']}\n"
            report_text += f"  活跃冲突: {plot_report['active_conflicts']}\n"
            report_text += f"  未回应伏笔: {plot_report['unresolved_foreshadowing']}\n"

            report_text += f"\n状态分布:\n"
            for status, count in plot_report['status_summary'].items():
                report_text += f"  {status}: {count}条\n"

            report_text += f"\n{'='*60}\n"

            self.quality_text.insert("1.0", report_text)
            self.log("✅ 质量报告已生成\n")

        except Exception as e:
            error_msg = f"生成质量报告失败: {str(e)}"
            self.quality_text.insert("1.0", error_msg)
            self.log(f"❌ {error_msg}\n")

    def build_visualizations_page(self):
        """构建可视化页面"""
        vis_frame = self.sub_tabview.tab("Visualizations")

        # 标题
        title_label = ctk.CTkLabel(
            vis_frame,
            text="📊 数据可视化",
            font=("Microsoft YaHei", 20, "bold")
        )
        title_label.pack(pady=10)

        # 说明文本
        info_text = """
生成各种可视化图表来分析小说的结构和质量：
• 情节线时间轴：显示所有情节线的时间分布和状态
• 角色关系图：展示角色之间的关联和互动强度
• 质量热力图：分析每章的质量指标（情节密度、角色活跃度等）
        """
        info_label = ctk.CTkLabel(
            vis_frame,
            text=info_text,
            font=("Microsoft YaHei", 11),
            justify="left"
        )
        info_label.pack(pady=5, padx=20)

        # 按钮区域
        button_frame = ctk.CTkFrame(vis_frame)
        button_frame.pack(pady=20, padx=20, fill="x")

        # 第一行按钮
        row1 = ctk.CTkFrame(button_frame)
        row1.pack(pady=5, fill="x")

        btn_timeline = ctk.CTkButton(
            row1,
            text="生成情节线时间轴",
            command=self.generate_timeline,
            font=("Microsoft YaHei", 13),
            width=200
        )
        btn_timeline.pack(side="left", padx=10)

        btn_relationship = ctk.CTkButton(
            row1,
            text="生成角色关系图",
            command=self.generate_relationship_graph,
            font=("Microsoft YaHei", 13),
            width=200
        )
        btn_relationship.pack(side="left", padx=10)

        btn_heatmap = ctk.CTkButton(
            row1,
            text="生成质量热力图",
            command=self.generate_quality_heatmap,
            font=("Microsoft YaHei", 13),
            width=200
        )
        btn_heatmap.pack(side="left", padx=10)

        # 第二行按钮
        row2 = ctk.CTkFrame(button_frame)
        row2.pack(pady=5, fill="x")

        btn_all = ctk.CTkButton(
            row2,
            text="生成全部可视化",
            command=self.generate_all_visualizations,
            font=("Microsoft YaHei", 13, "bold"),
            width=200,
            fg_color="#2E7D32"
        )
        btn_all.pack(side="left", padx=10)

        btn_open_folder = ctk.CTkButton(
            row2,
            text="打开可视化文件夹",
            command=self.open_visualizations_folder,
            font=("Microsoft YaHei", 13),
            width=200
        )
        btn_open_folder.pack(side="left", padx=10)

        # 显示区域（显示生成的图片）
        display_frame = ctk.CTkFrame(vis_frame)
        display_frame.pack(pady=10, padx=20, fill="both", expand=True)

        self.vis_status_label = ctk.CTkLabel(
            display_frame,
            text="点击上方按钮生成可视化图表\n生成的图表将保存在项目的 visualizations 文件夹中",
            font=("Microsoft YaHei", 12),
            text_color="gray"
        )
        self.vis_status_label.pack(expand=True)

    def generate_timeline(self):
        """生成情节线时间轴"""
        if not self.plot_tracker:
            self.log("❌ 请先初始化项目管理\n")
            return

        import threading

        def task():
            try:
                self.log("📊 开始生成情节线时间轴...\n")
                from visualizations import PlotlineTimeline
                from pathlib import Path
                import datetime

                output_dir = Path(self.filepath_var.get()) / "visualizations"
                output_dir.mkdir(exist_ok=True)

                filename = f"plotline_timeline_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                output_path = output_dir / filename

                viz = PlotlineTimeline(self.plot_tracker)
                viz.create_timeline(str(output_path))

                self.log(f"✅ 时间轴已生成: {filename}\n")
                self.vis_status_label.configure(
                    text=f"✅ 时间轴已生成\n{filename}"
                )
            except Exception as e:
                self.log(f"❌ 生成时间轴失败: {str(e)}\n")

        threading.Thread(target=task, daemon=True).start()

    def generate_relationship_graph(self):
        """生成角色关系图"""
        if not self.context_manager:
            self.log("❌ 请先初始化项目管理\n")
            return

        import threading

        def task():
            try:
                self.log("📊 开始生成角色关系图...\n")
                from visualizations import CharacterRelationshipGraph
                from pathlib import Path
                import datetime

                output_dir = Path(self.filepath_var.get()) / "visualizations"
                output_dir.mkdir(exist_ok=True)

                filename = f"character_relationships_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                output_path = output_dir / filename

                viz = CharacterRelationshipGraph(self.context_manager)
                viz.create_relationship_graph(str(output_path))

                self.log(f"✅ 关系图已生成: {filename}\n")
                self.vis_status_label.configure(
                    text=f"✅ 关系图已生成\n{filename}"
                )
            except Exception as e:
                self.log(f"❌ 生成关系图失败: {str(e)}\n")

        threading.Thread(target=task, daemon=True).start()

    def generate_quality_heatmap(self):
        """生成质量热力图"""
        if not self.context_manager or not self.plot_tracker:
            self.log("❌ 请先初始化项目管理\n")
            return

        import threading

        def task():
            try:
                self.log("📊 开始生成质量热力图...\n")
                from visualizations import QualityHeatmap
                from pathlib import Path
                import datetime

                output_dir = Path(self.filepath_var.get()) / "visualizations"
                output_dir.mkdir(exist_ok=True)

                filename = f"quality_heatmap_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                output_path = output_dir / filename

                viz = QualityHeatmap(self.context_manager, self.plot_tracker)
                viz.create_quality_heatmap(str(output_path))

                self.log(f"✅ 热力图已生成: {filename}\n")
                self.vis_status_label.configure(
                    text=f"✅ 热力图已生成\n{filename}"
                )
            except Exception as e:
                self.log(f"❌ 生成热力图失败: {str(e)}\n")

        threading.Thread(target=task, daemon=True).start()

    def generate_all_visualizations(self):
        """生成全部可视化"""
        if not self.context_manager or not self.plot_tracker:
            self.log("❌ 请先初始化项目管理\n")
            return

        import threading

        def task():
            try:
                self.log("📊 开始生成全部可视化...\n")
                from visualizations import generate_all_visualizations

                filepath = self.filepath_var.get()
                results = generate_all_visualizations(filepath)

                if results:
                    self.log(f"✅ 全部可视化已生成:\n")
                    for vis_type, path in results.items():
                        self.log(f"  - {vis_type}: {Path(path).name}\n")
                    self.vis_status_label.configure(
                        text=f"✅ 已生成 {len(results)} 个可视化图表"
                    )
                else:
                    self.log("⚠️ 未生成任何可视化\n")
            except Exception as e:
                self.log(f"❌ 生成可视化失败: {str(e)}\n")

        threading.Thread(target=task, daemon=True).start()

    def open_visualizations_folder(self):
        """打开可视化文件夹"""
        import os
        import platform
        from pathlib import Path

        vis_dir = Path(self.filepath_var.get()) / "visualizations"

        if not vis_dir.exists():
            vis_dir.mkdir(exist_ok=True)
            self.log("📁 已创建visualizations文件夹\n")

        # 根据操作系统打开文件夹
        try:
            if platform.system() == "Windows":
                os.startfile(vis_dir)
            elif platform.system() == "Darwin":  # macOS
                os.system(f"open '{vis_dir}'")
            else:  # Linux
                os.system(f"xdg-open '{vis_dir}'")

            self.log(f"📂 已打开文件夹: {vis_dir}\n")
        except Exception as e:
            self.log(f"❌ 打开文件夹失败: {str(e)}\n")
