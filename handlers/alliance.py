"""سیستم اتحاد"""

from models import User, Alliance, AllianceMember
from engines.economy import check_level_up


def fmt(n): return f"{n:,.0f}"


async def show_alliance_menu(message, user, Session):
    """منوی اتحاد"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        # چک کن عضو اتحادی هست یا نه
        membership = session.query(AllianceMember).filter_by(user_id=u.user_id).first()
        
        if membership:
            # عضو اتحاد هست
            alliance = membership.alliance
            members = session.query(AllianceMember).filter_by(alliance_id=alliance.id).all()
            
            text = (
                f"🤝 <b>اتحاد {alliance.name}</b>\n"
                f"🏷️ TAG: [{alliance.tag or '-'}]\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"👥 اعضا: {len(members)}\n"
                f"💰 خزانه: {fmt(alliance.treasury)}\n"
                f"🏆 قدرت کل: {fmt(alliance.total_power)}\n"
                f"👑 رهبر: {get_leader_name(alliance, session)}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"🎖️ رتبه شما: {membership.rank}\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"👥 <b>اعضا:</b>\n"
            )
            
            for m in members:
                mu = session.query(User).filter_by(user_id=m.user_id).first()
                if mu and mu.country:
                    rank_emoji = "👑" if m.rank == "leader" else "🎖️" if m.rank == "officer" else "👤"
                    text += f"{rank_emoji} {mu.country.flag_emoji} {mu.country.name}\n"
            
            kb = {"inline_keyboard": []}
            
            if membership.rank == "leader":
                kb["inline_keyboard"].append([{"text": "💰 کمک به خزانه", "callback_data": "all_donate"}])
                kb["inline_keyboard"].append([{"text": "💥 منحل کردن اتحاد", "callback_data": "all_disband"}])
            
            kb["inline_keyboard"].append([{"text": "🚪 خروج از اتحاد", "callback_data": "all_leave"}])
            kb["inline_keyboard"].append([{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}])
        else:
            # عضو اتحادی نیست
            alliances = session.query(Alliance).all()
            
            text = (
                f"🤝 <b>اتحادها</b>\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"⚠️ شما عضو هیچ اتحادی نیستید!\n"
                f"━━━━━━━━━━━━━━━━━\n"
                f"🏰 اتحادهای موجود: {len(alliances)}\n\n"
            )
            
            if alliances:
                text += "📋 لیست اتحادها:\n"
                for a in alliances[:10]:
                    members_count = session.query(AllianceMember).filter_by(alliance_id=a.id).count()
                    text += f"• <b>{a.name}</b> [{a.tag or '-'}] - {members_count} عضو\n"
            else:
                text += "هنوز اتحادی ساخته نشده!"
            
            kb = {"inline_keyboard": [
                [{"text": "🏰 ساخت اتحاد جدید", "callback_data": "all_create"}],
                [{"text": "📋 لیست اتحادها", "callback_data": "all_list"}],
                [{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}],
            ]}
        
        await message.reply(text, reply_markup=kb)
    finally:
        session.close()


def get_leader_name(alliance, session):
    if not alliance.leader_id:
        return "-"
    leader = session.query(User).filter_by(user_id=alliance.leader_id).first()
    if leader and leader.country:
        return f"{leader.country.flag_emoji} {leader.country.name}"
    return "-"


async def show_alliance_list(callback_query, user, Session):
    """لیست همه اتحادها"""
    session = Session()
    try:
        alliances = session.query(Alliance).all()
        
        if not alliances:
            await callback_query.message.reply("هنوز اتحادی ساخته نشده!")
            return
        
        text = "🏰 <b>لیست اتحادها</b>\n━━━━━━━━━━━━━━━━━\n\n"
        rows = []
        
        for a in alliances[:20]:
            members_count = session.query(AllianceMember).filter_by(alliance_id=a.id).count()
            text += (
                f"🏰 <b>{a.name}</b> [{a.tag or '-'}]\n"
                f"   👥 {members_count} عضو\n"
                f"   💰 {fmt(a.treasury)}\n\n"
            )
            rows.append([{
                "text": f"🏰 {a.name[:20]}",
                "callback_data": f"all_view:{a.id}"
            }])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_alliance"}])
        
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


async def create_alliance_start(callback_query, user, Session):
    """شروع ساخت اتحاد"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        
        # چک سطح
        if u.level < 5:
            await callback_query.answer("نیاز به سطح ۵!")
            return
        
        # چک پول
        if u.cash < 50_000:
            await callback_query.answer(f"نیاز به ۵۰,۰۰۰ دلار!")
            return
        
        # چک نبودن در اتحاد دیگه
        existing = session.query(AllianceMember).filter_by(user_id=u.user_id).first()
        if existing:
            await callback_query.answer("قبلاً عضو اتحادی هستی!")
            return
        
        await callback_query.message.reply(
            f"🏰 <b>ساخت اتحاد جدید</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 هزینه: ۵۰,۰۰۰ دلار\n"
            f"📝 برای ساخت، دستور زیر رو بفرست:\n\n"
            f"<code>/create_alliance نام اتحاد | TAG</code>\n\n"
            f"مثال:\n"
            f"<code>/create_alliance محور شرق | ME</code>\n\n"
            f"⚠️ نام نباید تکراری باشه"
        )
    finally:
        session.close()


