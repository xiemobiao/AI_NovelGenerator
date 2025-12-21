# 长篇小说生成完全指南

## 🎯 目标

本指南帮助你使用AI Novel Generator生成**连贯、完整、高质量的长篇小说**（50章以上），解决以下核心挑战：

1. ✅ **连续性保持** - 确保前后章节逻辑连贯
2. ✅ **情节完整性** - 所有情节线都有开始和结尾
3. ✅ **角色一致性** - 角色性格、能力保持一致
4. ✅ **伏笔管理** - 埋下的伏笔都得到回应
5. ✅ **时间线正确** - 时间流逝符合逻辑
6. ✅ **细节准确** - 重要细节不会自相矛盾

---

## 📊 新增的增强系统

### 1. 多层次上下文管理系统 (`context_manager.py`)

**功能**: 5层上下文追踪

```
全局层 → 卷层 → 章节层 → 场景层 → 实体层
```

**使用示例**:

```python
from context_manager import create_context_manager

# 创建管理器
cm = create_context_manager("./my_novel")

# 设置全局上下文
cm.update_global_context(
    world_setting={"type": "修仙世界", "power_system": "元婴体系"},
    themes=["成长", "复仇", "救赎"],
    tone="严肃史诗"
)

# 创建卷
cm.create_volume(
    "volume_1",
    "入门篇",
    "主角从凡人到筑基的历程",
    (1, 30),
    "主角拜入仙门，经历试炼"
)

# 添加章节上下文
cm.add_chapter_context(
    chapter_number=1,
    summary="主角遭遇灭门，踏上修仙路",
    key_events=["家族覆灭", "获得传承"],
    character_states={"主角": "悲痛、决心复仇"},
    location="云霞山脉",
    time_span="三天",
    mood="悲壮",
    foreshadowing=["神秘老者提到的天命"]
)

# 更新角色信息
cm.update_character(
    "主角",
    description="16岁少年，天资聪颖",
    personality="坚韧、冷静、重情义",
    abilities=["剑法天赋", "记忆力超群"],
    current_state="筑基初期",
    location="玄天宗",
    goals=["为家族复仇", "突破金丹"],
    importance="main"
)

# 生成章节时获取完整上下文
context = cm.build_context_for_chapter(5)
# 将这个context加入到LLM的prompt中
```

### 2. 情节线索追踪系统 (`plot_tracker.py`)

**功能**: 管理多条平行情节线

```python
from plot_tracker import create_plot_tracker, PlotImportance

tracker = create_plot_tracker("./my_novel")

# 创建主线
tracker.create_plotline(
    plot_id="main_revenge",
    title="复仇主线",
    description="主角为家族复仇的历程",
    importance=PlotImportance.MAIN,
    start_chapter=1,
    expected_end_chapter=100,
    related_characters=["主角", "仇人"],
    related_locations=["玄天宗", "魔窟"]
)

# 创建支线（作为主线的子线）
tracker.create_plotline(
    plot_id="romance",
    title="爱情支线",
    description="主角与师妹的感情发展",
    importance=PlotImportance.MAJOR,
    start_chapter=10,
    expected_end_chapter=80,
    related_characters=["主角", "师妹"],
    parent_plot="main_revenge"
)

# 激活情节线
tracker.activate_plotline("main_revenge", chapter=1)

# 添加里程碑事件
tracker.add_milestone(
    "main_revenge",
    chapter=20,
    event="发现仇人真实身份",
    significance="情节转折点，主角意识到复仇的艰难"
)

# 记录每章的情节发展
tracker.record_chapter_plot(
    "main_revenge",
    chapter=5,
    development="主角在试炼中展现实力，引起长老注意"
)

# 完结情节线
tracker.resolve_plotline(
    "main_revenge",
    chapter=100,
    resolution="主角成功复仇，但发现真相另有隐情"
)

# 获取当前活跃的情节
active_plots = tracker.get_active_plots(chapter=50)

# 检查超期未完成的情节
unresolved = tracker.get_unresolved_plots(current_chapter=50)
if unresolved:
    print("警告：以下情节线超期未解决：")
    for plot in unresolved:
        print(f"- {plot['title']}: 超期{plot['overdue_chapters']}章")

# 构建情节上下文
plot_context = tracker.build_plot_context(chapter=50)
```

