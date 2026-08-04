import asyncio
import json
from pathlib import Path

from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import create_async_engine

from scripts.init_database import ensure_tables_exist, iter_legacy_config_updates
from scripts.check_db import DB_PATH
from src.database.models import Model
from src.plugins.quiz.quiz_loader import load_quiz_bank


ROOT = Path(__file__).resolve().parents[1]


def test_quiz_bank_is_valid_and_uses_the_canonical_source_path():
    quiz_path = ROOT / "source" / "quiz_bank.json"
    questions = json.loads(quiz_path.read_text(encoding="utf-8-sig"))
    assert len(questions) >= 100
    assert {"category", "question", "options", "answer", "explanation"} <= questions[0].keys()
    assert "source/quiz_bank.json" in load_quiz_bank.__code__.co_consts
    assert DB_PATH == ROOT / "data" / "data.db"


def test_legacy_config_updates_preserve_group_and_private_push_preferences():
    legacy = {
        "knowledge_push": {
            "group_list": [{"id": 10001, "knowledge_push": False}],
            "friend_list": [{"id": 20002, "knowledge_push": True}],
        },
        "keyword_detection": {
            "group_list": [{"id": 10001, "keyword_detection": False}],
            "friend_list": [{"id": 20002, "keyword_detection": False}],
        },
    }
    assert list(iter_legacy_config_updates(legacy)) == [
        ("group", "10001", "knowledge_push", False),
        ("user", "20002", "knowledge_push", True),
        ("group", "10001", "keyword_detection", False),
    ]


def test_ensure_tables_exist_creates_the_complete_schema(tmp_path):
    database_path = tmp_path / "schema-check.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{database_path}")

    async def verify_schema():
        try:
            assert await ensure_tables_exist(engine) is True
            async with engine.connect() as connection:
                actual_tables = await connection.run_sync(
                    lambda sync_connection: set(inspect(sync_connection).get_table_names())
                )
            assert set(Model.metadata.tables) <= actual_tables
        finally:
            await engine.dispose()

    asyncio.run(verify_schema())
