"""موتور اقتصاد"""

from datetime import datetime
from config import MAX_STORAGE_HOURS, XP_PER_LEVEL_BASE, XP_MULTIPLIER


def get_income(building_type, level, user_level=1, country=None):
    """درآمد با بونوس سطح کاربر و کشور"""
    bonus_country = (country.economy_bonus or 1.0) if country else 1.0
    # فرمول درآمد پویا: (1 + سطح کاربر * 0.05)
    level_bonus = 1.0 + (user_level * 0.05)
    
    multiplier = bonus_country * level_bonus
    
    return {
        "cash": (building_type.income_cash or 0) * level * multiplier,
        "gold": (building_type.income_gold or 0) * level * multiplier,
        "oil": (building_type.income_oil or 0) * level * multiplier,
        "uranium": (building_type.income_uranium or 0) * level * multiplier,
        "steel": (building_type.income_steel or 0) * level * multiplier,
        "food": (building_type.income_food or 0) * level * multiplier,
    }


def calc_pending(user_building, user_level=1, country=None):
    """محاسبه درآمد انباشته"""
    last = user_building.last_collected_at or datetime.utcnow()
    elapsed = (datetime.utcnow() - last).total_seconds()
    elapsed = min(elapsed, MAX_STORAGE_HOURS * 3600)
    hours = elapsed / 3600
    
    per_hour = get_income(user_building.building_type, user_building.level, user_level, country)
    
    return {
        "hours": hours,
        "cash": per_hour["cash"] * hours,
        "gold": per_hour["gold"] * hours,
        "oil": per_hour["oil"] * hours,
        "uranium": per_hour["uranium"] * hours,
        "steel": per_hour["steel"] * hours,
        "food": per_hour["food"] * hours,
    }


def upgrade_cost(building_type, level):
    """هزینه ارتقا"""
    base = building_type.build_cost or 500
    mult = building_type.upgrade_multiplier or 1.5
    return int(base * (mult ** level))


def total_income(user_buildings, user_level=1, country=None):
    """کل درآمد در ساعت"""
    t = {"cash": 0, "gold": 0, "oil": 0, "uranium": 0, "steel": 0, "food": 0}
    for ub in user_buildings:
        inc = get_income(ub.building_type, ub.level, user_level, country)
        for k in t:
            t[k] += inc.get(k, 0)
    return t


def calc_power_score(user_buildings):
    """محاسبه قدرت کاربر"""
    total = 0
    for ub in user_buildings:
        total += (ub.building_type.power_score or 0) * ub.level
    return total


def xp_needed_for_level(level):
    """XP مورد نیاز برای سطح بعدی"""
    return int(XP_PER_LEVEL_BASE * (XP_MULTIPLIER ** (level - 1)))


def check_level_up(user):
    levels_gained = 0
    while user.xp >= xp_needed_for_level(user.level):
        user.xp -= xp_needed_for_level(user.level)
        user.level += 1
        levels_gained += 1
    return levels_gained 
