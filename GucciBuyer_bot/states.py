from aiogram.fsm.state import State, StatesGroup


class OrderStates(StatesGroup):
    """Состояния процесса оформления заявки."""

    # Общий шаг — выбор типа заявки
    choosing_type = State()

    # Ветка "Я уже нашел"
    found_photo = State()
    found_link = State()
    found_price = State()
    found_size = State()

    # Ветка "Помогите найти"
    help_photo = State()
    help_size = State()
    help_budget = State()

    # Подтверждение
    confirming = State()