---

## 🚀 完整工作流程

### 阶段1：项目规划（生成前）

#### 1.1 规划小说结构

```python
# 假设生成100章的长篇小说

# 分卷规划
volumes = [
    {"id": "vol_1", "title": "入门篇", "chapters": (1, 30)},
    {"id": "vol_2", "title": "成长篇", "chapters": (31, 60)},
    {"id": "vol_3", "title": "争霸篇", "chapters": (61, 90)},
    {"id": "vol_4", "title": "终章", "chapters": (91, 100)}
]

# 为每卷创建上下文
for vol in volumes:
    cm.create_volume(
        vol["id"],
        vol["title"],
        f"第{vol['chapters'][0]}-{vol['chapters'][1]}章的内容",
        vol["chapters"],
        "该卷的主要情节"
    )
```

#### 1.2 规划主要情节线

```python
# 主线情节
main_plots = [
    {
        "id": "main_quest",
        "title": "修炼之路",
        "start": 1,
        "end": 100,
        "importance": PlotImportance.MAIN
    },
    {
        "id": "revenge",
        "title": "复仇",
        "start": 1,
        "end": 80,
        "importance": PlotImportance.MAIN
    }
]

# 支线情节
sub_plots = [
    {
        "id": "romance",
        "title": "爱情线",
        "start": 15,
        "end": 85,
        "importance": PlotImportance.MAJOR,
        "parent": "main_quest"
    },
    {
        "id": "sect_politics",
        "title": "宗门斗争",
        "start": 20,
        "end": 70,
        "importance": PlotImportance.MAJOR
    },
    {
        "id": "hidden_treasure",
        "title": "秘宝线索",
        "start": 10,
        "end": 60,
        "importance": PlotImportance.MINOR
    }
]

# 创建所有情节线
for plot in main_plots + sub_plots:
    tracker.create_plotline(
        plot["id"],
        plot["title"],
        f"{plot['title']}的详细描述",
        plot["importance"],
        plot["start"],
        plot["end"],
        parent_plot=plot.get("parent")
    )
```

#### 1.3 规划主要角色

```python
main_characters = [
    {
        "name": "叶凡",
        "role": "主角",
        "description": "16岁少年，天资聪颖",
        "personality": "坚韧、冷静、重情义",
        "importance": "main"
    },
    {
        "name": "林若雪",
        "role": "女主角",
        "description": "仙门天才，冰清玉洁",
        "personality": "高冷、善良、执着",
        "importance": "main"
    },
    {
        "name": "玄机老祖",
        "role": "导师",
        "description": "宗门长老，高深莫测",
        "personality": "睿智、严厉、护短",
        "importance": "major"
    }
]

for char in main_characters:
    cm.update_character(
        char["name"],
        description=char["description"],
        personality=char["personality"],
        importance=char["importance"]
    )
```

---

### 阶段2：生成流程（每章）

#### 2.1 生成前准备

```python
def prepare_chapter_generation(chapter_number: int):
    """准备生成章节所需的完整上下文"""

    # 1. 获取多层次上下文
    context = cm.build_context_for_chapter(chapter_number)

    # 2. 获取情节上下文
    plot_context = tracker.build_plot_context(chapter_number)

    # 3. 获取当前活跃的情节
    active_plots = tracker.get_active_plots(chapter_number)

    # 4. 检查未回应的伏笔
    unresolved_fs = cm.get_unresolved_foreshadowing()

    # 5. 组合成完整提示词
    full_context = f"""
{context}

{plot_context}

【当前任务】
- 生成第{chapter_number}章
- 需要推进的情节: {', '.join([p['title'] for p in active_plots])}
- 考虑回应以下伏笔: {unresolved_fs[:3] if len(unresolved_fs) > 0 else '无'}
"""

    return full_context
```

