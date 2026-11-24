from pydantic import BaseModel
import os
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseModel):
    tg_token: str = os.getenv("TG_TOKEN", "")
    admin_id: int = int(os.getenv("ADMIN_ID", "0"))
    support_contact: str = os.getenv("SUPPORT_CONTACT", "")
    database_url: str = os.getenv("DATABASE_URL", "voice.db")
    free_quota: int = 300
    subscription_price: int = 19900
    subscription_days: int = 30
    yookassa_shop_id: str = os.getenv("YOOKASSA_SHOP_ID", "")
    yookassa_secret_key: str = os.getenv("YOOKASSA_SECRET_KEY", "")

settings = Settings()
