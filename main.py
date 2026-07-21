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
# SUPER ADMIN FUNCTIONS
# ============================================================

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


async def assign_admin_to_pvz(
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

        await db.commit()


async def remove_employee(
        telegram_id: int
):

    async with aiosqlite.connect(DATABASE) as db:

        await db.execute(
            """
            DELETE FROM users

            WHERE telegram_id = ?
            """,
            (
                telegram_id,
            )
        )

        await db.commit()


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


    await ensure_admin_exists(
        telegram_id,
        full_name,
        username
    )


    user = await get_user(
        telegram_id
    )


    if user:


        role = user[4]


        if role == ROLE_ADMIN:


            await message.answer(
                "👑 <b>WB TRAINER</b>\n\n"
                "Вы вошли как главный администратор.",
                reply_markup=admin_menu()
            )


        else:


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


    if not is_admin(
        message.from_user.id
    ):


        await message.answer(
            "❌ Нет доступа."
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


    name = message.text.strip()



    pvz_id, code = await create_pvz(
        name,
        message.from_user.id
    )



    await state.clear()



    await message.answer(
        "✅ <b>ПВЗ создан!</b>\n\n"
        f"📍 {name}\n"
        f"🔑 Код сотрудников:\n"
        f"<code>{code}</code>",
        reply_markup=admin_menu()
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


    if not is_admin(
        message.from_user.id
    ):


        await message.answer(
            "❌ Нет доступа."
        )

        return




    pvzs = await get_admin_pvz(
        message.from_user.id
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
# EMPLOYEES LIST
# ============================================================



@router.message(
    F.text == "👥 Сотрудники"
)
async def employees_list(
        message: Message
):


    if not is_admin(
        message.from_user.id
    ):


        await message.answer(
            "❌ Нет доступа."
        )

        return




    pvzs = await get_admin_pvz(
        message.from_user.id
    )



    if not pvzs:


        await message.answer(
            "👥 ПВЗ пока нет."
        )

        return




    text = (
        "👥 <b>Сотрудники ваших ПВЗ:</b>\n\n"
    )



    for pvz in pvzs:


        users = await get_pvz_employees(
            pvz[0]
        )


        text += (
            f"📍 <b>{pvz[1]}</b>\n\n"
        )



        if not users:


            text += (
                "Сотрудников нет\n\n"
            )

            continue




        for user in users:


            username = user[3]


            if username:

                name = "@" + username

            else:

                name = user[2]



            text += (
                f"👤 {name}\n"
                f"Роль: {user[4]}\n"
                f"ID: <code>{user[1]}</code>\n"
                f"Дата: {user[6][:10]}\n\n"
            )



    await message.answer(
        text,
        reply_markup=admin_menu()
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





# ============================================================
# START BOT
# ============================================================


async def main():


    print(
        "🚀 WB TRAINER запускается..."
    )


    await init_db()


    print(
        "✅ База данных готова"
    )


    await dp.start_polling(
        bot
    )





if __name__ == "__main__":


    asyncio.run(main())
