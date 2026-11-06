"""دیپلماسی پیشرفته"""

from datetime import datetime, timedelta
from models import User, Country, DiplomacyPact


def fmt(n): return f"{n:,.0f}"


async def show_diplomacy_menu(message, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        country = u.country
        
        # پیمان‌های فعال
        pacts = session.query(DiplomacyPact).filter(
            ((DiplomacyPact.country1_id == country.id) |
             (DiplomacyPact.country2_id == country.id))
        ).all()
        
        text = (
            f"🤝 <b>وزارت خارجه</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🌍 {country.flag_emoji} {country.name}\n"
            f"🏆 اعتبار: {u.reputation}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📜 <b>پیمان‌های فعال:</b> {len(pacts)}\n\n"
        )
        
        if pacts:
            for p in pacts:
                other_id = p.country2_id if p.country1_id == country.id else p.country1_id
                other = session.query(Country).filter_by(id=other_id).first()
                if other:
                    pact_name = {"peace": "🕊️ صلح", "trade": "💰 تجارت", "nap": "🤝 عدم تجاوز"}.get(p.pact_type, p.pact_type)
                    text += f"• {pact_name} با {other.flag_emoji} {other.name}\n"
        else:
            text += "هنوز هیچ پیمانی نداری."
        
        kb = {"inline_keyboard": [
            [{"text": "📜 لیست کشورها", "callback_data": "dip_countries"}],
            [{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}],
        ]}
        
        await message.reply(text, reply_markup=kb)
    finally:
        session.close()


async def show_countries_diplomacy(callback_query, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        countries = session.query(Country).filter(Country.id != u.country_id).all()
        
        text = "🌍 <b>کشورها</b>\n━━━━━━━━━━━━━━━━━\nبا کدوم کشور می‌خوای مذاکره کنی؟"
        rows = []
        
        for c in countries[:30]:
            owner = session.query(User).filter_by(country_id=c.id).first()
            if owner:
                rows.append([{
                    "text": f"{c.flag_emoji} {c.name}",
                    "callback_data": f"dip_view:{c.id}"
                }])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_diplomacy"}])
        
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


async def show_country_actions(callback_query, user, Session, country_id):
    """نمایش گزینه‌های دیپلماتیک با یک کشور"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        target = session.query(Country).filter_by(id=country_id).first()
        
        if not target:
            await callback_query.answer("کشور پیدا نشد!")
            return
            
        if target.id == u.country_id:
            await callback_query.answer("نمی‌تونی با خودت پیمان ببندی!")
            return
        
        # چک کردن اینکه پیمانی از قبل هست یا نه
        existing = session.query(DiplomacyPact).filter(
            ((DiplomacyPact.country1_id == u.country_id) & (DiplomacyPact.country2_id == target.id)) |
            ((DiplomacyPact.country1_id == target.id) & (DiplomacyPact.country2_id == u.country_id))
        ).first()

        text = (
            f"{target.flag_emoji} <b>{target.name}</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🏛️ پایتخت: {target.capital}\n"
            f"⚔️ بونوس حمله: {target.attack_bonus}x\n"
            f"🛡️ بونوس دفاع: {target.defense_bonus}x\n"
            f"━━━━━━━━━━━━━━━━━\n"
        )
        
        if existing:
            pact_name = {"peace": "🕊️ صلح", "trade": "💰 تجارت", "nap": "🤝 عدم تجاوز"}.get(existing.pact_type)
            text += f"✅ <b>شما با این کشور پیمان {pact_name} دارید!</b>\n"
            kb = {"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "dip_countries"}]]}
        else:
            text += "چه پیمانی پیشنهاد می‌دی؟"
            kb = {"inline_keyboard": [
                [{"text": "🕊️ پیمان صلح (۲۰ اعتبار)", "callback_data": f"dip_pact:peace:{target.id}"}],
                [{"text": "💰 پیمان تجارت (۵۰ اعتبار)", "callback_data": f"dip_pact:trade:{target.id}"}],
                [{"text": "🤝 عدم تجاوز (۳۰ اعتبار)", "callback_data": f"dip_pact:nap:{target.id}"}],
                [{"text": "🔙 بازگشت", "callback_data": "dip_countries"}]
            ]}
        
        await callback_query.message.reply(text, reply_markup=kb)
    finally:
        session.close()


async def make_pact(callback_query, user, Session, pact_type, target_id):
    """ثبت پیمان"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        target = session.query(Country).filter_by(id=target_id).first()
        
        if not target:
            await callback_query.answer("کشور پیدا نشد!")
            return
        
        # هزینه‌های اعتبار
        rep_cost = {"peace": 20, "trade": 50, "nap": 30}
        cost = rep_cost.get(pact_type, 20)
        
        if u.reputation < cost:
            await callback_query.answer(f"اعتبار کافی نداری! نیاز: {cost} (شما: {u.reputation})")
            return
            
        # ثبت پیمان
        pact = DiplomacyPact(
            country1_id=u.country_id, 
            country2_id=target.id, 
            pact_type=pact_type
        )
        session.add(pact)
        
        # کم کردن اعتبار
        u.reputation -= cost
        u.xp += 50
        session.commit()
        
        pact_name = {"peace": "🕊️ صلح", "trade": "💰 تجارت", "nap": "🤝 عدم تجاوز"}.get(pact_type)
        
        await callback_query.answer(f"✅ {pact_name} ثبت شد!")
        await callback_query.message.reply(
            f"✅ <b>پیمان ثبت شد!</b>\n\n"
            f"با: {target.flag_emoji} {target.name}\n"
            f"نوع: {pact_name}\n"
            f"🏆 اعتبار مصرف‌شده: {cost}\n"
            f"⭐ +50 XP"
        )
    finally:
        session.close()