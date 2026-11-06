"""دستاوردها"""

from models import User, UserBuilding, UserUnit, Achievement, UserAchievement
from engines.economy import check_level_up, calc_power_score


def fmt(n): return f"{n:,.0f}"


async def show_achievements(message, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        all_ach = session.query(Achievement).all()
        unlocked = {ua.achievement_id for ua in session.query(UserAchievement).filter_by(user_id=u.user_id).all()}
        
        text = (
            f"🏆 <b>دستاوردها</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎯 باز شده: {len(unlocked)}/{len(all_ach)}\n\n"
        )
        
        for ach in all_ach:
            if ach.id in unlocked:
                text += f"✅ {ach.emoji} <b>{ach.name}</b>\n"
                text += f"   💰 +{fmt(ach.reward_cash)} | ⭐ +{ach.reward_xp} XP\n\n"
            else:
                text += f"🔒 {ach.emoji} <b>{ach.name}</b>\n"
                text += f"   📝 {ach.description}\n\n"
        
        kb = {"inline_keyboard": [[{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}]]}
        
        await message.reply(text, reply_markup=kb)
    finally:
        session.close()


async def check_achievements(user, Session):
    """چک کردن دستاوردهای جدید - برگرداندن لیستی از دیکشنری‌های ساده"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        all_ach = session.query(Achievement).all()
        unlocked_ids = {ua.achievement_id for ua in session.query(UserAchievement).filter_by(user_id=u.user_id).all()}
        
        new_unlocks = []
        
        # آمار
        buildings_count = session.query(UserBuilding).filter_by(user_id=u.user_id).count()
        units = session.query(UserUnit).filter_by(user_id=u.user_id).all()
        units_count = sum(uu.quantity for uu in units)
        power = sum((uu.unit_type.attack_power or 0) * uu.quantity for uu in units)
        
        for ach in all_ach:
            if ach.id in unlocked_ids:
                continue
            
            passed = False
            if ach.requirement_type == "buildings" and buildings_count >= ach.requirement_value:
                passed = True
            elif ach.requirement_type == "units" and units_count >= ach.requirement_value:
                passed = True
            elif ach.requirement_type == "level" and u.level >= ach.requirement_value:
                passed = True
            elif ach.requirement_type == "cash" and u.cash >= ach.requirement_value:
                passed = True
            elif ach.requirement_type == "power" and power >= ach.requirement_value:
                passed = True
            
            if passed:
                session.add(UserAchievement(user_id=u.user_id, achievement_id=ach.id))
                u.cash += ach.reward_cash
                u.xp += ach.reward_xp
                # ✅ به جای برگرداندن شیء، دیکشنری ساده برمی‌گردونیم
                new_unlocks.append({
                    "emoji": ach.emoji,
                    "name": ach.name,
                    "reward_cash": ach.reward_cash,
                    "reward_xp": ach.reward_xp,
                })
        
        if new_unlocks:
            check_level_up(u)
        
        session.commit()
        return new_unlocks
    finally:
        session.close()
        