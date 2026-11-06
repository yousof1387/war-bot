"""سیستم حمله و نبرد"""

from datetime import datetime
from models import User, UserUnit
from engines.economy import check_level_up
from handlers.research import get_total_bonus

def fmt(n):
    return f"{n:,.0f}"


# =========================================================
# محاسبه قدرت نظامی کاربر
# =========================================================
def calc_user_power(user, session):
    """محاسبه کل قدرت نظامی کاربر"""
    units = session.query(UserUnit).filter_by(user_id=user.user_id).all()
    
    total_attack = 0
    total_defense = 0
    
    for uu in units:
        if uu.quantity <= 0:
            continue
        total_attack += (uu.unit_type.attack_power or 0) * uu.quantity
        total_defense += (uu.unit_type.defense_power or 0) * uu.quantity
    
    return {
        "attack": total_attack,
        "defense": total_defense,
        "total": total_attack + total_defense,
    }


# =========================================================
# منوی حمله
# =========================================================
async def show_attack_menu(message, user, Session):
    """منوی حمله"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        my_power = calc_user_power(u, session)
        
        text = (
            f"⚔️ <b>اتاق جنگ</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 پول: {fmt(u.cash)}\n"
            f"🏆 اعتبار: {u.reputation}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎯 <b>قدرت نظامی شما:</b>\n"
            f"⚔️ حمله: {fmt(my_power['attack'])}\n"
            f"🛡️ دفاع: {fmt(my_power['defense'])}\n"
            f"🏆 مجموع: {fmt(my_power['total'])}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>هشدار:</b> حمله به کشورها عواقب داره:\n"
            f"• اعتبار شما کم میشه\n"
            f"• ممکنه دشمنانت زیاد بشن\n"
            f"• غنیمت می‌گیری اگر ببری\n"
        )
        
        kb = {"inline_keyboard": [
            [{"text": "🎯 حمله به کشور", "callback_data": "atk_countries"}],
            [{"text": "🌊 حمله به تنگه‌ها", "callback_data": "atk_straits"}],
            [{"text": "📜 تاریخچه نبردها", "callback_data": "atk_history"}],
            [{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}],
        ]}
        
        await message.reply(text, reply_markup=kb)
    finally:
        session.close()


# =========================================================
# انتخاب کشور برای حمله
# =========================================================
async def show_attack_targets(callback_query, user, Session):
    """نمایش کشورها برای حمله"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        targets = session.query(User).filter(
            User.country_id != None,
            User.user_id != u.user_id
        ).all()
        
        if not targets:
            await callback_query.message.reply(
                "🌍 هنوز هیچ کشور دیگه‌ای توسط بازیکنی گرفته نشده!\n"
                "منتظر باش تا بازیکن‌های دیگه بیان."
            )
            return
        
        text = (
            f"🎯 <b>انتخاب هدف</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 پول شما: {fmt(u.cash)}\n"
            f"⚔️ قدرت شما: {fmt(calc_user_power(u, session)['total'])}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⚠️ حمله به هر کشور:\n"
            f"• ۱۰٪ سرباز از دست می‌دی\n"
            f"• ۵- اعتبار\n"
            f"• اگر برنده شدی: غنیمت می‌گیری\n"
            f"• اگر باختی: پول از دست می‌دی\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎯 کدوم کشور؟"
        )
        
        rows = []
        for target in targets[:30]:
            c = target.country
            target_power = calc_user_power(target, session)
            
            rows.append([
                {"text": f"{c.flag_emoji} {c.name} (قدرت: {fmt(target_power['total'])})",
                 "callback_data": f"atk_go:{target.user_id}"},
            ])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_battle"}])
        
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


