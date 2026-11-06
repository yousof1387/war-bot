"""جوایز و مأموریت‌های روزانه"""

from datetime import datetime, timedelta
from models import User, UserBuilding, UserUnit
from engines.economy import check_level_up


def fmt(n): return f"{n:,.0f}"


async def show_daily_menu(message, user, Session):
    """منوی جایزه روزانه"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        # چک کردن اینکه امروز جایزه گرفته یا نه
        can_claim = True
        streak = u.daily_streak or 0
        
        if u.last_daily_reward:
            # اگه کمتر از ۲۴ ساعت گذشته
            time_diff = datetime.utcnow() - u.last_daily_reward
            if time_diff < timedelta(hours=24):
                can_claim = False
                remaining = timedelta(hours=24) - time_diff
                hours = remaining.seconds // 3600
                minutes = (remaining.seconds % 3600) // 60
                time_str = f"{hours} ساعت و {minutes} دقیقه"
        
        text = (
            f"🎁 <b>جوایز روزانه</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🔥 استریک شما: {streak} روز\n"
            f"━━━━━━━━━━━━━━━━━\n"
        )
        
        if can_claim:
            reward_cash = 5000 + (streak * 1000) # هر روز ۱۰۰۰ بیشتر
            reward_xp = 50 + (streak * 10)
            
            text += (
                f"✅ <b>جایزه امروز آماده است!</b>\n\n"
                f"💰 پول: {fmt(reward_cash)}\n"
                f"⭐ XP: {fmt(reward_xp)}\n"
            )
            
            kb = {"inline_keyboard": [
                [{"text": "🎁 دریافت جایزه", "callback_data": "daily_claim"}],
                [{"text": "📋 مأموریت‌ها", "callback_data": "daily_missions"}],
                [{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}],
            ]}
        else:
            text += (
                f"⏳ <b>جایزه امروز رو گرفتی!</b>\n"
                f"⏰ زمان باقی‌مانده: {time_str}\n\n"
                f"💡 فردا برگرد تا استریکت بیشتر بشه!\n"
            )
            kb = {"inline_keyboard": [
                [{"text": "📋 مأموریت‌ها", "callback_data": "daily_missions"}],
                [{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}],
            ]}
        
        await message.reply(text, reply_markup=kb)
    finally:
        session.close()


async def claim_daily(callback_query, user, Session):
    """دریافت جایزه روزانه"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        # چک مجدد
        if u.last_daily_reward:
            time_diff = datetime.utcnow() - u.last_daily_reward
            if time_diff < timedelta(hours=24):
                await callback_query.answer("هنوز ۲۴ ساعت نشده!")
                return
                
            # اگه بین ۲۴ تا ۴۸ ساعت گذشته، استریک حفظ میشه
            if time_diff > timedelta(hours=48):
                u.daily_streak = 0
            else:
                u.daily_streak += 1
        else:
            u.daily_streak = 1
            
        streak = u.daily_streak
        reward_cash = 5000 + (streak * 1000)
        reward_xp = 50 + (streak * 10)
        
        u.cash += reward_cash
        u.xp += reward_xp
        u.last_daily_reward = datetime.utcnow()
        
        check_level_up(u)
        session.commit()
        
        await callback_query.answer("🎉 جایزه دریافت شد!")
        await callback_query.message.reply(
            f"🎁 <b>جایزه روزانه دریافت شد!</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🔥 استریک: {streak} روز\n"
            f"💰 پول: +{fmt(reward_cash)}\n"
            f"⭐ XP: +{fmt(reward_xp)}\n"
            f"💵 موجودی: {fmt(u.cash)}"
        )
    finally:
        session.close()


async def show_missions(callback_query, user, Session):
    """مأموریت‌های روزانه"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        # آمار امروز (بر اساس ساختمان‌ها و تجهیزات)
        buildings_count = session.query(UserBuilding).filter_by(user_id=u.user_id).count()
        units_count = session.query(UserUnit).filter_by(user_id=u.user_id).count()
        
        text = (
            f"📋 <b>مأموریت‌های روزانه</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⚠️ مأموریت‌ها به‌زودی فعال میشن!\n\n"
            f"💡 فعلاً می‌تونی:\n"
            f"🏢 ساختمان بسازی: {buildings_count}\n"
            f"⚔️ تجهیزات بخری: {units_count}\n"
            f"🎁 جایزه روزانه بگیری\n"
        )
        
        kb = {"inline_keyboard": [
            [{"text": "🔙 بازگشت", "callback_data": "menu_daily"}],
        ]}
        
        await callback_query.message.reply(text, reply_markup=kb)
    finally:
        session.close() 
        