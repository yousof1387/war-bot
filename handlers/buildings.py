"""هندلرهای ساختمان‌ها"""

from datetime import datetime
from models import User, BuildingType, UserBuilding
from engines.economy import calc_pending, upgrade_cost, total_income, check_level_up, xp_needed_for_level
from handlers.achievements import check_achievements

def fmt(n): return f"{n:,.0f}"

CATEGORIES = {
    "economic": ("💰", "اقتصادی"),
    "military": ("⚔️", "نظامی"),
    "research": ("🔬", "تحقیقاتی"),
    "infrastructure": ("🏗️", "زیرساختی"),
}
MAX_LEVEL = 15

async def show_buildings_menu(message, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        country = u.country
        ubs = session.query(UserBuilding).filter_by(user_id=u.user_id).all()
        all_bs = session.query(BuildingType).all()
        # ✅ اصلاح شد
        income = total_income(ubs, u.level, country)
        
        from collections import Counter
        cat_count = Counter(ub.building_type.category for ub in ubs)
        
        text = (
            f"🏗️ <b>مدیریت ساختمان‌ها</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⭐ سطح: {u.level} | ✨ XP: {u.xp}/{xp_needed_for_level(u.level)}\n"
            f"💵 پول نقد: {fmt(u.cash)}\n"
            f"📈 درآمد: {fmt(income['cash'])}/ساعت\n"
            f"━━━━━━━━━━━━━━━━━\n"
        )
        for cat_key, (emoji, name) in CATEGORIES.items():
            count = cat_count.get(cat_key, 0)
            total = sum(1 for b in all_bs if b.category == cat_key)
            text += f"{emoji} {name}: {count}/{total}\n"
        
        kb = {"inline_keyboard": [
            [{"text": "💰 اقتصادی", "callback_data": "bcat:economic"},
             {"text": "⚔️ نظامی", "callback_data": "bcat:military"}],
            [{"text": "🔬 تحقیقاتی", "callback_data": "bcat:research"},
             {"text": "🏗️ زیرساختی", "callback_data": "bcat:infrastructure"}],
            [{"text": "🏢 ساختمان‌های من", "callback_data": "bmy"},
             {"text": "💵 جمع‌آوری همه", "callback_data": "bcoll_all"}],
            [{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}],
        ]}
        await message.reply(text, reply_markup=kb)
    finally:
        session.close()

async def show_category(callback_query, user, Session, cat):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        country = u.country
        emoji, name = CATEGORIES.get(cat, ("🏗️", ""))
        buildings = session.query(BuildingType).filter_by(category=cat).order_by(BuildingType.required_level).all()
        ubs = session.query(UserBuilding).filter_by(user_id=u.user_id).all()
        owned = {ub.building_type_id: ub for ub in ubs}
        
        text = f"{emoji} <b>ساختمان‌های {name}</b>\n━━━━━━━━━━━━━━━━━\n⭐ سطح: {u.level} | 💵 {fmt(u.cash)}\n\n"
        rows = []
        for b in buildings:
            ub = owned.get(b.id)
            if ub:
                # ✅ اصلاح شد
                p = calc_pending(ub, u.level, country)
                text += f"{b.emoji} <b>{b.name}</b> (سطح {ub.level})\n   💰 آماده: {fmt(p['cash'])}\n\n"
                if ub.level < MAX_LEVEL:
                    cost = upgrade_cost(b, ub.level)
                    rows.append([
                        {"text": f"💵 جمع {b.name[:8]}", "callback_data": f"bcol:{ub.id}"},
                        {"text": f"⬆️ ارتقا {fmt(cost)}💵", "callback_data": f"bup:{ub.id}"},
                    ])
                else:
                    rows.append([{"text": f"💵 جمع {b.name[:8]}", "callback_data": f"bcol:{ub.id}"}])
            elif u.level < (b.required_level or 1):
                text += f"🔒 <b>{b.name}</b> (نیاز به سطح {b.required_level})\n\n"
            else:
                text += f"{b.emoji} <b>{b.name}</b>\n   💵 {fmt(b.build_cost)}\n   📈 {fmt(b.income_cash)}/ساعت\n\n"
                rows.append([{"text": f"🔨 ساخت {b.name[:12]}", "callback_data": f"bcreate:{b.id}"}])
                
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_build"}])
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()

async def show_my(callback_query, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        ubs = session.query(UserBuilding).filter_by(user_id=u.user_id).all()
        if not ubs:
            await callback_query.message.reply("🏗️ هنوز ساختمانی نساختی!")
            return
            
        text = f"🏢 <b>ساختمان‌های من</b>\n━━━━━━━━━━━━━━━━━\n💵 {fmt(u.cash)}\n\n"
        total = 0
        for ub in ubs:
            # ✅ اصلاح شد
            p = calc_pending(ub, u.level, u.country)
            total += p["cash"]
            text += f"{ub.building_type.emoji} {ub.building_type.name} (L{ub.level}) → {fmt(p['cash'])}\n"
        text += f"\n💰 مجموع: {fmt(total)}"
        
        kb = {"inline_keyboard": [
            [{"text": "💵 جمع‌آوری همه", "callback_data": "bcoll_all"}],
            [{"text": "🔙", "callback_data": "menu_build"}],
        ]}
        await callback_query.message.reply(text, reply_markup=kb)
    finally:
        session.close()

async def create_building(callback_query, user, Session, bid):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        b = session.query(BuildingType).filter_by(id=bid).first()
        if not b: return await callback_query.answer("پیدا نشد!")
        if u.level < (b.required_level or 1): return await callback_query.answer(f"نیاز به سطح {b.required_level}!")
        if session.query(UserBuilding).filter_by(user_id=u.user_id, building_type_id=bid).first():
            return await callback_query.answer("قبلاً داری!")
        if u.cash < b.build_cost: return await callback_query.answer(f"پول کمه! نیاز: {fmt(b.build_cost)}")
        
        u.cash -= b.build_cost
        session.add(UserBuilding(user_id=u.user_id, building_type_id=bid, level=1))
        u.xp += 25
        check_level_up(u)
        session.commit()
        # چک دستاوردها
        await callback_query.answer(f"✅ {b.name} ساخته شد!")
        await callback_query.message.reply(f"✅ <b>{b.name}</b> ساخته شد!\n💰 هزینه: {fmt(b.build_cost)}\n💵 باقی: {fmt(u.cash)}\n⭐ +25 XP")
        new_ach = await check_achievements(user, Session)
        for ach in new_ach:
            await callback_query.message.reply(
                f"🎉 <b>دستاورد جدید!</b>\n"
                f"{ach.emoji} <b>{ach.name}</b>\n"
                f"🎁 پاداش:\n"
                f"💰 +{fmt(ach.reward_cash)}\n"
                f"⭐ +{ach.reward_xp} XP"
            )
    finally:
        session.close()

async def upgrade(callback_query, user, Session, ubid):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        ub = session.query(UserBuilding).filter_by(id=ubid, user_id=u.user_id).first()
        if not ub: return await callback_query.answer("پیدا نشد!")
        if ub.level >= MAX_LEVEL: return await callback_query.answer("حداکثر سطح!")
        
        cost = upgrade_cost(ub.building_type, ub.level)
        if u.cash < cost: return await callback_query.answer(f"پول کمه! نیاز: {fmt(cost)}")
        
        u.cash -= cost
        ub.level += 1
        u.xp += 15 * ub.level
        check_level_up(u)
        session.commit()
        
        await callback_query.answer(f"⬆️ سطح {ub.level}!")
        await callback_query.message.reply(f"✅ <b>{ub.building_type.name}</b> به سطح {ub.level} ارتقا یافت!")
    finally:
        session.close()

async def collect(callback_query, user, Session, ubid):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        ub = session.query(UserBuilding).filter_by(id=ubid, user_id=u.user_id).first()
        if not ub: return await callback_query.answer("پیدا نشد!")
        
        # ✅ اصلاح شد
        p = calc_pending(ub, u.level, u.country)
        if p["cash"] < 1: return await callback_query.answer("هنوز درآمدی آماده نیست!")
        
        u.cash += p["cash"]; u.gold += p["gold"]; u.oil_barrels += p["oil"]
        u.uranium += p["uranium"]; u.steel += p["steel"]; u.food += p["food"]
        u.xp += 5; check_level_up(u)
        ub.last_collected_at = datetime.utcnow()
        session.commit()
        
        await callback_query.answer(f"✅ +{fmt(p['cash'])} 💵 | +5 XP")
        await callback_query.message.reply(f"💰 دریافت شد: {fmt(p['cash'])} دلار از {ub.building_type.name}")
    finally:
        session.close()

async def collect_all(callback_query, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        ubs = session.query(UserBuilding).filter_by(user_id=u.user_id).all()
        if not ubs: return await callback_query.answer("ساختمانی نداری!")
        
        total = {"cash": 0}; count = 0
        for ub in ubs:
            # ✅ اصلاح شد
            p = calc_pending(ub, u.level, u.country)
            if p["cash"] >= 1:
                u.cash += p["cash"]; u.gold += p["gold"]; u.oil_barrels += p["oil"]
                u.uranium += p["uranium"]; u.steel += p["steel"]; u.food += p["food"]
                total["cash"] += p["cash"]
                ub.last_collected_at = datetime.utcnow(); count += 1
        
        if count == 0: return await callback_query.answer("هنوز درآمدی آماده نیست!")
        u.xp += 3 * count; check_level_up(u); session.commit()
        
        await callback_query.answer(f"✅ از {count} ساختمان!")
        await callback_query.message.reply(f"💰 <b>درآمد کل:</b>\nاز {count} ساختمان دریافت شد.\n💵 +{fmt(total['cash'])}\n⭐ +{3 * count} XP")
    finally:
        session.close()
        