# =========================================================
# انجام حمله
# =========================================================
async def do_attack(callback_query, user, Session, target_id):
    """انجام حمله"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        target = session.query(User).filter_by(user_id=target_id).first()
        
        if not target:
            await callback_query.answer("هدف پیدا نشد!")
            return
        
        if target.user_id == u.user_id:
            await callback_query.answer("به خودت حمله نکن! 😅")
            return
        
        my_power = calc_user_power(u, session)
        their_power = calc_user_power(target, session)

        my_country = u.country
        their_country = target.country

        # ✅ اعمال بونوس تحقیقات
        atk_bonus = 1.0 + get_total_bonus(u, session, "attack")
        def_bonus = 1.0 + get_total_bonus(target, session, "defense")

        my_attack = my_power["attack"] * (my_country.attack_bonus or 1.0) * atk_bonus
        their_defense = their_power["defense"] * (their_country.defense_bonus or 1.0) * def_bonus
        
        if my_attack > their_defense:
            loot_cash = int(target.cash * 0.2)
            loot_oil = target.oil_barrels * 0.2
            loot_gold = target.gold * 0.2
            
            u.cash += loot_cash
            u.oil_barrels += loot_oil
            u.gold += loot_gold
            
            target.cash -= loot_cash
            target.oil_barrels -= loot_oil
            target.gold -= loot_gold
            
            u.reputation -= 5
            u.xp += 100
            check_level_up(u)
            
            lost_soldiers = int(u.soldiers * 0.1)
            u.soldiers -= lost_soldiers
            
            session.commit()
            
            await callback_query.answer("🎉 پیروزی!")
            await callback_query.message.reply(
                f"🏆 <b>پیروزی!</b>\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"🎯 هدف: {their_country.flag_emoji} {their_country.name}\n"
                f"⚔️ قدرت شما: {fmt(my_attack)}\n"
                f"🛡️ دفاع دشمن: {fmt(their_defense)}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"💰 <b>غنیمت:</b>\n"
                f"💵 {fmt(loot_cash)} دلار\n"
                f"🛢️ {fmt(loot_oil)} بشکه نفت\n"
                f"🥇 {loot_gold:.2f} اونس طلا\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"💀 تلفات: {fmt(lost_soldiers)} سرباز\n"
                f"🏆 اعتبار: -5\n"
                f"⭐ +100 XP"
            )
        else:
            lost_cash = int(u.cash * 0.15)
            lost_soldiers = int(u.soldiers * 0.2)
            
            u.cash -= lost_cash
            u.soldiers -= lost_soldiers
            u.reputation -= 10
            u.xp += 20
            check_level_up(u)
            
            session.commit()
            
            await callback_query.answer("💀 شکست!")
            await callback_query.message.reply(
                f"💀 <b>شکست!</b>\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"🎯 هدف: {their_country.flag_emoji} {their_country.name}\n"
                f"⚔️ قدرت شما: {fmt(my_attack)}\n"
                f"🛡️ دفاع دشمن: {fmt(their_defense)}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"💸 <b>خسارات:</b>\n"
                f"💵 -{fmt(lost_cash)} دلار\n"
                f"💀 -{fmt(lost_soldiers)} سرباز\n"
                f"🏆 اعتبار: -10\n"
                f"⭐ +20 XP\n\n"
                f"⚠️ دفعه بعد تجهیزات بیشتری بخر!"
            )
    finally:
        session.close()
    from handlers.research import get_total_bonus
    # داخل تابع do_attack:
    # ✅ اعمال بونوس تحقیقات
    atk_bonus = 1.0 + get_total_bonus(u, session, "attack")
    def_bonus = 1.0 + get_total_bonus(target, session, "defense")
    my_attack = my_power["attack"] * (my_country.attack_bonus or 1.0) * atk_bonus
    their_defense = their_power["defense"] * (their_country.defense_bonus or 1.0) * def_bonus

# =========================================================
# تاریخچه نبردها
# =========================================================
async def show_battle_history(callback_query, user, Session):
    """تاریخچه نبردها"""
    await callback_query.message.reply(
        "📜 <b>تاریخچه نبردها</b>\n"
        "━━━━━━━━━━━━━━━━━\n"
        "⚠️ هنوز هیچ نبردی ثبت نشده!\n\n"
        "💡 بعد از اولین حمله، تاریخچه اینجا نمایش داده میشه.",
        reply_markup={"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "menu_battle"}]]}
    )
    