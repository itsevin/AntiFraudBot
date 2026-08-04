# -*- coding: utf-8 -*-
"""
数据库初始化脚本 (最终版)
一键完成：表结构创建 + 数据迁移 + 数据导入 + 自动配置
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# 确保项目根目录在 sys.path 中
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# 初始化 NoneBot 环境
import nonebot
from nonebot.adapters.onebot.v11 import Adapter as OneBotV11Adapter

try:
    nonebot.init()
    driver = nonebot.get_driver()
    driver.register_adapter(OneBotV11Adapter)
    nonebot.load_plugin("nonebot_plugin_orm")
    nonebot.load_plugin("src.database")  # 加载模型定义
except Exception as e:
    print(f"⚠️ 初始化警告 (如果只是插件加载重复可忽略): {e}")

from sqlalchemy import delete, select, func, text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# 导入所有模型
from src.database.models import (
    QuizQuestion, Keyword, GroupConfig, DetectionLog,
    UserScore, AIAnalysisLog, ConversationContext, ChatbotLog, UserConfig
)

# 数据库路径
DB_PATH = os.path.join(project_root, "data", "data.db")
DB_URL = f"sqlite+aiosqlite:///{DB_PATH}"


def iter_legacy_config_updates(data):
    """Yield normalized legacy config updates without touching the database."""
    feature_map = {
        "knowledge_push": "knowledge_push",
        "example_push": "example_push",
        "keyword_detection": "keyword_detection",
        "url_detection": "url_detection",
    }

    for legacy_feature, model_field in feature_map.items():
        feature_data = data.get(legacy_feature, {})
        for item in feature_data.get("group_list", []):
            group_id = str(item.get("id", "")).strip()
            if group_id:
                yield (
                    "group",
                    group_id,
                    model_field,
                    bool(item.get(legacy_feature, True)),
                )

        if model_field not in {"knowledge_push", "example_push"}:
            continue
        for item in feature_data.get("friend_list", []):
            user_id = str(item.get("id", "")).strip()
            if user_id:
                yield (
                    "user",
                    user_id,
                    model_field,
                    bool(item.get(legacy_feature, True)),
                )


# ==================== 0. 自动建表 ====================
async def ensure_tables_exist(engine):
    """使用 SQLAlchemy 自动创建所有表"""
    print("\n[0/5] 🔧 检查并创建数据库表...")
    try:
        data_dir = os.path.join(project_root, "data")
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

        from src.database.models import Model
        async with engine.begin() as conn:
            await conn.run_sync(Model.metadata.create_all)
            table_names = await conn.run_sync(
                lambda sync_conn: set(Model.metadata.tables).intersection(
                    sync_conn.dialect.get_table_names(sync_conn)
                )
            )
        expected_tables = set(Model.metadata.tables)
        if table_names != expected_tables:
            missing = ", ".join(sorted(expected_tables - table_names))
            raise RuntimeError(f"数据库缺少预期表: {missing}")
        print("  ✅ 所有数据库表已就绪！")
        return True
    except Exception as e:
        print(f"  ❌ 创建表失败: {e}")
        return False


# ==================== 1. 结构修复 ====================
async def check_and_repair_schema(session):
    """手动修复表结构变更"""
    print("\n[1/5] 🛠️ 正在检查数据库结构...")
    repairs = []
    try:
        await session.execute(text("SELECT example_push FROM group_configs LIMIT 1"))
    except Exception:
        repairs.append("ALTER TABLE group_configs ADD COLUMN example_push BOOLEAN DEFAULT 1")

    if repairs:
        for sql in repairs:
            try:
                await session.execute(text(sql))
                await session.commit()
                print(f"  ✅ 执行修复: {sql}")
            except Exception as e:
                print(f"  ⚠️ 修复失败: {e}")
    else:
        print("  ✅ 数据库结构正常。")


# ==================== 2. 旧配置迁移 ====================
async def migrate_old_config(session):
    """将旧版 data/data.json 中的群聊和私聊开关迁移到数据库。"""
    print("\n[2/5] 📖 检查旧配置文件...")
    json_path = os.path.join(project_root, "data", "data.json")
    if not os.path.exists(json_path):
        print("  ℹ️ 无旧配置，跳过。")
        return

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        migrated = 0

        for scope, subject_id, model_field, enabled in iter_legacy_config_updates(data):
            if scope == "group":
                result = await session.execute(
                    select(GroupConfig).where(GroupConfig.group_id == subject_id)
                )
                config = result.scalar_one_or_none()
                if config is None:
                    config = GroupConfig(group_id=subject_id)
                    session.add(config)
            else:
                result = await session.execute(
                    select(UserConfig).where(UserConfig.user_id == subject_id)
                )
                config = result.scalar_one_or_none()
                if config is None:
                    config = UserConfig(user_id=subject_id)
                    session.add(config)

            setattr(config, model_field, enabled)
            migrated += 1

        await session.commit()
        print(f"  ✅ 旧配置迁移完成，共处理 {migrated} 项配置。")

    except Exception as e:
        print(f"  ❌ 迁移失败: {e}")


# ==================== 3. 数据导入 ====================
async def import_content_data(session):
    """导入题库和关键词"""
    # 清理重复 UserScore (修复 MultipleResultsFound 错误)
    print("\n[3/6] 🧹 检查数据库重复数据...")
    try:
        # 按 (user_id, group_id) 分组，找出重复记录
        stmt = (
            select(UserScore.user_id, UserScore.group_id)
            .group_by(UserScore.user_id, UserScore.group_id)
            .having(func.count(UserScore.id) > 1)
        )
        res = await session.execute(stmt)
        duplicates = res.all()

        if duplicates:
            print(f"  ⚠️ 发现 {len(duplicates)} 组重复积分数据，正在清理...")
            cleaned_count = 0
            for uid, gid in duplicates:
                # 查出该组所有 ID，按倒序排列（保留最大的ID，即最新的）
                q = select(UserScore.id).where(UserScore.user_id == uid)
                if gid is not None:
                    q = q.where(UserScore.group_id == gid)
                else:
                    q = q.where(UserScore.group_id.is_(None))
                q = q.order_by(UserScore.id.desc())

                ids = (await session.execute(q)).scalars().all()
                if len(ids) > 1:
                    # 删除除了第一个之外的所有记录
                    to_delete = ids[1:]
                    await session.execute(delete(UserScore).where(UserScore.id.in_(to_delete)))
                    cleaned_count += len(to_delete)

            await session.commit()
            print(f"  ✅ 清理完成，删除了 {cleaned_count} 条重复记录")
        else:
            print("  ✅ 数据库数据正常，无重复记录")

    except Exception as e:
        print(f"  ❌ 清理重复数据失败: {e}")

    # 导入题库
    print("\n[4/6] 📦 导入基础数据...")
    quiz_path = os.path.join(project_root, "source", "quiz_bank.json")
    if os.path.exists(quiz_path):
        try:
            with open(quiz_path, "r", encoding="utf-8") as f:
                questions = json.load(f)
            q_count = 0
            for q in questions:
                # 简单排重
                res = await session.execute(select(QuizQuestion).where(QuizQuestion.question == q["question"]))
                if not res.scalar_one_or_none():
                    session.add(QuizQuestion(
                        category=q["category"], question=q["question"], options=q["options"],
                        answer=q["answer"], explanation=q["explanation"], difficulty=q.get("difficulty", 1),
                        is_active=True
                    ))
                    q_count += 1
            await session.commit()
            if q_count: print(f"  ✅ 导入了 {q_count} 道题目")
        except Exception as e: print(f"  ❌ 题库导入错: {e}")

    # 导入关键词 (支持带分类格式)
    txt_path = os.path.join(project_root, "source", "keyword.txt")
    if os.path.exists(txt_path):
        with open(txt_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]

        exist_res = await session.execute(select(Keyword.word))
        existing = set(exist_res.scalars().all())

        new_count = 0
        for line in lines:
            # 解析 "关键词|分类" 格式
            if "|" in line:
                parts = line.split("|", 1)
                word = parts[0].strip()
                category = parts[1].strip()
            else:
                word = line
                category = "通用"

            if word and word not in existing:
                session.add(Keyword(word=word, category=category, risk_level=1, is_active=True))
                existing.add(word)
                new_count += 1

        await session.commit()
        if new_count: print(f"  ✅ 导入了 {new_count} 个关键词")


# ==================== 4. 自动配置 ====================
def auto_configure_env():
    """自动修改 .env.prod 添加必须的配置"""
    print("\n[4/5] ⚙️ 正在自动配置环境...")
    env_path = os.path.join(project_root, ".env.prod")

    if not os.path.exists(env_path):
        example_env = os.path.join(project_root, ".env.prod.example")
        if os.path.exists(example_env):
            with open(example_env, "r", encoding="utf-8") as f:
                content = f.read()
            with open(env_path, "w", encoding="utf-8") as f:
                f.write(content)
            print("  ✅ 已从 .env.prod.example 创建 .env.prod")
        else:
            print("  ⚠️ 未找到 .env.prod.example，跳过配置。")
            return

    try:
        with open(env_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = []
        has_chatbot_config = False
        has_startup_check = False
        has_database_url = False

        for line in lines:
            if "chatbot_enabled" in line: has_chatbot_config = True
            if "sqlalchemy_database_url" in line.lower(): has_database_url = True
            if "alembic_startup_check" in line:
                has_startup_check = True
                # 强制覆盖为 false
                if "true" in line.lower():
                    line = "alembic_startup_check=false # 自动修正为false以跳过检查\n"
                    print("  ✅ 修正 alembic_startup_check 为 false")
            new_lines.append(line)

        # 添加启动检查跳过
        if not has_startup_check:
            new_lines.append("\n# 跳过数据库启动检查 (脚本自动添加)\n")
            new_lines.append("alembic_startup_check=false\n")
            print("  ✅ 添加 alembic_startup_check=false")

        if not has_database_url:
            new_lines.append("sqlalchemy_database_url=sqlite+aiosqlite:///data/data.db\n")
            print("  ✅ 添加 SQLite 数据库地址")

        # 添加聊天机器人配置 (如果缺失)
        if not has_chatbot_config:
            new_lines.append("\n# ==================== AI 聊天机器人配置 (脚本自动添加) ====================\n")
            new_lines.append("chatbot_enabled=true\n")
            new_lines.append("chatbot_context_timeout=600\n")
            new_lines.append("chatbot_max_context_rounds=5\n")
            new_lines.append("chatbot_rag_enabled=true\n")
            new_lines.append("chatbot_rag_top_k=3\n")
            new_lines.append("chatbot_trigger_at_me=true\n")
            new_lines.append("chatbot_trigger_keywords=[\"反诈咨询\", \"AI咨询\", \"智能客服\"]\n")
            new_lines.append("chatbot_use_group_stats=true\n")
            print("  ✅ 添加默认聊天机器人配置")

        with open(env_path, "w", encoding="utf-8") as f:
            f.writelines(new_lines)

    except Exception as e:
        print(f"  ❌ 自动配置失败: {e}")


# ==================== 主程序 ====================
async def main():
    print("=" * 50)
    print("🚀 AntiFraudBot 全自动初始化 (Final)")
    print("=" * 50)

    engine = create_async_engine(DB_URL, echo=False)
    try:
        # 步骤 0: 自动建表
        if not await ensure_tables_exist(engine):
            return

        # 步骤 1-3: 数据操作。初始化脚本使用与建表相同的引擎，
        # 避免 NoneBot 运行时配置尚未更新时连接到另一个数据库。
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            await check_and_repair_schema(session)
            await migrate_old_config(session)
            await import_content_data(session)
    finally:
        await engine.dispose()

    # 步骤 4: 自动配置环境
    auto_configure_env()

    print("\n" + "=" * 50)
    print("✨ 全部就绪！直接启动即可：")
    print("👉 poetry run nb run")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
