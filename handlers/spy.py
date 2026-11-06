"""سیستم جاسوسی"""

import random
from datetime import datetime, timedelta
from models import User, UserUnit, UserBuilding, SpyMission


def fmt(n): return f"{n:,.0f}"


async def show_spy_menu(message, user, Session):
    """منوی جاسوسی"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        # هزینه‌ها
        cost_army = 5000
        cost_econ = 5000
        cost_research = 10000
        
        text = (
            f"🕵️ <b>آژانس اطلاعاتی</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 پول: {fmt(u.cash)}\n"
            f"🏆 اعتبار: {u.reputation}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⚠️ <b>عملیات‌های جاسوسی:</b>\n"
            f"• شانس موفقیت: ۷۰٪\n"
            f"• در صورت لو رفتن: -۵ اعتبار\n"
            f"• ۲۰٪ پول از دست می‌دهی\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🎯 عملیات مورد نظر رو انتخاب کن:"
        )
        
        kb = {"inline_keyboard": [
            [{"text": f"⚔️ جاسوسی ارتش ({fmt(cost_army)}💵)",
              "callback_data": f"spy_start:army:{cost_army}"}],
            [{"text": f"💰 جاسوسی اقتصاد ({fmt(cost_econ)}💵)",
              "callback_data": f"spy_start:economy:{cost_econ}"}],
            [{"text": f"🔬 جاسوسی تحقیقات ({fmt(cost_research)}💵)",
              "callback_data": f"spy_start:research:{cost_research}"}],
            [{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}],
        ]}
        
        await message.reply(text, reply_markup=kb)
    finally:
        session.close()


async def show_spy_targets(callback_query, user, Session, mission_type, cost):
    """نمایش اهداف"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        # همه بازیکن‌های دیگه
        targets = session.query(User).filter(
            User.country_id != None,
            User.user_id != u.user_id
        ).all()
        
        if not targets:
            await callback_query.message.reply(
                "🌍 هنوز بازیکن دیگه‌ای نیست که جاسوسی کنی!"
            )
            return
        
        mission_names = {
            "army": "⚔️ ارتش",
            "economy": "💰 اقتصاد",
            "research": "🔬 تحقیقات",
        }
        
        text = (
            f"🕵️ <b>جاسوسی {mission_names.get(mission_type, '')}</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 هزینه: {fmt(cost)}\n"
            f"🎯 کدوم کشور؟"
        )
        
        rows = []
        for t in targets[:30]:
            c = t.country
            rows.append([{
                "text": f"{c.flag_emoji} {c.name}",
                "callback_data": f"spy_go:{mission_type}:{t.user_id}:{cost}"
            }])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_spy"}])
        
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


async def do_spy(callback_query, user, Session, mission_type, target_id, cost):
    """انجام عملیات جاسوسی"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        target = session.query(User).filter_by(user_id=target_id).first()
        
        if not target:
            await callback_query.answer("هدف پیدا نشد!")
            return
        
        if u.user_id == target.user_id:
            await callback_query.answer("خودت رو جاسوسی نکن! 😅")
            return
        
        # چک پول
        if u.cash < cost:
            await callback_query.answer(f"پول کمه! نیاز: {fmt(cost)}")
            return
        
        u.cash -= cost
        
        # شانس موفقیت 70٪
        success = random.random() < 0.7
        
        if success:
            # عملیات موفق - اطلاعات جمع‌آوری کن
            if mission_type == "army":
                units = session.query(UserUnit).filter_by(user_id=target.user_id).all()
                attack = sum((uu.unit_type.attack_power or 0) * uu.quantity for uu in units)
                defense = sum((uu.unit_type.defense_power or 0) * uu.quantity for uu in units)
                total_qty = sum(uu.quantity for uu in units)
                
                result_text = (
                    f"⚔️ <b>ارتش {target.country.flag_emoji} {target.country.name}:</b>\n"
                    f"🎖️ تعداد تجهیزات: {fmt(total_qty)}\n"
                    f"⚔️ قدرت حمله: {fmt(attack)}\n"
                    f"🛡️ قدرت دفاع: {fmt(defense)}\n"
                    f"💀 سربازان: {target.soldiers:,}\n"
                )
            elif mission_type == "economy":
                result_text = (
                    f"💰 <b>اقتصاد {target.country.flag_emoji} {target.country.name}:</b>\n"
                    f"💵 پول نقد: {fmt(target.cash)}\n"
                    f"🥇 طلا: {target.gold:,.1f}\n"
                    f"🛢️ نفت: {fmt(target.oil_barrels)}\n"
                    f"☢️ اورانیوم: {target.uranium:,.1f}\n"
                    f"⚙️ فولاد: {fmt(target.steel)}\n"
                    f"🌾 غذا: {fmt(target.food)}\n"
                )
            else:  # research
                result_text = (
                    f"🔬 <b>تحقیقات {target.country.flag_emoji} {target.country.name}:</b>\n"
                    f"⭐ سطح: {target.level}\n"
                    f"✨ XP: {target.xp}\n"
                    f"🏆 قدرت کل: {fmt(target.power_score)}\n"
                )
            
            # ثبت ماموریت
            session.add(SpyMission(
                spy_id=u.user_id, target_id=target.user_id,
                mission_type=mission_type, success=True,
                result_data=result_text,
            ))
            
            u.xp += 50
            session.commit()
            
            await callback_query.answer("✅ عملیات موفق!")
            await callback_query.message.reply(
                f"🕵️ <b>جاسوسی موفق!</b>\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"{result_text}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"⭐ +50 XP"
            )
        else:
            # عملیات لو رفت
            lost_cash = int(u.cash * 0.2)  # ۲۰٪ دیگه از پول هم می‌ره
            u.cash -= lost_cash
            u.reputation -= 5
            
            # ثبت ماموریت
            session.add(SpyMission(
                spy_id=u.user_id, target_id=target.user_id,
                mission_type=mission_type, success=False,
                result_data="عملیات لو رفت!",
            ))
            
            session.commit()
            
            await callback_query.answer("❌ عملیات لو رفت!")
            await callback_query.message.reply(
                f"❌ <b>عملیات لو رفت!</b>\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"🎯 هدف: {target.country.flag_emoji} {target.country.name}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"💸 خسارت: -{fmt(lost_cash)} دلار\n"
                f"🏆 اعتبار: -5\n\n"
                f"⚠️ دشمن از تلاش شما باخبر شد!"
            )
    finally:
        session.close()
        