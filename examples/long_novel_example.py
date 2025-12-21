#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
长篇小说生成完整示例
演示如何使用增强系统生成100章连贯小说
"""

import json
from pathlib import Path

# 导入增强系统
from context_manager import create_context_manager
from plot_tracker import create_plot_tracker, PlotImportance
from logger_config import setup_logger

# 导入原有系统
from novel_generator import (
    Novel_architecture_generate,
    Chapter_blueprint_generate,
    generate_chapter_draft,
    finalize_chapter
)
from llm_adapters import create_llm_adapter

# 设置日志
logger = setup_logger("LongNovelExample", log_dir="./logs")


class EnhancedNovelGenerator:
    """增强的小说生成器，整合所有系统"""

    def __init__(self, project_name: str, llm_config: dict, novel_config: dict):
        """
        初始化增强生成器

        Args:
            project_name: 项目名称
            llm_config: LLM配置
            novel_config: 小说配置
        """
        self.project_name = project_name
        self.output_dir = Path(f"./{project_name}")
        self.output_dir.mkdir(exist_ok=True)

        # 创建LLM适配器
        self.llm = create_llm_adapter(**llm_config)

        # 小说配置
        self.config = novel_config

        # 初始化增强系统
        self.context_manager = create_context_manager(str(self.output_dir))
        self.plot_tracker = create_plot_tracker(str(self.output_dir))

        logger.info(f"初始化项目: {project_name}")

    def setup_project(self, volumes: list, plotlines: list, characters: list):
        """
        设置项目结构

        Args:
            volumes: 卷列表
            plotlines: 情节线列表
            characters: 角色列表
        """
        logger.info("设置项目结构...")

        # 1. 设置全局上下文
        self.context_manager.update_global_context(
            world_setting=self.config.get("world_setting", {}),
            themes=self.config.get("themes", []),
            tone=self.config.get("tone", "")
        )

        # 2. 创建卷
        for vol in volumes:
            self.context_manager.create_volume(
                vol["id"],
                vol["title"],
                vol["summary"],
                vol["chapters"],
                vol["main_plot"]
            )
            logger.info(f"创建卷: {vol['title']}")

        # 3. 创建情节线
        for plot in plotlines:
            self.plot_tracker.create_plotline(
                plot["id"],
                plot["title"],
                plot["description"],
                plot["importance"],
                plot["start_chapter"],
                plot["end_chapter"],
                related_characters=plot.get("characters", []),
                parent_plot=plot.get("parent")
            )
            logger.info(f"创建情节线: {plot['title']}")

        # 4. 设置角色
        for char in characters:
            self.context_manager.update_character(
                char["name"],
                **char["attributes"]
            )
            logger.info(f"设置角色: {char['name']}")

        logger.info("项目结构设置完成")

    def generate_architecture_and_blueprint(self):
        """生成小说架构和目录"""
        logger.info("生成小说架构...")

        # 生成架构
        Novel_architecture_generate(
            llm=self.llm,
            topic=self.config["topic"],
            genre=self.config["genre"],
            num_chapters=self.config["num_chapters"],
            word_number=self.config["word_number"],
            filepath=str(self.output_dir),
            content_guidance=self.config.get("content_guidance")
        )

        logger.info("生成章节目录...")

        # 生成目录
        Chapter_blueprint_generate(
            llm=self.llm,
            filepath=str(self.output_dir),
            num_chapters=self.config["num_chapters"]
        )

        logger.info("架构和目录生成完成")

    def build_enhanced_context(self, chapter_number: int) -> str:
        """
        构建增强上下文

        Args:
            chapter_number: 章节号

        Returns:
            完整的上下文字符串
        """
        # 获取多层次上下文
        context = self.context_manager.build_context_for_chapter(chapter_number)

        # 获取情节上下文
        plot_context = self.plot_tracker.build_plot_context(chapter_number)

        # 组合
        enhanced_context = f"""
{context}

{plot_context}

