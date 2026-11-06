"""تنگه‌های نفتی"""

from models import User, Strait, Country
from handlers.battle import calc_user_power
from models import User, Strait, Country

def fmt(n): return f"{n:,.0f}"


async def show_straits_menu(message, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        straits = session.query(Strait).all()
        
        text = (
            f"🌊 <b>تنگه‌های نفتی</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 پول: {fmt(u.cash)}\n"
            f"🎖️ سرباز: {u.soldiers:,}\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
        )
        
        rows = []
        for s in straits:
            status = "🔴 بسته" if s.is_closed else "🟢 باز"
            
            if s.controller_country:
                c = s.controller_country
                text += (
                    f"{s.name}\n"
                    f"   👑 صاحب: {c.flag_emoji} {c.name}\n"
                    f"   📊 وضعیت: {status}\n"
                    f"   💰 مالیات: {s.tax_rate * 100:.0f}%\n"
                    f"   🛢️ نفت/ساعت: {fmt(s.oil_output_per_hour)}\n\n"
                )
            else:
                text += (
                    f"{s.name}\n"
                    f"   🌐 بدون صاحب\n"
                    f"   🛢️ نفت/ساعت: {fmt(s.oil_output_per_hour)}\n\n"
                )
            
            rows.append([
                {"text": f"🌊 {s.name[:15]}", "callback_data": f"str_view:{s.id}"},
            ])
        
        rows.append([{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}])
        
        await message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


async def view_strait(callback_query, user, Session, strait_id):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        s = session.query(Strait).filter_by(id=strait_id).first()
        
        if not s:
            await callback_query.answer("تنگه پیدا نشد!")
            return
        
        text = f"🌊 <b>{s.name}</b>\n━━━━━━━━━━━━━━━━━\n"
        text += f"📝 {s.description}\n"
        text += f"🛢️ نفت/ساعت: {fmt(s.oil_output_per_hour)}\n"
        text += f"🛡️ سطح دفاع: {s.defense_level}\n"
        
        rows = []
        
        if s.controller_country_id == u.country_id:
            # خودت صاحبشی
            text += f"\n👑 <b>تو صاحب این تنگه هستی!</b>\n"
            text += f"💰 مالیات: {s.tax_rate * 100:.0f}%\n"
            text += f"📊 وضعیت: {'🔴 بسته' if s.is_closed else '🟢 باز'}\n"
            
            if s.is_closed:
                rows.append([{"text": "🔓 باز کردن تنگه", "callback_data": f"str_open:{s.id}"}])
            else:
                rows.append([{"text": "🔒 بستن تنگه", "callback_data": f"str_close:{s.id}"}])
            
            rows.append([{"text": "💰 افزایش مالیات +5%", "callback_data": f"str_tax:{s.id}"}])
            rows.append([{"text": "💵 کاهش مالیات -5%", "callback_data": f"str_untax:{s.id}"}])
            
        elif s.controller_country:
            # یکی دیگه صاحبشه
            c = s.controller_country
            text += f"\n👑 صاحب: {c.flag_emoji} {c.name}\n"
            text += f"💰 مالیات: {s.tax_rate * 100:.0f}%\n"
            text += f"📊 وضعیت: {'🔴 بسته' if s.is_closed else '🟢 باز'}\n\n"
            text += f"⚔️ برای تصرف، حمله کن:\n"
            rows.append([{"text": "⚔️ حمله به تنگه", "callback_data": f"str_attack:{s.id}"}])
        else:
            # بدون صاحب
            text += f"\n🌐 <b>این تنگه بدون صاحبه!</b>\n\n"
            text += f"⚔️ با ۱۰,۰۰۰ سرباز می‌تونی تصرفش کنی\n"
            rows.append([{"text": "🎯 تصرف تنگه", "callback_data": f"str_take:{s.id}"}])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_strait"}])
        
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


async def take_strait(callback_query, user, Session, strait_id):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        s = session.query(Strait).filter_by(id=strait_id).first()
        
        if not s:
            await callback_query.answer("تنگه پیدا نشد!")
            return
        
        if s.controller_country_id:
            await callback_query.answer("این تنگه صاحب داره! باید حمله کنی.")
            return
        
        # نیاز به ۱۰,۰۰۰ سرباز
        if u.soldiers < 10_000:
            await callback_query.answer(f"نیاز به ۱۰,۰۰۰ سرباز! (شما: {u.soldiers:,})")
            return
        
        u.soldiers -= 10_000
        s.controller_country_id = u.country_id
        session.commit()
        
        await callback_query.answer(f"🎉 {s.name} تصرف شد!")
        await callback_query.message.reply(
            f"🎉 <b>پیروزی!</b>\n\n"
            f"🌊 {s.name} تصرف شد!\n"
            f"💀 تلفات: ۱۰,۰۰۰ سرباز\n"
            f"🛢️ درآمد: {fmt(s.oil_output_per_hour)} بشکه/ساعت\n"
            f"💰 حالا می‌تونی مالیات بذاری"
        )
    finally:
        session.close()


async def close_strait(callback_query, user, Session, strait_id):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        s = session.query(Strait).filter_by(id=strait_id).first()
        
        if s.controller_country_id != u.country_id:
            await callback_query.answer("تو صاحب این تنگه نیستی!")
            return
        
        s.is_closed = True
        session.commit()
        
        await callback_query.answer(f"🔒 {s.name} بسته شد!")
        await callback_query.message.reply(
            f"🔒 <b>بحران جهانی!</b>\n\n"
            f"🌊 {s.name} بسته شد!\n"
            f"⚠️ قیمت نفت جهانی بالا میره!\n"
            f"💰 درآمد تو: {fmt(s.oil_output_per_hour * 2)} بشکه/ساعت (۲ برابر!)"
        )
    finally:
        session.close()


async def open_strait(callback_query, user, Session, strait_id):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        s = session.query(Strait).filter_by(id=strait_id).first()
        
        if s.controller_country_id != u.country_id:
            await callback_query.answer("تو صاحب این تنگه نیستی!")
            return
        
        s.is_closed = False
        session.commit()
        
        await callback_query.answer(f"🔓 {s.name} باز شد!")
        await callback_query.message.reply(
            f"🔓 <b>تنگه باز شد!</b>\n\n"
            f"🌊 {s.name}\n"
            f"💵 درآمد عادی برقرار شد."
        )
    finally:
        session.close()


async def change_tax(callback_query, user, Session, strait_id, increase=True):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        s = session.query(Strait).filter_by(id=strait_id).first()
        
        if s.controller_country_id != u.country_id:
            await callback_query.answer("تو صاحب این تنگه نیستی!")
            return
        
        if increase:
            if s.tax_rate >= 0.5:
                await callback_query.answer("حداکثر مالیات ۵۰٪ هست!")
                return
            s.tax_rate = min(0.5, s.tax_rate + 0.05)
        else:
            s.tax_rate = max(0, s.tax_rate - 0.05)
        
        session.commit()
        await callback_query.answer(f"💰 مالیات: {s.tax_rate * 100:.0f}%")
    finally:
        session.close()


async def attack_strait(callback_query, user, Session, strait_id):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        s = session.query(Strait).filter_by(id=strait_id).first()
        
        if s.controller_country_id == u.country_id:
            await callback_query.answer("این تنگه مال خودته!")
            return
        
        # قدرت
        from handlers.battle import calc_user_power
        my_power = calc_user_power(u, session)
        
        # دفاع تنگه
        strait_defense = s.defense_level * 2000
        
        if my_power["attack"] <= strait_defense:
            await callback_query.answer(f"قدرت کافی نداری! نیاز: {fmt(strait_defense)}")
            return
        
        # پیروزی
        old_owner_id = s.controller_country_id
        s.controller_country_id = u.country_id
        s.is_closed = False
        s.tax_rate = 0
        
        lost_soldiers = int(u.soldiers * 0.15)
        u.soldiers -= lost_soldiers
        u.reputation -= 10
        
        session.commit()
        
        await callback_query.answer("🎉 تنگه تصرف شد!")
        await callback_query.message.reply(
            f"🎉 <b>پیروزی!</b>\n\n"
            f"🌊 {s.name} تصرف شد!\n"
            f"💀 تلفات: {lost_soldiers:,} سرباز\n"
            f"🏆 اعتبار: -10\n"
            f"💰 حالا صاحب این تنگه‌ای!"
        )
    finally:
        session.close()
    

async def show_attack_straits(callback_query, user, Session):
    """نمایش تنگه‌ها برای حمله (از منوی نبرد)"""
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        straits = session.query(Strait).filter(Strait.controller_country_id != None).all()
        
        text = (
            f"🌊 <b>حمله به تنگه‌ها</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⚔️ قدرت حمله شما: {fmt(calc_user_power(u, session)['attack'])}\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"⚠️ برای تصرف تنگه، باید قدرت حمله‌ات از دفاع تنگه بیشتر باشه.\n\n"
        )
        
        rows = []
        if not straits:
            text += "🌐 هنوز هیچ تنگه‌ای توسط بازیکنی تصرف نشده!\n"
            text += "می‌تونی از منوی 🌊 تنگه‌ها، تنگه‌های آزاد رو تصرف کنی."
        else:
            for s in straits:
                c = s.controller_country
                text += f"🌊 <b>{s.name}</b>\n"
                text += f"   👑 صاحب: {c.flag_emoji} {c.name}\n"
                text += f"   🛡️ دفاع: {fmt(s.defense_level * 2000)}\n"
                text += f"   💰 مالیات: {s.tax_rate * 100:.0f}%\n\n"
                rows.append([
                    {"text": f"⚔️ حمله به {s.name}", "callback_data": f"str_attack:{s.id}"}
                ])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_battle"}])
        
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()
