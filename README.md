# Voice2Text Bot

Telegram bot for transcribing voice messages and video notes with faster-whisper. Speech recognition runs on the bot's host using the CPU.

## Что умеет

- Принимает голосовые сообщения и видеокружки, возвращает текст транскрипции.
- Обрабатывает аудио локально через faster-whisper с моделью `small` и вычислениями INT8.
- Хранит дневную квоту и статус подписки в SQLite. Подписки через YooKassa и сообщения в поддержку подключаются по желанию.

## Локальный запуск

Понадобятся Python 3.12 и токен собственного Telegram-бота от [BotFather](https://t.me/BotFather).

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
cp .env.example .env
```

В PowerShell активируйте окружение командой `.\.venv\Scripts\Activate.ps1`. Скопируйте пример конфигурации командой `Copy-Item .env.example .env`.

Заполните `TG_TOKEN` в `.env` и запустите:

```bash
python -m app.bot
```

Отправьте боту `/start`, затем голосовое сообщение. При первом распознавании модель скачается и сохранится в локальном кэше. База `voice.db` создаётся при запуске.

## Проверка без Telegram

Передайте путь к своему аудиофайлу. Модель загрузится при первом вызове.

```bash
python -c "from app.services.transcribe import transcribe_file; print(transcribe_file('example.ogg'))"
```

## Опциональные настройки

- `WHISPER_MODEL_CACHE` задаёт папку для кэша модели.
- `DATABASE_URL` задаёт путь к файлу SQLite.
- `ADMIN_ID` включает пересылку обращений администратору. `SUPPORT_CONTACT` задаёт контакт для связи.
- `YOOKASSA_SHOP_ID` и `YOOKASSA_SECRET_KEY` включают оплату подписок. Возврат после оплаты ведёт на публичный адрес бота.
