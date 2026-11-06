"""ربات جنگ جهانی قرن ۲۱"""

from balethon import Client
from balethon.conditions import command, regex

import config
from models import init_db, User, Country
from handlers.buildings import show_buildings_menu, show_category, show_my, create_building, upgrade, collect, collect_all
from handlers.dashboard import show_dashboard
from handlers.military import show_military_menu, show_military_category, show_my_army, buy_unit, show_foreign_countries, show_foreign_units, buy_foreign_unit
from handlers.battle import show_attack_menu, show_attack_targets, do_attack, show_battle_history
from handlers.market import (
    show_market_menu, show_buy_options, do_buy,
    show_sell_options, do_sell, show_portfolio
)
from handlers.straits import (
    show_straits_menu, view_strait, take_strait,
    close_strait, open_strait, change_tax, attack_strait
)
from handlers.leaderboard import show_leaderboard, show_lb_military, show_lb_level
from handlers.research import show_research_menu, do_research
from handlers.daily import show_daily_menu, claim_daily, show_missions 
import asyncio
from engines.market import update_market_prices
from models import Strait, UserUnit
from handlers.spy import show_spy_menu, show_spy_targets, do_spy
from handlers.alliance import (
    show_alliance_menu, show_alliance_list, show_alliance_detail,
    create_alliance_start, leave_alliance, donate_to_treasury,
)
from handlers.diplomacy import show_diplomacy_menu, show_countries_diplomacy
from models import Alliance, AllianceMember 
from engines.economy import check_level_up
from handlers.achievements import show_achievements, check_achievements
from handlers.events import trigger_random_event
from handlers.straits import show_attack_straits

bot = Client(config.BOT_TOKEN)
Session = init_db(config.DATABASE_URL)


@bot.on_message(command("start"))
async def start_handler(message):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=message.author.id).first()
        if not user:
            user = User(user_id=message.author.id, username=getattr(message.author, "username", None), full_name=getattr(message.author, "first_name", "بازیکن"))
            session.add(user)
            session.commit()
        if not user.country_id: await show_countries(message)
        else: await show_dashboard(message, user, Session)
    finally: session.close()


async def show_countries(message):
    session = Session()
    try:
        countries = session.query(Country).order_by(Country.region, Country.name).all()
        text = f"🌍 به <b>{config.GAME_NAME}</b> خوش اومدی!\n\nکشورت رو انتخاب کن:\n\n"
        regions = {}
        for c in countries: regions.setdefault(c.region, []).append(c)
        rows = []
        for region, rc in regions.items():
            rows.append([{"text": f"━━━ {region} ━━━", "callback_data": "noop"}])
            row = []
            for i, c in enumerate(rc, 1):
                row.append({"text": f"{c.flag_emoji} {c.name}", "callback_data": f"pick:{c.id}"})
                if i % 2 == 0: rows.append(row); row = []
            if row: rows.append(row)
        await message.reply(text, reply_markup={"inline_keyboard": rows})
    finally: session.close()


@bot.on_callback_query(regex(r"^noop$"))
async def noop_handler(callback_query): 
    await callback_query.answer("....")


@bot.on_callback_query(regex(r"^pick:(\d+)$"))
async def pick_handler(callback_query):
    session = Session()
    try:
        cid = int(callback_query.data.split(":")[1])
        country = session.query(Country).filter_by(id=cid).first()
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if not country or not user: return await callback_query.answer("خطا!")
        if session.query(User).filter(User.country_id == cid, User.user_id != user.user_id).first(): return await callback_query.answer("قبلاً گرفته شده!")
        user.country_id = cid; user.cash = country.initial_cash; user.soldiers = country.initial_soldiers
        user.population = country.initial_population; user.oil_barrels = country.oil_reserves * 0.1
        session.commit()
        await callback_query.answer(f"🎉 {country.name}!")
        await callback_query.message.reply(f"{country.flag_emoji} تبریک! تو رهبر <b>{country.name}</b> هستی!\n💰 خزانه: {country.initial_cash:,.0f}\n\n/dashboard رو بزن.")
    finally: session.close()


@bot.on_message(command("dashboard"))
async def dashboard_handler(message):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=message.author.id).first()
        if not user or not user.country_id: return await message.reply("اول /start")
        await show_dashboard(message, user, Session)
    finally: session.close()


@bot.on_message(command("help"))
async def help_handler(message):
    await message.reply(f"📖 <b>راهنمای {config.GAME_NAME}</b>\n\n/start - شروع\n/dashboard - داشبورد\n/help - راهنما")


