# ============================================================
# WB TRAINER
# Версия: 0.1
# Автор идеи: tg - @slayip + ChatGPT
# Все права защищены.
# ============================================================

import asyncio
import json
import random
import secrets
from datetime import datetime

import aiosqlite

from aiogram import Bot, Dispatcher, Router, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = "8645122183:AAGgVMowY4tEBfnOpFr7bqssb0tfWalskTM"

ADMINS = [
    1691654877,
]

DATABASE = "wb_trainer.db"

# ============================================================
# КОНСТАНТЫ
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

dp = Dispatcher(storage=storage)

router = Router()

dp.include_router(router)

# ============================================================
# СОСТОЯНИЯ (FSM)
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
# DATABASE
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
# СЛУЖЕБНЫЕ ФУНКЦИИ
# ============================================================

def generate_invite_code():
    return "WB-" + secrets.token_hex(3).upper()

# ============================================================
# DATABASE FUNCTIONS
# ============================================================


async def get_user(telegram_id: int):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *
            FROM users
            WHERE telegram_id = ?
            """,
            (telegram_id,)
        )

        user = await cursor.fetchone()

        return user



async def add_user(
        telegram_id: int,
        full_name: str,
        username: str | None,
        role: str = ROLE_EMPLOYEE,
        pvz_id: int | None = None
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



async def get_pvz_by_code(code: str):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM pvz

            WHERE invite_code = ?

            """,
            (code,)
        )

        pvz = await cursor.fetchone()

        return pvz



async def get_pvz_by_id(pvz_id: int):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM pvz

            WHERE id = ?

            """,
            (pvz_id,)
        )

        return await cursor.fetchone()



async def get_pvz_employees(pvz_id: int):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM users

            WHERE pvz_id = ?

            """,
            (pvz_id,)
        )

        return await cursor.fetchall()



async def save_result(
        user_id: int,
        score: int,
        correct: int,
        total: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            INSERT INTO results
            (
                user_id,
                score,
                correct_answers,
                total_questions,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)

            """,
            (
                user_id,
                score,
                correct,
                total,
                datetime.now().isoformat()
            )
        )

        await db.commit()



async def get_user_results(user_id: int):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM results

            WHERE user_id = ?

            ORDER BY id DESC

            """,
            (user_id,)
        )

        return await cursor.fetchall()

# ============================================================
# KEYBOARDS
# ============================================================


def employee_menu():

    keyboard = ReplyKeyboardMarkup(
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

    return keyboard



def admin_menu():

    keyboard = ReplyKeyboardMarkup(
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

    return keyboard



def registration_menu():

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🔑 Ввести код ПВЗ"
                )
            ]
        ],
        resize_keyboard=True
    )

    return keyboard



def back_menu():

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="⬅ Назад"
                )
            ]
        ],
        resize_keyboard=True
    )

    return keyboard



def cancel_menu():

    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="❌ Отмена"
                )
            ]
        ],
        resize_keyboard=True
    )

    return keyboard

# ============================================================
# USER MANAGEMENT
# ============================================================


def is_admin(telegram_id: int) -> bool:

    return telegram_id in ADMINS



async def create_admin_user(
        telegram_id: int,
        full_name: str
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            INSERT OR IGNORE INTO users
            (
                telegram_id,
                full_name,
                role,
                pvz_id,
                created_at
            )

            VALUES (?, ?, ?, ?, ?)

            """,
            (
                telegram_id,
                full_name,
                ROLE_ADMIN,
                None,
                datetime.now().isoformat()
            )
        )

        await db.commit()



async def get_user_role(
        telegram_id: int
):

    user = await get_user(telegram_id)

    if user is None:
        return None

    return user[3]



async def ensure_admin_exists(
        telegram_id: int,
        full_name: str
):

    if not is_admin(telegram_id):
        return


    user = await get_user(telegram_id)


    if user is None:

        await create_admin_user(
            telegram_id,
            full_name
        )



async def get_user_id(
        telegram_id: int
):

    user = await get_user(telegram_id)


    if user is None:
        return None


    return user[0]



async def user_is_registered(
        telegram_id: int
):

    user = await get_user(telegram_id)

    return user is not None



async def change_user_role(
        telegram_id: int,
        role: str
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            UPDATE users

            SET role = ?

            WHERE telegram_id = ?

            """,
            (
                role,
                telegram_id
            )
        )

        await db.commit()

# ============================================================
# START / REGISTRATION
# ============================================================


@router.message(CommandStart())
async def start_command(
        message: Message,
        state: FSMContext
):

    telegram_id = message.from_user.id
    full_name = message.from_user.full_name
    username = message.from_user.username

    # Проверяем главного администратора

    await ensure_admin_exists(
        telegram_id,
        full_name
    )


    user = await get_user(
        telegram_id
    )


    # Если пользователь уже есть

    if user:


        role = user[3]


        if role == ROLE_ADMIN:

            await message.answer(
                "👑 <b>WB TRAINER</b>\n\n"
                "Вы вошли как главный администратор.",
                reply_markup=admin_menu()
            )


        elif role == ROLE_EMPLOYEE:

            await message.answer(
                "🎓 <b>WB TRAINER</b>\n\n"
                "Добро пожаловать!\n"
                "Выберите действие:",
                reply_markup=employee_menu()
            )


        return



    # Если пользователь новый

    await message.answer(
        "🎓 <b>WB TRAINER</b>\n\n"
        "Вы ещё не зарегистрированы.\n\n"
        "Введите код вашего ПВЗ:",
        reply_markup=registration_menu()
    )


    await state.set_state(
        RegisterState.waiting_invite_code
    )



