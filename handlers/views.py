from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from config import ADMIN_ID, PRICE_PER_1000_VIEWS
from database import (
    get_or_create_user, get_balance,
    create_order, set_order_link, get_order, set_order_status, deduct_balance,
)
from keyboards import main_menu

router = Router()


class ViewOrder(StatesGroup):
    waiting_for_amount = State()
    waiting_for_link = State()
    admin_enter_deduct = State()


# ── Entry point ─────────────────────────────────────────────────────

@router.message(F.text == "👁 Просмотры")
async def views_menu(message: Message, state: FSMContext):
    await get_or_create_user(message.from_user.id)
    await state.set_state(ViewOrder.waiting_for_amount)
    await message.answer(
        "👁 <b>Просмотры для Telegram-постов</b>\n\n"
        "💬 Введите количество просмотров:\n"
        "(Цена: 0.01$ за просмотр)\n\n"
        "📝 Напишите число:",
        parse_mode="HTML",
    )


@router.message(ViewOrder.waiting_for_amount, F.text)
async def receive_amount(message: Message, state: FSMContext):
    try:
        amount = int(message.text.strip())

        if amount <= 0:
            await message.answer("❌ Количество должно быть больше 0!")
            return

        from config import PRICE_PER_1000_VIEWS
        price = (amount // 1000) * PRICE_PER_1000_VIEWS  # цена в центах за каждые 1000

        if amount % 1000 != 0:
            price += PRICE_PER_1000_VIEWS  # округляем вверх

        order_id = await create_order(
            user_id=message.from_user.id,
            service_type=f"Просмотры {amount}",
            amount=amount,
            price=0,  # Пока не списываем
        )

        await state.update_data(order_id=order_id, amount=amount, price=price)
        await state.set_state(ViewOrder.waiting_for_link)

        await message.answer(
            f"✅ Заявка создана\n"
            f"🆔 ID: <b>#{order_id}</b>\n"
            f"👁 Просмотров: <b>{amount:,}</b>\n"
            f"💰 Сумма: <b>${price / 100:.2f}</b>\n\n"
            "📎 Отправьте ссылку на пост:".replace(",", " "),
            parse_mode="HTML",
        )
    except ValueError:
        await message.answer("❌ Введите корректное число!")

@router.message(ViewOrder.waiting_for_link, F.text)
async def receive_link(message: Message, state: FSMContext):
    data = await state.get_data()
    order_id = data["order_id"]
    link = message.text.strip()

    await set_order_link(order_id, link)

    from aiogram import Bot
    bot: Bot = message.bot

    # Отправляем админу на подтверждение
    await bot.send_message(
        ADMIN_ID,
        f"🆕 <b>Новая заявка #{order_id}</b>\n"
        f"👤 User ID: <code>{message.from_user.id}</code>\n"
        f"👁 Просмотров: <b>{data['amount']:,}</b>\n"
        f"💰 Сумма: <b>${data['price'] / 100:.2f}</b>\n"
        f"🔗 Ссылка: {link}\n\n"
        "<b>Админ вводит финальную сумму к списанию</b>".replace(",", " "),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Подтвердить",
                                  callback_data=f"view_admin_ok:{order_id}:{message.from_user.id}:{data['amount']}")],
            [InlineKeyboardButton(text="❌ Отклонить",
                                  callback_data=f"view_admin_no:{order_id}:{message.from_user.id}")],
        ]),
        parse_mode="HTML",
    )

    await message.answer("✅ Ссылка отправлена. Ожидайте подтверждения админа.")
    await state.clear()


# ── Admin confirmation ───────────────────────────────────────────

@router.callback_query(F.data.startswith("view_admin_ok:"))
async def view_admin_ok(call: CallbackQuery, state: FSMContext):
    _, order_id, user_id, amount = call.data.split(":")
    order_id = int(order_id)
    user_id = int(user_id)
    amount = int(amount)

    await state.update_data(order_id=order_id, user_id=user_id, amount=amount)
    await state.set_state(ViewOrder.admin_enter_deduct)
    await call.message.answer(
        f"💰 Введите сумму для списания пользователю (в $):\n"
        f"(рекомендуемо: ${amount * 0.01:.2f})"
    )


@router.message(ViewOrder.admin_enter_deduct, F.text)
async def admin_enter_deduct_amount(message: Message, state: FSMContext):
    try:
        data = await state.get_data()

        # Парсим число (может быть с $ или без)
        amount_str = message.text.strip().replace("$", "").strip()
        deduct_amount = int(float(amount_str) * 100)  # конвертируем в центы

        order_id = data["order_id"]
        user_id = data["user_id"]

        balance = await get_balance(user_id)

        if balance < deduct_amount:
            await message.answer(
                f"❌ У пользователя недостаточно средств!\n"
                f"Баланс: ${balance / 100:.2f}\n"
                f"Нужно: ${deduct_amount / 100:.2f}"
            )
            return

        # Списываем деньги и обновляем заявку
        await deduct_balance(user_id, deduct_amount)
        await set_order_status(order_id, "В обработке")

        await message.bot.send_message(
            user_id,
            f"✅ <b>Заявка #{order_id} принята!</b>\n"
            f"💸 Списано: <b>${deduct_amount / 100:.2f}</b>\n"
            "Ожидайте выполнения.",
            parse_mode="HTML",
        )

        await message.answer(f"✅ Списано ${deduct_amount / 100:.2f} пользователю")
        await state.clear()
    except ValueError:
        await message.answer("❌ Введите корректную сумму! (например: 1.5 или $1.5)")


@router.callback_query(F.data.startswith("view_admin_no:"))
async def view_admin_no(call: CallbackQuery, state: FSMContext):
    _, order_id, user_id = call.data.split(":")
    order_id = int(order_id)
    user_id = int(user_id)

    await set_order_status(order_id, "Отклонено")

    await call.bot.send_message(
        user_id,
        f"❌ Заявка #{order_id} отклонена.\nСвяжитесь с поддержкой.",
    )

    await call.message.edit_text("❌ Заявка отклонена.")
    await call.answer()
    await state.clear()