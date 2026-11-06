"""لیدربورد"""

from models import User, Country, UserUnit
from engines.economy import calc_power_score


def fmt(n): return f"{n:,.0f}"


async def show_leaderboard(message, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        # Top 10 ثروتمند
        rich = session.query(User).filter(
            User.country_id != None
        ).order_by(User.cash.desc()).limit(10).all()
        
        text = f"🏆 <b>جدول رتبه‌بندی</b>\n"
        text += f"━━━━━━━━━━━━━━━━━\n\n"
        text += f"💰 <b>ثروتمندترین‌ها:</b>\n"
        
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for i, r in enumerate(rich):
            medal = medals[i] if i < len(medals) else "🔸"
            c = r.country
            marker = " ⬅️ شما" if r.user_id == u.user_id else ""
            text += f"{medal} {c.flag_emoji} {c.name}: {fmt(r.cash)} 💵{marker}\n"
        
        # رتبه کاربر
        my_rank = session.query(User).filter(
            User.country_id != None,
            User.cash > u.cash
        ).count() + 1
        
        text += f"\n📊 رتبه شما: <b>#{my_rank}</b>\n"
        
        kb = {"inline_keyboard": [
            [{"text": "🏆 برترین ارتش", "callback_data": "lb_military"}],
            [{"text": "⭐ برترین سطح", "callback_data": "lb_level"}],
            [{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}],
        ]}
        
        await message.reply(text, reply_markup=kb)
    finally:
        session.close()


async def show_lb_military(callback_query, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        # همه کاربران
        all_users = session.query(User).filter(User.country_id != None).all()
        
        # محاسبه قدرت نظامی هر کدوم
        powers = []
        for usr in all_users:
            units = session.query(UserUnit).filter_by(user_id=usr.user_id).all()
            atk = sum((uu.unit_type.attack_power or 0) * uu.quantity for uu in units)
            dfn = sum((uu.unit_type.defense_power or 0) * uu.quantity for uu in units)
            powers.append((usr, atk + dfn))
        
        powers.sort(key=lambda x: x[1], reverse=True)
        
        text = f"🏆 <b>برترین ارتش‌ها</b>\n━━━━━━━━━━━━━━━━━\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, (usr, power) in enumerate(powers[:10]):
            medal = medals[i] if i < len(medals) else "🔸"
            c = usr.country
            marker = " ⬅️ شما" if usr.user_id == u.user_id else ""
            text += f"{medal} {c.flag_emoji} {c.name}: {fmt(power)} ⚔️{marker}\n"
        
        await callback_query.message.reply(text, reply_markup={
            "inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "menu_lb"}]]
        })
    finally:
        session.close()


async def show_lb_level(callback_query, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        top = session.query(User).filter(
            User.country_id != None
        ).order_by(User.level.desc(), User.xp.desc()).limit(10).all()
        
        text = f"⭐ <b>برترین سطوح</b>\n━━━━━━━━━━━━━━━━━\n\n"
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        
        for i, r in enumerate(top):
            medal = medals[i] if i < len(medals) else "🔸"
            c = r.country
            marker = " ⬅️ شما" if r.user_id == u.user_id else ""
            text += f"{medal} {c.flag_emoji} {c.name}: سطح {r.level}{marker}\n"
        
        await callback_query.message.reply(text, reply_markup={
            "inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "menu_lb"}]]
        })
    finally:
        session.close() 
        