# =====================================================
# داشبورد و ساختمان‌ها
# =====================================================
@bot.on_callback_query(regex(r"^menu_dashboard$"))
async def menu_dashboard(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_dashboard(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^menu_build$"))
async def menu_build(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_buildings_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^bcat:(\w+)$"))
async def bcat_handler(callback_query):
    session = Session()
    try:
        cat = callback_query.data.split(":")[1]
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_category(callback_query, user, Session, cat)
    finally: session.close()


@bot.on_callback_query(regex(r"^bmy$"))
async def bmy_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_my(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^bcreate:(\d+)$"))
async def bcreate_handler(callback_query):
    session = Session()
    try:
        bid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await create_building(callback_query, user, Session, bid)
    finally: session.close()


@bot.on_callback_query(regex(r"^bup:(\d+)$"))
async def bup_handler(callback_query):
    session = Session()
    try:
        ubid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await upgrade(callback_query, user, Session, ubid)
    finally: session.close()


@bot.on_callback_query(regex(r"^bcol:(\d+)$"))
async def bcol_handler(callback_query):
    session = Session()
    try:
        ubid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await collect(callback_query, user, Session, ubid)
    finally: session.close()


@bot.on_callback_query(regex(r"^bcoll_all$"))
async def bcoll_all_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await collect_all(callback_query, user, Session)
    finally: session.close()


# =====================================================
# نظامی
# =====================================================
@bot.on_callback_query(regex(r"^menu_army$"))
async def menu_army(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_military_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^mcat:(\w+)$"))
async def mcat_handler(callback_query):
    session = Session()
    try:
        cat = callback_query.data.split(":")[1]
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_military_category(callback_query, user, Session, cat)
    finally: session.close()


@bot.on_callback_query(regex(r"^mymy$"))
async def mymy_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_my_army(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^mbuy:(\d+):(\d+)$"))
async def mbuy_handler(callback_query):
    session = Session()
    try:
        parts = callback_query.data.split(":")
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await buy_unit(callback_query, user, Session, int(parts[1]), int(parts[2]))
    finally: session.close()


@bot.on_callback_query(regex(r"^mforeign$"))
async def mforeign_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_foreign_countries(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^mfc:(\d+)$"))
async def mfc_handler(callback_query):
    session = Session()
    try:
        cid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_foreign_units(callback_query, user, Session, cid)
    finally: session.close()


@bot.on_callback_query(regex(r"^mfbuy:(\d+):(\d+)$"))
async def mfbuy_handler(callback_query):
    session = Session()
    try:
        parts = callback_query.data.split(":")
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await buy_foreign_unit(callback_query, user, Session, int(parts[1]), int(parts[2]))
    finally: session.close()


# =====================================================
# حمله
# =====================================================
@bot.on_callback_query(regex(r"^menu_battle$"))
async def menu_battle(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_attack_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^atk_countries$"))
async def atk_countries_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_attack_targets(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^atk_go:(\d+)$"))
async def atk_go_handler(callback_query):
    session = Session()
    try:
        target_id = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await do_attack(callback_query, user, Session, target_id)
    finally: session.close()


@bot.on_callback_query(regex(r"^atk_history$"))
async def atk_history_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_battle_history(callback_query, user, Session)
    finally: session.close()

@bot.on_callback_query(regex(r"^atk_straits$"))
async def atk_straits_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if not user:
            await callback_query.answer("اول /start")
            return
        await show_attack_straits(callback_query, user, Session)
    finally:
        session.close()
# =====================================================
# بازار
# =====================================================
@bot.on_callback_query(regex(r"^menu_market$"))
async def menu_market(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_market_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^mkt_buy:(\d+)$"))
async def mkt_buy_handler(callback_query):
    session = Session()
    try:
        cid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_buy_options(callback_query, user, Session, cid)
    finally: session.close()


@bot.on_callback_query(regex(r"^mkt_dobuy:(\d+):(\d+)$"))
async def mkt_dobuy_handler(callback_query):
    session = Session()
    try:
        parts = callback_query.data.split(":")
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await do_buy(callback_query, user, Session, int(parts[1]), int(parts[2]))
    finally: session.close()


@bot.on_callback_query(regex(r"^mkt_sell:(\d+)$"))
async def mkt_sell_handler(callback_query):
    session = Session()
    try:
        cid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_sell_options(callback_query, user, Session, cid)
    finally: session.close()


@bot.on_callback_query(regex(r"^mkt_dosell:(\d+):(\d+)$"))
async def mkt_dosell_handler(callback_query):
    session = Session()
    try:
        parts = callback_query.data.split(":")
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await do_sell(callback_query, user, Session, int(parts[1]), int(parts[2]))
    finally: session.close()


@bot.on_callback_query(regex(r"^mkt_portfolio$"))
async def mkt_portfolio_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_portfolio(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^mkt_update$"))
async def mkt_update_handler(callback_query):
    await callback_query.answer("📊 قیمت‌ها هر ۵ دقیقه خودکار بروزرسانی می‌شن!")


# =====================================================
# تنگه‌ها
# =====================================================
@bot.on_callback_query(regex(r"^menu_strait$"))
async def menu_strait(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_straits_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^str_view:(\d+)$"))
async def str_view_handler(callback_query):
    session = Session()
    try:
        sid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await view_strait(callback_query, user, Session, sid)
    finally: session.close()


@bot.on_callback_query(regex(r"^str_take:(\d+)$"))
async def str_take_handler(callback_query):
    session = Session()
    try:
        sid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await take_strait(callback_query, user, Session, sid)
    finally: session.close()


@bot.on_callback_query(regex(r"^str_close:(\d+)$"))
async def str_close_handler(callback_query):
    session = Session()
    try:
        sid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await close_strait(callback_query, user, Session, sid)
    finally: session.close()


@bot.on_callback_query(regex(r"^str_open:(\d+)$"))
async def str_open_handler(callback_query):
    session = Session()
    try:
        sid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await open_strait(callback_query, user, Session, sid)
    finally: session.close()


@bot.on_callback_query(regex(r"^str_tax:(\d+)$"))
async def str_tax_handler(callback_query):
    session = Session()
    try:
        sid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await change_tax(callback_query, user, Session, sid, True)
    finally: session.close()


@bot.on_callback_query(regex(r"^str_untax:(\d+)$"))
async def str_untax_handler(callback_query):
    session = Session()
    try:
        sid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await change_tax(callback_query, user, Session, sid, False)
    finally: session.close()


@bot.on_callback_query(regex(r"^str_attack:(\d+)$"))
async def str_attack_handler(callback_query):
    session = Session()
    try:
        sid = int(callback_query.data.split(":")[1])
        user =session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await attack_strait(callback_query, user, Session, sid)
    finally: session.close()


# =====================================================
# لیدربورد
# =====================================================
@bot.on_callback_query(regex(r"^menu_lb$"))
async def menu_lb(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_leaderboard(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^lb_military$"))
async def lb_military_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_lb_military(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^lb_level$"))
async def lb_level_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_lb_level(callback_query, user, Session)
    finally: session.close()


# =====================================================
# تحقیقات
# =====================================================
@bot.on_callback_query(regex(r"^menu_research$"))
async def menu_research(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_research_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^res_do:(\d+)$"))
async def res_do_handler(callback_query):
    session = Session()
    try:
        rid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await do_research(callback_query, user, Session, rid)
    finally: session.close()

# =====================================================
# جوایز روزانه
# =====================================================
@bot.on_callback_query(regex(r"^menu_daily$"))
async def menu_daily(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_daily_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^daily_claim$"))
async def daily_claim_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await claim_daily(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^daily_missions$"))
async def daily_missions_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_missions(callback_query, user, Session)
    finally: session.close()
    

# =========================================================
# تسک پس‌زمینه: نوسان بازار و درآمد تنگه‌ها
# =========================================================
async def background_tasks():
    while True:
        try:
            session = Session()
            
            # ۱. بروزرسانی بازار
            update_market_prices(session)
            
            # ۲. درآمد خودکار تنگه‌ها
            straits = session.query(Strait).filter(Strait.controller_country_id != None, Strait.is_closed == False).all()
            for s in straits:
                # پیدا کردن کاربر صاحب این تنگه
                owner = session.query(User).filter_by(country_id=s.controller_country_id).first()
                if owner:
                    # اضافه کردن نفت به کاربر
                    owner.oil_barrels += s.oil_output_per_hour
                    
            session.commit()
            session.close()
            print("⏰ تسک پس‌زمینه اجرا شد (بازار + تنگه‌ها)")
            
        except Exception as e:
            print(f"خطا در پس‌زمینه: {e}")
            
        # هر ۵ دقیقه یکبار اجرا میشه
        await asyncio.sleep(300)
        
# =====================================================
# جاسوسی
# =====================================================
@bot.on_callback_query(regex(r"^menu_spy$"))
async def menu_spy(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_spy_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^spy_start:(\w+):(\d+)$"))
async def spy_start_handler(callback_query):
    session = Session()
    try:
        parts = callback_query.data.split(":")
        mission_type = parts[1]
        cost = int(parts[2])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_spy_targets(callback_query, user, Session, mission_type, cost)
    finally: session.close()


@bot.on_callback_query(regex(r"^spy_go:(\w+):(\d+):(\d+)$"))
async def spy_go_handler(callback_query):
    session = Session()
    try:
        parts = callback_query.data.split(":")
        mission_type = parts[1]
        target_id = int(parts[2])
        cost = int(parts[3])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await do_spy(callback_query, user, Session, mission_type, target_id, cost)
    finally: session.close()


# =====================================================
# اتحاد
# =====================================================
@bot.on_callback_query(regex(r"^menu_alliance$"))
async def menu_alliance(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_alliance_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^all_list$"))
async def all_list_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_alliance_list(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^all_create$"))
async def all_create_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await create_alliance_start(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^all_view:(\d+)$"))
async def all_view_handler(callback_query):
    session = Session()
    try:
        aid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_alliance_detail(callback_query, user, Session, aid)
    finally: session.close()


@bot.on_callback_query(regex(r"^all_leave$"))
async def all_leave_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await leave_alliance(callback_query, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^all_donate$"))
async def all_donate_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await donate_to_treasury(callback_query, user, Session)
    finally: session.close()


# =====================================================
# دیپلماسی
# =====================================================
@bot.on_callback_query(regex(r"^menu_diplomacy$"))
async def menu_diplomacy(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_diplomacy_menu(callback_query.message, user, Session)
    finally: session.close()


@bot.on_callback_query(regex(r"^dip_countries$"))
async def dip_countries_handler(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_countries_diplomacy(callback_query, user, Session)
    finally: session.close()

@bot.on_callback_query(regex(r"^dip_view:(\d+)$"))
async def dip_view_handler(callback_query):
    session = Session()
    try:
        cid = int(callback_query.data.split(":")[1])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        from handlers.diplomacy import show_country_actions
        if user: await show_country_actions(callback_query, user, Session, cid)
    finally: session.close()


@bot.on_callback_query(regex(r"^dip_pact:(\w+):(\d+)$"))
async def dip_pact_handler(callback_query):
    session = Session()
    try:
        parts = callback_query.data.split(":")
        pact_type = parts[1]
        target_id = int(parts[2])
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        from handlers.diplomacy import make_pact
        if user: await make_pact(callback_query, user, Session, pact_type, target_id)
    finally: session.close()

# =====================================================
# ساخت اتحاد (دستور متنی)
# =====================================================
@bot.on_message(regex(r"^/create_alliance\s+(.+?)\s*\|\s*(.+)$"))
async def create_alliance_cmd(message):
    session = Session()
    try:
        text = message.text
        parts = text.split("|")
        if len(parts) != 2:
            await message.reply("فرمت اشتباه! مثال:\n<code>/create_alliance محور شرق | ME</code>")
            return
        
        name = parts[0].replace("/create_alliance", "").strip()
        tag = parts[1].strip()
        
        u = session.query(User).filter_by(user_id=message.author.id).first()
        if not u or not u.country_id:
            await message.reply("اول /start")
            return
        
        if u.level < 5:
            await message.reply("نیاز به سطح ۵!")
            return
        
        if u.cash < 50_000:
            await message.reply(f"نیاز به ۵۰,۰۰۰ دلار! (شما: {fmt(u.cash)})")
            return
        
        if session.query(Alliance).filter_by(name=name).first():
            await message.reply("این اسم قبلاً استفاده شده!")
            return
        
        if session.query(AllianceMember).filter_by(user_id=u.user_id).first():
            await message.reply("قبلاً عضو اتحادی هستی!")
            return
        
        u.cash -= 50_000
        
        a = Alliance(name=name, tag=tag, leader_id=u.user_id)
        session.add(a)
        session.flush()
        
        session.add(AllianceMember(
            alliance_id=a.id, user_id=u.user_id, rank="leader"
        ))
        
        u.xp += 200
        check_level_up(u)
        session.commit()
        
        await message.reply(
            f"🎉 <b>اتحاد ساخته شد!</b>\n\n"
            f"🏰 نام: <b>{name}</b>\n"
            f"🏷️ TAG: [{tag}]\n"
            f"👑 رهبر: {u.country.flag_emoji} {u.country.name}\n"
            f"💰 هزینه: ۵۰,۰۰۰ دلار\n"
            f"⭐ +200 XP"
        )
    finally:
        session.close()
        
# =====================================================
# دستاوردها
# =====================================================
@bot.on_callback_query(regex(r"^menu_achieve$"))
async def menu_achieve(callback_query):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=callback_query.author.id).first()
        if user: await show_achievements(callback_query.message, user, Session)
    finally: session.close()


@bot.on_message(command("achievements"))
async def achievements_cmd(message):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=message.author.id).first()
        if not user or not user.country_id:
            await message.reply("اول /start")
            return
        await show_achievements(message, user, Session)
    finally: session.close()        

# =====================================================
# اجرا
# =====================================================
if __name__ == "__main__":
    print(f"🚀 {config.GAME_NAME} v{config.GAME_VERSION}")
    print("━" * 40)
    print("در حال اجرا...")
    print("━" * 40)
    
    # ✅ اجرای تسک پس‌زمینه
    loop = asyncio.get_event_loop()
    loop.create_task(background_tasks())
    
    bot.run() 
    