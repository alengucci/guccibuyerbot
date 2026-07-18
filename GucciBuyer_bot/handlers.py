import html
import logging

from aiogram import Bot, F, Router
from aiogram.filters import Command, CommandStart, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from config import ADMIN_ID, OWNER_USERNAME
from keyboards import (
    BTN_BACK,
    BTN_CONTACT,
    BTN_NEW_ORDER,
    back_kb,
    confirm_kb,
    main_menu_kb,
    one_more_kb,
    order_type_kb,
)
from states import OrderStates

router = Router()
logger = logging.getLogger(__name__)

TYPE_TITLES = {
    "found": "🔍 Я уже нашел",
    "help": "🤔 Помогите найти",
}

ASK_PHOTO = "📸 Пришли <b>фото товара</b> (именно изображением)."
NOT_A_PHOTO = "❌ Это не фото. Пришли, пожалуйста, именно <b>изображение</b> товара."


# ─────────────────────────── Вспомогательные функции ───────────────────────────


def parse_amount(raw: str) -> int | None:
    """Возвращает число, если строка состоит только из цифр, иначе None."""
    cleaned = raw.strip().replace(" ", "").replace(" ", "")
    if cleaned.isdigit() and int(cleaned) > 0:
        return int(cleaned)
    return None


def user_title(message_from) -> str:
    name = message_from.full_name or "без имени"
    username = f" (@{message_from.username})" if message_from.username else " (без username)"
    return f"{name}{username}"


def build_preview(data: dict) -> str:
    order_type = data["order_type"]
    lines = [
        "<b>─── ПРЕДПРОСМОТР ЗАЯВКИ ───</b>",
        "",
        f"📋 <b>Тип:</b> {TYPE_TITLES[order_type]}",
    ]
    if order_type == "found":
        lines += [
            f"🔗 <b>Ссылка:</b> {html.escape(data['link'])}",
            f"💰 <b>Цена:</b> {data['price']} ¥",
            f"📏 <b>Размер:</b> {html.escape(data['size'])}",
        ]
    else:
        lines += [
            f"📏 <b>Размер:</b> {html.escape(data['size'])}",
            f"💸 <b>Бюджет:</b> {data['budget']} ¥",
        ]
    lines += ["", "Всё верно?"]
    return "\n".join(lines)


def build_admin_text(data: dict, from_user) -> str:
    order_type = data["order_type"]
    lines = [
        "─── НОВАЯ ЗАЯВКА НА ВЫКУП ───",
        f"👤 Пользователь: {html.escape(user_title(from_user))}",
        f"🆔 ID: <code>{from_user.id}</code>",
        "",
        f"📋 ТИП: {TYPE_TITLES[order_type]}",
        "",
    ]
    if order_type == "found":
        lines += [
            f"🔗 Ссылка: {html.escape(data['link'])}",
            f"💰 Цена: {data['price']} ¥",
            f"📏 Размер: {html.escape(data['size'])}",
        ]
    else:
        lines += [
            f"📏 Размер: {html.escape(data['size'])}",
            f"💸 Бюджет: {data['budget']} ¥",
        ]
    return "\n".join(lines)


