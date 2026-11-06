"""موتور بازار و بورس"""

import random
from models import Commodity


def update_market_prices(session):
    """نوسان قیمت کالاها (شبیه بورس واقعی)"""
    commodities = session.query(Commodity).all()
    
    for c in commodities:
        # تغییر تصادفی بین -5% تا +5%
        change = random.uniform(-c.volatility, c.volatility)
        
        # قیمت جدید
        new_price = c.current_price * (1 + change)
        
        # جلوگیری از قیمت منفی یا خیلی زیاد
        min_price = c.base_price * 0.2
        max_price = c.base_price * 5.0
        c.current_price = max(min_price, min(new_price, max_price))
    
    session.commit()
    print("📊 قیمت‌های بازار بروزرسانی شد.") 
    