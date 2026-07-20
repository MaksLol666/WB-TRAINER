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


# ============================================================
# НАСТРОЙКИ
# ============================================================

TOKEN = "8645122183:AAGgVMowY4tEBfnOpFr7bqssb0tfWalskTM"

ADMINS = [
    1691654877,
]

DATABASE = "wb_trainer.db"


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
        

