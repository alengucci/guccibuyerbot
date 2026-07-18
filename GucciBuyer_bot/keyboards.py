from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

# ─────────────────────────── Главное меню (reply) ───────────────────────────

BTN_NEW_ORDER = "🛍️ Оформить заявку"
BTN_CONTACT = "📞 Связаться с владельцем"
BTN_BACK = "🔙 Назад"


def main_menu_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=BTN_NEW_ORDER)],
            [KeyboardButton(text=BTN_CONTACT)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выбери действие",
    )


def back_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_BACK)]],
        resize_keyboard=True,
    )


# ─────────────────────────── Инлайн-клавиатуры ───────────────────────────


def order_type_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Я уже нашел", callback_data="type:found")],
            [InlineKeyboardButton(text="🤔 Помогите найти", callback_data="type:help")],
        ]
    )


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить", callback_data="order:confirm")],
            [
                InlineKeyboardButton(
                    text="✏️ Отменить и начать заново", callback_data="order:restart"
                )
            ],
        ]
    )


def one_more_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Оформить еще одну заявку", callback_data="order:more"
                )
            ],
        ]
    )
