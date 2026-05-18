from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import ADMIN_ID, PAYMENT_DETAILS
from keyboards import payment_methods_kb, admin_payment_kb

router = Router()

DEFAULT_REPLENISH = 50_000


class PaymentState(StatesGroup):
    waiting_for_receipt = State()


# ── Entry ─────────────────────────────────────────────────────────────────

@router.message(F.text == "💰 Пополнить баланс")
async def balance_menu(message: Message):
    await message.answer(
        "💳 Выберите способ оплаты:",
        reply_markup=payment_methods_kb(),
    )


# ── Method chosen ─────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("pay_method:"))
async def pay_method_chosen(call: CallbackQuery, state: FSMContext):
    method = call.data.split(":", 1)[1]
    details = PAYMENT_DETAILS[method]

    await state.update_data(method=method)
    await state.set_state(PaymentState.waiting_for_receipt)

    await call.message.edit_text(
        f"💳 <b>Способ оплаты: {method}</b>\n\n"
        f"Реквизиты:\n<code>{details}</code>\n\n"
        "Переведите нужную сумму и отправьте <b>скриншот чека</b> в этот чат.",
        parse_mode="HTML",
    )


# ── Receipt received ──────────────────────────────────────────────────────

@router.message(PaymentState.waiting_for_receipt, F.photo)
async def receipt_received(message: Message, state: FSMContext):
    data   = await state.get_data()
    method = data.get("method", "Не указан")

    placeholder_amount = DEFAULT_REPLENISH

    caption = (
        f"📥 <b>Чек от пользователя</b>\n"
        f"👤 ID: <code>{message.from_user.id}</code>\n"
        f"👤 Username: @{message.from_user.username or '—'}\n"
        f"💳 Метод: {method}\n\n"
        "⚠️ Введите сумму и подтвердите."
    )

    await message.bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=caption,
        reply_markup=admin_payment_kb(message.from_user.id, placeholder_amount),
        parse_mode="HTML",
    )

    await message.answer("✅ Чек отправлен на проверку. Ожидайте подтверждения.")
    await state.clear()


@router.message(PaymentState.waiting_for_receipt)
async def receipt_not_photo(message: Message):
    await message.answer("📸 Пожалуйста, отправьте именно <b>фото</b> чека.", parse_mode="HTML")