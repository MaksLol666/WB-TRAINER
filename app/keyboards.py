from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def super_admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Все ПВЗ")],
            [KeyboardButton(text="👥 Владельцы ПВЗ")],
            [KeyboardButton(text="👤 Все сотрудники")],
            [KeyboardButton(text="📝 Управление тестами")],
            [KeyboardButton(text="📊 Общая статистика")],
            [KeyboardButton(text="➕ Создать ПВЗ")],
            [KeyboardButton(text="🗑 Удалить ПВЗ"), KeyboardButton(text="🚫 Снять владельца")],
        ],
        resize_keyboard=True,
    )


def admin_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏢 Мои ПВЗ")],
            [KeyboardButton(text="👥 Сотрудники")],
            [KeyboardButton(text="📊 Статистика ПВЗ")],
            [KeyboardButton(text="🔑 Код приглашения")],
            [KeyboardButton(text="❌ Удалить сотрудника")],
        ],
        resize_keyboard=True,
    )


def employee_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📚 Начать тест")],
            [KeyboardButton(text="📊 Мои результаты")],
            [KeyboardButton(text="👤 Профиль")],
        ],
        resize_keyboard=True,
    )


def registration_menu():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="🔑 Ввести код ПВЗ")]], resize_keyboard=True)


def owner_management_menu():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👥 Добавить сотрудника")],
            [KeyboardButton(text="❌ Удалить сотрудника")],
            [KeyboardButton(text="⬅ Назад")],
        ],
        resize_keyboard=True,
    )


def delete_confirm_menu():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Подтвердить")], [KeyboardButton(text="❌ Отмена")]],
        resize_keyboard=True,
    )


def back_menu():
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text="⬅ Назад")]], resize_keyboard=True)
