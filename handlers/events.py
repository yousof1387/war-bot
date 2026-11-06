"""رویدادهای تصادفی"""

import random
from models import User


def fmt(n): return f"{n:,.0f}"


EVENTS = [
    {
        "name": "☀️ آفتاب درخشان",
        "desc": "درآمد شما ۱۰٪ افزایش یافت!",
        "effect": "income",
        "value": 0.10,
    },
    {
        "name": "🌧️ باران فصلی",
        "desc": "درآمد شما ۵٪ کاهش یافت.",
        "effect": "income",
        "value": -0.05,
    },
    {
        "name": "🎉 جشن ملی",
        "desc": "+۱۰۰ XP گرفتید!",
        "effect": "xp",
        "value": 100,
    },
    {
        "name": "💎 اکتشاف طلا",
        "desc": "۱۰۰۰ دلار جایزه گرفتید!",
        "effect": "cash",
        "value": 1000,
    },
    {
        "name": "🔥 بحران اقتصادی",
        "desc": "۵۰۰ دلار از دست دادید.",
        "effect": "cash",
        "value": -500,
    },
]


async def trigger_random_event(user, Session):
    """یه رویداد تصادفی برای کاربر اجرا کن"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        if not u:
            return None
        
        event = random.choice(EVENTS)
        
        if event["effect"] == "xp":
            u.xp += int(event["value"])
        elif event["effect"] == "cash":
            u.cash += int(event["value"])
            if u.cash < 0:
                u.cash = 0
        
        session.commit()
        
        return {
            "name": event["name"],
            "desc": event["desc"],
        }
    finally:
        session.close()
        