# ============================================================
# WB TRAINER
# Версия: 0.2
# Полная переработка структуры
# ============================================================

import asyncio
import secrets
import logging

from datetime import datetime

import aiosqlite


from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from aiogram.filters import CommandStart

from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup


# ============================================================
# LOGGING
# ============================================================


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)



# ============================================================
# SETTINGS
# ============================================================


TOKEN = "8645122183:AAGgVMowY4tEBfnOpFr7bqssb0tfWalskTM"


ADMINS = [
    1691654877
]


DATABASE = "wb_trainer.db"



# ============================================================
# CONSTANTS
# ============================================================


ROLE_ADMIN = "admin"
ROLE_EMPLOYEE = "employee"


QUESTION_SINGLE = "single"
QUESTION_MULTI = "multi"
QUESTION_SEQUENCE = "sequence"
QUESTION_SITUATION = "situation"



# ============================================================
# BOT
# ============================================================


bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(
        parse_mode=ParseMode.HTML
    )
)


storage = MemoryStorage()


dp = Dispatcher(
    storage=storage
)


router = Router()


dp.include_router(router)



# ============================================================
# FSM
# ============================================================


class RegisterState(StatesGroup):

    waiting_invite_code = State()



class CreatePVZState(StatesGroup):

    waiting_name = State()



class AddQuestionState(StatesGroup):

    waiting_category = State()
    waiting_type = State()
    waiting_question = State()
    waiting_answers = State()
    waiting_correct = State()
    waiting_explanation = State()



class TestState(StatesGroup):

    answering = State()




# ============================================================
# DATABASE INIT
# ============================================================


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





# ============================================================
# SERVICE FUNCTIONS
# ============================================================



def generate_invite_code():

    return "WB-" + secrets.token_hex(3).upper()




def is_admin(user_id: int):

    return user_id in ADMINS






# ============================================================
# USERS DATABASE
# ============================================================



async def get_user(
        telegram_id: int
):


    async with aiosqlite.connect(DATABASE) as db:


        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
            (
                telegram_id,
            )
        )


        return await cursor.fetchone()







async def add_user(
        telegram_id: int,
        full_name: str,
        username: str | None,
        role: str,
        pvz_id: int | None
):


    async with aiosqlite.connect(DATABASE) as db:


        await db.execute(
            """
            INSERT OR IGNORE INTO users

            (
                telegram_id,
                full_name,
                username,
                role,
                pvz_id,
                created_at
            )


            VALUES (?, ?, ?, ?, ?, ?)

            """,

            (
                telegram_id,
                full_name,
                username,
                role,
                pvz_id,
                datetime.now().isoformat()
            )

        )


        await db.commit()






async def update_user_pvz(
        telegram_id: int,
        pvz_id: int
):


    async with aiosqlite.connect(DATABASE) as db:


        await db.execute(
            """
            UPDATE users

            SET pvz_id = ?

            WHERE telegram_id = ?

            """,

            (
                pvz_id,
                telegram_id
            )
        )


        await db.commit()






async def get_user_role(
        telegram_id: int
):


    user = await get_user(
        telegram_id
    )


    if not user:

        return None


    return user[4]

# ============================================================
# KEYBOARDS
# ============================================================


def employee_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📚 Начать тест"
                )
            ],
            [
                KeyboardButton(
                    text="📊 Мои результаты"
                )
            ],
            [
                KeyboardButton(
                    text="👤 Профиль"
                )
            ]
        ],
        resize_keyboard=True
    )





def admin_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🏢 Мои ПВЗ"
                )
            ],
            [
                KeyboardButton(
                    text="👥 Сотрудники"
                )
            ],
            [
                KeyboardButton(
                    text="📝 Управление тестами"
                )
            ],
            [
                KeyboardButton(
                    text="📊 Статистика"
                )
            ],
            [
                KeyboardButton(
                    text="➕ Создать ПВЗ"
                )
            ]
        ],
        resize_keyboard=True
    )





def registration_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🔑 Ввести код ПВЗ"
                )
            ]
        ],
        resize_keyboard=True
    )





def back_menu():

    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="⬅ Назад"
                )
            ]
        ],
        resize_keyboard=True
    )





# ============================================================
# ADMIN USER CREATION
# ============================================================


async def create_admin_user(
        telegram_id: int,
        full_name: str,
        username: str | None
):


    async with aiosqlite.connect(DATABASE) as db:


        await db.execute(
            """
            INSERT OR IGNORE INTO users

            (
                telegram_id,
                full_name,
                username,
                role,
                pvz_id,
                created_at
            )

            VALUES (?, ?, ?, ?, ?, ?)

            """,

            (
                telegram_id,
                full_name,
                username,
                ROLE_ADMIN,
                None,
                datetime.now().isoformat()
            )
        )


        await db.commit()






async def ensure_admin_exists(
        telegram_id: int,
        full_name: str,
        username: str | None
):


    if not is_admin(telegram_id):

        return



    user = await get_user(
        telegram_id
    )


    if user is None:


        await create_admin_user(
            telegram_id,
            full_name,
            username
        )







# ============================================================
# PVZ DATABASE
# ============================================================



async def create_pvz(
        name: str,
        owner_id: int
):


    code = generate_invite_code()



    async with aiosqlite.connect(DATABASE) as db:


        cursor = await db.execute(
            """
            INSERT INTO pvz

            (
                name,
                invite_code,
                owner_id,
                created_at
            )


            VALUES (?, ?, ?, ?)

            """,

            (
                name,
                code,
                owner_id,
                datetime.now().isoformat()
            )
        )


        await db.commit()


        return cursor.lastrowid, code






async def get_pvz_by_code(
        code: str
):


    async with aiosqlite.connect(DATABASE) as db:


        cursor = await db.execute(
            """
            SELECT *

            FROM pvz

            WHERE invite_code = ?

            """,

            (
                code,
            )
        )


        return await cursor.fetchone()






async def get_admin_pvz(
        owner_id: int
):


    async with aiosqlite.connect(DATABASE) as db:


        cursor = await db.execute(
            """
            SELECT *

            FROM pvz

            WHERE owner_id = ?

            """,

            (
                owner_id,
            )
        )


        return await cursor.fetchall()






async def get_pvz_employees(
        pvz_id: int
):


    async with aiosqlite.connect(DATABASE) as db:


        cursor = await db.execute(
            """
            SELECT *

            FROM users

            WHERE pvz_id = ?

            """,

            (
                pvz_id,
            )
        )


        return await cursor.fetchall()