async def start_order(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(OrderStates.choosing_type)
    await message.answer(
        "Выбери тип заявки:",
        reply_markup=order_type_kb(),
    )


# ─────────────────────────── Главное меню ───────────────────────────


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"👋 Привет, <b>{html.escape(message.from_user.full_name)}</b>!\n\n"
        "Это <b>GucciBuyerbot</b> — бот для заявок на выкуп вещей из Китая 🇨🇳\n\n"
        "Выбери, что тебя интересует:",
        reply_markup=main_menu_kb(),
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Заявка отменена. Ты в главном меню.", reply_markup=main_menu_kb())


@router.message(F.text == BTN_CONTACT)
async def contact_owner(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        f"По всем вопросам пишите владельцу: {OWNER_USERNAME}",
        reply_markup=back_kb(),
    )


@router.message(F.text == BTN_BACK)
async def go_back(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer("Главное меню:", reply_markup=main_menu_kb())


@router.message(F.text == BTN_NEW_ORDER)
async def new_order(message: Message, state: FSMContext) -> None:
    await start_order(message, state)


# ─────────────────────────── Шаг 1. Тип заявки ───────────────────────────


@router.callback_query(OrderStates.choosing_type, F.data.startswith("type:"))
async def choose_type(callback: CallbackQuery, state: FSMContext) -> None:
    order_type = callback.data.split(":", 1)[1]
    await state.update_data(order_type=order_type)
    await callback.message.edit_text(f"📋 Тип заявки: {TYPE_TITLES[order_type]}")

    if order_type == "found":
        await state.set_state(OrderStates.found_photo)
    else:
        await state.set_state(OrderStates.help_photo)

    await callback.message.answer(ASK_PHOTO)
    await callback.answer()


# ─────────────────────────── Ветка "Я уже нашел" ───────────────────────────


@router.message(OrderStates.found_photo, F.photo)
async def found_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(OrderStates.found_link)
    await message.answer("🔗 Теперь пришли <b>ссылку на товар</b> (текстом).")


@router.message(OrderStates.found_link, F.text)
async def found_link(message: Message, state: FSMContext) -> None:
    await state.update_data(link=message.text.strip())
    await state.set_state(OrderStates.found_price)
    await message.answer("💰 Введи <b>цену в юанях</b> (только цифры, например: 450).")


@router.message(OrderStates.found_price, F.text)
async def found_price(message: Message, state: FSMContext) -> None:
    price = parse_amount(message.text)
    if price is None:
        await message.answer("❌ Нужны <b>только цифры</b>. Например: 450")
        return
    await state.update_data(price=price)
    await state.set_state(OrderStates.found_size)
    await message.answer('📏 Введи <b>размер</b> (например: "EU 43" или "M").')


@router.message(OrderStates.found_size, F.text)
async def found_size(message: Message, state: FSMContext) -> None:
    await state.update_data(size=message.text.strip())
    await show_preview(message, state)


# ─────────────────────────── Ветка "Помогите найти" ───────────────────────────


@router.message(OrderStates.help_photo, F.photo)
async def help_photo(message: Message, state: FSMContext) -> None:
    await state.update_data(photo_id=message.photo[-1].file_id)
    await state.set_state(OrderStates.help_size)
    await message.answer('📏 Введи <b>размер</b> (например: "EU 43" или "M").')


@router.message(OrderStates.help_size, F.text)
async def help_size(message: Message, state: FSMContext) -> None:
    await state.update_data(size=message.text.strip())
    await state.set_state(OrderStates.help_budget)
    await message.answer(
        "💸 Введи <b>максимальный бюджет в юанях</b> (только цифры, например: 800)."
    )


@router.message(OrderStates.help_budget, F.text)
async def help_budget(message: Message, state: FSMContext) -> None:
    budget = parse_amount(message.text)
    if budget is None:
        await message.answer("❌ Нужны <b>только цифры</b>. Например: 800")
        return
    await state.update_data(budget=budget)
    await show_preview(message, state)


# ─────────────────────────── Шаг 3. Подтверждение ───────────────────────────


async def show_preview(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    await state.set_state(OrderStates.confirming)
    await message.answer_photo(
        photo=data["photo_id"],
        caption=build_preview(data),
        reply_markup=confirm_kb(),
    )


@router.callback_query(OrderStates.confirming, F.data == "order:restart")
async def restart_order(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Начинаем заново")
    await start_order(callback.message, state)


@router.callback_query(OrderStates.confirming, F.data == "order:confirm")
async def confirm_order(callback: CallbackQuery, state: FSMContext, bot: Bot) -> None:
    data = await state.get_data()
    await callback.message.edit_reply_markup(reply_markup=None)

    admin_text = build_admin_text(data, callback.from_user)
    try:
        await bot.send_photo(ADMIN_ID, photo=data["photo_id"], caption=admin_text)
    except Exception:
        logger.exception("Не удалось отправить заявку админу %s", ADMIN_ID)
        await callback.answer()
        await callback.message.answer(
            "⚠️ Не получилось отправить заявку. Попробуй ещё раз позже или напиши "
            f"владельцу напрямую: {OWNER_USERNAME}",
            reply_markup=main_menu_kb(),
        )
        await state.clear()
        return

    await state.clear()
    await callback.answer("Отправлено")
    await callback.message.answer(
        "✅ Заявка отправлена! Спасибо. Мы свяжемся с вами в ближайшее время.",
        reply_markup=main_menu_kb(),
    )
    await callback.message.answer(
        "Хочешь оформить ещё одну?",
        reply_markup=one_more_kb(),
    )


@router.callback_query(F.data == "order:more")
async def one_more_order(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer()
    await start_order(callback.message, state)


# ─────────────────────────── Фолбэки внутри сценария ───────────────────────────


@router.message(StateFilter(OrderStates.found_photo, OrderStates.help_photo))
async def photo_required(message: Message) -> None:
    """Любой не-фото контент на шаге с фото."""
    await message.answer(NOT_A_PHOTO)


@router.message(OrderStates.choosing_type)
async def type_required(message: Message) -> None:
    await message.answer(
        "Сначала выбери тип заявки кнопкой ниже 👇", reply_markup=order_type_kb()
    )


@router.message(
    StateFilter(
        OrderStates.found_link,
        OrderStates.found_price,
        OrderStates.found_size,
        OrderStates.help_size,
        OrderStates.help_budget,
    )
)
async def text_required(message: Message) -> None:
    await message.answer("❌ Здесь нужен <b>текст</b>. Пришли, пожалуйста, текстовое сообщение.")


@router.message(OrderStates.confirming)
async def confirm_required(message: Message) -> None:
    await message.answer("Нажми кнопку под заявкой: «✅ Подтвердить» или «✏️ Отменить и начать заново».")


@router.message()
async def fallback(message: Message) -> None:
    await message.answer("Не понял 🤔 Воспользуйся кнопками меню.", reply_markup=main_menu_kb())
