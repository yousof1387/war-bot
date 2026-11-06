"""مدل‌های دیتابیس"""

from sqlalchemy import (
    create_engine, Column, Integer, String, Float, BigInteger,
    ForeignKey, DateTime, Text, Boolean
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    user_id = Column(BigInteger, primary_key=True)
    username = Column(String(64), nullable=True)
    full_name = Column(String(128), nullable=True)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    
    cash = Column(Float, default=100_000.0)
    gold = Column(Float, default=0.0)
    oil_barrels = Column(Float, default=0.0)
    uranium = Column(Float, default=0.0)
    steel = Column(Float, default=0.0)
    food = Column(Float, default=1000.0)
    
    population = Column(BigInteger, default=10_000_000)
    soldiers = Column(BigInteger, default=100_000)
    workers = Column(BigInteger, default=500_000)
    
    level = Column(Integer, default=1)
    xp = Column(Integer, default=0)
    power_score = Column(Float, default=0.0)
    reputation = Column(Integer, default=100)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, default=datetime.utcnow)

    country = relationship("Country", back_populates="owner", foreign_keys=[country_id])
    alliance_membership = relationship("AllianceMember", foreign_keys="AllianceMember.user_id", uselist=False, cascade="all, delete-orphan")
    buildings = relationship("UserBuilding", back_populates="user", cascade="all, delete-orphan")
    units = relationship("UserUnit", back_populates="user", cascade="all, delete-orphan")
    stocks = relationship("StockHolding", back_populates="user", cascade="all, delete-orphan")
    achievements = relationship("UserAchievement", cascade="all, delete-orphan")
    # جوایز روزانه
    last_daily_reward = Column(DateTime, nullable=True)
    daily_streak = Column(Integer, default=0)

class Country(Base):
    __tablename__ = "countries"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    flag_emoji = Column(String(8), nullable=True)
    capital = Column(String(64), nullable=True)
    region = Column(String(64), nullable=True)
    description = Column(Text, nullable=True)
    
    initial_soldiers = Column(BigInteger, default=100_000)
    initial_population = Column(BigInteger, default=10_000_000)
    initial_cash = Column(Float, default=100_000.0)
    
    attack_bonus = Column(Float, default=1.0)
    defense_bonus = Column(Float, default=1.0)
    economy_bonus = Column(Float, default=1.0)
    
    oil_reserves = Column(Float, default=0.0)
    gold_reserves = Column(Float, default=0.0)
    uranium_reserves = Column(Float, default=0.0)

    owner = relationship("User", back_populates="country", uselist=False, foreign_keys="User.country_id")
    controlled_straits = relationship("Strait", back_populates="controller_country")


class MilitaryUnitType(Base):
    __tablename__ = "military_unit_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    category = Column(String(32), nullable=False)
    country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    
    weapon_type = Column(String(64), nullable=True)
    range_km = Column(Integer, nullable=True)
    emoji = Column(String(8), nullable=True)
    
    attack_power = Column(Float, default=10.0)
    defense_power = Column(Float, default=10.0)
    
    cost = Column(Float, default=100.0)
    upkeep_cost = Column(Float, default=1.0)
    required_level = Column(Integer, default=1)
    
    country = relationship("Country")


class UserUnit(Base):
    __tablename__ = "user_units"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    unit_type_id = Column(Integer, ForeignKey("military_unit_types.id"), nullable=False)
    quantity = Column(Integer, default=0)

    user = relationship("User", back_populates="units")
    unit_type = relationship("MilitaryUnitType")


class BuildingType(Base):
    __tablename__ = "building_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), nullable=False)
    category = Column(String(32), default="economic")
    emoji = Column(String(8), nullable=True)
    description = Column(Text,nullable=True)
    
    build_cost = Column(Float, default=500.0)
    upgrade_multiplier = Column(Float, default=1.5)
    required_level = Column(Integer, default=1)
    
    income_cash = Column(Float, default=0.0)
    income_gold = Column(Float, default=0.0)
    income_oil = Column(Float, default=0.0)
    income_uranium = Column(Float, default=0.0)
    income_steel = Column(Float, default=0.0)
    income_food = Column(Float, default=0.0)
    
    power_score = Column(Float, default=0.0)


class UserBuilding(Base):
    __tablename__ = "user_buildings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    building_type_id = Column(Integer, ForeignKey("building_types.id"), nullable=False)
    level = Column(Integer, default=1)
    built_at = Column(DateTime, default=datetime.utcnow)
    last_collected_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="buildings")
    building_type = relationship("BuildingType")


