"""هندلرهای نظامی"""

from models import User, MilitaryUnitType, UserUnit
from engines.economy import check_level_up
from utils.diplomacy import (
    get_relation, get_price_multiplier, get_required_level,
    get_reputation_cost, get_relation_emoji, get_relation_name,
)

def fmt(n): return f"{n:,.0f}"

MILITARY_CATS = {
    "drones": ("🛩️", "پهپاد"), "missiles": ("🚀", "موشک"), "fighters": ("✈️", "جنگنده"),
    "bombers": ("🛬", "بمب‌افکن"), "air_defense": ("🛡️", "پدافند هوایی"), "naval": ("🚢", "ناوگان دریایی"),
    "submarines": ("🛥️", "زیردریایی"), "tanks": ("🛡️", "تانک"), "artillery": ("💥", "توپخانه"),
    "armor": ("🚗", "زرهی"), "atgm": ("🎯", "ضدتانک"),
}

async def show_military_menu(message, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        country = u.country
        units = session.query(MilitaryUnitType).filter_by(country_id=country.id).all()
        user_units = session.query(UserUnit).filter_by(user_id=u.user_id).all()
        
        total_attack = sum((uu.unit_type.attack_power or 0) * uu.quantity for uu in user_units)
        total_defense = sum((uu.unit_type.defense_power or 0) * uu.quantity for uu in user_units)
        total_qty = sum(uu.quantity for uu in user_units)
        
        text = (
            f"⚔️ <b>ارتش {country.flag_emoji} {country.name}</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 پول نقد: {fmt(u.cash)}\n"
            f"🎖️ تجهیزات شما: {total_qty}\n"
            f"⚔️ قدرت حمله: {fmt(total_attack)}\n"
            f"🛡️ قدرت دفاع: {fmt(total_defense)}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"🌍 کشور شما این تجهیزات رو داره:"
        )
        
        rows = []
        from collections import Counter
        cat_count = Counter(unit.category for unit in units)
        row = []
        for cat in MILITARY_CATS:
            if cat_count.get(cat, 0) > 0:
                emoji, name = MILITARY_CATS[cat]
                row.append({"text": f"{emoji} {name}", "callback_data": f"mcat:{cat}"})
                if len(row) == 2: rows.append(row); row = []
        if row: rows.append(row)
        
        rows.append([{"text": "🌍 خرید خارجی", "callback_data": "mforeign"}])
        rows.append([{"text": "🎖️ ارتش من", "callback_data": "mymy"}])
        rows.append([{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}])
        
        await message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()

async def show_military_category(callback_query, user, Session, cat):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        emoji, name = MILITARY_CATS.get(cat, ("🎯", ""))
        units = session.query(MilitaryUnitType).filter_by(country_id=u.country_id, category=cat).all()
        user_units = session.query(UserUnit).filter_by(user_id=u.user_id).all()
        owned = {uu.unit_type_id: uu for uu in user_units}
        
        text = f"{emoji} <b>تجهیزات {name}</b>\n💵 {fmt(u.cash)}\n\n"
        rows = []
        for unit in units:
            uu = owned.get(unit.id); qty = uu.quantity if uu else 0
            text += f"{unit.emoji} <b>{unit.name}</b>\n⚔️ {fmt(unit.attack_power)} | 🛡️ {fmt(unit.defense_power)}\n💵 {fmt(unit.cost)}\n✅ دارید: {qty}\n\n"
            rows.append([{"text": f"🛒 خرید ۱ عدد - {fmt(unit.cost)}💵", "callback_data": f"mbuy:{unit.id}:1"}])
            rows.append([{"text": "خرید ۵ عدد", "callback_data": f"mbuy:{unit.id}:5"}, {"text": "خرید ۱۰ عدد", "callback_data": f"mbuy:{unit.id}:10"}])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_army"}])
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()

async def show_my_army(callback_query, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        user_units = session.query(UserUnit).filter_by(user_id=u.user_id).all()
        user_units = [uu for uu in user_units if uu.quantity > 0]
        
        if not user_units: return await callback_query.message.reply("⚔️ هنوز هیچ تجهیزاتی نداری!")
        
        text = f"🎖️ <b>ارتش من</b>\n━━━━━━━━━━━━━━━━━\n"
        total_attack = 0; total_defense = 0; total_qty = 0
        by_cat = {}
        for uu in user_units: by_cat.setdefault(uu.unit_type.category, []).append(uu)
        
        for cat, units in by_cat.items():
            emoji, name = MILITARY_CATS.get(cat, ("🎯", ""))
            text += f"\n{emoji} <b>{name}:</b>\n"
            for uu in units:
                attack = (uu.unit_type.attack_power or 0) * uu.quantity
                defense = (uu.unit_type.defense_power or 0) * uu.quantity
                total_attack += attack; total_defense += defense; total_qty += uu.quantity
                text += f"  {uu.unit_type.emoji} {uu.unit_type.name} × {uu.quantity}\n"
        
        text += f"\n━━━━━━━━━━━━━━━━━\n📊 <b>جمع کل:</b>\n🎖️ {fmt(total_qty)}\n⚔️ {fmt(total_attack)}\n🛡️ {fmt(total_defense)}"
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "menu_army"}]]})
    finally:
        session.close()