async def show_alliance_detail(callback_query, user, Session, alliance_id):
    """نمایش جزئیات اتحاد"""
    session = Session()
    try:
        a = session.query(Alliance).filter_by(id=alliance_id).first()
        if not a:
            await callback_query.answer("اتحاد پیدا نشد!")
            return
        
        members = session.query(AllianceMember).filter_by(alliance_id=a.id).all()
        
        text = (
            f"🏰 <b>{a.name}</b> [{a.tag or '-'}]\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"👥 اعضا: {len(members)}\n"
            f"💰 خزانه: {fmt(a.treasury)}\n"
            f"🏆 قدرت کل: {fmt(a.total_power)}\n"
            f"👑 رهبر: {get_leader_name(a, session)}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📝 {a.description or 'بدون توضیح'}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"👥 <b>اعضا:</b>\n"
        )
        
        for m in members:
            mu = session.query(User).filter_by(user_id=m.user_id).first()
            if mu and mu.country:
                rank_emoji = "👑" if m.rank == "leader" else "🎖️" if m.rank == "officer" else "👤"
                text += f"{rank_emoji} {mu.country.flag_emoji} {mu.country.name}\n"
        
        kb = {"inline_keyboard": [
            [{"text": "✉️ درخواست عضویت", "callback_data": f"all_join:{a.id}"}],
            [{"text": "🔙 بازگشت", "callback_data": "all_list"}],
        ]}
        
        await callback_query.message.reply(text, reply_markup=kb)
    finally:
        session.close()


async def leave_alliance(callback_query, user, Session):
    """خروج از اتحاد"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        membership = session.query(AllianceMember).filter_by(user_id=u.user_id).first()
        
        if not membership:
            await callback_query.answer("عضو اتحادی نیستی!")
            return
        
        # اگه رهبره، نمیتونه خارج بشه (باید اول منحل کنه)
        if membership.rank == "leader":
            await callback_query.answer("رهبر نمی‌تونه خارج بشه! اول اتحاد رو منحل کن.")
            return
        
        alliance_name = membership.alliance.name
        session.delete(membership)
        session.commit()
        
        await callback_query.answer(f"✅ از {alliance_name} خارج شدی!")
        await callback_query.message.reply(f"✅ از اتحاد <b>{alliance_name}</b> خارج شدی."
        )
    finally:
        session.close()


async def donate_to_treasury(callback_query, user, Session):
    """کمک به خزانه"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        membership = session.query(AllianceMember).filter_by(user_id=u.user_id).first()
        
        if not membership:
            await callback_query.answer("عضو اتحادی نیستی!")
            return
        
        amount = 10_000
        if u.cash < amount:
            await callback_query.answer(f"پول کمه! نیاز: {fmt(amount)}")
            return
        
        u.cash -= amount
        membership.alliance.treasury += amount
        u.xp += 50
        check_level_up(u)
        session.commit()
        
        await callback_query.answer(f"✅ {fmt(amount)} دلار کمک کردی!")
        await callback_query.message.reply(
            f"✅ <b>کمک موفق!</b>\n\n"
            f"💰 کمک: {fmt(amount)} دلار\n"
            f"🏦 خزانه اتحاد: {fmt(membership.alliance.treasury)}\n"
            f"⭐ +50 XP"
        )
    finally:
        session.close()
        