【生成指导】
- 当前章节号: {chapter_number}
- 确保推进所有活跃情节线
- 保持角色性格和能力一致
- 如有合适机会，回应未解决的伏笔
"""
        return enhanced_context

    def generate_single_chapter(self, chapter_number: int):
        """
        生成单个章节

        Args:
            chapter_number: 章节号
        """
        logger.info(f"开始生成第{chapter_number}章...")

        # 构建增强上下文
        enhanced_context = self.build_enhanced_context(chapter_number)

        # TODO: 修改 generate_chapter_draft 函数以支持额外的上下文
        # 这里简化处理，实际需要修改原函数
        logger.info(f"增强上下文已准备 ({len(enhanced_context)} 字符)")

        # 生成章节
        generate_chapter_draft(
            llm=self.llm,
            chapter_number=chapter_number,
            filepath=str(self.output_dir),
            word_number=self.config["word_number"]
        )

        logger.info(f"第{chapter_number}章生成完成")

    def update_tracking_systems(self, chapter_number: int):
        """
        更新追踪系统

        Args:
            chapter_number: 章节号
        """
        logger.info(f"更新第{chapter_number}章的追踪信息...")

        # 读取章节内容
        chapter_file = self.output_dir / f"chapter_{chapter_number}.txt"
        if not chapter_file.exists():
            logger.warning(f"章节文件不存在: {chapter_file}")
            return

        with open(chapter_file, 'r', encoding='utf-8') as f:
            content = f.read()

        # 提取信息（简化处理，实际应用中可用LLM辅助）
        # 这里需要实现或使用LLM来提取章节信息

        # 更新章节上下文（示例）
        self.context_manager.add_chapter_context(
            chapter_number,
            summary=f"第{chapter_number}章内容摘要",  # 实际应从内容提取
            key_events=["事件1", "事件2"],  # 实际应从内容提取
            character_states={},
            location="",
            time_span="",
            mood=""
        )

        # 更新情节追踪（示例）
        active_plots = self.plot_tracker.get_active_plots(chapter_number)
        for plot in active_plots:
            self.plot_tracker.record_chapter_plot(
                plot["plot_id"],
                chapter_number,
                f"第{chapter_number}章推进了 {plot['title']}"
            )

        logger.info(f"第{chapter_number}章追踪信息已更新")

    def run_quality_check(self, current_chapter: int):
        """
        运行质量检查

        Args:
            current_chapter: 当前章节号
        """
        logger.info(f"\n{'='*60}")
        logger.info(f"第{current_chapter}章质量检查")
        logger.info(f"{'='*60}\n")

        # 1. 一致性报告
        consistency_report = self.context_manager.generate_consistency_report()
        logger.info("【一致性报告】")
        logger.info(f"总章节数: {consistency_report['total_chapters']}")
        logger.info(f"总角色数: {consistency_report['total_characters']}")
        logger.info(f"未回应伏笔: {consistency_report['unresolved_foreshadowing']}")

        if consistency_report['missing_information']:
            logger.warning("缺失信息:")
            for info in consistency_report['missing_information']:
                logger.warning(f"  - {info}")

        # 2. 情节线报告
        plot_report = self.plot_tracker.generate_plot_report()
        logger.info("\n【情节线报告】")
        logger.info(f"总情节线: {plot_report['total_plotlines']}")
        logger.info(f"活跃冲突: {plot_report['active_conflicts']}")
        logger.info(f"未回应伏笔: {plot_report['unresolved_foreshadowing']}")

        # 3. 检查超期情节
        unresolved_plots = self.plot_tracker.get_unresolved_plots(current_chapter)
        if unresolved_plots:
            logger.warning("超期未解决的情节:")
            for plot in unresolved_plots:
                logger.warning(f"  - {plot['title']}: 超期{plot['overdue_chapters']}章")

        return len(unresolved_plots) == 0 and len(consistency_report['missing_information']) == 0

    def generate_full_novel(self, check_interval: int = 10):
        """
        生成完整小说

        Args:
            check_interval: 质量检查间隔
        """
        total_chapters = self.config["num_chapters"]

        logger.info(f"开始生成{total_chapters}章小说...")

        for chapter_num in range(1, total_chapters + 1):
            try:
                # 生成章节
                self.generate_single_chapter(chapter_num)

                # 定稿章节
                finalize_chapter(
                    llm=self.llm,
                    chapter_number=chapter_num,
                    filepath=str(self.output_dir)
                )

                # 更新追踪系统
                self.update_tracking_systems(chapter_num)

                # 定期质量检查
                if chapter_num % check_interval == 0:
                    is_ok = self.run_quality_check(chapter_num)

                    if not is_ok:
                        logger.warning("发现质量问题，建议检查")
                        # 在实际应用中可以暂停，等待人工干预

                logger.info(f"进度: {chapter_num}/{total_chapters} ({chapter_num/total_chapters*100:.1f}%)")

            except Exception as e:
                logger.error(f"第{chapter_num}章生成失败: {e}", exc_info=True)
                # 可以选择继续或中止

        logger.info(f"\n{'='*60}")
        logger.info(f"🎉 {total_chapters}章小说生成完成！")
        logger.info(f"{'='*60}\n")

        # 最终质量检查
        self.run_quality_check(total_chapters)


def main():
    """主函数 - 完整示例"""

    # ==================== 配置 ====================

    # LLM配置
    llm_config = {
        "interface_format": "OpenAI",
        "api_key": "your-api-key",
        "base_url": "https://api.openai.com/v1",
        "model_name": "gpt-4o-mini",
        "temperature": 0.8,
        "max_tokens": 8192,
        "timeout": 600
    }

    # 小说配置
    novel_config = {
        "topic": "一个普通少年意外获得修仙传承，从凡人成长为强者的热血历程",
        "genre": "玄幻修仙",
        "num_chapters": 100,
        "word_number": 3000,
        "world_setting": {
            "type": "修仙世界",
            "power_system": "炼气→筑基→金丹→元婴→化神",
            "tech_level": "古代+修仙"
        },
        "themes": ["成长", "热血", "逆袭", "守护"],
        "tone": "热血励志，偶有轻松",
        "content_guidance": "注重战斗描写和修炼过程，人物刻画立体"
    }

    # 卷规划
    volumes = [
        {
            "id": "vol_1",
            "title": "炼气篇",
            "summary": "主角入门修仙，经历重重考验",
            "chapters": (1, 25),
            "main_plot": "主角拜入宗门，打好修炼基础"
        },
        {
            "id": "vol_2",
            "title": "筑基篇",
            "summary": "主角突破筑基，崭露头角",
            "chapters": (26, 50),
            "main_plot": "主角参与宗门大比，获得重要机缘"
        },
        {
            "id": "vol_3",
            "title": "金丹篇",
            "summary": "主角冲击金丹，面对生死危机",
            "chapters": (51, 75),
            "main_plot": "主角历练江湖，对抗邪教"
        },
        {
            "id": "vol_4",
            "title": "巅峰篇",
            "summary": "主角成就元婴，守护家园",
            "chapters": (76, 100),
            "main_plot": "主角对抗魔族入侵，拯救修仙界"
        }
    ]

    # 情节线规划
    plotlines = [
        {
            "id": "main_cultivation",
            "title": "修炼之路",
            "description": "主角的修为提升历程",
            "importance": PlotImportance.MAIN,
            "start_chapter": 1,
            "end_chapter": 100,
            "characters": ["叶凡"]
        },
        {
            "id": "sect_conflict",
            "title": "宗门危机",
            "description": "宗门面临外部威胁",
            "importance": PlotImportance.MAIN,
            "start_chapter": 20,
            "end_chapter": 85,
            "characters": ["叶凡", "掌门", "长老们"]
        },
        {
            "id": "romance",
            "title": "爱情线",
            "description": "主角与师妹的感情发展",
            "importance": PlotImportance.MAJOR,
            "start_chapter": 15,
            "end_chapter": 90,
            "characters": ["叶凡", "林若雪"],
            "parent": "main_cultivation"
        },
        {
            "id": "hidden_heritage",
            "title": "身世之谜",
            "description": "主角的真实身世",
            "importance": PlotImportance.MAJOR,
            "start_chapter": 30,
            "end_chapter": 95,
            "characters": ["叶凡", "神秘老者"]
        }
    ]

    # 角色设定
    characters = [
        {
            "name": "叶凡",
            "attributes": {
                "description": "16岁少年，黑发黑眼，身材匀称",
                "personality": "坚韧不拔、善良正直、重情重义",
                "abilities": ["剑法天赋", "悟性极高"],
                "importance": "main",
                "current_state": "炼气初期",
                "goals": ["变强", "保护重要的人", "探寻身世"]
            }
        },
        {
            "name": "林若雪",
            "attributes": {
                "description": "17岁少女，白衣飘飘，容貌绝美",
                "personality": "高冷、善良、内心细腻",
                "abilities": ["冰系功法", "琴道"],
                "importance": "main",
                "current_state": "炼气后期"
            }
        },
        {
            "name": "玄机老祖",
            "attributes": {
                "description": "宗门长老，白发白须，仙风道骨",
                "personality": "睿智、严厉、护短",
                "abilities": ["元婴巅峰", "阵法大师"],
                "importance": "major",
                "current_state": "元婴巅峰"
            }
        }
    ]

    # ==================== 生成流程 ====================

    # 1. 创建增强生成器
    generator = EnhancedNovelGenerator(
        "immortal_path_100",
        llm_config,
        novel_config
    )

    # 2. 设置项目结构
    generator.setup_project(volumes, plotlines, characters)

    # 3. 生成架构和目录
    generator.generate_architecture_and_blueprint()

    # 4. 激活初始情节线
    generator.plot_tracker.activate_plotline("main_cultivation", 1)

    # 5. 生成完整小说
    generator.generate_full_novel(check_interval=10)

    logger.info("✅ 全部完成！")


if __name__ == "__main__":
    # 注意：实际使用前需要：
    # 1. 填入真实的API密钥
    # 2. 修改 generate_chapter_draft 支持额外上下文
    # 3. 实现自动信息提取功能

    print("""
    ╔══════════════════════════════════════════════════════════╗
    ║                                                          ║
    ║     长篇小说生成完整示例                                  ║
    ║                                                          ║
    ║     本示例演示如何使用增强系统生成100章连贯小说           ║
    ║                                                          ║
    ║     使用前请：                                           ║
    ║     1. 在代码中填入你的API密钥                            ║
    ║     2. 根据需要调整配置                                   ║
    ║     3. 运行 python examples/long_novel_example.py        ║
    ║                                                          ║
    ╚══════════════════════════════════════════════════════════╝
    """)

    try:
        main()
    except KeyboardInterrupt:
        print("\n\n用户中止生成")
    except Exception as e:
        print(f"\n\n错误: {e}")
        import traceback
        traceback.print_exc()
