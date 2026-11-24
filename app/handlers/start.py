from aiogram import Router
from aiogram.filters import CommandStart, StateFilter
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from html import escape
from app.config import settings

router = Router()

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Главное меню"), KeyboardButton(text="Оформить подписку")],
        [KeyboardButton(text="Моя подписка"), KeyboardButton(text="Техподдержка")]
    ],
    resize_keyboard=True
)

class SupportStates(StatesGroup):
    waiting = State()

@router.message(CommandStart())
async def cmd_start(msg: Message):
    await msg.answer(
        f"Привет, {escape(msg.from_user.first_name or 'друг')}!\n"
        "Пришлите голосовое или видеосообщение — я верну текст. "
        f"Первые {settings.free_quota//60} минут каждый день бесплатно.\n\n"
        "🏷 Безлимит — 199 ₽/мес. Оплатить: /subscribe",
        reply_markup=main_menu
    )

@router.message(lambda m: m.text == "Техподдержка")
async def support_entry(msg: Message, state: FSMContext):
    contact = f"\nДля срочной связи: {escape(settings.support_contact)}" if settings.support_contact else ""
    if not settings.admin_id:
        await msg.answer(f"Поддержка через бота не настроена.{contact}")
        return
    await state.set_state(SupportStates.waiting)
    await msg.answer(
        "Пожалуйста, опишите вашу проблему или вопрос.\n"
        f"Укажите, как к вам обращаться (имя, username).{contact}"
    )

@router.message(StateFilter(SupportStates.waiting))
async def support_message(msg: Message, state: FSMContext):
    await state.clear()
    admin_id = settings.admin_id
    text = f"[Техподдержка]\nОт: {msg.from_user.full_name} (@{msg.from_user.username}) id={msg.from_user.id}\n\n{msg.text}"
    try:
        await msg.bot.send_message(admin_id, text, parse_mode=None)
        await msg.answer("Ваше сообщение отправлено в поддержку. Мы ответим вам как можно скорее!")
    except Exception:
        await msg.answer("Не удалось отправить сообщение в поддержку. Попробуйте позже.")
