# visualizations.py
# -*- coding: utf-8 -*-
"""
可视化模块
提供情节线时间轴、角色关系图、质量热力图等可视化功能
"""

import matplotlib
matplotlib.use('Agg')  # 使用非GUI后端

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, FancyArrowPatch
import numpy as np
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import json
from datetime import datetime

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

from logger_config import get_logger

logger = get_logger("Visualizations")


class PlotlineTimeline:
    """情节线时间轴可视化"""

    def __init__(self, plot_tracker):
        """
        初始化时间轴可视化

        Args:
            plot_tracker: PlotlineTracker实例
        """
        self.plot_tracker = plot_tracker
        self.colors = {
            'main': '#FF6B6B',      # 主线 - 红色
            'major': '#4ECDC4',     # 主要支线 - 青色
            'minor': '#95E1D3',     # 次要支线 - 浅青色
            'background': '#FFE66D' # 背景线 - 黄色
        }
        self.status_colors = {
            'planned': '#CCCCCC',    # 计划 - 灰色
            'active': '#4CAF50',     # 活跃 - 绿色
            'suspended': '#FFA726',  # 暂停 - 橙色
            'resolved': '#2196F3',   # 完结 - 蓝色
            'abandoned': '#757575'   # 放弃 - 深灰
        }

    def create_timeline(self, output_path: str, max_chapter: Optional[int] = None):
        """
        创建情节线时间轴图

        Args:
            output_path: 输出文件路径
            max_chapter: 最大章节数（如果不指定，自动计算）
        """
        plotlines = self.plot_tracker.plotlines

        if not plotlines:
            logger.warning("没有情节线数据，无法生成时间轴")
            return

        # 计算最大章节数
        if max_chapter is None:
            max_chapter = max(
                plot.get("expected_end_chapter", plot.get("actual_end_chapter", 10))
                for plot in plotlines.values()
            )

        # 按重要性和开始章节排序情节线
        sorted_plots = sorted(
            plotlines.values(),
            key=lambda x: (
                self._importance_order(x["importance"]),
                x["start_chapter"]
            )
        )

        # 创建图形
        fig, ax = plt.subplots(figsize=(16, max(8, len(sorted_plots) * 0.6)))

        # 绘制每条情节线
        for idx, plot in enumerate(sorted_plots):
            y_pos = len(sorted_plots) - idx - 1
            self._draw_plotline(ax, plot, y_pos, max_chapter)

        # 设置坐标轴
        ax.set_xlim(0, max_chapter + 1)
        ax.set_ylim(-1, len(sorted_plots))
        ax.set_xlabel('章节', fontsize=12, fontweight='bold')
        ax.set_title('情节线时间轴', fontsize=16, fontweight='bold', pad=20)

        # 设置y轴标签（情节线标题）
        ax.set_yticks(range(len(sorted_plots)))
        ax.set_yticklabels([
            f"{plot['title']} ({plot['importance']})"
            for plot in sorted_plots
        ])

        # 添加网格
        ax.grid(axis='x', alpha=0.3, linestyle='--')

        # 添加图例
        self._add_legend(ax)

        # 调整布局
        plt.tight_layout()

        # 保存图形
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"时间轴已保存到: {output_path}")

    def _draw_plotline(self, ax, plot: Dict, y_pos: int, max_chapter: int):
        """绘制单条情节线"""
        start = plot["start_chapter"]
        expected_end = plot["expected_end_chapter"]
        actual_end = plot.get("actual_end_chapter")
        status = plot["status"]

        # 确定结束点
        end = actual_end if actual_end else expected_end

        # 选择颜色
        importance_color = self.colors.get(plot["importance"], '#CCCCCC')
        status_color = self.status_colors.get(status, '#CCCCCC')

        # 绘制主线条
        line_width = self._get_line_width(plot["importance"])
        ax.plot([start, end], [y_pos, y_pos],
                color=importance_color,
                linewidth=line_width,
                solid_capstyle='round',
                alpha=0.7)

        # 绘制起点和终点标记
        ax.plot(start, y_pos, 'o',
                color=importance_color,
                markersize=8,
                markeredgecolor='white',
                markeredgewidth=2)

        if status == 'resolved':
            # 已完结：实心圆
            ax.plot(end, y_pos, 'o',
                    color=status_color,
                    markersize=10,
                    markeredgecolor='white',
                    markeredgewidth=2)
        elif status == 'abandoned':
            # 已放弃：叉号
            ax.plot(end, y_pos, 'x',
                    color=status_color,
                    markersize=12,
                    markeredgewidth=3)
        else:
            # 进行中或暂停：空心圆
            ax.plot(end, y_pos, 'o',
                    color='white',
                    markersize=10,
                    markeredgecolor=status_color,
                    markeredgewidth=2)

        # 绘制里程碑
        milestones = plot.get("milestones", [])
        for ms in milestones:
            ms_chapter = ms["chapter"]
            if start <= ms_chapter <= end:
                ax.plot(ms_chapter, y_pos, '^',
                        color='gold',
                        markersize=10,
                        markeredgecolor='darkgoldenrod',
                        markeredgewidth=1.5,
                        zorder=10)

        # 如果超期，添加警告标记
        if status in ['active', 'suspended'] and actual_end is None:
            current_pos = min(max_chapter, expected_end + 5)
            ax.plot(current_pos, y_pos, '!',
                    color='red',
                    markersize=15,
                    markeredgecolor='white',
                    markeredgewidth=1)

    def _importance_order(self, importance: str) -> int:
        """返回重要性的排序顺序"""
        order = {
            'main': 0,
            'major': 1,
            'minor': 2,
            'background': 3
        }
        return order.get(importance, 999)

    def _get_line_width(self, importance: str) -> float:
        """根据重要性返回线条宽度"""
        widths = {
            'main': 6,
            'major': 4,
            'minor': 3,
            'background': 2
        }
        return widths.get(importance, 2)

    def _add_legend(self, ax):
        """添加图例"""
        # 重要性图例
        importance_patches = [
            mpatches.Patch(color=self.colors['main'], label='主线'),
            mpatches.Patch(color=self.colors['major'], label='主要支线'),
            mpatches.Patch(color=self.colors['minor'], label='次要支线'),
            mpatches.Patch(color=self.colors['background'], label='背景线')
        ]

        # 状态图例
        status_elements = [
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=self.status_colors['active'],
                      markersize=8, label='进行中'),
            plt.Line2D([0], [0], marker='o', color='w',
                      markerfacecolor=self.status_colors['resolved'],
                      markersize=8, label='已完结'),
            plt.Line2D([0], [0], marker='^', color='w',
                      markerfacecolor='gold',
                      markersize=8, label='里程碑'),
            plt.Line2D([0], [0], marker='!', color='w',
                      markerfacecolor='red',
                      markersize=10, label='超期')
        ]

        # 组合图例
        all_handles = importance_patches + status_elements
        ax.legend(handles=all_handles, loc='upper left', bbox_to_anchor=(1.01, 1),
                 fontsize=10, framealpha=0.9)


