# plot_tracker.py
# -*- coding: utf-8 -*-
"""
情节线索追踪系统
管理多条平行情节线，确保每条线索都有完整的发展和收尾
"""

import json
from typing import Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime
from enum import Enum
from logger_config import get_logger

logger = get_logger("PlotTracker")


class PlotStatus(Enum):
    """情节状态"""
    PLANNED = "planned"         # 已计划
    ACTIVE = "active"           # 进行中
    SUSPENDED = "suspended"     # 暂停
    RESOLVED = "resolved"       # 已解决
    ABANDONED = "abandoned"     # 已放弃


class PlotImportance(Enum):
    """情节重要性"""
    MAIN = "main"              # 主线
    MAJOR = "major"            # 主要支线
    MINOR = "minor"            # 次要支线
    BACKGROUND = "background"  # 背景线


class PlotlineTracker:
    """情节线追踪器"""

    def __init__(self, filepath: str):
        """
        初始化情节追踪器

        Args:
            filepath: 小说项目目录
        """
        self.filepath = Path(filepath)
        self.plot_file = self.filepath / "plotlines.json"

        # 加载或初始化情节数据
        self.plotlines: Dict[str, Dict] = {}
        self.load()

    def load(self):
        """从文件加载情节数据"""
        if self.plot_file.exists():
            try:
                with open(self.plot_file, 'r', encoding='utf-8') as f:
                    self.plotlines = json.load(f)
                logger.info(f"加载情节数据: {len(self.plotlines)} 条情节线")
            except Exception as e:
                logger.error(f"加载情节数据失败: {e}")
                self.plotlines = {}
        else:
            self.plotlines = {}

    def save(self):
        """保存情节数据到文件"""
        try:
            with open(self.plot_file, 'w', encoding='utf-8') as f:
                json.dump(self.plotlines, f, ensure_ascii=False, indent=2)
            logger.info("保存情节数据")
        except Exception as e:
            logger.error(f"保存情节数据失败: {e}")

    def create_plotline(
        self,
        plot_id: str,
        title: str,
        description: str,
        importance: PlotImportance,
        start_chapter: int,
        expected_end_chapter: int,
        related_characters: List[str] = None,
        related_locations: List[str] = None,
        parent_plot: Optional[str] = None
    ):
        """
        创建新的情节线

        Args:
            plot_id: 情节ID
            title: 标题
            description: 描述
            importance: 重要性
            start_chapter: 起始章节
            expected_end_chapter: 预期结束章节
            related_characters: 相关角色
            related_locations: 相关地点
            parent_plot: 父情节线ID（如果是子线）
        """
        if plot_id in self.plotlines:
            logger.warning(f"情节线已存在: {plot_id}")
            return

        self.plotlines[plot_id] = {
            "plot_id": plot_id,
            "title": title,
            "description": description,
            "importance": importance.value,
            "status": PlotStatus.PLANNED.value,
            "start_chapter": start_chapter,
            "expected_end_chapter": expected_end_chapter,
            "actual_end_chapter": None,
            "related_characters": related_characters or [],
            "related_locations": related_locations or [],
            "parent_plot": parent_plot,
            "child_plots": [],
            "milestones": [],  # 里程碑事件
            "chapters": [],    # 涉及的章节
            "conflicts": [],   # 冲突点
            "resolutions": [], # 解决方案
            "foreshadowing": [],  # 伏笔
            "callbacks": [],      # 回应
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        # 如果有父情节，添加到父情节的子线列表
        if parent_plot and parent_plot in self.plotlines:
            self.plotlines[parent_plot]["child_plots"].append(plot_id)

        self.save()
        logger.info(f"创建情节线: {plot_id} - {title}")

    def update_plotline(self, plot_id: str, **kwargs):
        """更新情节线信息"""
        if plot_id not in self.plotlines:
            logger.error(f"情节线不存在: {plot_id}")
            return

        for key, value in kwargs.items():
            if key in self.plotlines[plot_id]:
                self.plotlines[plot_id][key] = value

        self.plotlines[plot_id]["updated_at"] = datetime.now().isoformat()
        self.save()
        logger.info(f"更新情节线: {plot_id}")

    def add_milestone(self, plot_id: str, chapter: int, event: str, significance: str):
        """
        添加情节里程碑

        Args:
            plot_id: 情节ID
            chapter: 章节号
            event: 事件描述
            significance: 重要性说明
        """
        if plot_id not in self.plotlines:
            logger.error(f"情节线不存在: {plot_id}")
            return

        milestone = {
            "chapter": chapter,
            "event": event,
            "significance": significance,
            "added_at": datetime.now().isoformat()
        }

        self.plotlines[plot_id]["milestones"].append(milestone)
        if chapter not in self.plotlines[plot_id]["chapters"]:
            self.plotlines[plot_id]["chapters"].append(chapter)

        self.save()
        logger.info(f"添加里程碑: {plot_id} - 第{chapter}章")

    def record_chapter_plot(self, plot_id: str, chapter: int, development: str):
        """
        记录情节在某章的发展

        Args:
            plot_id: 情节ID
            chapter: 章节号
            development: 发展描述
        """
        if plot_id not in self.plotlines:
            logger.error(f"情节线不存在: {plot_id}")
            return

        if chapter not in self.plotlines[plot_id]["chapters"]:
            self.plotlines[plot_id]["chapters"].append(chapter)
            self.plotlines[plot_id]["chapters"].sort()

        # 记录发展
        if "developments" not in self.plotlines[plot_id]:
            self.plotlines[plot_id]["developments"] = {}

        self.plotlines[plot_id]["developments"][str(chapter)] = {
            "description": development,
            "recorded_at": datetime.now().isoformat()
        }

        self.save()

    def activate_plotline(self, plot_id: str, chapter: int):
        """激活情节线"""
        self.update_plotline(
            plot_id,
            status=PlotStatus.ACTIVE.value,
            actual_start_chapter=chapter
        )
        logger.info(f"激活情节线: {plot_id} 在第{chapter}章")

    def suspend_plotline(self, plot_id: str, chapter: int, reason: str = ""):
        """暂停情节线"""
        self.update_plotline(
            plot_id,
            status=PlotStatus.SUSPENDED.value,
            suspended_at_chapter=chapter,
            suspension_reason=reason
        )
        logger.info(f"暂停情节线: {plot_id} 在第{chapter}章")

    def resolve_plotline(self, plot_id: str, chapter: int, resolution: str):
        """
        解决/完结情节线

        Args:
            plot_id: 情节ID
            chapter: 完结章节
            resolution: 解决方式
        """
        self.plotlines[plot_id]["resolutions"].append({
            "chapter": chapter,
            "resolution": resolution,
            "resolved_at": datetime.now().isoformat()
        })

        self.update_plotline(
            plot_id,
            status=PlotStatus.RESOLVED.value,
            actual_end_chapter=chapter
        )

        logger.info(f"完结情节线: {plot_id} 在第{chapter}章")

    def get_active_plots(self, chapter: int = None) -> List[Dict]:
        """
        获取活跃的情节线

        Args:
            chapter: 如果指定，返回该章节活跃的情节线

        Returns:
            情节线列表
        """
        active_plots = []

        for plot_id, plot in self.plotlines.items():
            if plot["status"] == PlotStatus.ACTIVE.value:
                if chapter is None:
                    active_plots.append(plot)
                else:
                    # 检查是否在该章节活跃
                    start = plot.get("actual_start_chapter", plot["start_chapter"])
                    end = plot.get("actual_end_chapter", plot["expected_end_chapter"])
                    if start <= chapter <= end:
                        active_plots.append(plot)

        return active_plots

    def get_plotline_status_summary(self) -> Dict[str, int]:
        """获取情节状态统计"""
        summary = {status.value: 0 for status in PlotStatus}

        for plot in self.plotlines.values():
            status = plot["status"]
            summary[status] = summary.get(status, 0) + 1

        return summary

    def get_unresolved_plots(self, current_chapter: int) -> List[Dict]:
        """
        获取应该但尚未解决的情节线

        Args:
            current_chapter: 当前章节号

        Returns:
            超期未解决的情节线列表
        """
        unresolved = []

        for plot in self.plotlines.values():
            if plot["status"] in [PlotStatus.ACTIVE.value, PlotStatus.SUSPENDED.value]:
                expected_end = plot["expected_end_chapter"]
                if current_chapter > expected_end:
                    unresolved.append({
                        "plot_id": plot["plot_id"],
                        "title": plot["title"],
                        "expected_end": expected_end,
                        "overdue_chapters": current_chapter - expected_end
                    })

        return unresolved

    def get_chapter_plots(self, chapter: int) -> List[Dict]:
        """获取某章涉及的所有情节线"""
        chapter_plots = []

        for plot in self.plotlines.values():
            if chapter in plot["chapters"]:
                chapter_plots.append(plot)

        return chapter_plots

    def build_plot_context(self, chapter: int) -> str:
        """
        构建当前章节的情节上下文

        Args:
            chapter: 章节号

        Returns:
            格式化的情节上下文
        """
        context_parts = []

        # 1. 活跃的主线情节
        active_main = [
            p for p in self.get_active_plots(chapter)
            if p["importance"] in [PlotImportance.MAIN.value, PlotImportance.MAJOR.value]
        ]

        if active_main:
            context_parts.append("【活跃情节线】")
            for plot in active_main:
                context_parts.append(f"\n情节: {plot['title']}")
                context_parts.append(f"描述: {plot['description']}")

                # 最近的发展
                developments = plot.get("developments", {})
                recent_chapters = [c for c in plot["chapters"] if c < chapter][-3:]
                if recent_chapters:
                    context_parts.append("近期发展:")
                    for ch in recent_chapters:
                        if str(ch) in developments:
                            context_parts.append(f"  第{ch}章: {developments[str(ch)]['description']}")

                # 未完成的冲突
                unresolved_conflicts = [
                    c for c in plot.get("conflicts", [])
                    if c.get("resolved") is not True
                ]
                if unresolved_conflicts:
                    context_parts.append(f"待解决冲突: {len(unresolved_conflicts)}个")

        # 2. 未回应的伏笔
        all_foreshadowing = []
        for plot in self.plotlines.values():
            for fs in plot.get("foreshadowing", []):
                if not fs.get("resolved"):
                    all_foreshadowing.append(f"{plot['title']}: {fs.get('content', '')}")

        if all_foreshadowing:
            context_parts.append("\n【未回应的伏笔】")
            for fs in all_foreshadowing[:5]:  # 最多显示5个
                context_parts.append(f"- {fs}")

        # 3. 即将到来的里程碑
        upcoming_milestones = []
        for plot in active_main:
            for milestone in plot.get("milestones", []):
                if milestone["chapter"] >= chapter:
                    upcoming_milestones.append(
                        f"第{milestone['chapter']}章: {milestone['event']}"
                    )

        if upcoming_milestones:
            context_parts.append("\n【即将到来的事件】")
            for ms in sorted(upcoming_milestones)[:3]:
                context_parts.append(f"- {ms}")

        return "\n".join(context_parts)

    def generate_plot_report(self) -> Dict:
        """生成情节线报告"""
        report = {
            "total_plotlines": len(self.plotlines),
            "status_summary": self.get_plotline_status_summary(),
            "main_plots": [],
            "active_conflicts": 0,
            "unresolved_foreshadowing": 0
        }

        # 统计主线情节
        for plot in self.plotlines.values():
            if plot["importance"] == PlotImportance.MAIN.value:
                report["main_plots"].append({
                    "title": plot["title"],
                    "status": plot["status"],
                    "progress": f"{len(plot['chapters'])} 章"
                })

            # 统计冲突和伏笔
            report["active_conflicts"] += len([
                c for c in plot.get("conflicts", [])
                if not c.get("resolved")
            ])
            report["unresolved_foreshadowing"] += len([
                f for f in plot.get("foreshadowing", [])
                if not f.get("resolved")
            ])

        return report


# 便捷函数
def create_plot_tracker(filepath: str) -> PlotlineTracker:
    """创建情节追踪器实例"""
    return PlotlineTracker(filepath)


if __name__ == "__main__":
    # 测试代码
    tracker = create_plot_tracker("./test_novel")

    # 创建主线情节
    tracker.create_plotline(
        "main_quest",
        "主角的成长之路",
        "主角从普通人成长为强者的历程",
        PlotImportance.MAIN,
        1,
        100,
        related_characters=["主角", "导师"],
        related_locations=["魔法学院", "试炼之地"]
    )

    # 创建支线情节
    tracker.create_plotline(
        "romance_subplot",
        "爱情线",
        "主角与女主角的感情发展",
        PlotImportance.MAJOR,
        5,
        80,
        related_characters=["主角", "女主角"],
        parent_plot="main_quest"
    )

    # 激活主线
    tracker.activate_plotline("main_quest", 1)

    # 添加里程碑
    tracker.add_milestone(
        "main_quest",
        10,
        "主角觉醒特殊能力",
        "转折点，开启新的修炼方向"
    )

    # 记录章节发展
    tracker.record_chapter_plot(
        "main_quest",
        5,
        "主角在试炼中遭遇强敌，险些丧命"
    )

    # 构建上下文
    context = tracker.build_plot_context(6)
    print(context)

    # 生成报告
    report = tracker.generate_plot_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
