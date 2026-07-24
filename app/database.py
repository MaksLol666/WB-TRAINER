import secrets
from datetime import datetime

import aiosqlite

from app.config import ADMINS, DATABASE
from app.constants import ROLE_ADMIN, ROLE_EMPLOYEE, ROLE_SUPER_ADMIN


def _now():
    return datetime.now().isoformat()


def generate_invite_code():
    return "WB-" + secrets.token_hex(3).upper()


def is_super_admin(user_id: int):
    return user_id in ADMINS


async def init_db():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE,
            full_name TEXT,
            username TEXT,
            role TEXT,
            pvz_id INTEGER,
            created_at TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS pvz(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            invite_code TEXT UNIQUE,
            owner_id INTEGER,
            created_at TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS questions(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT,
            difficulty INTEGER,
            type TEXT,
            question TEXT,
            answers TEXT,
            correct_answers TEXT,
            explanation TEXT,
            weight INTEGER DEFAULT 1,
            created_at TEXT
        )
        """)
        await db.execute("""
        CREATE TABLE IF NOT EXISTS results(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            score INTEGER,
            correct_answers INTEGER,
            total_questions INTEGER,
            created_at TEXT
        )
        """)
        await db.commit()


async def fetchone(query: str, params=()):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(query, params)
        return await cursor.fetchone()


async def fetchall(query: str, params=()):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(query, params)
        return await cursor.fetchall()


async def execute(query: str, params=()):
    async with aiosqlite.connect(DATABASE) as db:
        cursor = await db.execute(query, params)
        await db.commit()
        return cursor


async def get_user(telegram_id: int):
    return await fetchone("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,))


async def add_user(telegram_id: int, full_name: str, username: str | None, role: str, pvz_id: int | None):
    await execute(
        """INSERT OR IGNORE INTO users(telegram_id, full_name, username, role, pvz_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (telegram_id, full_name, username, role, pvz_id, _now()),
    )


async def update_user_pvz(telegram_id: int, pvz_id: int | None):
    await execute("UPDATE users SET pvz_id = ? WHERE telegram_id = ?", (pvz_id, telegram_id))


async def update_user_role(telegram_id: int, role: str):
    await execute("UPDATE users SET role = ? WHERE telegram_id = ?", (role, telegram_id))


async def delete_user(telegram_id: int):
    await execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))


async def get_user_role(telegram_id: int):
    user = await get_user(telegram_id)
    return user[4] if user else None


async def is_admin(telegram_id: int):
    return await get_user_role(telegram_id) == ROLE_ADMIN


async def is_employee(telegram_id: int):
    return await get_user_role(telegram_id) == ROLE_EMPLOYEE


async def get_pvz_users(pvz_id: int):
    return await fetchall("SELECT * FROM users WHERE pvz_id = ? ORDER BY id", (pvz_id,))


async def get_pvz_employees_only(pvz_id: int):
    return await fetchall("SELECT * FROM users WHERE pvz_id = ? AND role = ? ORDER BY id", (pvz_id, ROLE_EMPLOYEE))


async def get_pvz_owner(pvz_id: int):
    return await fetchone("SELECT * FROM users WHERE pvz_id = ? AND role = ? LIMIT 1", (pvz_id, ROLE_ADMIN))


async def create_super_admin_user(telegram_id: int, full_name: str, username: str | None):
    await add_user(telegram_id, full_name, username, ROLE_SUPER_ADMIN, None)


async def ensure_super_admin_exists(telegram_id: int, full_name: str, username: str | None):
    if is_super_admin(telegram_id) and await get_user(telegram_id) is None:
        await create_super_admin_user(telegram_id, full_name, username)


async def get_all_users():
    return await fetchall("SELECT * FROM users ORDER BY id")


async def get_all_admins():
    return await fetchall("SELECT * FROM users WHERE role = ? ORDER BY id", (ROLE_ADMIN,))


async def get_all_super_admins():
    return await fetchall("SELECT * FROM users WHERE role = ? ORDER BY id", (ROLE_SUPER_ADMIN,))


async def change_user_role(telegram_id: int, role: str):
    await update_user_role(telegram_id, role)


async def assign_owner_to_pvz(telegram_id: int, pvz_id: int):
    await set_pvz_owner(pvz_id, telegram_id)


async def remove_owner_from_pvz(telegram_id: int):
    await remove_pvz_owner(telegram_id)


async def delete_employee(telegram_id: int):
    await execute("DELETE FROM users WHERE telegram_id = ? AND role = ?", (telegram_id, ROLE_EMPLOYEE))


async def create_pvz(name: str, owner_id: int):
    code = generate_invite_code()
    cursor = await execute(
        "INSERT INTO pvz(name, invite_code, owner_id, created_at) VALUES (?, ?, ?, ?)",
        (name, code, owner_id, _now()),
    )
    return cursor.lastrowid, code


async def get_pvz_by_code(code: str):
    return await fetchone("SELECT * FROM pvz WHERE invite_code = ?", (code,))


async def get_pvz_by_id(pvz_id: int):
    return await fetchone("SELECT * FROM pvz WHERE id = ?", (pvz_id,))


