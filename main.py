# ============================================================
# WB TRAINER
# Версия: 0.3
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
# ROLES
# ============================================================

ROLE_SUPER_ADMIN = "super_admin"
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



class DeleteState(StatesGroup):

    waiting_employee_id = State()

    waiting_pvz_id = State()

    confirm_delete = State()




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


def is_super_admin(
        user_id: int
):

    return user_id in ADMINS


async def is_admin(
        telegram_id: int
):

    user = await get_user(
        telegram_id
    )

    if not user:

        return False

    return user[4] == ROLE_ADMIN


async def is_employee(
        telegram_id: int
):

    user = await get_user(
        telegram_id
    )

    if not user:

        return False

    return user[4] == ROLE_EMPLOYEE


async def is_owner_of_pvz(
        telegram_id: int,
        pvz_id: int
):

    pvzs = await get_admin_pvz(
        telegram_id
    )

    for pvz in pvzs:

        if pvz[0] == pvz_id:

            return True

    return False





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
        pvz_id: int | None
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



async def update_user_role(
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



async def delete_user(
        telegram_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            DELETE FROM users

            WHERE telegram_id = ?
            """,
            (
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



async def get_pvz_users(
        pvz_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM users

            WHERE pvz_id = ?

            ORDER BY id
            """,
            (
                pvz_id,
            )
        )

        return await cursor.fetchall()



async def get_pvz_employees_only(
        pvz_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM users

            WHERE pvz_id = ?
            AND role = ?

            ORDER BY id
            """,
            (
                pvz_id,
                ROLE_EMPLOYEE
            )
        )

        return await cursor.fetchall()



async def get_pvz_owner(
        pvz_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM users

            WHERE pvz_id = ?
            AND role = ?

            LIMIT 1
            """,
            (
                pvz_id,
                ROLE_ADMIN
            )
        )

        return await cursor.fetchone()

# ============================================================
# KEYBOARDS
# ============================================================


def super_admin_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="🏢 Все ПВЗ"
                )
            ],

            [
                KeyboardButton(
                    text="👥 Владельцы ПВЗ"
                )
            ],

            [
                KeyboardButton(
                    text="👤 Все сотрудники"
                )
            ],

            [
                KeyboardButton(
                    text="📝 Управление тестами"
                )
            ],

            [
                KeyboardButton(
                    text="📊 Общая статистика"
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
                    text="📊 Статистика ПВЗ"
                )
            ],

            [
                KeyboardButton(
                    text="🔑 Код приглашения"
                )
            ]

        ],
        resize_keyboard=True
    )





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





def owner_management_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="👥 Добавить сотрудника"
                )
            ],

            [
                KeyboardButton(
                    text="❌ Удалить сотрудника"
                )
            ],

            [
                KeyboardButton(
                    text="⬅ Назад"
                )
            ]

        ],
        resize_keyboard=True
    )





