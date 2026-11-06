"""تحقیقات"""

from models import User, ResearchType, UserResearch, UserUnit


def fmt(n): return f"{n:,.0f}"


def get_total_bonus(user, session, bonus_type):
    """محاسبه مجموع بونوس یک نوع (مثلا attack)"""
    researches = session.query(UserResearch).filter_by(user_id=user.user_id).all()
    total = 0.0
    for ur in researches:
        if ur.research.bonus_type == bonus_type:
            total += ur.research.bonus_value
    return total


async def show_research_menu(message, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        researches = session.query(ResearchType).all()
        
        done_ids = {r.research_type_id for r in session.query(UserResearch).filter_by(user_id=u.user_id).all()}
        
        text = (
            f"🔬 <b>تحقیقات</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 پول: {fmt(u.cash)}\n"
            f"⭐ سطح: {u.level}\n"
            f"✅ انجام‌شده: {len(done_ids)} / {len(researches)}\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
        )
        
        rows = []
        for r in researches:
            done = r.id in done_ids
            emoji = "✅" if done else "🔒" if u.level < r.required_level else "🔬"
            
            text += (
                f"{emoji} {r.emoji} <b>{r.name}</b>\n"
                f"   📝 {r.description}\n"
                f"   💵 {fmt(r.cost_cash)}\n"
                f"   ⭐ نیاز: سطح {r.required_level}\n"
            )
            
            if not done and u.level >= r.required_level:
                rows.append([{
                    "text": f"🔬 تحقیق {r.name[:15]}",
                    "callback_data": f"res_do:{r.id}"
                }])
            elif done:
                text += f"   ✅ انجام شده!\n"
            text += "\n"
        
        rows.append([{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}])
        
        await message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


async def do_research(callback_query, user, Session, research_id):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        r = session.query(ResearchType).filter_by(id=research_id).first()
        
        if not r:
            await callback_query.answer("تحقیق پیدا نشد!")
            return
        
        done = session.query(UserResearch).filter_by(user_id=u.user_id, research_type_id=r.id).first()
        if done:
            await callback_query.answer("قبلاً انجام دادی!")
            return
        
        if u.level < r.required_level:
            await callback_query.answer(f"نیاز به سطح {r.required_level}!")
            return
        
        if u.cash < r.cost_cash:
            await callback_query.answer(f"پول کمه! نیاز: {fmt(r.cost_cash)}")
            return
        
        u.cash -= r.cost_cash
        session.add(UserResearch(user_id=u.user_id, research_type_id=r.id))
        u.xp += 100
        session.commit()
        
        await callback_query.answer(f"✅ {r.name} کامل شد!")
        await callback_query.message.reply(
            f"✅ <b>تحقیق موفق!</b>\n\n"
            f"{r.emoji} <b>{r.name}</b>\n"
            f"📝 {r.description}\n\n"
            f"💰 هزینه: {fmt(r.cost_cash)}\n"
            f"⭐ +100 XP\n"
            f"💵 باقی: {fmt(u.cash)}"
        )
    finally:
        session.close() 
        