#### 2.2 生成章节

```python
from novel_generator import generate_chapter_draft
from llm_adapters import create_llm_adapter

llm = create_llm_adapter(...)

for chapter_num in range(1, 101):
    # 准备上下文
    enhanced_context = prepare_chapter_generation(chapter_num)

    # 生成章节（将enhanced_context加入到prompt中）
    generate_chapter_draft(
        llm=llm,
        chapter_number=chapter_num,
        filepath="./my_novel",
        additional_context=enhanced_context  # 需要修改原函数支持这个参数
    )

    print(f"第{chapter_num}章生成完成")
```

#### 2.3 生成后更新

```python
def update_after_chapter(chapter_number: int, chapter_content: str):
    """章节生成后更新所有追踪系统"""

    # 1. 提取章节信息（可以用LLM辅助）
    summary = extract_summary(chapter_content)
    key_events = extract_key_events(chapter_content)
    characters_in_chapter = extract_characters(chapter_content)
    new_foreshadowing = extract_foreshadowing(chapter_content)

    # 2. 更新章节上下文
    cm.add_chapter_context(
        chapter_number,
        summary=summary,
        key_events=key_events,
        character_states={},  # 从内容提取
        location="",  # 从内容提取
        time_span="",
        mood="",
        foreshadowing=new_foreshadowing
    )

    # 3. 更新情节追踪
    active_plots = tracker.get_active_plots(chapter_number)
    for plot in active_plots:
        # 记录该章对每条情节线的推进
        development = extract_plot_development(chapter_content, plot['title'])
        if development:
            tracker.record_chapter_plot(
                plot['plot_id'],
                chapter_number,
                development
            )

    # 4. 更新角色信息
    for char_name in characters_in_chapter:
        cm.record_character_appearance(char_name, chapter_number)
        # 如果有状态变化，更新状态

    print(f"第{chapter_number}章信息已更新")


# 使用示例
for chapter_num in range(1, 101):
    # ... 生成章节 ...

    # 读取生成的章节
    with open(f"./my_novel/chapter_{chapter_num}.txt", 'r', encoding='utf-8') as f:
        content = f.read()

    # 更新追踪系统
    update_after_chapter(chapter_num, content)
```

---

### 阶段3：质量控制（定期检查）

#### 3.1 每10章检查一次

```python
def quality_check(current_chapter: int):
    """质量检查"""

    print(f"\n{'='*60}")
    print(f"第{current_chapter}章质量检查")
    print(f"{'='*60}\n")

    # 1. 一致性报告
    consistency_report = cm.generate_consistency_report()
    print("【一致性报告】")
    print(f"总章节数: {consistency_report['total_chapters']}")
    print(f"总角色数: {consistency_report['total_characters']}")
    print(f"未回应伏笔: {consistency_report['unresolved_foreshadowing']}")

    if consistency_report['missing_information']:
        print("\n⚠️  缺失信息:")
        for info in consistency_report['missing_information']:
            print(f"  - {info}")

    # 2. 情节线报告
    plot_report = tracker.generate_plot_report()
    print("\n【情节线报告】")
    print(f"总情节线: {plot_report['total_plotlines']}")
    print(f"状态统计: {plot_report['status_summary']}")
    print(f"活跃冲突: {plot_report['active_conflicts']}")
    print(f"未回应伏笔: {plot_report['unresolved_foreshadowing']}")

    # 3. 检查超期情节
    unresolved_plots = tracker.get_unresolved_plots(current_chapter)
    if unresolved_plots:
        print("\n⚠️  超期未解决的情节:")
        for plot in unresolved_plots:
            print(f"  - {plot['title']}: 超期{plot['overdue_chapters']}章")

    # 4. 主要角色检查
    print("\n【主要角色】")
    for char in consistency_report['main_characters']:
        print(f"  {char['name']}: 出场{char['appearances']}次")
        print(f"    首次: 第{char['first_chapter']}章")
        print(f"    最近: 第{char['last_chapter']}章")


# 每10章检查一次
for chapter in range(10, 101, 10):
    quality_check(chapter)
```

