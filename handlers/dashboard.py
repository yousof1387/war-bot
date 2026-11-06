"""داشبورد"""

from models import User, UserBuilding
from engines.economy import total_income, calc_power_score, xp_needed_for_level
from utils.constants import get_level_title
from handlers.daily import show_daily_menu
from handlers.research import get_total_bonus
from handlers.research import get_total_bonus

def fmt(n):
    return f"{n:,.0f}"


async def show_dashboard(message, user, Session):
    session = Session()

    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()

        country = u.country

        ubs = session.query(UserBuilding).filter_by(user_id=u.user_id).all()

       
        # ...
        # ✅ محاسبه بونوس درآمد از تحقیقات
        income_bonus = 1.0 + get_total_bonus(u, session, "income")
        income = total_income(ubs, u.level, country)
        income['cash'] *= income_bonus # اضافه کردن بونوس به درآمد کل

        power = calc_power_score(ubs)

        title = get_level_title(u.level)
        xp_next = xp_needed_for_level(u.level)

        bar_total = 10
        filled = min(int((u.xp / xp_next) * bar_total), bar_total) if xp_next > 0 else 0
        bar = "█" * filled + "░" * (bar_total - filled)

        text = (
            f"{country.flag_emoji} <b>{country.name}</b>\n"
            f"👑 {title} | ⭐ سطح {u.level}\n"
            f"✨ XP: {u.xp}/{xp_next}\n"
            f"[{bar}]\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💰 <b>منابع:</b>\n"
            f"💵 پول نقد: {fmt(u.cash)}\n"
            f"🥇 طلا: {u.gold:,.1f}\n"
            f"🛢️ نفت: {fmt(u.oil_barrels)}\n"
            f"☢️ اورانیوم: {u.uranium:,.1f}\n"
            f"⚙️ فولاد: {fmt(u.steel)}\n"
            f"🌾 غذا: {fmt(u.food)}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"👥 جمعیت: {u.population:,}\n"
            f"🎖️ سرباز: {u.soldiers:,}\n"
            f"🏆 اعتبار: {u.reputation}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🏢 ساختمان‌ها: {len(ubs)}\n"
            f"📈 درآمد: {fmt(income['cash'])}/ساعت\n"
            f"🏆 قدرت: {fmt(power)}\n"
            f"⚔️ حمله: {country.attack_bonus}x | 🛡️ دفاع: {country.defense_bonus}x\n"
        )

        kb = {"inline_keyboard": [
    [{"text": "🏗️ ساختمان‌ها", "callback_data": "menu_build"},
     {"text": "⚔️ ارتش", "callback_data": "menu_army"}],
    [{"text": "💥 حمله", "callback_data": "menu_battle"},
     {"text": "💰 بازار", "callback_data": "menu_market"}],
    [{"text": "🔬 تحقیقات", "callback_data": "menu_research"},
     {"text": "🌊 تنگه‌ها", "callback_data": "menu_strait"}],
    [{"text": "🕵️ جاسوسی", "callback_data": "menu_spy"},
     {"text": "🤝 اتحاد", "callback_data": "menu_alliance"}],
    [{"text": "🌐 دیپلماسی", "callback_data": "menu_diplomacy"},
     {"text": "🎁 جوایز", "callback_data": "menu_daily"}],
    [{"text": "🏆 دستاوردها", "callback_data": "menu_achieve"},
     {"text": "🏅 لیدربورد", "callback_data": "menu_lb"}],
    [{"text": "🔄 بروزرسانی", "callback_data": "menu_dashboard"}],
]}

        await message.reply(text, reply_markup=kb)

    finally:
        session.close()