# =========================================================
# ✅ بخش بازار (بورس کالا)
# =========================================================
class Commodity(Base):
    __tablename__ = "commodities"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    emoji = Column(String(8), nullable=True)
    
    current_price = Column(Float, default=100.0)
    base_price = Column(Float, default=100.0)
    volatility = Column(Float, default=0.05)
    
    resource_key = Column(String(32), nullable=True)  # oil, gold, uranium, steel, food


class StockHolding(Base):
    __tablename__ = "stock_holdings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    commodity_id = Column(Integer, ForeignKey("commodities.id"), nullable=False)
    quantity = Column(Float, default=0.0)
    avg_buy_price = Column(Float, default=0.0)
    
    user = relationship("User", back_populates="stocks")
    commodity = relationship("Commodity")


# =========================================================
# ✅ بخش تنگه‌ها
# =========================================================
class Strait(Base):
    __tablename__ = "straits"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    description = Column(Text, nullable=True)
    
    controller_country_id = Column(Integer, ForeignKey("countries.id"), nullable=True)
    defense_level = Column(Integer, default=1)
    
    oil_output_per_hour = Column(Float, default=100.0)
    tax_rate = Column(Float, default=0.0)  # 0 تا 50٪
    is_closed = Column(Boolean, default=False)
    
    controller_country = relationship("Country", back_populates="controlled_straits")


# =========================================================
# ✅ بخش تحقیقات
# =========================================================
class ResearchType(Base):
    __tablename__ = "research_types"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    emoji = Column(String(8), nullable=True)
    description = Column(Text, nullable=True)
    
    cost_cash = Column(Float, default=50000.0)
    required_level = Column(Integer, default=1)
    
    bonus_type = Column(String(32), nullable=True)  # attack, defense, economy, income
    bonus_value = Column(Float, default=0.1)


class UserResearch(Base):
    __tablename__ = "user_researches"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    research_type_id = Column(Integer, ForeignKey("research_types.id"), nullable=False)
    completed_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User")
    research = relationship("ResearchType")

# =========================================================
# ✅ سیستم جاسوسی
# =========================================================
class SpyMission(Base):
    __tablename__ = "spy_missions"
    
    id = Column(Integer, primary_key=True)
    spy_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    target_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    mission_type = Column(String(32), nullable=False)  # "army", "economy", "research"
    
    success = Column(Boolean, default=False)
    result_data = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)


# =========================================================
# ✅ اتحادها
# =========================================================
class Alliance(Base):
    __tablename__ = "alliances"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(64), unique=True, nullable=False)
    tag = Column(String(8), nullable=True)  # TAG کوتاه
    
    leader_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    description = Column(Text, nullable=True)
    
    treasury = Column(Float, default=0.0)  # خزانه مشترک
    total_power = Column(Float, default=0.0)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    members = relationship("AllianceMember", back_populates="alliance", cascade="all, delete-orphan")


class AllianceMember(Base):
    __tablename__ = "alliance_members"
    
    id = Column(Integer, primary_key=True)
    alliance_id = Column(Integer, ForeignKey("alliances.id"), nullable=False)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    
    rank = Column(String(16), default="member")  # leader / officer / member
    joined_at = Column(DateTime, default=datetime.utcnow)
    
    alliance = relationship("Alliance", back_populates="members")


# =========================================================
# ✅ دیپلماسی (پیمان‌ها)
# =========================================================
class DiplomacyPact(Base):
    __tablename__ = "diplomacy_pacts"
    
    id = Column(Integer, primary_key=True)
    country1_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    country2_id = Column(Integer, ForeignKey("countries.id"), nullable=False)
    
    pact_type = Column(String(32), nullable=False)  # "peace" / "trade" / "nap" (عدم تجاوز)
    expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# =========================================================
# ✅ دستاوردها
# =========================================================
class Achievement(Base):
    __tablename__ = "achievements"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    emoji = Column(String(8), nullable=True)
    
    requirement_type = Column(String(32), nullable=True)  # buildings, units, level, cash, wins
    requirement_value = Column(Float, default=0.0)
    
    reward_cash = Column(Float, default=0.0)
    reward_xp = Column(Integer, default=0)


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(BigInteger, ForeignKey("users.user_id"), nullable=False)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False)
    unlocked_at = Column(DateTime, default=datetime.utcnow)

def init_db(db_url: str = "sqlite:///game.db"):
    engine = create_engine(db_url, echo=False)
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)

if __name__ == "__main__":
    init_db()
    print("✅ دیتابیس ساخته شد.") 
    