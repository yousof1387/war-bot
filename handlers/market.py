"""بازار و بورس"""

from datetime import datetime
from models import User, Commodity, StockHolding
from engines.economy import check_level_up


def fmt(n): return f"{n:,.0f}"


async def show_market_menu(message, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        commodities = session.query(Commodity).all()
        
        text = (
            f"💰 <b>بازار جهانی</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 پول شما: {fmt(u.cash)}\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
        )
        
        rows = []
        for c in commodities:
            text += (
                f"{c.emoji} <b>{c.name}</b>\n"
                f"   💵 قیمت: {fmt(c.current_price)}\n"
                f"   📊 نوسان: ±{c.volatility * 100:.1f}%\n\n"
            )
            rows.append([
                {"text": f"🛒 خرید {c.emoji}", "callback_data": f"mkt_buy:{c.id}"},
                {"text": f"💸 فروش {c.emoji}", "callback_data": f"mkt_sell:{c.id}"},
            ])
        
        rows.append([{"text": "📊 سبد من", "callback_data": "mkt_portfolio"}])
        rows.append([{"text": "🔄 بروزرسانی قیمت‌ها", "callback_data": "mkt_update"}])
        rows.append([{"text": "🔙 داشبورد", "callback_data": "menu_dashboard"}])
        
        await message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


async def show_buy_options(callback_query, user, Session, commodity_id):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        c = session.query(Commodity).filter_by(id=commodity_id).first()
        
        if not c:
            await callback_query.answer("کالا پیدا نشد!")
            return
        
        text = (
            f"{c.emoji} <b>خرید {c.name}</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"💵 پول شما: {fmt(u.cash)}\n"
            f"📊 قیمت فعلی: {fmt(c.current_price)} برای ۱ واحد\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"چه تعداد می‌خری؟"
        )
        
        rows = []
        for qty in [1, 10, 50, 100]:
            total = c.current_price * qty
            rows.append([{
                "text": f"خرید {qty} عدد = {fmt(total)} 💵",
                "callback_data": f"mkt_dobuy:{c.id}:{qty}"
            }])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_market"}])
        
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


async def do_buy(callback_query, user, Session, commodity_id, qty):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        c = session.query(Commodity).filter_by(id=commodity_id).first()
        
        if not c:
            await callback_query.answer("کالا پیدا نشد!")
            return
        
        total_cost = c.current_price * qty
        
        if u.cash < total_cost:
            await callback_query.answer(f"پول کمه! نیاز: {fmt(total_cost)}")
            return
        
        # کم کردن پول
        u.cash -= total_cost
        
        # ثبت خرید در پروفایل کالا
        holding = session.query(StockHolding).filter_by(
            user_id=u.user_id, commodity_id=c.id
        ).first()
        
        if holding:
            # محاسبه میانگین قیمت خرید
            total_old = holding.quantity * holding.avg_buy_price
            total_new = qty * c.current_price
            total_qty = holding.quantity + qty
            
            holding.avg_buy_price = (total_old + total_new) / total_qty
            holding.quantity = total_qty
        else:
            holding = StockHolding(
                user_id=u.user_id, commodity_id=c.id,
                quantity=qty, avg_buy_price=c.current_price
            )
            session.add(holding)
        
        u.xp += int(qty * 2)
        check_level_up(u)
        session.commit()
        
        await callback_query.answer(f"✅ {qty} واحد خریده شد!")
        await callback_query.message.reply(
            f"✅ <b>خرید موفق!</b>\n\n"
            f"{c.emoji} {c.name} × {qty}\n"
            f"💵 قیمت واحد: {fmt(c.current_price)}\n"
            f"💰 هزینه: {fmt(total_cost)}\n"
            f"💵 باقی: {fmt(u.cash)}"
        )
    finally:
        session.close()


async def show_sell_options(callback_query, user, Session, commodity_id):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        c = session.query(Commodity).filter_by(id=commodity_id).first()
        
        if not c:
            await callback_query.answer("کالا پیدا نشد!")
            return
        
        holding = session.query(StockHolding).filter_by(
            user_id=u.user_id, commodity_id=c.id
        ).first()
        
        if not holding or holding.quantity <= 0:
            await callback_query.answer("شما چیزی از این کالا ندارید!")
            return
        
        text = (
            f"{c.emoji} <b>فروش {c.name}</b>\n"
            f"━━━━━━━━━━━━━━━━━\n"
            f"📦 شما دارید: {holding.quantity} واحد\n"
            f"💰 قیمت خرید: {fmt(holding.avg_buy_price)}\n"
            f"📊 قیمت فعلی: {fmt(c.current_price)}\n"
            f"━━━━━━━━━━━━━━━━━\n\n"
            f"چه تعداد می‌فروشی؟"
        )
        
        rows = []
        for qty in [1, 10, 50]:
            if qty <= holding.quantity:
                total = c.current_price * qty
                rows.append([{
                    "text": f"فروش {qty} عدد = {fmt(total)} 💵",
                    "callback_data": f"mkt_dosell:{c.id}:{qty}"
                }])
        
        if holding.quantity >= 1:
            total = c.current_price * holding.quantity
            rows.append([{
                "text": f"فروش همه = {fmt(total)} 💵",
                "callback_data": f"mkt_dosell:{c.id}:{int(holding.quantity)}"
            }])
        
        rows.append([{"text": "🔙 بازگشت", "callback_data": "menu_market"}])
        
        await callback_query.message.reply(text, reply_markup={"inline_keyboard": rows})
    finally:
        session.close()


async def do_sell(callback_query, user, Session, commodity_id, qty):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        c = session.query(Commodity).filter_by(id=commodity_id).first()
        holding = session.query(StockHolding).filter_by(
            user_id=u.user_id, commodity_id=c.id
        ).first()
        
        if not holding or holding.quantity < qty:
            await callback_query.answer("موجودی کافی نداری!")
            return
        
        total_gain = c.current_price * qty
        profit = (c.current_price - holding.avg_buy_price) * qty
        
        u.cash += total_gain
        holding.quantity -= qty
        
        if holding.quantity <= 0:
            session.delete(holding)
        
        u.xp += int(qty * 3)
        check_level_up(u)
        session.commit()
        
        profit_emoji = "📈" if profit >= 0 else "📉"
        
        await callback_query.answer(f"✅ {qty} واحد فروخته شد!")
        await callback_query.message.reply(
            f"✅ <b>فروش موفق!</b>\n\n"
            f"{c.emoji} {c.name} × {qty}\n"
            f"💵 قیمت فروش: {fmt(c.current_price)}\n"
            f"💰 دریافتی: {fmt(total_gain)}\n"
            f"{profit_emoji} سود/ضرر: {profit:+,.0f}\n"
            f"💵 موجودی: {fmt(u.cash)}"
        )
    finally:
        session.close()


async def show_portfolio(callback_query, user, Session):
    session = Session()
    try:
        u = session.query(User).filter_by(user_id=user.user_id).first()
        holdings = session.query(StockHolding).filter_by(user_id=u.user_id).all()
        
        if not holdings:
            await callback_query.message.reply(
                "📊 <b>سبد شما</b>\n\n"
                "هنوز چیزی نخریدی!"
            )
            return
        
        text = f"📊 <b>سبد سهام شما</b>\n━━━━━━━━━━━━━━━━━\n"
        total_value = 0
        
        for h in holdings:
            c = h.commodity
            current_value = c.current_price * h.quantity
            profit = (c.current_price - h.avg_buy_price) * h.quantity
            total_value += current_value
            
            text += (
                f"\n{c.emoji} <b>{c.name}</b>\n"
                f"   📦 {h.quantity} واحد\n"
                f"   💰 خرید: {fmt(h.avg_buy_price)}\n"
                f"   📊 فعلی: {fmt(c.current_price)}\n"
                f"   {'📈' if profit >= 0 else '📉'} سود: {profit:+,.0f}\n"
            )
        
        text += f"\n━━━━━━━━━━━━━━━━━\n💰 ارزش کل: {fmt(total_value)}\n💵 پول: {fmt(u.cash)}"
        
        await callback_query.message.reply(text, reply_markup={
            "inline_keyboard": [[{"text": "🔙 بازگشت", "callback_data": "menu_market"}]]
        })
    finally:
        session.close()
        