class CharacterRelationshipGraph:
    """角色关系图可视化"""

    def __init__(self, context_manager):
        """
        初始化关系图可视化

        Args:
            context_manager: MultiLevelContextManager实例
        """
        self.context_manager = context_manager

    def create_relationship_graph(self, output_path: str):
        """
        创建角色关系图

        Args:
            output_path: 输出文件路径
        """
        characters = self.context_manager.global_context.get("characters", {})

        if not characters:
            logger.warning("没有角色数据，无法生成关系图")
            return

        # 创建图形
        fig, ax = plt.subplots(figsize=(14, 14))
        ax.set_aspect('equal')
        ax.axis('off')

        # 布局角色（圆形布局）
        char_list = list(characters.keys())
        n_chars = len(char_list)
        positions = self._circular_layout(n_chars)

        # 绘制关系线（基于共同出现的章节）
        self._draw_relationships(ax, char_list, characters, positions)

        # 绘制角色节点
        self._draw_characters(ax, char_list, characters, positions)

        # 设置标题
        ax.set_title('角色关系图', fontsize=18, fontweight='bold', pad=20)

        # 调整布局
        plt.tight_layout()

        # 保存图形
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"关系图已保存到: {output_path}")

    def _circular_layout(self, n: int, radius: float = 5.0) -> List[Tuple[float, float]]:
        """生成圆形布局的坐标"""
        positions = []
        for i in range(n):
            angle = 2 * np.pi * i / n - np.pi / 2  # 从顶部开始
            x = radius * np.cos(angle)
            y = radius * np.sin(angle)
            positions.append((x, y))
        return positions

    def _draw_relationships(self, ax, char_list: List[str], characters: Dict,
                          positions: List[Tuple[float, float]]):
        """绘制角色之间的关系线"""
        # 计算共同出现次数
        for i, char1 in enumerate(char_list):
            for j, char2 in enumerate(char_list):
                if i >= j:
                    continue

                # 计算共同出现的章节数
                appearances1 = set(characters[char1].get("appearances", []))
                appearances2 = set(characters[char2].get("appearances", []))
                common_chapters = len(appearances1 & appearances2)

                if common_chapters > 0:
                    # 线条宽度与共同出现次数成正比
                    line_width = min(common_chapters * 0.5, 5)
                    alpha = min(common_chapters * 0.1, 0.7)

                    x1, y1 = positions[i]
                    x2, y2 = positions[j]

                    ax.plot([x1, x2], [y1, y2],
                           color='#BDBDBD',
                           linewidth=line_width,
                           alpha=alpha,
                           zorder=1)

    def _draw_characters(self, ax, char_list: List[str], characters: Dict,
                        positions: List[Tuple[float, float]]):
        """绘制角色节点"""
        # 颜色方案
        colors = plt.cm.Set3(np.linspace(0, 1, len(char_list)))

        for idx, (char_name, (x, y)) in enumerate(zip(char_list, positions)):
            char_data = characters[char_name]
            n_appearances = len(char_data.get("appearances", []))

            # 节点大小与出现次数成正比
            node_size = min(500 + n_appearances * 50, 2000)

            # 绘制圆形节点
            circle = Circle((x, y), radius=np.sqrt(node_size) / 50,
                          facecolor=colors[idx],
                          edgecolor='white',
                          linewidth=3,
                          zorder=10,
                          alpha=0.9)
            ax.add_patch(circle)

            # 添加角色名称
            ax.text(x, y, char_name,
                   ha='center', va='center',
                   fontsize=10,
                   fontweight='bold',
                   zorder=11)

            # 添加出现次数标签
            ax.text(x, y - np.sqrt(node_size) / 50 - 0.3,
                   f'{n_appearances}章',
                   ha='center', va='top',
                   fontsize=8,
                   color='#666666',
                   zorder=11)

        # 设置坐标范围
        ax.set_xlim(-7, 7)
        ax.set_ylim(-7, 7)


