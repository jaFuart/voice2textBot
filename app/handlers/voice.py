import asyncio
from html import escape
from pathlib import Path
from tempfile import TemporaryDirectory

import aiosqlite
from aiogram import F, Router
from aiogram.types import Message

from app.config import settings
from app.db import reserve_daily_quota
from app.services.transcribe import transcribe_file

router = Router()


@router.message(F.voice | F.video_note)
async def process_voice(msg: Message):
    media = msg.voice or msg.video_note
    async with aiosqlite.connect(settings.database_url) as conn:
        allowed = await reserve_daily_quota(conn, msg.from_user.id, media.duration)
    if not allowed:
        await msg.reply("Дневной лимит исчерпан. Подписка: /subscribe")
        return

    with TemporaryDirectory() as directory:
        path = Path(directory) / ("voice.ogg" if msg.voice else "video.mp4")
        await msg.bot.download(media, destination=path)
        text = await asyncio.to_thread(transcribe_file, str(path))

    if not text:
        await msg.reply("Не удалось распознать речь в сообщении.")
        return

    for offset in range(0, len(text), 1900):
        heading = "📝 <b>Текст:</b>\n" if offset == 0 else ""
        await msg.reply(heading + escape(text[offset:offset + 1900]))
