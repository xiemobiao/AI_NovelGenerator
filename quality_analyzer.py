# quality_analyzer.py
# -*- coding: utf-8 -*-
"""
小说质量分析器
提供小说整体质量评估报告
"""

import os
import json
from typing import Dict, List, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


def analyze_novel_quality(filepath: str) -> Dict[str, Any]:
    """
    分析小说质量，生成综合报告

    Args:
        filepath: 小说项目路径

    Returns:
        质量报告字典
    """
    project_dir = Path(filepath)

    # 初始化报告
    report = {
        "overall_score": 0,
        "statistics": {},
        "completeness": {},
        "issues": [],
        "suggestions": []
    }

    try:
        # 1. 统计章节数量和字数
        chapters_dir = project_dir / "chapters"
        chapter_stats = analyze_chapters(chapters_dir)
        report["statistics"] = chapter_stats

        # 2. 检查项目完整性
        completeness = check_project_completeness(project_dir)
        report["completeness"] = completeness

        # 3. 分析蓝图覆盖率
        blueprint_coverage = analyze_blueprint_coverage(project_dir)
        report["blueprint_coverage"] = blueprint_coverage

        # 4. 检测潜在问题
        issues = detect_issues(project_dir, chapter_stats)
        report["issues"] = issues

        # 5. 生成改进建议
        suggestions = generate_suggestions(chapter_stats, completeness, issues)
        report["suggestions"] = suggestions

        # 6. 计算综合评分（0-100）
        overall_score = calculate_overall_score(chapter_stats, completeness, issues)
        report["overall_score"] = overall_score

        logger.info(f"质量分析完成，总分: {overall_score}")

    except Exception as e:
        logger.error(f"质量分析失败: {e}")
        report["error"] = str(e)

    return report