---

## 💡 最佳实践

### 1. 开始前的充分规划

**❌ 不好的做法**:
```
直接开始生成，边写边想
```

**✅ 好的做法**:
```python
# 1. 完整的大纲（至少到卷级别）
# 2. 主要情节线的规划（起承转合）
# 3. 主要角色的完整设定
# 4. 重要转折点的预设
```

### 2. 分卷生成，阶段验收

**推荐策略**:
```
第一卷（1-30章）→ 全面检查 → 第二卷（31-60章）→ 检查 → ...
```

**每卷结束时**:
1. 运行完整的质量检查
2. 人工审阅关键章节
3. 修正发现的问题
4. 调整后续规划

### 3. 主动管理情节线

```python
# ❌ 不要让情节线自生自灭
tracker.create_plotline(...)
# 然后就忘了...

# ✅ 主动管理每条情节线
tracker.create_plotline(...)
tracker.activate_plotline(...)  # 在合适的章节激活
tracker.add_milestone(...)      # 设置里程碑
tracker.record_chapter_plot(...) # 记录每章发展
tracker.resolve_plotline(...)   # 在计划的章节完结
```

### 4. 重要信息显式记录

```python
# ❌ 依赖LLM记忆
# 希望LLM记得主角在第10章获得的能力

# ✅ 显式记录
cm.update_character(
    "主角",
    abilities=["炼体术（第10章获得）", "御剑术（第15章学会）"],
    power_level="筑基后期",
    important_items=["玄天剑（第5章获得）"]
)
```

### 5. 定期使用一致性检查

```python
# 每10章运行一次
from consistency_checker import consistency_check

for chapter in range(10, 101, 10):
    issues = consistency_check(
        llm=llm,
        chapter_number=chapter,
        filepath="./my_novel"
    )

    if issues:
        print(f"⚠️  第{chapter}章发现问题:")
        for issue in issues:
            print(f"  - {issue}")
        # 根据问题调整后续生成
```

### 6. 伏笔管理策略

```python
# 埋伏笔时
cm.add_chapter_context(
    20,
    ...
    foreshadowing=["神秘人提到的古老预言", "主角体内的奇异印记"]
)

tracker.create_plotline(
    "mystery_bloodline",
    "血脉之谜",
    "主角身世之谜",
    PlotImportance.MAJOR,
    start_chapter=20,  # 埋伏笔
    expected_end_chapter=70,  # 计划揭秘
    ...
)

# 回应伏笔时（第70章）
cm.add_chapter_context(
    70,
    ...
    callbacks=["主角体内的奇异印记"]  # 标记已回应
)

tracker.resolve_plotline(
    "mystery_bloodline",
    70,
    "揭示主角乃远古大帝转世"
)
```

---

## 🔧 辅助工具函数

### 自动化辅助函数

