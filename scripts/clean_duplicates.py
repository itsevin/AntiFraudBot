
import sys
import os
import asyncio
from dotenv import load_dotenv

# 添加项目根目录到 Python 路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(ROOT_DIR)

# 加载环境变量
load_dotenv(os.path.join(ROOT_DIR, ".env.prod"))

from sqlalchemy import select, func, delete, Column, Integer, String
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# 定义临时模型，避免依赖 project models
Base = declarative_base()

class UserScore(Base):
    __tablename__ = 'user_scores'
    id = Column(Integer, primary_key=True)
    user_id = Column(String)
    group_id = Column(String, nullable=True)

async def get_standalone_session():
    # 默认使用 SQLite
    db_file = os.getenv("SQLITE_FILE", "data.db")
    if not os.path.isabs(db_file):
        db_file = os.path.join(ROOT_DIR, db_file)

    db_url = f"sqlite+aiosqlite:///{db_file}"
    print(f"🔌 连接数据库: {db_url}")

    engine = create_async_engine(db_url)
    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    return async_session()

async def clean_duplicates():
    print("🧹 开始清理重复的用户积分数据...")

    try:
        session = await get_standalone_session()
        async with session:
            # 1. 查找重复的 (user_id, group_id) 组合
            # 注意：group_id 可能为 NULL
            stmt = (
                select(UserScore.user_id, UserScore.group_id, func.count(UserScore.id).label('count'))
                .group_by(UserScore.user_id, UserScore.group_id)
                .having(func.count(UserScore.id) > 1)
            )

            result = await session.execute(stmt)
            duplicates = result.all()

            if not duplicates:
                print("✅ 未发现重复数据，无需清理。")
                return

            print(f"⚠️ 发现 {len(duplicates)} 组重复数据，开始处理...")

            total_deleted = 0

            for user_id, group_id, count in duplicates:
                # 查找该组合的所有记录，按 ID 倒序排列（保留最新的）
                query = select(UserScore.id).where(UserScore.user_id == user_id)
                if group_id is not None:
                    query = query.where(UserScore.group_id == group_id)
                else:
                    query = query.where(UserScore.group_id.is_(None))

                query = query.order_by(UserScore.id.desc())

                ids_result = await session.execute(query)
                all_ids = ids_result.scalars().all()

                # 保留第一个（最新的），删除其余的
                ids_to_delete = all_ids[1:]

                if ids_to_delete:
                    del_stmt = delete(UserScore).where(UserScore.id.in_(ids_to_delete))
                    await session.execute(del_stmt)
                    total_deleted += len(ids_to_delete)
                    print(f"  - 用户 {user_id} (群: {group_id}): 删除了 {len(ids_to_delete)} 条旧记录")

            await session.commit()
            print(f"\n🎉 清理完成！共删除了 {total_deleted} 条重复记录。")

    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(clean_duplicates())