def delete_confirm_menu():

    return ReplyKeyboardMarkup(
        keyboard=[

            [
                KeyboardButton(
                    text="✅ Подтвердить"
                )
            ],

            [
                KeyboardButton(
                    text="❌ Отмена"
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
# SUPER ADMIN USER CREATION
# ============================================================


async def create_super_admin_user(
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
                ROLE_SUPER_ADMIN,
                None,
                datetime.now().isoformat()
            )
        )


        await db.commit()





async def ensure_super_admin_exists(
        telegram_id: int,
        full_name: str,
        username: str | None
):

    if not is_super_admin(telegram_id):

        return


    user = await get_user(
        telegram_id
    )


    if user is None:

        await create_super_admin_user(
            telegram_id,
            full_name,
            username
        )





# ============================================================
# SUPER ADMIN FUNCTIONS
# ============================================================



async def get_all_users():

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM users

            ORDER BY id
            """
        )


        return await cursor.fetchall()





async def get_all_admins():

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM users

            WHERE role = ?

            ORDER BY id
            """,
            (
                ROLE_ADMIN,
            )
        )


        return await cursor.fetchall()





async def get_all_super_admins():

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM users

            WHERE role = ?

            ORDER BY id
            """,
            (
                ROLE_SUPER_ADMIN,
            )
        )


        return await cursor.fetchall()





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





async def assign_owner_to_pvz(
        telegram_id: int,
        pvz_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            UPDATE users

            SET
                role = ?,
                pvz_id = ?

            WHERE telegram_id = ?
            """,
            (
                ROLE_ADMIN,
                pvz_id,
                telegram_id
            )
        )


        await db.execute(
            """
            UPDATE pvz

            SET owner_id = ?

            WHERE id = ?
            """,
            (
                telegram_id,
                pvz_id
            )
        )


        await db.commit()





async def remove_owner_from_pvz(
        telegram_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            UPDATE users

            SET
                role = ?,
                pvz_id = NULL

            WHERE telegram_id = ?
            """,
            (
                ROLE_EMPLOYEE,
                telegram_id
            )
        )


        await db.execute(
            """
            UPDATE pvz

            SET owner_id = NULL

            WHERE owner_id = ?
            """,
            (
                telegram_id
            )
        )


        await db.commit()





async def delete_employee(
        telegram_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            DELETE FROM users

            WHERE telegram_id = ?

            AND role = ?
            """,
            (
                telegram_id,
                ROLE_EMPLOYEE
            )
        )


        await db.commit()


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





async def get_pvz_by_id(
        pvz_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM pvz

            WHERE id = ?
            """,
            (
                pvz_id,
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

            ORDER BY id
            """,
            (
                owner_id,
            )
        )


        return await cursor.fetchall()





async def rename_pvz(
        pvz_id: int,
        name: str
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            UPDATE pvz

            SET name = ?

            WHERE id = ?
            """,
            (
                name,
                pvz_id
            )
        )


        await db.commit()





async def delete_pvz(
        pvz_id: int
):

    async with aiosqlite.connect(DATABASE) as db:


        # удаляем сотрудников ПВЗ

        await db.execute(
            """
            DELETE FROM users

            WHERE pvz_id = ?
            """,
            (
                pvz_id,
            )
        )


        # удаляем сам ПВЗ

        await db.execute(
            """
            DELETE FROM pvz

            WHERE id = ?
            """,
            (
                pvz_id,
            )
        )


        await db.commit()





async def set_pvz_owner(
        pvz_id: int,
        owner_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            UPDATE pvz

            SET owner_id = ?

            WHERE id = ?
            """,
            (
                owner_id,
                pvz_id
            )
        )


        await db.execute(
            """
            UPDATE users

            SET
                role = ?,
                pvz_id = ?

            WHERE telegram_id = ?
            """,
            (
                ROLE_ADMIN,
                pvz_id,
                owner_id
            )
        )


        await db.commit()





async def remove_pvz_owner(
        owner_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            UPDATE users

            SET
                role = ?,
                pvz_id = NULL

            WHERE telegram_id = ?
            """,
            (
                ROLE_EMPLOYEE,
                owner_id
            )
        )


        await db.execute(
            """
            UPDATE pvz

            SET owner_id = NULL

            WHERE owner_id = ?
            """,
            (
                owner_id,
            )
        )


        await db.commit()

# ============================================================
# SAVE TEST RESULT
# ============================================================


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


# ============================================================
# GET USER RESULTS
# ============================================================


async def get_user_results(
        user_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM results

            WHERE user_id = ?

            ORDER BY id DESC

            """,
            (
                user_id,
            )
        )

        return await cursor.fetchall()

# ============================================================
# GET PVZ BY ID
# ============================================================


async def get_pvz_by_id(
        pvz_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM pvz

            WHERE id = ?

            """,
            (
                pvz_id,
            )
        )


        return await cursor.fetchone()

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


    # создаём супер админа при первом входе

    await ensure_super_admin_exists(
        telegram_id,
        full_name,
        username
    )


    user = await get_user(
        telegram_id
    )



    if user:


        role = user[4]



        if role == ROLE_SUPER_ADMIN:


            await message.answer(
                "👑 <b>WB TRAINER</b>\n\n"
                "Вы вошли как главный администратор.",
                reply_markup=super_admin_menu()
            )


        elif role == ROLE_ADMIN:


            await message.answer(
                "🏢 <b>WB TRAINER</b>\n\n"
                "Вы вошли как владелец ПВЗ.",
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
# EMPLOYEE REGISTRATION
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
            "❌ Такой код ПВЗ не найден."
        )

        return




    telegram_id = message.from_user.id

    full_name = message.from_user.full_name

    username = message.from_user.username



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
        f"📍 ПВЗ: <b>{pvz[1]}</b>\n\n"
        "Теперь вы можете проходить обучение.",
        reply_markup=employee_menu()
    )


# ============================================================
# CREATE PVZ
# ============================================================


@router.message(
    F.text == "➕ Создать ПВЗ"
)
async def create_pvz_start(
        message: Message,
        state: FSMContext
):


    if not is_super_admin(
        message.from_user.id
    ):


        await message.answer(
            "❌ Создавать ПВЗ может только главный администратор."
        )

        return



    await message.answer(
        "🏢 Введите название нового ПВЗ:"
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


    if not is_super_admin(
        message.from_user.id
    ):


        await state.clear()

        await message.answer(
            "❌ Нет доступа."
        )

        return



    name = message.text.strip()



    if len(name) < 2:


        await message.answer(
            "❌ Название слишком короткое."
        )

        return




    pvz_id, code = await create_pvz(
        name,
        message.from_user.id
    )



    await state.clear()



    await message.answer(
        "✅ <b>ПВЗ создан!</b>\n\n"
        f"📍 Название:\n"
        f"<b>{name}</b>\n\n"
        f"🆔 ID ПВЗ: <code>{pvz_id}</code>\n\n"
        f"🔑 Код сотрудников:\n"
        f"<code>{code}</code>\n\n"
        "Передайте этот код сотрудникам для регистрации.",
        reply_markup=super_admin_menu()
    )


# ============================================================
# MY PVZ
# ============================================================


@router.message(
    F.text == "🏢 Мои ПВЗ"
)
async def my_pvz(
        message: Message
):


    user_id = message.from_user.id


    user = await get_user(
        user_id
    )


    if not user:


        await message.answer(
            "❌ Пользователь не найден."
        )

        return



    role = user[4]



    # =========================
    # ВЛАДЕЛЕЦ ПВЗ
    # =========================

    if role == ROLE_ADMIN:


        pvzs = await get_admin_pvz(
            user_id
        )


        if not pvzs:


            await message.answer(
                "🏢 У вас пока нет ПВЗ."
            )

            return



        text = (
            "🏢 <b>Ваши ПВЗ:</b>\n\n"
        )


        for pvz in pvzs:


            employees = await get_pvz_employees_only(
                pvz[0]
            )


            text += (
                f"📍 <b>{pvz[1]}</b>\n"
                f"🔑 Код сотрудников: "
                f"<code>{pvz[2]}</code>\n"
                f"👥 Сотрудников: {len(employees)}\n\n"
            )



        await message.answer(
            text,
            reply_markup=admin_menu()
        )

        return





    # =========================
    # SUPER ADMIN
    # =========================


    if role == ROLE_SUPER_ADMIN:


        async with aiosqlite.connect(DATABASE) as db:


            cursor = await db.execute(
                """
                SELECT *

                FROM pvz

                ORDER BY id
                """
            )


            pvzs = await cursor.fetchall()



        if not pvzs:


            await message.answer(
                "🏢 ПВЗ пока нет."
            )

            return



        text = (
            "👑 <b>Все ПВЗ системы:</b>\n\n"
        )


        for pvz in pvzs:


            owner = "нет"


            if pvz[3]:


                owner_user = await get_user(
                    pvz[3]
                )


                if owner_user:

                    if owner_user[3]:

                        owner = "@" + owner_user[3]

                    else:

                        owner = owner_user[2]



            employees = await get_pvz_employees_only(
                pvz[0]
            )


            text += (
                f"📍 <b>{pvz[1]}</b>\n"
                f"🆔 ID: <code>{pvz[0]}</code>\n"
                f"👤 Владелец: {owner}\n"
                f"👥 Сотрудников: {len(employees)}\n\n"
            )



        await message.answer(
            text,
            reply_markup=super_admin_menu()
        )

        return




    await message.answer(
        "❌ Нет доступа."
        )


# ============================================================
# EMPLOYEES LIST
# ============================================================


async def get_pvz_employees_only(
        pvz_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM users

            WHERE pvz_id = ?

            AND role = ?

            ORDER BY id
            """,
            (
                pvz_id,
                ROLE_EMPLOYEE
            )
        )

        return await cursor.fetchall()





async def get_all_pvz_users():

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *

            FROM users

            WHERE role != ?

            ORDER BY pvz_id, id
            """,
            (
                ROLE_SUPER_ADMIN,
            )
        )

        return await cursor.fetchall()





@router.message(
    F.text == "👥 Сотрудники"
)
async def employees_list(
        message: Message
):


    user = await get_user(
        message.from_user.id
    )


    if not user:


        await message.answer(
            "❌ Пользователь не найден."
        )

        return



    role = user[4]



    # ==================================
    # ВЛАДЕЛЕЦ ПВЗ
    # ==================================

    if role == ROLE_ADMIN:


        pvzs = await get_admin_pvz(
            message.from_user.id
        )


        if not pvzs:


            await message.answer(
                "🏢 У вас нет ПВЗ."
            )

            return



        text = (
            "👥 <b>Сотрудники ваших ПВЗ:</b>\n\n"
        )


        for pvz in pvzs:


            employees = await get_pvz_employees_only(
                pvz[0]
            )


            text += (
                f"📍 <b>{pvz[1]}</b>\n\n"
            )


            if not employees:


                text += (
                    "Сотрудников нет\n\n"
                )

                continue



            for employee in employees:


                username = employee[3]


                if username:

                    name = "@" + username

                else:

                    name = employee[2]



                text += (
                    f"👤 {name}\n"
                    f"ID: <code>{employee[1]}</code>\n"
                    f"Дата: {employee[6][:10]}\n\n"
                )



        await message.answer(
            text,
            reply_markup=admin_menu()
        )

        return





    # ==================================
    # SUPER ADMIN
    # ==================================

    if role == ROLE_SUPER_ADMIN:


        users = await get_all_pvz_users()



        if not users:


            await message.answer(
                "👥 Пользователей пока нет."
            )

            return



        text = (
            "👑 <b>Все пользователи системы:</b>\n\n"
        )



        current_pvz = None



        for employee in users:


            pvz_id = employee[5]


            if pvz_id != current_pvz:


                current_pvz = pvz_id


                pvz = await get_pvz_by_id(
                    pvz_id
                )


                if pvz:


                    text += (
                        f"📍 <b>{pvz[1]}</b>\n"
                    )



            username = employee[3]


            if username:

                name = "@" + username

            else:

                name = employee[2]



            text += (
                f"👤 {name}\n"
                f"Роль: {employee[4]}\n"
                f"ID: <code>{employee[1]}</code>\n\n"
            )



        await message.answer(
            text,
            reply_markup=super_admin_menu()
        )

        return





    await message.answer(
        "❌ Нет доступа."
    )

# ============================================================
# RESULTS
# ============================================================


@router.message(
    F.text == "📊 Мои результаты"
)
async def my_results(
        message: Message
):


    user = await get_user(
        message.from_user.id
    )


    if not user:


        await message.answer(
            "❌ Вы не зарегистрированы."
        )

        return



    results = await get_user_results(
        user[0]
    )



    if not results:


        await message.answer(
            "📊 У вас пока нет результатов тестов."
        )

        return



    text = (
        "📊 <b>Ваши результаты:</b>\n\n"
    )



    for result in results:


        text += (
            f"🏆 Баллы: {result[2]}\n"
            f"✅ Правильных: {result[3]}/{result[4]}\n"
            f"📅 {result[5][:10]}\n\n"
        )



    await message.answer(
        text,
        reply_markup=employee_menu()
    )





# ============================================================
# PROFILE
# ============================================================



@router.message(
    F.text == "👤 Профиль"
)
async def profile(
        message: Message
):


    user = await get_user(
        message.from_user.id
    )


    if not user:


        await message.answer(
            "❌ Профиль не найден."
        )

        return




    username = user[3]



    if username:

        username = "@" + username

    else:

        username = "нет"




    pvz_text = "Нет ПВЗ"



    if user[5]:


        pvz = await get_pvz_by_id(
            user[5]
        )


        if pvz:

            pvz_text = pvz[1]




    await message.answer(
        "👤 <b>Профиль</b>\n\n"
        f"Имя: {user[2]}\n"
        f"Username: {username}\n"
        f"Роль: {user[4]}\n"
        f"ПВЗ: {pvz_text}\n"
        f"ID: <code>{user[1]}</code>"
    )





# ============================================================
# TEMP TEST SYSTEM
# ============================================================


@router.message(
    F.text == "📚 Начать тест"
)
async def start_test(
        message: Message
):


    await message.answer(
        "📝 Тестовая система пока в разработке.\n\n"
        "Следующий этап — добавление базы вопросов WB."
    )


# ============================================================
# DELETE EMPLOYEE + DELETE PVZ
# ============================================================


@router.message(
    F.text == "❌ Удалить сотрудника"
)
async def delete_employee_start(
        message: Message,
        state: FSMContext
):


    user = await get_user(
        message.from_user.id
    )


    if not user:


        await message.answer(
            "❌ Пользователь не найден."
        )

        return



    if user[4] not in [
        ROLE_ADMIN,
        ROLE_SUPER_ADMIN
    ]:


        await message.answer(
            "❌ Нет доступа."
        )

        return




    await message.answer(
        "Введите Telegram ID сотрудника, которого нужно удалить:"
    )


    await state.set_state(
        DeleteState.waiting_employee_id
    )





@router.message(
    DeleteState.waiting_employee_id
)
async def delete_employee_confirm(
        message: Message,
        state: FSMContext
):


    try:

        employee_id = int(
            message.text
        )

    except:


        await message.answer(
            "❌ ID должен быть числом."
        )

        return




    employee = await get_user(
        employee_id
    )



    if not employee:


        await message.answer(
            "❌ Пользователь не найден."
        )

        await state.clear()

        return




    current_user = await get_user(
        message.from_user.id
    )



    # владелец может удалять только своих

    if current_user[4] == ROLE_ADMIN:


        if employee[5] != current_user[5]:


            await message.answer(
                "❌ Этот сотрудник не относится к вашему ПВЗ."
            )

            await state.clear()

            return




    await state.update_data(
        delete_employee_id=employee_id
    )



    username = employee[3]


    if username:

        name = "@" + username

    else:

        name = employee[2]



    await message.answer(
        "⚠️ Подтвердите удаление:\n\n"
        f"👤 {name}\n"
        f"ID: <code>{employee_id}</code>",
        reply_markup=delete_confirm_menu()
    )


    await state.set_state(
        DeleteState.confirm_delete
    )





@router.message(
    DeleteState.confirm_delete,
    F.text == "✅ Подтвердить"
)
async def delete_employee_apply(
        message: Message,
        state: FSMContext
):


    data = await state.get_data()


    employee_id = data.get(
        "delete_employee_id"
    )



    if employee_id:


        await delete_employee(
            employee_id
        )



    await state.clear()



    await message.answer(
        "✅ Сотрудник удалён.",
        reply_markup=admin_menu()
    )





@router.message(
    DeleteState.confirm_delete,
    F.text == "❌ Отмена"
)
async def delete_cancel(
        message: Message,
        state: FSMContext
):


    await state.clear()


    await message.answer(
        "❌ Удаление отменено."
    )





# ============================================================
# DELETE PVZ (SUPER ADMIN)
# ============================================================


@router.message(
    F.text == "🗑 Удалить ПВЗ"
)
async def delete_pvz_start(
        message: Message,
        state: FSMContext
):


    if not is_super_admin(
        message.from_user.id
    ):


        await message.answer(
            "❌ Нет доступа."
        )

        return



    await message.answer(
        "Введите ID ПВЗ для удаления:"
    )


    await state.set_state(
        DeleteState.waiting_pvz_id
    )





@router.message(
    DeleteState.waiting_pvz_id
)
async def delete_pvz_apply(
        message: Message,
        state: FSMContext
):


    try:

        pvz_id = int(
            message.text
        )

    except:


        await message.answer(
            "❌ ID должен быть числом."
        )

        return




    pvz = await get_pvz_by_id(
        pvz_id
    )


    if not pvz:


        await message.answer(
            "❌ ПВЗ не найден."
        )

        await state.clear()

        return




    await delete_pvz(
        pvz_id
    )


    await state.clear()


    await message.answer(
        "🗑 ПВЗ удалён.",
        reply_markup=super_admin_menu()
        )


# ============================================================
# ASSIGN PVZ OWNER
# ============================================================

class AssignOwnerState(StatesGroup):

    waiting_user_id = State()

    waiting_pvz_id = State()


@router.message(
    F.text == "👥 Владельцы ПВЗ"
)
async def owners_menu(
        message: Message,
        state: FSMContext
):

    if not is_super_admin(
        message.from_user.id
    ):

        await message.answer(
            "❌ Нет доступа."
        )

        return

    await state.clear()

    admins = await get_all_admins()

    text = "👥 <b>Владельцы ПВЗ</b>\n\n"

    if admins:

        for admin in admins:

            pvz_name = "Не назначен"

            if admin[5]:

                pvz = await get_pvz_by_id(admin[5])

                if pvz:
                    pvz_name = pvz[1]

            username = (
                f"@{admin[3]}"
                if admin[3]
                else admin[2]
            )

            text += (
                f"{username}\n"
                f"ID: <code>{admin[1]}</code>\n"
                f"ПВЗ: {pvz_name}\n\n"
            )

    else:

        text += "Пока владельцев нет.\n\n"

    text += (
        "Отправьте Telegram ID пользователя, "
        "которого нужно сделать владельцем ПВЗ."
    )

    await message.answer(text)

    await state.set_state(
        AssignOwnerState.waiting_user_id
    )


@router.message(
    AssignOwnerState.waiting_user_id
)
async def assign_owner_user(
        message: Message,
        state: FSMContext
):

    try:
        telegram_id = int(message.text)
    except:
        await message.answer(
            "❌ ID должен быть числом."
        )
        return

    user = await get_user(
        telegram_id
    )

    if not user:

        await message.answer(
            "❌ Пользователь не найден."
        )
        return

    await state.update_data(
        owner_id=telegram_id
    )

    async with aiosqlite.connect(DATABASE) as db:

        cursor = await db.execute(
            """
            SELECT *
            FROM pvz
            ORDER BY id
            """
        )

        pvzs = await cursor.fetchall()

    if not pvzs:

        await message.answer(
            "❌ В системе нет ПВЗ."
        )

        await state.clear()

        return

    text = (
        "Введите ID ПВЗ.\n\n"
        "Доступные ПВЗ:\n\n"
    )

    for pvz in pvzs:

        text += (
            f"{pvz[0]} — {pvz[1]}\n"
        )

    await message.answer(text)

    await state.set_state(
        AssignOwnerState.waiting_pvz_id
    )


@router.message(
    AssignOwnerState.waiting_pvz_id
)
async def assign_owner_finish(
        message: Message,
        state: FSMContext
):

    try:
        pvz_id = int(message.text)
    except:
        await message.answer(
            "❌ ID ПВЗ должен быть числом."
        )
        return

    pvz = await get_pvz_by_id(
        pvz_id
    )

    if not pvz:

        await message.answer(
            "❌ ПВЗ не найден."
        )

        return

    data = await state.get_data()

    owner_id = data["owner_id"]

    await set_pvz_owner(
        pvz_id,
        owner_id
    )

    await state.clear()

    await message.answer(
        "✅ Владелец успешно назначен.",
        reply_markup=super_admin_menu()
    )
    

# ============================================================
# REMOVE PVZ OWNER
# ============================================================

class RemoveOwnerState(StatesGroup):

    waiting_owner_id = State()


@router.message(
    F.text == "🚫 Снять владельца"
)
async def remove_owner_start(
        message: Message,
        state: FSMContext
):

    if not is_super_admin(message.from_user.id):

        await message.answer(
            "❌ Нет доступа."
        )

        return

    admins = await get_all_admins()

    if not admins:

        await message.answer(
            "Владельцев ПВЗ пока нет."
        )

        return

    text = "👥 <b>Владельцы ПВЗ</b>\n\n"

    for admin in admins:

        username = (
            f"@{admin[3]}"
            if admin[3]
            else admin[2]
        )

        pvz_name = "Не назначен"

        if admin[5]:

            pvz = await get_pvz_by_id(admin[5])

            if pvz:

                pvz_name = pvz[1]

        text += (
            f"{username}\n"
            f"ID: <code>{admin[1]}</code>\n"
            f"ПВЗ: {pvz_name}\n\n"
        )

    text += "Введите Telegram ID владельца:"

    await message.answer(text)

    await state.set_state(
        RemoveOwnerState.waiting_owner_id
    )


@router.message(
    RemoveOwnerState.waiting_owner_id
)
async def remove_owner_finish(
        message: Message,
        state: FSMContext
):

    try:

        owner_id = int(message.text)

    except:

        await message.answer(
            "❌ ID должен быть числом."
        )

        return

    user = await get_user(owner_id)

    if not user:

        await message.answer(
            "❌ Пользователь не найден."
        )

        await state.clear()

        return

    if user[4] != ROLE_ADMIN:

        await message.answer(
            "❌ Этот пользователь не является владельцем ПВЗ."
        )

        await state.clear()

        return

    await remove_pvz_owner(owner_id)

    await state.clear()

    await message.answer(
        "✅ Владелец снят с ПВЗ.",
        reply_markup=super_admin_menu()
    )
    

# ============================================================
# ERROR SAFE HANDLER
# ============================================================


@router.message()
async def unknown_message(
        message: Message
):


    await message.answer(
        "Я не понял команду.\n"
        "Используйте кнопки меню."
    )