async def get_admin_pvz(owner_id: int):
    return await fetchall("SELECT * FROM pvz WHERE owner_id = ? ORDER BY id", (owner_id,))


async def get_all_pvz():
    return await fetchall("SELECT * FROM pvz ORDER BY id")


async def rename_pvz(pvz_id: int, name: str):
    await execute("UPDATE pvz SET name = ? WHERE id = ?", (name, pvz_id))


async def delete_pvz(pvz_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("DELETE FROM users WHERE pvz_id = ?", (pvz_id,))
        await db.execute("DELETE FROM pvz WHERE id = ?", (pvz_id,))
        await db.commit()


async def set_pvz_owner(pvz_id: int, owner_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("UPDATE pvz SET owner_id = ? WHERE id = ?", (owner_id, pvz_id))
        await db.execute("UPDATE users SET role = ?, pvz_id = ? WHERE telegram_id = ?", (ROLE_ADMIN, pvz_id, owner_id))
        await db.commit()


async def remove_pvz_owner(owner_id: int):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("UPDATE users SET role = ?, pvz_id = NULL WHERE telegram_id = ?", (ROLE_EMPLOYEE, owner_id))
        await db.execute("UPDATE pvz SET owner_id = NULL WHERE owner_id = ?", (owner_id,))
        await db.commit()


async def is_owner_of_pvz(telegram_id: int, pvz_id: int):
    return any(pvz[0] == pvz_id for pvz in await get_admin_pvz(telegram_id))


async def add_question(category: str, difficulty: int, question_type: str, question: str, answers: str, correct_answers: str, explanation: str, weight: int = 1):
    cursor = await execute(
        """INSERT INTO questions(category, difficulty, type, question, answers, correct_answers, explanation, weight, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (category, difficulty, question_type, question, answers, correct_answers, explanation, weight, _now()),
    )
    return cursor.lastrowid


async def update_question(question_id: int, category: str, difficulty: int, question_type: str, question: str, answers: str, correct_answers: str, explanation: str, weight: int = 1):
    cursor = await execute(
        """UPDATE questions SET category = ?, difficulty = ?, type = ?, question = ?, answers = ?,
        correct_answers = ?, explanation = ?, weight = ? WHERE id = ?""",
        (category, difficulty, question_type, question, answers, correct_answers, explanation, weight, question_id),
    )
    return cursor.rowcount > 0


async def delete_question(question_id: int):
    cursor = await execute("DELETE FROM questions WHERE id = ?", (question_id,))
    return cursor.rowcount > 0


async def get_question(question_id: int):
    return await fetchone("SELECT * FROM questions WHERE id = ?", (question_id,))


async def question_exists(question_id: int):
    return await get_question(question_id) is not None


async def get_all_questions():
    return await fetchall("SELECT * FROM questions ORDER BY category, difficulty, id")


async def get_questions_count():
    result = await fetchone("SELECT COUNT(*) FROM questions")
    return result[0]


async def get_categories():
    rows = await fetchall("SELECT DISTINCT category FROM questions ORDER BY category")
    return [row[0] for row in rows]


async def get_questions_by_category(category: str):
    return await fetchall("SELECT * FROM questions WHERE category = ? ORDER BY difficulty, id", (category,))


async def get_random_questions(limit: int):
    return await fetchall("SELECT * FROM questions ORDER BY RANDOM() LIMIT ?", (limit,))


async def get_random_questions_by_category(category: str, limit: int):
    return await fetchall("SELECT * FROM questions WHERE category = ? ORDER BY RANDOM() LIMIT ?", (category, limit))


async def get_questions_by_type(question_type: str):
    return await fetchall("SELECT * FROM questions WHERE type = ? ORDER BY difficulty, id", (question_type,))


async def search_questions(text: str):
    return await fetchall("SELECT * FROM questions WHERE question LIKE ? ORDER BY id", (f"%{text}%",))


async def save_result(user_id: int, score: int, correct: int, total: int):
    await execute(
        "INSERT INTO results(user_id, score, correct_answers, total_questions, created_at) VALUES (?, ?, ?, ?, ?)",
        (user_id, score, correct, total, _now()),
    )


async def get_user_results(user_id: int):
    return await fetchall("SELECT * FROM results WHERE user_id = ? ORDER BY id DESC", (user_id,))


async def get_all_pvz_users():
    return await fetchall("SELECT * FROM users WHERE role != ? ORDER BY pvz_id, id", (ROLE_SUPER_ADMIN,))


async def get_system_statistics():
    pvz_count = (await fetchone("SELECT COUNT(*) FROM pvz"))[0]
    owners_count = (await fetchone("SELECT COUNT(*) FROM users WHERE role = ?", (ROLE_ADMIN,)))[0]
    employees_count = (await fetchone("SELECT COUNT(*) FROM users WHERE role = ?", (ROLE_EMPLOYEE,)))[0]
    tests_count = (await fetchone("SELECT COUNT(*) FROM results"))[0]
    return pvz_count, owners_count, employees_count, tests_count