def analyze_chapters(chapters_dir: Path) -> Dict[str, Any]:
    """分析章节统计信息"""
    stats = {
        "total_chapters": 0,
        "total_words": 0,
        "average_words": 0,
        "min_words": float('inf'),
        "max_words": 0,
        "chapter_lengths": []
    }

    if not chapters_dir.exists():
        return stats

    chapter_files = sorted(
        chapters_dir.glob("chapter_*.txt"),
        key=lambda x: int(x.stem.split('_')[1])
    )

    for chapter_file in chapter_files:
        try:
            with open(chapter_file, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                word_count = len(content)

                stats["total_chapters"] += 1
                stats["total_words"] += word_count
                stats["min_words"] = min(stats["min_words"], word_count)
                stats["max_words"] = max(stats["max_words"], word_count)
                stats["chapter_lengths"].append({
                    "chapter": int(chapter_file.stem.split('_')[1]),
                    "words": word_count
                })
        except Exception as e:
            logger.warning(f"读取章节失败 {chapter_file}: {e}")

    if stats["total_chapters"] > 0:
        stats["average_words"] = stats["total_words"] / stats["total_chapters"]

    if stats["min_words"] == float('inf'):
        stats["min_words"] = 0

    return stats


def check_project_completeness(project_dir: Path) -> Dict[str, Any]:
    """检查项目文件完整性"""
    required_files = {
        "Novel_architecture.txt": "小说架构",
        "Novel_directory.txt": "章节蓝图",
        "character_state.txt": "角色状态",
        "global_summary.txt": "全局摘要"
    }

    optional_files = {
        "plotlines.json": "情节线管理",
        "config.json": "项目配置"
    }

    completeness = {
        "required_files": {},
        "optional_files": {},
        "missing_required": [],
        "missing_optional": [],
        "completion_rate": 0
    }

    # 检查必需文件
    for filename, description in required_files.items():
        file_path = project_dir / filename
        exists = file_path.exists()
        completeness["required_files"][filename] = {
            "exists": exists,
            "description": description
        }
        if not exists:
            completeness["missing_required"].append(description)

    # 检查可选文件
    for filename, description in optional_files.items():
        file_path = project_dir / filename
        exists = file_path.exists()
        completeness["optional_files"][filename] = {
            "exists": exists,
            "description": description
        }
        if not exists:
            completeness["missing_optional"].append(description)

    # 计算完成率
    total_files = len(required_files)
    existing_files = sum(1 for v in completeness["required_files"].values() if v["exists"])
    completeness["completion_rate"] = (existing_files / total_files * 100) if total_files > 0 else 0

    return completeness


def analyze_blueprint_coverage(project_dir: Path) -> Dict[str, Any]:
    """分析蓝图覆盖率"""
    coverage = {
        "planned_chapters": 0,
        "completed_chapters": 0,
        "coverage_rate": 0
    }

    try:
        # 读取蓝图
        blueprint_file = project_dir / "Novel_directory.txt"
        if blueprint_file.exists():
            with open(blueprint_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 简单计数：查找章节标记
                coverage["planned_chapters"] = content.count("第") if "章" in content else 0

        # 统计已完成章节
        chapters_dir = project_dir / "chapters"
        if chapters_dir.exists():
            coverage["completed_chapters"] = len(list(chapters_dir.glob("chapter_*.txt")))

        # 计算覆盖率
        if coverage["planned_chapters"] > 0:
            coverage["coverage_rate"] = (
                coverage["completed_chapters"] / coverage["planned_chapters"] * 100
            )

    except Exception as e:
        logger.warning(f"分析蓝图覆盖率失败: {e}")

    return coverage


def detect_issues(project_dir: Path, chapter_stats: Dict) -> List[Dict[str, str]]:
    """检测潜在问题"""
    issues = []

    # 检查章节长度异常
    if chapter_stats.get("total_chapters", 0) > 0:
        avg_words = chapter_stats.get("average_words", 0)
        for chapter_info in chapter_stats.get("chapter_lengths", []):
            chapter_num = chapter_info["chapter"]
            words = chapter_info["words"]

            # 章节过短
            if words < 500:
                issues.append({
                    "type": "warning",
                    "category": "章节长度",
                    "message": f"第{chapter_num}章字数过少（{words}字），建议至少500字"
                })

            # 章节长度与平均值差异过大
            elif avg_words > 0 and abs(words - avg_words) > avg_words * 0.5:
                issues.append({
                    "type": "info",
                    "category": "章节长度",
                    "message": f"第{chapter_num}章长度（{words}字）与平均值（{int(avg_words)}字）差异较大"
                })

    # 检查向量库
    vector_store_dir = project_dir / "vectorstore"
    if not vector_store_dir.exists():
        issues.append({
            "type": "info",
            "category": "知识库",
            "message": "未创建向量知识库，可导入参考资料提升生成质量"
        })

    return issues


def generate_suggestions(chapter_stats: Dict, completeness: Dict, issues: List) -> List[str]:
    """生成改进建议"""
    suggestions = []

    # 基于完整性的建议
    if completeness.get("missing_required"):
        suggestions.append(f"缺少必需文件：{', '.join(completeness['missing_required'])}")

    # 基于章节统计的建议
    if chapter_stats.get("total_chapters", 0) == 0:
        suggestions.append("尚未生成章节，请先创建小说架构和蓝图")
    elif chapter_stats.get("total_chapters", 0) < 5:
        suggestions.append("章节数量较少，建议继续生成更多内容")

    # 基于问题的建议
    warning_issues = [i for i in issues if i.get("type") == "warning"]
    if warning_issues:
        suggestions.append(f"发现{len(warning_issues)}个需要注意的问题，建议查看详情")

    # 字数建议
    avg_words = chapter_stats.get("average_words", 0)
    if 0 < avg_words < 2000:
        suggestions.append("平均章节长度偏短，建议增加章节字数以丰富内容")

    return suggestions


def calculate_overall_score(chapter_stats: Dict, completeness: Dict, issues: List) -> int:
    """计算综合评分（0-100）"""
    score = 100

    # 扣分项：缺少必需文件（每个-15分）
    missing_required = len(completeness.get("missing_required", []))
    score -= missing_required * 15

    # 扣分项：无章节内容（-30分）
    if chapter_stats.get("total_chapters", 0) == 0:
        score -= 30

    # 扣分项：章节过短（每个-5分）
    short_chapters = sum(1 for info in chapter_stats.get("chapter_lengths", [])
                        if info["words"] < 500)
    score -= min(short_chapters * 5, 20)  # 最多扣20分

    # 扣分项：严重问题（每个-10分）
    warnings = sum(1 for i in issues if i.get("type") == "warning")
    score -= warnings * 10

    # 确保分数在0-100范围内
    return max(0, min(100, score))
