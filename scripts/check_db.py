"""Inspect the local AntiFraudBot SQLite database without modifying it."""

from pathlib import Path
import sqlite3


ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "data.db"


def main() -> int:
    if not DB_PATH.exists():
        print(f"❌ {DB_PATH.relative_to(ROOT)} 不存在")
        return 1

    with sqlite3.connect(DB_PATH) as connection:
        cursor = connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        print(f"📂 数据库中的表: {tables}")

        for table in ("keywords", "quiz_questions", "user_scores"):
            if table not in tables:
                print(f"❌ 未找到 {table} 表")
                return 1
            cursor.execute(f"SELECT count(*) FROM {table}")
            print(f"📊 {table} 表行数: {cursor.fetchone()[0]}")

        cursor.execute(
            """
            SELECT user_id, group_id, count(*) AS duplicate_count
            FROM user_scores
            GROUP BY user_id, group_id
            HAVING duplicate_count > 1
            """
        )
        duplicates = cursor.fetchall()
        print(f"⚠️ user_scores 重复组: {len(duplicates)}")
        if duplicates:
            return 1

    print("✅ 数据库结构检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
