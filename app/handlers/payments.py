from aiogram import Router, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime, timedelta
import aiosqlite
from app.config import settings
from app.db import add_or_update_user, get_user
from yookassa import Payment, Configuration
import uuid
import aiohttp
import asyncio

router = Router()

# Настройка глобальных параметров YooKassa
Configuration.account_id = settings.yookassa_shop_id
Configuration.secret_key = settings.yookassa_secret_key

def create_yookassa_payment(user_id: int, amount: int, description: str, return_url: str):
    payment = Payment.create({
        "amount": {
            "value": f"{amount/100:.2f}",
            "currency": "RUB"
        },
        "confirmation": {
            "type": "redirect",
            "return_url": return_url
        },
        "capture": True,
        "description": description,
        "metadata": {
            "user_id": str(user_id)
        }
    })
    return payment.confirmation.confirmation_url, payment.id

@router.message(F.text.in_(["/my_sub", "Моя подписка"]))
async def my_sub(msg: Message):
    async with aiosqlite.connect(settings.database_url) as conn:
        row = await get_user(conn, msg.from_user.id)
        if row and row[0]:
            sub_until = row[0]
            dt = datetime.fromisoformat(sub_until)
            if dt > datetime.utcnow():
                await msg.reply(f"Ваша подписка активна до {dt.strftime('%d.%m.%Y')} 🟢")
                return
        await msg.reply("У вас нет активной подписки. Оформите безлимит: /subscribe")

@router.message(F.text.in_(["/subscribe", "Оформить подписку"]))
async def subscribe(msg: Message, state: FSMContext):
    async with aiosqlite.connect(settings.database_url) as conn:
        row = await get_user(conn, msg.from_user.id)
        if row and row[0]:
            sub_until = row[0]
            dt = datetime.fromisoformat(sub_until)
            if dt > datetime.utcnow():
                await msg.reply(f"Ваша подписка уже активна до {dt.strftime('%d.%m.%Y')} 🟢")
                return
    if not settings.yookassa_shop_id or not settings.yookassa_secret_key:
        await msg.reply("YooKassa не настроена. Обратитесь к администратору.")
        return
    amount = settings.subscription_price
    description = "Подписка Voice2Text Bot на 30 дней"
    bot = await msg.bot.me()
    url, payment_id = await asyncio.to_thread(
        create_yookassa_payment, msg.from_user.id, amount, description, f"https://t.me/{bot.username}"
    )
    await state.update_data(payment_id=payment_id)
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Оплатить YooKassa", url=url)],
            [InlineKeyboardButton(text="Я оплатил", callback_data="check_payment")]
        ]
    )
    await msg.reply(
        "💳 Для активации безлимита оплатите подписку через YooKassa по кнопке ниже.\n"
        "После оплаты нажмите «Я оплатил»!",
        reply_markup=kb
    )

@router.callback_query(F.data == "check_payment")
async def check_payment(call: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    payment_id = data.get("payment_id")
    if not payment_id:
        await call.answer("Платёж не найден. Попробуйте ещё раз оформить подписку.", show_alert=True)
        return
    payment = await asyncio.to_thread(Payment.find_one, payment_id)
    if payment.status == "succeeded":
        sub_until = datetime.utcnow() + timedelta(days=settings.subscription_days)
        async with aiosqlite.connect(settings.database_url) as conn:
            await add_or_update_user(conn, call.from_user.id, sub_until.isoformat())
        await state.clear()
        await call.answer()
        await call.message.answer("✅ Подписка активирована! Спасибо за оплату.")
    else:
        await call.answer("Платёж не найден или не оплачен. Попробуйте позже.", show_alert=True)

# --- Фоновая задача для напоминаний о скором окончании подписки ---
async def subscription_reminder_task(bot):
    while True:
        try:
            async with aiosqlite.connect(settings.database_url) as conn:
                cursor = await conn.execute("SELECT rowid, sub_until FROM users WHERE sub_until IS NOT NULL")
                rows = await cursor.fetchall()
                now = datetime.utcnow()
                for row in rows:
                    user_id, sub_until = row
                    if not sub_until:
                        continue
                    dt = datetime.fromisoformat(sub_until)
                    if dt.date() == (now + timedelta(days=1)).date():
                        try:
                            await bot.send_message(user_id, f"⏰ Ваша подписка истекает {dt.strftime('%d.%m.%Y')}. Оформить новую: /subscribe")
                        except Exception:
                            pass
        except Exception:
            pass
        await asyncio.sleep(60 * 60 * 12)  # Проверять 2 раза в сутки
