from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton,
)
from config import ADMIN_ID, VIEW_TARIFFS, PAYMENT_DETAILS


def main_menu(user_id: int) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="👁 Просмотры"), KeyboardButton(text="👥 Подписчики")],
        [KeyboardButton(text="❤️ Лайки"),     KeyboardButton(text="💰 Пополнить баланс")],
        [KeyboardButton(text="📋 Мои заказы")],
    ]
    if user_id == ADMIN_ID:
        rows.append([KeyboardButton(text="👑 Админ Панель")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def view_tariffs_kb() -> InlineKeyboardMarkup:
    buttons = []
    for label, amount, price in VIEW_TARIFFS:
        buttons.append([
            InlineKeyboardButton(
                text=f"{label} — {price:,} сум".replace(",", " "),
                callback_data=f"view_tariff:{amount}:{price}:{label}",
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Дать заявку", callback_data=f"submit_order:{order_id}"),
            InlineKeyboardButton(text="🔙 Назад",        callback_data="back_to_views"),
        ]
    ])


def final_confirm_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Подтвердить", callback_data=f"confirm_order:{order_id}")]
    ])


def payment_methods_kb() -> InlineKeyboardMarkup:
    methods = list(PAYMENT_DETAILS.keys())
    buttons = [[InlineKeyboardButton(text=m, callback_data=f"pay_method:{m}")] for m in methods]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ── Admin keyboards ─────────────────────────────────────────────────────────

def admin_main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Заявки на накрутку",  callback_data="admin_orders")],
        [InlineKeyboardButton(text="📊 Статистика",          callback_data="admin_stats")],
    ])


def admin_orders_list_kb(orders: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for o in orders:
        buttons.append([
            InlineKeyboardButton(
                text=f"Заявка #{o['order_id']} — {o['service_type']}",
                callback_data=f"admin_view_order:{o['order_id']}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_order_actions_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Выполнено", callback_data=f"admin_done:{order_id}")],
        [InlineKeyboardButton(text="🔙 Назад к списку", callback_data="admin_orders")],
    ])


def admin_payment_kb(user_id: int, amount: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="✅ Подтвердить",
                callback_data=f"admin_pay_ok:{user_id}:{amount}",
            ),
            InlineKeyboardButton(
                text="❌ Отклонить",
                callback_data=f"admin_pay_no:{user_id}",
            ),
        ]
    ])


def user_orders_list_kb(orders: list[dict]) -> InlineKeyboardMarkup:
    buttons = []
    for o in orders:
        buttons.append([
            InlineKeyboardButton(
                text=f"Заявка #{o['order_id']} — {o['service_type']}",
                callback_data=f"user_view_order:{o['order_id']}",
            )
        ])
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="user_back")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)