class QualityHeatmap:
    """质量分析热力图"""

    def __init__(self, context_manager, plot_tracker):
        """
        初始化热力图可视化

        Args:
            context_manager: MultiLevelContextManager实例
            plot_tracker: PlotlineTracker实例
        """
        self.context_manager = context_manager
        self.plot_tracker = plot_tracker

    def create_quality_heatmap(self, output_path: str, max_chapter: Optional[int] = None):
        """
        创建质量分析热力图

        Args:
            output_path: 输出文件路径
            max_chapter: 最大章节数
        """
        # 获取章节列表
        chapter_summaries = self.context_manager.chapter_contexts
        if not chapter_summaries:
            logger.warning("没有章节数据，无法生成热力图")
            return

        if max_chapter is None:
            max_chapter = max(chapter_summaries.keys())

        # 准备数据矩阵（5个维度 x 章节数）
        metrics = ['情节密度', '角色活跃度', '地点多样性', '冲突强度', '整体质量']
        data_matrix = np.zeros((len(metrics), max_chapter))

        for chapter_num in range(1, max_chapter + 1):
            scores = self._calculate_chapter_metrics(chapter_num)
            for i, metric in enumerate(metrics):
                data_matrix[i, chapter_num - 1] = scores.get(metric, 0)

        # 创建图形
        fig, ax = plt.subplots(figsize=(max(12, max_chapter * 0.4), 6))

        # 绘制热力图
        im = ax.imshow(data_matrix, cmap='RdYlGn', aspect='auto',
                      vmin=0, vmax=10, interpolation='nearest')

        # 设置坐标轴
        ax.set_xticks(range(max_chapter))
        ax.set_xticklabels(range(1, max_chapter + 1))
        ax.set_yticks(range(len(metrics)))
        ax.set_yticklabels(metrics)

        ax.set_xlabel('章节', fontsize=12, fontweight='bold')
        ax.set_title('章节质量热力图', fontsize=16, fontweight='bold', pad=20)

        # 添加颜色条
        cbar = plt.colorbar(im, ax=ax)
        cbar.set_label('评分 (0-10)', rotation=270, labelpad=20)

        # 在单元格中显示数值
        for i in range(len(metrics)):
            for j in range(max_chapter):
                value = data_matrix[i, j]
                if value > 0:  # 只显示有数据的单元格
                    text_color = 'white' if value < 5 else 'black'
                    ax.text(j, i, f'{value:.1f}',
                           ha='center', va='center',
                           color=text_color,
                           fontsize=8)

        # 调整布局
        plt.tight_layout()

        # 保存图形
        plt.savefig(output_path, dpi=150, bbox_inches='tight')
        plt.close()

        logger.info(f"热力图已保存到: {output_path}")

    def _calculate_chapter_metrics(self, chapter_num: int) -> Dict[str, float]:
        """
        计算章节的各项质量指标

        Args:
            chapter_num: 章节号

        Returns:
            质量指标字典
        """
        scores = {}

        # 1. 情节密度（该章涉及的情节线数量）
        chapter_plots = self.plot_tracker.get_chapter_plots(chapter_num)
        scores['情节密度'] = min(len(chapter_plots) * 2, 10)

        # 2. 角色活跃度（该章出现的角色数量）
        chapter_data = self.context_manager.chapter_contexts.get(chapter_num, {})
        characters = chapter_data.get("characters", [])
        scores['角色活跃度'] = min(len(characters) * 1.5, 10)

        # 3. 地点多样性（该章出现的地点数量）
        locations = chapter_data.get("locations", [])
        scores['地点多样性'] = min(len(locations) * 2.5, 10)

        # 4. 冲突强度（该章涉及的冲突数量）
        conflicts = 0
        for plot in chapter_plots:
            conflicts += len([c for c in plot.get("conflicts", [])
                            if c.get("chapter") == chapter_num])
        scores['冲突强度'] = min(conflicts * 3, 10)

        # 5. 整体质量（平均分）
        if scores:
            scores['整体质量'] = np.mean([
                scores.get('情节密度', 0),
                scores.get('角色活跃度', 0),
                scores.get('地点多样性', 0),
                scores.get('冲突强度', 0)
            ])

        return scores