# ============================================================
# РЕГИСТРАЦИЯ ПО КОДУ ПВЗ
# ============================================================


@router.message(
    RegisterState.waiting_invite_code
)
async def register_by_code(
        message: Message,
        state: FSMContext
):

    code = message.text.strip().upper()


    pvz = await get_pvz_by_code(
        code
    )


    if not pvz:

        await message.answer(
            "❌ Такой код ПВЗ не найден.\n\n"
            "Проверьте код и попробуйте снова."
        )

        return



    telegram_id = message.from_user.id
    full_name = message.from_user.full_name


    await add_user(
    telegram_id,
    full_name,
    username,
    ROLE_EMPLOYEE,
    pvz[0]
)


    await state.clear()


    await message.answer(
        "✅ Регистрация успешно завершена!\n\n"
        "Теперь вы можете проходить обучение и тесты.",
        reply_markup=employee_menu()
    )

# ============================================================
# CREATE PVZ (ADMIN)
# ============================================================


@router.message(
    F.text == "➕ Создать ПВЗ"
)
async def create_pvz_start(
        message: Message,
        state: FSMContext
):

    telegram_id = message.from_user.id


    if not is_admin(telegram_id):

        await message.answer(
            "❌ У вас нет доступа к этому разделу."
        )

        return


    await message.answer(
        "🏢 <b>Создание нового ПВЗ</b>\n\n"
        "Введите название точки:"
    )


    await state.set_state(
        CreatePVZState.waiting_name
    )



@router.message(
    CreatePVZState.waiting_name
)
async def create_pvz_finish(
        message: Message,
        state: FSMContext
):

    name = message.text.strip()


    telegram_id = message.from_user.id


    pvz_id, code = await create_pvz(
        name,
        telegram_id
    )


    await state.clear()


    await message.answer(
        "✅ <b>ПВЗ создан!</b>\n\n"
        f"🏢 Название:\n{name}\n\n"
        f"🔑 Код подключения сотрудников:\n"
        f"<code>{code}</code>\n\n"
        "Передайте этот код сотрудникам.",
        reply_markup=admin_menu()
    )

# ============================================================
# PVZ MANAGEMENT
# ============================================================


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
            (owner_id,)
        )

        return await cursor.fetchall()



@router.message(
    F.text == "🏢 Мои ПВЗ"
)
async def my_pvz(
        message: Message
):

    telegram_id = message.from_user.id


    if not is_admin(telegram_id):

        await message.answer(
            "❌ Нет доступа."
        )

        return



    pvzs = await get_admin_pvz(
        telegram_id
    )


    if not pvzs:

        await message.answer(
            "🏢 У вас пока нет созданных ПВЗ."
        )

        return



    text = (
        "🏢 <b>Ваши ПВЗ:</b>\n\n"
    )


    for pvz in pvzs:

        employees = await get_pvz_employees(
            pvz[0]
        )


        text += (
            f"📍 <b>{pvz[1]}</b>\n"
            f"🔑 Код: <code>{pvz[2]}</code>\n"
            f"👥 Сотрудников: {len(employees)}\n\n"
        )


    await message.answer(
        text,
        reply_markup=admin_menu()
        )

# ============================================================
# EMPLOYEES MANAGEMENT
# ============================================================


async def get_all_pvz_employees(
        owner_id: int
):

    pvzs = await get_admin_pvz(
        owner_id
    )


    employees = []


    async with aiosqlite.connect(DATABASE) as db:

        for pvz in pvzs:

            cursor = await db.execute(
                """
                SELECT *

                FROM users

                WHERE pvz_id = ?

                """,
                (pvz[0],)
            )

            users = await cursor.fetchall()


            employees.append(
                {
                    "pvz": pvz,
                    "users": users
                }
            )


    return employees



@router.message(
    F.text == "👥 Сотрудники"
)
async def employees_list(
        message: Message
):

    telegram_id = message.from_user.id


    if not is_admin(telegram_id):

        await message.answer(
            "❌ Нет доступа."
        )

        return



    data = await get_all_pvz_employees(
        telegram_id
    )


    if not data:

        await message.answer(
            "👥 Сотрудников пока нет."
        )

        return



    text = (
        "👥 <b>Сотрудники ваших ПВЗ:</b>\n\n"
    )


    for item in data:

        pvz = item["pvz"]
        users = item["users"]


        text += (
            f"📍 <b>{pvz[1]}</b>\n\n"
        )


        if not users:

            text += (
                "Нет сотрудников\n\n"
            )

            continue


        for user in users:

                name = (
    f"@{user[3]}"
    if user[3]
    else user[2]
)

text += (
    f"👤 {name}\n"
    f"Имя: {user[2]}\n"
    f"Роль: {user[4]}\n"
    f"ID: <code>{user[1]}</code>\n"
    f"Дата: {user[6][:10]}\n\n"
)

    await message.answer(
        text,
        reply_markup=admin_menu()
    )
    
# ============================================================
# START BOT
# ============================================================


async def main():

    print("🚀 WB TRAINER запускается...")


    await init_db()


    print("✅ База данных готова")


    await dp.start_polling(
        bot
    )



if __name__ == "__main__":

    asyncio.run(main())
