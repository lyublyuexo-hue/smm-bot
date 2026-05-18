from aiogram import Router, F
from aiogram.filters import Filter, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID
from database import (
    get_order, set_order_status, add_balance, get_stats, get_all_orders,
)
from keyboards import (
    admin_main_kb, admin_orders_list_kb, admin_order_actions_kb, user_orders_list_kb, main_menu,
)

router = Router()


class IsAdmin(Filter):
    async def __call__(self, event: Message | CallbackQuery) -> bool:
        user_id = event.from_user.id if isinstance(event, Message) else event.from_user.id
        return user_id == ADMIN_ID


class PaymentConfirm(StatesGroup):
    waiting_for_amount = State()


# ── User orders ────────────────────────────────────────────────────────────

@router.message(F.text == "📋 Мои заказы")
async def my_orders(message: Message):
    from database import get_user_orders

    user_orders = await get_user_orders(message.from_user.id)

    if not user_orders:
        await message.answer(
            "📋 У вас нет заказов.",
            reply_markup=main_menu(message.from_user.id),
        )
        return

    await message.answer(
        f"📋 <b>Ваши заказы ({len(user_orders)})</b>\n\nВыберите заказ:",
        reply_markup=user_orders_list_kb(user_orders),
        parse_mode="HTML",
    )


@router.callback_query(F.data.startswith("user_view_order:"))
async def user_view_order(call: CallbackQuery):
    order_id = int(call.data.split(":")[1])
    order = await get_order(order_id)

    if not order or order['user_id'] != call.from_user.id:
        await call.answer("Заказ не найден.", show_alert=True)
        return

    text = (
        f"📄 <b>Заказ #{order_id}</b>\n\n"
        f"📦 Услуга: {order['service_type']}\n"
        f"🔢 Количество: {order['amount']:,}\n"
        f"💰 Цена: {order['price']:,} сум\n"
        f"🔗 Ссылка: {order['link'] or '—'}\n"
        f"📌 Статус: {order['status']}"
    ).replace(",", " ")

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    back_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 Назад", callback_data="user_back")],
    ])

    await call.message.edit_text(
        text,
        reply_markup=back_kb,
        parse_mode="HTML",
    )


@router.callback_query(F.data == "user_back")
async def user_back(call: CallbackQuery):
    await call.message.edit_text(
        "👋 Выберите нужную услугу:",
        reply_markup=main_menu(call.from_user.id),
    )


# ── Admin panel entry ────────────────────────────────────────────────────

