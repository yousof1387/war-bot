"""مقادیر ثابت بازی"""

CATEGORIES = {
    "economic": ("💰", "اقتصادی"),
    "military": ("⚔️", "نظامی"),
    "research": ("🔬", "تحقیقاتی"),
    "infrastructure": ("🏗️", "زیرساختی"),
}

MILITARY_CATEGORIES = {
    "drones": ("🛩️", "پهپاد"),
    "missiles": ("🚀", "موشک"),
    "fighters": ("✈️", "جنگنده"),
    "bombers": ("🛬", "بمب‌افکن"),
    "air_defense": ("🛡️", "پدافند هوایی"),
    "naval": ("🚢", "ناوگان دریایی"),
    "submarines": ("🛥️", "زیردریایی"),
    "tanks": ("🛡️", "تانک"),
    "artillery": ("💥", "توپخانه"),
    "armor": ("🚗", "زرهی"),
    "atgm": ("🎯", "ضدتانک"),
}

LEVEL_TITLES = [
    (1, "روستایی"), (5, "شهر کوچک"), (10, "شهر متوسط"),
    (20, "کلان‌شهر"), (30, "استان"), (50, "قدرت منطقه‌ای"),
    (75, "قدرت جهانی"), (100, "ابرقدرت"), (150, "امپراتوری"), (200, "افسانه"),
]

def get_level_title(level):
    title = "روستایی"
    for lvl, t in LEVEL_TITLES:
        if level >= lvl:
            title = t
    return title 