def generate_all_visualizations(
    filepath: str,
    output_dir: Optional[str] = None
) -> Dict[str, str]:
    """
    生成所有可视化图表

    Args:
        filepath: 项目路径
        output_dir: 输出目录（如果不指定，使用filepath/visualizations）

    Returns:
        生成的文件路径字典
    """
    from context_manager import create_context_manager
    from plot_tracker import create_plot_tracker

    # 设置输出目录
    if output_dir is None:
        output_dir = Path(filepath) / "visualizations"
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(exist_ok=True)

    results = {}

    try:
        # 加载系统
        context_manager = create_context_manager(filepath)
        plot_tracker = create_plot_tracker(filepath)

        # 1. 生成情节线时间轴
        timeline_path = output_dir / f"plotline_timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        timeline_viz = PlotlineTimeline(plot_tracker)
        timeline_viz.create_timeline(str(timeline_path))
        results['timeline'] = str(timeline_path)

        # 2. 生成角色关系图
        relationship_path = output_dir / f"character_relationships_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        relationship_viz = CharacterRelationshipGraph(context_manager)
        relationship_viz.create_relationship_graph(str(relationship_path))
        results['relationships'] = str(relationship_path)

        # 3. 生成质量热力图
        heatmap_path = output_dir / f"quality_heatmap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        heatmap_viz = QualityHeatmap(context_manager, plot_tracker)
        heatmap_viz.create_quality_heatmap(str(heatmap_path))
        results['heatmap'] = str(heatmap_path)

        logger.info(f"所有可视化已生成到: {output_dir}")
    except Exception as e:
        logger.error(f"生成可视化时出错: {e}")

    return results


if __name__ == "__main__":
    # 测试代码
    # generate_all_visualizations("./test_novel")
    pass