@router.message(IsAdmin(), Command("admin"))
async def admin_panel(message: Message):
    stats = await get_stats()
    await message.answer(
        f"👑 <b>Админ Панель</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"⏳ Заявок в обработке: <b>{stats['pending']}</b>\n"
        f"✅ Выполнено заявок: <b>{stats['done']}</b>",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


# ── Stats button ─────────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data == "admin_stats")
async def admin_stats(call: CallbackQuery):
    stats = await get_stats()
    await call.message.edit_text(
        f"📊 <b>Статистика</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"⏳ Заявок в обработке: <b>{stats['pending']}</b>\n"
        f"✅ Выполнено заявок: <b>{stats['done']}</b>",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


# ── All orders ───────────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data == "admin_orders")
async def admin_all_orders(call: CallbackQuery):
    orders = await get_all_orders()
    if not orders:
        await call.message.edit_text(
            "📋 Заявок нет.",
            reply_markup=admin_main_kb(),
        )
        return

    await call.message.edit_text(
        f"📋 <b>Все заявки ({len(orders)})</b>\n\nВыберите заявку:",
        reply_markup=admin_orders_list_kb(orders),
        parse_mode="HTML",
    )


# ── Orders by service ───────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data.startswith("admin_service:"))
async def admin_service_orders(call: CallbackQuery):
    service = call.data.split(":", 1)[1]
    orders = await get_all_orders()
    filtered = [o for o in orders if service.lower() in o['service_type'].lower()]

    if not filtered:
        await call.message.edit_text(
            f"📋 Заявок на '{service}' нет.",
            reply_markup=admin_main_kb(),
        )
        return

    await call.message.edit_text(
        f"📋 <b>{service} ({len(filtered)})</b>\n\nВыберите заявку:",
        reply_markup=admin_orders_list_kb(filtered),
        parse_mode="HTML",
    )


# ── View single order ────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data.startswith("admin_view_order:"))
async def admin_view_order(call: CallbackQuery):
    order_id = int(call.data.split(":")[1])
    order = await get_order(order_id)

    if not order:
        await call.answer("Заявка не найдена.", show_alert=True)
        return

    text = (
        f"📄 <b>Заявка #{order_id}</b>\n\n"
        f"👤 User ID: <code>{order['user_id']}</code>\n"
        f"📦 Услуга: {order['service_type']}\n"
        f"🔢 Количество: {order['amount']:,}\n"
        f"💰 Цена: {order['price']:,} сум\n"
        f"🔗 Ссылка: {order['link'] or '—'}\n"
        f"📌 Статус: {order['status']}"
    ).replace(",", " ")

    await call.message.edit_text(
        text,
        reply_markup=admin_order_actions_kb(order_id),
        parse_mode="HTML",
    )


# ── Mark order as done ────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data.startswith("admin_done:"))
async def admin_mark_done(call: CallbackQuery):
    order_id = int(call.data.split(":")[1])
    order = await get_order(order_id)

    if not order:
        await call.answer("Заявка не найдена.", show_alert=True)
        return

    await set_order_status(order_id, "Выполнено")

    await call.bot.send_message(
        order["user_id"],
        f"🎉 Ваша заявка <b>#{order_id}</b> выполнена!\n"
        f"📦 Услуга: {order['service_type']}\n"
        f"🔗 Пост: {order['link']}",
        parse_mode="HTML",
    )

    await call.message.edit_text(f"✅ Заявка #{order_id} помечена как выполненная.")
    await call.answer("Готово!")


# ── Back ──────────────────────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data == "admin_back")
async def admin_back(call: CallbackQuery):
    stats = await get_stats()
    await call.message.edit_text(
        f"👑 <b>Админ Панель</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"⏳ Заявок в обработке: <b>{stats['pending']}</b>\n"
        f"✅ Выполнено заявок: <b>{stats['done']}</b>",
        reply_markup=admin_main_kb(),
        parse_mode="HTML",
    )


# ── Payment confirmation ─────────────────────────────────────────────────

@router.callback_query(IsAdmin(), F.data.startswith("admin_pay_ok:"))
async def admin_pay_ok(call: CallbackQuery, state: FSMContext):
    user_id = int(call.data.split(":")[1])
    await state.update_data(user_id=user_id)
    await state.set_state(PaymentConfirm.waiting_for_amount)

    await call.message.answer("💰 Введите сумму для начисления (сум):")
    await call.answer()


@router.message(IsAdmin(), PaymentConfirm.waiting_for_amount)
async def admin_enter_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())
        data = await state.get_data()
        user_id = data["user_id"]

        await add_balance(user_id, amount)

        await message.bot.send_message(
            user_id,
            f"✅ <b>Баланс пополнен!</b>\n"
            f"💰 Начислено: <b>{amount:,} сум</b>".replace(",", " "),
            parse_mode="HTML",
        )

        await message.answer(f"✅ Начислено {amount:,} сум пользователю {user_id}".replace(",", " "))
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите корректное число!")


@router.callback_query(IsAdmin(), F.data.startswith("admin_pay_no:"))
async def admin_pay_no(call: CallbackQuery):
    user_id = int(call.data.split(":")[1])

    await call.bot.send_message(
        user_id,
        "❌ Ваш чек не прошёл проверку. Свяжитесь с поддержкой.",
    )

    await call.message.edit_caption(
        caption=call.message.caption + "\n\n❌ <b>Отклонено.</b>",
        parse_mode="HTML",
    )
    await call.answer("Отклонено.")