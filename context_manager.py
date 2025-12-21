# context_manager.py
# -*- coding: utf-8 -*-
"""
增强的上下文管理系统
实现多层次、多维度的小说上下文追踪，确保长篇小说的连续性
"""

import json
import os
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from logger_config import get_logger

logger = get_logger("ContextManager")


class MultiLevelContextManager:
    """
    多层次上下文管理器

    管理5个层次的上下文：
    1. 全局层：整体世界观、核心设定
    2. 卷/部层：大的故事阶段
    3. 章节层：单个章节的内容
    4. 场景层：具体场景细节
    5. 实体层：角色、物品、地点等
    """

    def __init__(self, filepath: str):
        """
        初始化上下文管理器

        Args:
            filepath: 小说项目目录
        """
        self.filepath = Path(filepath)
        self.context_dir = self.filepath / "context_data"
        self.context_dir.mkdir(exist_ok=True)

        # 上下文文件路径
        self.global_context_file = self.context_dir / "global_context.json"
        self.volume_context_file = self.context_dir / "volume_contexts.json"
        self.chapter_context_file = self.context_dir / "chapter_contexts.json"
        self.scene_context_file = self.context_dir / "scene_contexts.json"
        self.entity_context_file = self.context_dir / "entity_contexts.json"

        # 初始化上下文
        self.global_context = self._load_or_init(self.global_context_file, self._init_global)
        self.volume_contexts = self._load_or_init(self.volume_context_file, dict)
        self.chapter_contexts = self._load_or_init(self.chapter_context_file, dict)
        self.scene_contexts = self._load_or_init(self.scene_context_file, dict)
        self.entity_contexts = self._load_or_init(self.entity_context_file, self._init_entities)

    def _load_or_init(self, filepath: Path, init_func):
        """加载或初始化上下文数据"""
        if filepath.exists():
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载上下文失败 {filepath}: {e}")
        return init_func()

    def _init_global(self) -> Dict:
        """初始化全局上下文"""
        return {
            "world_setting": {},  # 世界观设定
            "core_rules": [],     # 核心规则
            "main_conflicts": [], # 主要冲突
            "themes": [],         # 主题
            "tone": "",           # 基调
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

    def _init_entities(self) -> Dict:
        """初始化实体上下文"""
        return {
            "characters": {},  # 角色
            "locations": {},   # 地点
            "items": {},       # 物品
            "organizations": {} # 组织
        }

    def _save_context(self, filepath: Path, data: Any):
        """保存上下文到文件"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"保存上下文: {filepath}")
        except Exception as e:
            logger.error(f"保存上下文失败 {filepath}: {e}")

    # ==================== 全局层 ====================

    def update_global_context(self, **kwargs):
        """更新全局上下文"""
        for key, value in kwargs.items():
            if key in self.global_context:
                self.global_context[key] = value
        self.global_context["updated_at"] = datetime.now().isoformat()
        self._save_context(self.global_context_file, self.global_context)
        logger.info("更新全局上下文")

    def get_global_context(self) -> Dict:
        """获取全局上下文"""
        return self.global_context

    # ==================== 卷/部层 ====================

    def create_volume(self, volume_id: str, title: str, summary: str,
                     chapters_range: tuple, main_plot: str):
        """
        创建卷/部上下文

        Args:
            volume_id: 卷ID（如 "volume_1"）
            title: 卷标题
            summary: 卷摘要
            chapters_range: 章节范围 (start, end)
            main_plot: 主要情节
        """
        self.volume_contexts[volume_id] = {
            "title": title,
            "summary": summary,
            "chapters_range": chapters_range,
            "main_plot": main_plot,
            "key_events": [],
            "character_developments": {},
            "unresolved_mysteries": [],
            "created_at": datetime.now().isoformat()
        }
        self._save_context(self.volume_context_file, self.volume_contexts)
        logger.info(f"创建卷上下文: {volume_id}")

    def update_volume(self, volume_id: str, **kwargs):
        """更新卷上下文"""
        if volume_id in self.volume_contexts:
            for key, value in kwargs.items():
                if key in self.volume_contexts[volume_id]:
                    self.volume_contexts[volume_id][key] = value
            self._save_context(self.volume_context_file, self.volume_contexts)
            logger.info(f"更新卷上下文: {volume_id}")

    def get_volume_context(self, chapter_number: int) -> Optional[Dict]:
        """根据章节号获取所属卷的上下文"""
        for volume_id, volume in self.volume_contexts.items():
            start, end = volume["chapters_range"]
            if start <= chapter_number <= end:
                return volume
        return None

    # ==================== 章节层 ====================

    def add_chapter_context(self, chapter_number: int,
                           summary: str,
                           key_events: List[str],
                           character_states: Dict[str, str],
                           location: str,
                           time_span: str,
                           mood: str,
                           foreshadowing: List[str] = None,
                           callbacks: List[str] = None):
        """
        添加章节上下文

        Args:
            chapter_number: 章节号
            summary: 章节摘要
            key_events: 关键事件列表
            character_states: 角色状态字典
            location: 主要地点
            time_span: 时间跨度
            mood: 情绪基调
            foreshadowing: 埋下的伏笔
            callbacks: 回应的伏笔
        """
        chapter_id = f"chapter_{chapter_number}"
        self.chapter_contexts[chapter_id] = {
            "chapter_number": chapter_number,
            "summary": summary,
            "key_events": key_events,
            "character_states": character_states,
            "location": location,
            "time_span": time_span,
            "mood": mood,
            "foreshadowing": foreshadowing or [],
            "callbacks": callbacks or [],
            "created_at": datetime.now().isoformat()
        }
        self._save_context(self.chapter_context_file, self.chapter_contexts)
        logger.info(f"添加章节上下文: chapter_{chapter_number}")

    def get_chapter_context(self, chapter_number: int) -> Optional[Dict]:
        """获取章节上下文"""
        chapter_id = f"chapter_{chapter_number}"
        return self.chapter_contexts.get(chapter_id)

    def get_recent_chapters_context(self, current_chapter: int, n: int = 5) -> List[Dict]:
        """获取最近N章的上下文"""
        contexts = []
        for i in range(max(1, current_chapter - n), current_chapter):
            context = self.get_chapter_context(i)
            if context:
                contexts.append(context)
        return contexts

    # ==================== 场景层 ====================

    def add_scene_context(self, chapter_number: int, scene_number: int,
                         location: str,
                         characters: List[str],
                         action: str,
                         emotion: str,
                         details: Dict[str, Any] = None):
        """
        添加场景上下文

        Args:
            chapter_number: 章节号
            scene_number: 场景号
            location: 地点
            characters: 出场角色
            action: 主要动作
            emotion: 情感基调
            details: 其他细节
        """
        scene_id = f"chapter_{chapter_number}_scene_{scene_number}"
        self.scene_contexts[scene_id] = {
            "chapter_number": chapter_number,
            "scene_number": scene_number,
            "location": location,
            "characters": characters,
            "action": action,
            "emotion": emotion,
            "details": details or {},
            "created_at": datetime.now().isoformat()
        }
        self._save_context(self.scene_context_file, self.scene_contexts)

    # ==================== 实体层 ====================

    def update_character(self, name: str, **attributes):
        """
        更新角色信息

        可更新属性:
        - description: 描述
        - personality: 性格
        - abilities: 能力
        - relationships: 关系
        - current_state: 当前状态
        - location: 当前位置
        - goals: 目标
        - secrets: 秘密
        """
        if name not in self.entity_contexts["characters"]:
            self.entity_contexts["characters"][name] = {
                "name": name,
                "first_appearance": None,
                "last_appearance": None,
                "appearance_count": 0,
                "created_at": datetime.now().isoformat()
            }

        for key, value in attributes.items():
            self.entity_contexts["characters"][name][key] = value

        self.entity_contexts["characters"][name]["updated_at"] = datetime.now().isoformat()
        self._save_context(self.entity_context_file, self.entity_contexts)
        logger.info(f"更新角色: {name}")

    def record_character_appearance(self, name: str, chapter_number: int):
        """记录角色出场"""
        if name not in self.entity_contexts["characters"]:
            self.update_character(name)

        char = self.entity_contexts["characters"][name]
        if char["first_appearance"] is None:
            char["first_appearance"] = chapter_number
        char["last_appearance"] = chapter_number
        char["appearance_count"] = char.get("appearance_count", 0) + 1

        self._save_context(self.entity_context_file, self.entity_contexts)

    def get_character(self, name: str) -> Optional[Dict]:
        """获取角色信息"""
        return self.entity_contexts["characters"].get(name)

    def get_all_characters(self) -> Dict[str, Dict]:
        """获取所有角色"""
        return self.entity_contexts["characters"]

    def update_location(self, name: str, **attributes):
        """
        更新地点信息

        可更新属性:
        - description: 描述
        - type: 类型（城市、建筑、自然等）
        - features: 特征
        - atmosphere: 氛围
        - importance: 重要性
        """
        if name not in self.entity_contexts["locations"]:
            self.entity_contexts["locations"][name] = {
                "name": name,
                "first_mentioned": None,
                "created_at": datetime.now().isoformat()
            }

        for key, value in attributes.items():
            self.entity_contexts["locations"][name][key] = value

        self._save_context(self.entity_context_file, self.entity_contexts)

    def update_item(self, name: str, **attributes):
        """
        更新物品信息

        可更新属性:
        - description: 描述
        - owner: 当前持有者
        - properties: 属性
        - significance: 重要性
        """
        if name not in self.entity_contexts["items"]:
            self.entity_contexts["items"][name] = {
                "name": name,
                "first_mentioned": None,
                "created_at": datetime.now().isoformat()
            }

        for key, value in attributes.items():
            self.entity_contexts["items"][name][key] = value

        self._save_context(self.entity_context_file, self.entity_contexts)

    # ==================== 上下文检索 ====================

    def build_context_for_chapter(self, chapter_number: int) -> str:
        """
        构建章节生成所需的完整上下文

        Args:
            chapter_number: 当前章节号

        Returns:
            格式化的上下文字符串
        """
        context_parts = []

        # 1. 全局上下文
        context_parts.append("【全局设定】")
        global_ctx = self.get_global_context()
        if global_ctx.get("world_setting"):
            context_parts.append(f"世界观: {json.dumps(global_ctx['world_setting'], ensure_ascii=False)}")
        if global_ctx.get("core_rules"):
            context_parts.append(f"核心规则: {', '.join(global_ctx['core_rules'])}")
        if global_ctx.get("themes"):
            context_parts.append(f"主题: {', '.join(global_ctx['themes'])}")

        # 2. 卷上下文
        volume_ctx = self.get_volume_context(chapter_number)
        if volume_ctx:
            context_parts.append(f"\n【当前卷：{volume_ctx['title']}】")
            context_parts.append(f"卷摘要: {volume_ctx['summary']}")
            context_parts.append(f"主要情节: {volume_ctx['main_plot']}")
            if volume_ctx.get("unresolved_mysteries"):
                context_parts.append(f"未解之谜: {', '.join(volume_ctx['unresolved_mysteries'])}")

        # 3. 近期章节上下文
        recent_contexts = self.get_recent_chapters_context(chapter_number, n=3)
        if recent_contexts:
            context_parts.append("\n【近期章节回顾】")
            for ctx in recent_contexts:
                context_parts.append(
                    f"第{ctx['chapter_number']}章: {ctx['summary']}"
                )
                if ctx.get("foreshadowing"):
                    context_parts.append(f"  伏笔: {', '.join(ctx['foreshadowing'])}")

        # 4. 主要角色当前状态
        main_characters = [
            char for char in self.entity_contexts["characters"].values()
            if char.get("importance") == "main" or char.get("appearance_count", 0) > 5
        ]
        if main_characters:
            context_parts.append("\n【主要角色状态】")
            for char in main_characters[:5]:  # 最多5个
                context_parts.append(f"{char['name']}: {char.get('current_state', '未知')}")
                if char.get("location"):
                    context_parts.append(f"  位置: {char['location']}")

        return "\n".join(context_parts)

    def get_unresolved_foreshadowing(self) -> List[Dict]:
        """获取所有未回应的伏笔"""
        all_foreshadowing = []
        all_callbacks = set()

        # 收集所有伏笔和回应
        for chapter_id, ctx in self.chapter_contexts.items():
            for fs in ctx.get("foreshadowing", []):
                all_foreshadowing.append({
                    "chapter": ctx["chapter_number"],
                    "content": fs
                })
            for cb in ctx.get("callbacks", []):
                all_callbacks.add(cb)

        # 找出未回应的伏笔
        unresolved = [
            fs for fs in all_foreshadowing
            if fs["content"] not in all_callbacks
        ]

        return unresolved

    # ==================== 分析和报告 ====================

    def generate_consistency_report(self) -> Dict[str, Any]:
        """生成一致性报告"""
        report = {
            "total_chapters": len(self.chapter_contexts),
            "total_characters": len(self.entity_contexts["characters"]),
            "total_locations": len(self.entity_contexts["locations"]),
            "total_items": len(self.entity_contexts["items"]),
            "unresolved_foreshadowing": len(self.get_unresolved_foreshadowing()),
            "main_characters": [],
            "missing_information": []
        }

        # 分析主要角色
        for name, char in self.entity_contexts["characters"].items():
            if char.get("appearance_count", 0) > 5:
                report["main_characters"].append({
                    "name": name,
                    "appearances": char.get("appearance_count", 0),
                    "first_chapter": char.get("first_appearance"),
                    "last_chapter": char.get("last_appearance")
                })

        # 检查缺失信息
        for name, char in self.entity_contexts["characters"].items():
            if char.get("appearance_count", 0) > 3:
                if not char.get("description"):
                    report["missing_information"].append(f"角色 {name} 缺少描述")
                if not char.get("personality"):
                    report["missing_information"].append(f"角色 {name} 缺少性格设定")

        return report


# 便捷函数
def create_context_manager(filepath: str) -> MultiLevelContextManager:
    """创建上下文管理器实例"""
    return MultiLevelContextManager(filepath)


if __name__ == "__main__":
    # 测试代码
    manager = create_context_manager("./test_novel")

    # 设置全局上下文
    manager.update_global_context(
        world_setting={"type": "魔法世界", "tech_level": "中世纪"},
        themes=["成长", "友情", "冒险"],
        tone="轻松幽默"
    )

    # 创建卷
    manager.create_volume(
        "volume_1",
        "起始之章",
        "主角的冒险开始",
        (1, 20),
        "主角获得神秘力量并开始修炼"
    )

    # 添加章节上下文
    manager.add_chapter_context(
        1,
        "主角意外穿越到异世界",
        ["穿越事件", "遇到导师"],
        {"主角": "震惊、困惑", "导师": "神秘、友善"},
        "魔法学院",
        "一天",
        "紧张但充满希望",
        foreshadowing=["导师提到的预言"]
    )

    # 更新角色
    manager.update_character(
        "主角",
        description="17岁少年，黑发黑眼",
        personality="善良、勇敢、好奇",
        importance="main",
        current_state="刚穿越，正在适应",
        location="魔法学院"
    )

    # 构建上下文
    context = manager.build_context_for_chapter(2)
    print(context)

    # 生成报告
    report = manager.generate_consistency_report()
    print(json.dumps(report, ensure_ascii=False, indent=2))
