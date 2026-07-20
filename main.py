# ============================================================
# WB TRAINER
# Версия: 0.1
# Автор идеи: tg - @slayip + ChatGPT
# Все права защищены.
# ============================================================

import asyncio
import json
import random
import string
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