async def buy_unit(callback_query, user, Session, unit_id, qty):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        unit = session.query(MilitaryUnitType).filter_by(id=unit_id).first()
        
        if not unit or unit.country_id != u.country_id: return await callback_query.answer("تجهیزات نامعتبر!")
        if u.level < (unit.required_level or 1): return await callback_query.answer(f"نیاز به سطح {unit.required_level}!")
        
        cost = unit.cost * qty
        if u.cash < cost: return await callback_query.answer(f"پول کمه! نیاز: {fmt(cost)}")
        
        u.cash -= cost
        uu = session.query(UserUnit).filter_by(user_id=u.user_id, unit_type_id=unit_id).first()
        if uu: uu.quantity += qty
        else: session.add(UserUnit(user_id=u.user_id, unit_type_id=unit_id, quantity=qty))
        
        u.xp += 10 * qty; check_level_up(u); session.commit()
        await callback_query.answer(f"✅ {qty} × {unit.name} خریده شد!")
        await callback_query.message.reply(f"✅ <b>{qty} × {unit.emoji} {unit.name}</b> خریداری شد!\n💰 هزینه: {fmt(cost)}\n💵 باقی: {fmt(u.cash)}")
    finally:
        session.close()

async def show_foreign_countries(callback_query, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        from models import Country
        countries = session.query(Country).filter(Country.id != u.country_id).all()
        
        text = f"🌍 <b>خرید خارجی</b>\n💵 {fmt(u.cash)} | 🏆 {u.reputation}\n\n🟢 دوست (×1.2)\n🟡 بی‌طرف (×1.5)\n🔴 دشمن (×2.0)\n\nانتخاب کن:"
        rows = []; row = []
        for i, c in enumerate(countries, 1):
            rel = get_relation(u.country.name, c.name)
            row.append({"text": f"{get_relation_emoji(rel)} {c.flag_emoji} {c.name}", "callback_data": f"mfc:{c.id}"})
            if i % 2 == 0: rows.append(row); row = []
        if row: rows.append(row)
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_army"}])
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()

async def show_foreign_units(callback_query, user, Session, country_id):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        from models import Country
        target = session.query(Country).filter_by(id=country_id).first()
        
        rel = get_relation(u.country.name, target.name)
        mult = get_price_multiplier(rel); req_lvl = get_required_level(rel)
        
        if u.level < req_lvl: return await callback_query.answer(f"نیاز به سطح {req_lvl}!")
        
        units = session.query(MilitaryUnitType).filter_by(country_id=target.id).all()
        if not units: return await callback_query.answer("این کشور تجهیزات نداره!")
        
        text = f"🌍 <b>{target.flag_emoji} {target.name}</b>\n{get_relation_emoji(rel)} {get_relation_name(rel)} | 💰 ×{mult}\n💵 {fmt(u.cash)}\n\n"
        rows = []
        from collections import defaultdict
        by_cat = defaultdict(list)
        for unit in units: by_cat[unit.category].append(unit)
        
        for cat, cat_units in by_cat.items():
            emoji, name = MILITARY_CATS.get(cat, ("🎯", ""))
            text += f"{emoji} <b>{name}:</b>\n"
            for unit in cat_units[:3]:
                price = int(unit.cost * mult)
                text += f"  {unit.name} - {fmt(price)}💵\n"
                rows.append([{"text": f"🛒 {unit.name[:18]}", "callback_data": f"mfbuy:{unit.id}:1"}])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "mforeign"}])
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()

async def buy_foreign_unit(callback_query, user, Session, unit_id, qty):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        unit = session.query(MilitaryUnitType).filter_by(id=unit_id).first()
        
        if not unit or unit.country_id == u.country_id: return await callback_query.answer("تجهیزات نامعتبر!")
        
        rel = get_relation(u.country.name, unit.country.name)
        mult = get_price_multiplier(rel); req_lvl = get_required_level(rel); rep_cost = get_reputation_cost(rel)
        
        if u.level < req_lvl: return await callback_query.answer(f"نیاز به سطح {req_lvl}!")
        
        price = int(unit.cost * mult * qty)
        if u.cash < price: return await callback_query.answer(f"پول کمه! نیاز: {fmt(price)}")
        
        u.cash -= price; u.reputation += rep_cost
        uu = session.query(UserUnit).filter_by(user_id=u.user_id, unit_type_id=unit_id).first()
        if uu: uu.quantity += qty
        else: session.add(UserUnit(user_id=u.user_id, unit_type_id=unit_id, quantity=qty))
        
        u.xp += 10 * qty; check_level_up(u); session.commit()
        await callback_query.answer(f"✅ {qty} × {unit.name} خریده شد!")
        
        rep_text = f"🏆 اعتبار: {rep_cost:+d}" if rep_cost != 0 else "🏆 اعتبار: بدون تغییر"
        await callback_query.message.reply(f"✅ <b>{qty} × {unit.name}</b>\nاز: {unit.country.flag_emoji} {unit.country.name}\n💰 هزینه: {fmt(price)}\n{rep_text}\n💵 باقی: {fmt(u.cash)}")
    finally:
        session.close()