```python
def auto_extract_chapter_info(llm, chapter_content: str) -> Dict:
    """
    使用LLM自动提取章节信息

    Returns:
        包含summary, key_events, characters等的字典
    """
    extraction_prompt = f"""
请分析以下章节内容，提取关键信息：

{chapter_content}

请以JSON格式返回：
{{
    "summary": "章节摘要（1-2句话）",
    "key_events": ["事件1", "事件2", ...],
    "characters": ["角色1", "角色2", ...],
    "location": "主要地点",
    "mood": "情绪基调",
    "foreshadowing": ["伏笔1", ...],
    "plot_developments": {{
        "情节线名称": "该情节线在本章的发展"
    }}
}}
"""

    response = llm.invoke(extraction_prompt)
    import json
    return json.loads(response)


def smart_context_builder(cm, tracker, chapter_number: int,
                          max_context_length: int = 3000) -> str:
    """
    智能构建上下文，控制长度

    根据重要性筛选和压缩上下文信息
    """
    # 获取完整上下文
    full_context = cm.build_context_for_chapter(chapter_number)
    plot_context = tracker.build_plot_context(chapter_number)

    combined = full_context + "\n\n" + plot_context

    # 如果超长，进行压缩
    if len(combined) > max_context_length:
        # 只保留最重要的信息
        # 1. 全局设定（必须）
        # 2. 当前卷信息（必须）
        # 3. 最近3章摘要（必须）
        # 4. 主线情节（必须）
        # 5. 最重要的2-3个角色状态
        pass  # 实现压缩逻辑

    return combined


def batch_generate_with_monitoring(start_chapter: int, end_chapter: int,
                                   check_interval: int = 10):
    """
    批量生成并监控
    """
    for chapter in range(start_chapter, end_chapter + 1):
        try:
            # 生成章节
            context = prepare_chapter_generation(chapter)
            generate_chapter_draft(...)

            # 更新追踪
            content = read_chapter(chapter)
            update_after_chapter(chapter, content)

            # 定期检查
            if chapter % check_interval == 0:
                quality_check(chapter)

                # 如果发现严重问题，暂停
                unresolved = tracker.get_unresolved_plots(chapter)
                if len(unresolved) > 3:
                    print("⚠️  发现多个超期情节，建议检查")
                    choice = input("继续生成? (y/n): ")
                    if choice.lower() != 'y':
                        break

        except Exception as e:
            print(f"第{chapter}章生成失败: {e}")
            # 记录错误，继续或中止
```

---

## 📊 效果对比

### 不使用增强系统

```
问题:
❌ 第80章主角能力突然退化（忘记了之前的设定）
❌ 第60章埋的伏笔到100章都没回应
❌ 支线情节线突然消失
❌ 角色性格前后不一致
❌ 时间线混乱（昨天还在A地，今天就到了千里之外的B地）
```

### 使用增强系统

```
优势:
✅ 所有角色信息有据可查，保持一致
✅ 所有情节线都有完整规划和追踪
✅ 伏笔系统化管理，不会遗漏
✅ 每章生成都基于完整上下文
✅ 定期质量检查，及时发现问题
✅ 最终产出连贯、完整的长篇小说
```

---

## 🎯 100章小说生成检查清单

### 生成前 (0%)
- [ ] 完成全局设定
- [ ] 规划3-5个卷
- [ ] 创建3-5条主要情节线
- [ ] 设定5-10个主要角色
- [ ] 规划关键转折点（每20-30章）

### 第一卷完成 (30%)
- [ ] 运行质量检查
- [ ] 人工审阅关键章节
- [ ] 确认情节线进展正常
- [ ] 调整后续规划

### 第二卷完成 (60%)
- [ ] 全面质量检查
- [ ] 检查伏笔回应情况
- [ ] 确认主线进度
- [ ] 调整终章规划

### 第三卷完成 (90%)
- [ ] 准备收尾
- [ ] 列出所有未完成情节线
- [ ] 规划终章内容
- [ ] 最后质量检查

### 全部完成 (100%)
- [ ] 最终一致性检查
- [ ] 生成完整性报告
- [ ] 导出为电子书格式
- [ ] 庆祝完成！🎉

---

## 📝 总结

通过使用这套增强系统，你可以：

1. **系统化管理复杂信息** - 不再依赖记忆或手工记录
2. **确保长篇连贯性** - 自动维护上下文和追踪情节
3. **提高生成质量** - 每章都基于完整准确的上下文
4. **及时发现问题** - 定期检查，避免积累大问题
5. **轻松完成长篇** - 从50章到500章都不是问题！

**关键建议**:
- 📝 **前期规划要充分**（至少规划到卷级别）
- 🔄 **过程追踪要勤快**（每章都更新系统）
- 🔍 **定期检查要严格**（每10章全面检查）
- 🎯 **问题修正要及时**（发现问题立即调整）

有了这套系统，**生成100章、200章甚至更长的小说都不再是难题**！

---

## 💬 获取帮助

如有问题，请查看:
- [开发文档](./DEVELOPMENT.md)
- [API文档](./API_DOCUMENTATION.md)
- [GitHub Issues](https://github.com/YILING0013/AI_NovelGenerator/issues)
