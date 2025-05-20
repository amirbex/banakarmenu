# --- فایل اصلی پروژه "منو بناکار" ---
# شامل: خوشامد، مسیر منعطف، پیشنهاد از منو، نوشیدنی ابداعی هوشمند، پاسخ‌ انسانی با تایپ مرحله‌ای

import asyncio
import random
import json
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.generativeai as genai

# --- کلیدهای API ---
TELEGRAM_TOKEN = '8038668469:AAF8rEHamunjBCt-I2e5rCOa7JF25N94s2U'
GOOGLE_API_KEY = 'AIzaSyC8VK_y5ESVLZNXI80wy7KBJ5_IxEoxh7E'
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-2.0-flash")

# --- لیست نهایی مواد اولیه (سبک اینوتکس) ---
ingredients = {
    # سیروپ
    'سیروپ پاپ کرن', 'سیروپ بلک بری', 'سیروپ گرانادین(انار با پوست)', 'سیروپ زعفران',
    'سیروپ خیار', 'سیروپ گرین میکس', 'سیروپ وانیل', 'سیروپ شکلات', 'سیروپ آیریش',
    'سیروپ ردمیکس', 'سیروپ پشن فروت', 'سیروپ رام', 'سیروپ آدامس آبی',
    'سیروپ گواوا', 'سیروپ ویمتو', 'سیروپ کوکی', 'سیروپ فندق', 'سیروپ بادیان',

    # آبمیوه
    'آب آلبالو', 'آب پرتقال', 'آب آناناس', 'آب انار فلفلی', 'آب سیب سبز',
    'آب هلو', 'آب انبه', 'آب انگور سفید', 'آب زردآلو', 'آب انار',

    # میوه و سبزیجات
    'ریحان ایتالیایی', 'لیمو زرد', 'گل خوراکی', 'نعنا موهیتو تازه',
    'توت فرنگی', 'پرتقال تازه',

    # عرقیات
    'عرق بیدمشک', 'عرق بهارنارنج',

    # گازدار
    'سودا کلاسیک', 'سودا', 'سیب گازدار', 'انرژی زا'
}

# --- پیام خوشامد ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    reply_keyboard = [["📋 راهنمای منو", "🥼 نوشیدنی ابداعی"]]
    await update.message.reply_text(
        f"سلام {user.first_name} ☀️\n\nمن دستیار هوشمند کافه بناکارم. اینجام تا بهت کمک کنم یا یه ترکیب جدید بسازم یا از منوی خوش‌طعمامون چیزی برات پیدا کنم!\nیکی از گزینه‌های زیر رو انتخاب کن:",
        reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
    )
    context.user_data['flow'] = None

# --- پیام در حال فکر کردن ---
async def send_typing_thinking(update: Update):
    return await update.message.reply_text("🤔 دارم فکر می‌کنم چی برات بهتره... یکم صبر کن!")

async def send_chunked_text(text, update: Update, chunk_size=500):
    for i in range(0, len(text), chunk_size):
        await update.message.reply_text(text[i:i+chunk_size])

# --- مسیر ساخت نوشیدنی ابداعی ---
async def custom_drink_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['flow'] = 'custom'
    await update.message.reply_text("چه نوع طعمی دوست داری؟ شیرین، ترش، ملایم، عجیب یا یه حس خاص؟")

async def handle_custom_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    taste = update.message.text
    context.user_data['taste'] = taste
    ingredient_list = ', '.join(ingredients)
    prompt = f"""با توجه به طعم {taste} و فقط از بین مواد زیر، یک نوشیدنی بدون الکل طراحی کن. اسم جذاب، لیست مواد با مقدار، جمله تبلیغاتی، طرز تهیه حرفه‌ای بده.

مواد:
{ingredient_list}
"""

    thinking_msg = await send_typing_thinking(update)
    try:
        response = await model.generate_content(prompt)  # استفاده از await داخل تابع async
        result = response.candidates[0].content.parts[0].text
        await thinking_msg.delete()
        await send_chunked_text(result, update)
    except Exception as e:
        await thinking_msg.delete()
        await update.message.reply_text(f"متأسفم، مشکلی در دریافت پاسخ از Gemini پیش اومد: {e}")

# --- مسیر پیشنهاد منو ---
async def handle_menu_intro(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['flow'] = 'menu'
    await update.message.reply_text("چه طعمی، حسی یا سبک نوشیدنی مدنظرت هست؟ مثلاً شیرین، ترش، خنک یا کلاسیک؟")

async def handle_menu_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    request = update.message.text
    prompt = f"کاربر دنبال نوشیدنی با این مشخصاته: {request}\nبا توجه به لیست منو زیر، فقط اسم و ویژگی آیتم‌های مناسب رو بگو:\n" + '\n'.join([f"- {item['Drink Name']} ({item['Flavor Description']})" for item in sample_menu])
    thinking_msg = await send_typing_thinking(update)
    try:
        response = model.generate_content(prompt)  # اگر Gemini async است، این خط را به await تغییر بده
        result = response.candidates[0].content.parts[0].text
        await thinking_msg.delete()
        await send_chunked_text(result, update)
    except Exception as e:
        await thinking_msg.delete()
        await update.message.reply_text(f"متأسفم، نتونستم پیشنهادی از منو پیدا کنم: {e}")


# --- هدایت مکالمه بر اساس مسیر جاری ---
async def dynamic_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    flow = context.user_data.get('flow')
    if flow == 'custom':
        await handle_custom_prompt(update, context)
    elif flow == 'menu':
        await handle_menu_search(update, context)
    else:
        reply_keyboard = [["📋 راهنمای منو", "🥼 نوشیدنی ابداعی"]]
        await update.message.reply_text(
            "مطمئن نیستم قراره چی کار کنیم. لطفاً یکی از گزینه‌های زیر رو انتخاب کن:",
            reply_markup=ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True, resize_keyboard=True)
        )

# --- اجرای اصلی ---
def main():
    global sample_menu
    sample_menu = [
    {
        "Drink Name": "Doppio (Single Origin)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه عصاره گیری شده تحت فشار، طعم قوی و خالص",
        "Ingredients": ["قهوه عصاره گیری شده"],
        "Price": 141000,
    },
    {
        "Drink Name": "Doppio (Commercial)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه عصاره گیری شده تحت فشار، طعمی متعادل‌تر و ملایم‌تر",
        "Ingredients": ["قهوه عصاره گیری شده"],
        "Price": 128000,
    },
    {
        "Drink Name": "Americano (Single Origin)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو با مقدار دلخواه آب، طعمی قوی و تلخ",
        "Ingredients": ["قهوه دپویو", "آب"],
        "Price": 141000,
    },
    {
        "Drink Name": "Americano (Commercial)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو با مقدار دلخواه آب، طعمی ملایم‌تر و متعادل‌تر",
        "Ingredients": ["قهوه دپویو", "آب"],
        "Price": 128000,
    },
    {
        "Drink Name": "Cappuccino (Single Origin)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو همراه با شیر و فوم شیر حجیم، طعمی غنی و کرمی",
        "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
        "Price": 150000,
    },
    {
        "Drink Name": "Cappuccino (Commercial)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو همراه با شیر و فوم شیر، طعمی ملایم‌تر و متعادل‌تر",
        "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
        "Price": 137000,
    },
    {
        "Drink Name": "Caffè Latte (Single Origin)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو همراه با شیر و فوم شیر اندک، طعمی ملایم و کرمی",
        "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
        "Price": 152000,
    },
    {
        "Drink Name": "Caffè Latte (Commercial)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو همراه با شیر و فوم شیر اندک، طعمی متعادل‌تر",
        "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
        "Price": 139000,
    },
    {
        "Drink Name": "Affogato (Single Origin)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو همراه با دو اسکوپ بستنی وانیلی، طعمی شیرین و دلچسب",
        "Ingredients": ["قهوه دپویو", "بستنی وانیلی"],
        "Price": 154000,
    },
    {
        "Drink Name": "Affogato (Commercial)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو همراه با دو اسکوپ بستنی وانیلی، طعمی ملایم‌تر و شیرین",
        "Ingredients": ["قهوه دپویو", "بستنی وانیلی"],
        "Price": 141000,
    },
    {
        "Drink Name": "Caffè Macchiato (Single Origin)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو همراه با شیر و فوم اندک، طعمی قوی و صاف",
        "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
        "Price": 148000,
    },
    {
        "Drink Name": "Caffè Macchiato (Commercial)",
        "Category": "نوشیدنی بر پایه اسپرسو",
        "Flavor Description": "قهوه دپویو همراه با شیر و فوم اندک، طعمی ملایم‌تر و صاف",
        "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
        "Price": 135000,
    },
    {
        "Drink Name": "Iced Americano",
        "Category": "نوشیدنی های سرد",
        "Flavor Description": "قهوه سرد و تلخ با طعمی خنک و شفاف",
        "Ingredients": ["قهوه دپویو", "آب", "یخ"],
        "Price": 0  # قیمت مشخص نیست
    },
    {
        "Drink Name": "CocoMoco Frappe",
        "Category": "نوشیدنی های سرد",
        "Flavor Description": "طعم شیرین و شکلاتی با حس خامه‌ای و کمی قهوه‌ای",
        "Ingredients": ["قهوه", "شیر نارگیل", "افزودنی طعم‌دهنده", "خامه حجیم شده"],
        "Price": 177000
    },
    {
        "Drink Name": "CreamNut Frappe",
        "Category": "نوشیدنی های سرد",
        "Flavor Description": "طعم فندقی شکلاتی با بافتی کرمی و غنی",
        "Ingredients": ["قهوه", "شیر", "شکلات فندقی", "خامه حجیم شده"],
        "Price": 185000
    },
    {
        "Drink Name": "Single Origin Cold Brew",
        "Category": "نوشیدنی های سرد",
        "Flavor Description": "قهوه عصاره‌گیری شده با طعم ملایم، کمی شیرین، کم‌اسیدی",
        "Ingredients": ["قهوه", "آب", "یخ"],
        "Price": 161000
    },
    {
        "Drink Name": "Iced Mocha",
        "Category": "نوشیدنی های سرد",
        "Flavor Description": "شکلاتی، شیرین و قوی با حس خنکی یخ",
        "Ingredients": ["قهوه دپویو", "شیر", "سس شکلات", "یخ"],
        "Price": 0  # قیمت مشخص نیست
    },
    {
        "Drink Name": "Iced Latte",
        "Category": "نوشیدنی های سرد",
        "Flavor Description": "ملایم، شیرین و کرمی با حس خنکی دلپذیر",
        "Ingredients": ["قهوه دپویو", "شیر", "یخ"],
        "Price": 0  # قیمت مشخص نیست
    },
    {
        "Drink Name": "Matchate",
        "Category": "نوشیدنی های گرم",
        "Flavor Description": "طعمی خاص از چای ماچا با ترکیب پسته و شکلات سفید، شیرین و گیاهی",
        "Ingredients": ["ماچا", "پسته", "شکلات سفید", "شیر"],
        "Price": 189000
    },
    {
        "Drink Name": "Pink Chocolate",
        "Category": "نوشیدنی های گرم",
        "Flavor Description": "شیرین و توتی با رایحه شکلات سفید و بافت کرمی",
        "Ingredients": ["توت فرنگی", "شکلات سفید", "شیر"],
        "Price": 177000
    },
    {
        "Drink Name": "Coco Chocolate",
        "Category": "نوشیدنی های گرم",
        "Flavor Description": "شکلاتی، کلاسیک و شیرین با شیر داغ",
        "Ingredients": ["شکلات", "شیر"],
        "Price": 169000
    },
    {
        "Drink Name": "Ardental",
        "Category": "نوشیدنی های گرم",
        "Flavor Description": "تند، شیرین و ادویه‌دار، ترکیبی سنتی از ماسالا و جنسینگ",
        "Ingredients": ["ماسالا", "جنسینگ", "خشخاش", "شیر"],
        "Price": 185000
    },
    {
        "Drink Name": "Tea Latte Caramel",
        "Category": "نوشیدنی های گرم",
        "Flavor Description": "شیرین و کرمی با رایحه کارامل و چای",
        "Ingredients": ["عصاره چای", "کارامل", "شیر"],
        "Price": 156000
    },
    {
        "Drink Name": "Iced Matcha Latte",
        "Category": "ماچا",
        "Flavor Description": "ملایم، گیاهی، شیرین با حس خنکی یخ",
        "Ingredients": ["ماچا", "شیر", "یخ"],
        "Price": 197000
    },
    {
        "Drink Name": "Matcha Latte",
        "Category": "ماچا",
        "Flavor Description": "گیاهی، گرم و کرمی با شیر داغ",
        "Ingredients": ["ماچا", "شیر"],
        "Price": 199000
    },
    {
        "Drink Name": "Iced Matcha",
        "Category": "ماچا",
        "Flavor Description": "تلخ، خنک و گیاهی با ته‌مزه‌ی سبز تازه",
        "Ingredients": ["ماچا", "یخ", "آب"],
        "Price": 177000
    },
    {
        "Drink Name": "Matcha",
        "Category": "ماچا",
        "Flavor Description": "طعم خالص و تلخ چای ماچا دم‌آوری شده",
        "Ingredients": ["ماچا", "آب"],
        "Price": 187000
    },
    {
        "Drink Name": "Mango Matcha",
        "Category": "ماچا",
        "Flavor Description": "ترکیبی از شیرینی انبه با ماچا، شیرین و استوایی",
        "Ingredients": ["ماچا", "سیروپ انبه"],
        "Price": 207000
    },
    {
        "Drink Name": "Matcha Shake",
        "Category": "ماچا",
        "Flavor Description": "خامه‌ای، شیرین و وانیلی با طعم سبز ماچا",
        "Ingredients": ["ماچا", "بستنی وانیلی"],
        "Price": 199000
    },
    {
        "Drink Name": "MatchaGatto",
        "Category": "ماچا",
        "Flavor Description": "تلخ و شیرین با ترکیب بستنی و ماچا گرم",
        "Ingredients": ["ماچا", "دو اسکوپ بستنی"],
        "Price": 199000
    },
    {
        "Drink Name": "Special Black Tea",
        "Category": "دمنوش",
        "Flavor Description": "کلاسیک، قوی، عطری با ته‌مزه بهاری",
        "Ingredients": ["چای سیلان", "گل بهارنارنج"],
        "Price": 79000
    },
    {
        "Drink Name": "Helin",
        "Category": "دمنوش",
        "Flavor Description": "ملایم، گیاهی، کمی شیرین با طعم عسل",
        "Ingredients": ["چای سیر چینی", "چاتمین", "میوه گرمسیری", "عسل"],
        "Price": 141000
    },
    {
        "Drink Name": "Gabriel",
        "Category": "دمنوش",
        "Flavor Description": "شیرین و معطر با ترکیب سیب، بابونه، دارچین و گل ستاره‌ای",
        "Ingredients": ["سیب", "بابونه", "دارچین", "گل ستاره‌ای"],
        "Price": 153000
    },
    {
        "Drink Name": "Oten",
        "Category": "دمنوش",
        "Flavor Description": "میوه‌ای و تازه با طعم بهار نارنج و بادام",
        "Ingredients": ["میوه قرمز", "بادام", "بهارنارنج"],
        "Price": 163000
    },
    {
        "Drink Name": "Énergisant",
        "Category": "دمنوش",
        "Flavor Description": "قوی، انرژی‌بخش، تند و ادویه‌دار",
        "Ingredients": ["چای سیاه", "میخک", "هل", "زنجبیل", "دارچین"],
        "Price": 164000
    },
    {
        "Drink Name": "Landa",
        "Category": "دمنوش",
        "Flavor Description": "ملایم، آرامش‌بخش و گلی با رایحه هل و گل رز",
        "Ingredients": ["لاوندر", "گل گاوزبان", "گل سرخ", "هل"],
        "Price": 151000
    },
    {
        "Drink Name": "Marseille",
        "Category": "دمنوش",
        "Flavor Description": "گلی، سنتی، شیرین با ترکیب چای فرانسوی و توت سفید",
        "Ingredients": ["چای فرانسوی", "گل سرخ", "توت سفید"],
        "Price": 147000
    },
    {
        "Drink Name": "Rozelin",
        "Category": "دمنوش",
        "Flavor Description": "استوایی و ادویه‌ای با رایحه رز و زنجبیل",
        "Ingredients": ["آناناس", "رز", "زنجبیل"],
        "Price": 157000
    },
    {
        "Drink Name": "Yerba Mate",
        "Category": "دمنوش",
        "Flavor Description": "گیاهی، تلخ و غلیظ با پس‌طعم نعناع و انرژی‌زا",
        "Ingredients": ["یربا ماته", "نعناع"],
        "Price": 147000
    },
    {
        "Drink Name": "Anti-Froid",
        "Category": "دمنوش",
        "Flavor Description": "خنک، ضدسرفه و لیمویی با عطر رزماری",
        "Ingredients": ["به", "لیمو", "ارگانو", "رزماری"],
        "Price": 143000
    },
    {
        "Drink Name": "Saint-Honoré Tart",
        "Category": "دسر",
        "Flavor Description": "کرم‌دار، کره‌ای، بادامی با شیرینی کاراملی لطیف",
        "Ingredients": ["خمیر سوفله بادام", "کرم دیپلمات", "کارامل"],
        "Price": 149000
    },
    {
        "Drink Name": "Chocolate Hazelnut Éclair",
        "Category": "دسر",
        "Flavor Description": "شکلاتی، فندقی و خامه‌ای با بافت لطیف",
        "Ingredients": ["خمیر شو", "شکلات", "کرم موسلین", "پرالین فندق"],
        "Price": 139000
    },
    {
        "Drink Name": "Berries Éclair",
        "Category": "دسر",
        "Flavor Description": "توتی، شیرین و سبک با بافت خامه‌ای",
        "Ingredients": ["خمیر شو", "توت فرنگی", "کرم"],
        "Price": 142000
    },
    {
        "Drink Name": "Pistache Éclair",
        "Category": "دسر",
        "Flavor Description": "پسته‌ای، خامه‌ای، شیرین با رایحه لطیف پسته",
        "Ingredients": ["خمیر شو", "پسته", "کرم موسلین", "پرالین پسته"],
        "Price": 159000
    },
    {
        "Drink Name": "Cheesecake with Hazelnut Chocolate Topping",
        "Category": "دسر",
        "Flavor Description": "شکلاتی، پنیری و خامه‌ای با بیسکوئیت کره‌ای",
        "Ingredients": ["بیسکوئیت", "پنیر", "شکلات", "فندق"],
        "Price": 147000
    },
    {
        "Drink Name": "Honey Cake",
        "Category": "دسر",
        "Flavor Description": "لایه‌ای، شیرین، عسلی با طعمی نرم و لطیف",
        "Ingredients": ["عسل", "پنیر خامه‌ای", "پودر بیسکوئیت"],
        "Price": 137000
    },
    {
        "Drink Name": "Cheesecake",
        "Category": "دسر",
        "Flavor Description": "پنیری، ساده، سبک با پایه بیسکوئیت کره‌ای",
        "Ingredients": ["بیسکوئیت", "پنیر", "خامه"],
        "Price": 131000
    },
    {
        "Drink Name": "Tres Leches Cake",
        "Category": "دسر",
        "Flavor Description": "کیک نرم و مرطوب با طعم شیر عسلی و شیر غلیظ",
        "Ingredients": ["شیر عسلی", "شیر غلیظ", "خامه", "کیک"],
        "Price": 127000
    },
    {
        "Drink Name": "Cheesecake with Peanut Butter Topping",
        "Category": "دسر",
        "Flavor Description": "پنیری، کره بادام زمینی‌دار، شیرین و خامه‌ای",
        "Ingredients": ["بیسکوئیت", "پنیر", "کره بادام زمینی"],
        "Price": 147000
    },
    {
        "Drink Name": "Cheesecake with Lotus Topping",
        "Category": "دسر",
        "Flavor Description": "پنیری، شیرین و کره‌ای با عطر بیسکویت لوتوس",
        "Ingredients": ["بیسکوئیت", "پنیر", "لوتوس"],
        "Price": 147000
    },
    {
        "Drink Name": "Creamy Mushroom Soup",
        "Category": "سوپ و سالاد",
        "Flavor Description": "خامه‌ای، قارچی، لطیف و پنیر‌دار با تست قارچ کبابی",
        "Ingredients": ["قارچ", "خامه", "پنیر گودا", "قارچ گریل شده"],
        "Price": 187000
    },
    {
        "Drink Name": "Shandy Salad",
        "Category": "سوپ و سالاد",
        "Flavor Description": "مزه‌دار، پروتئینی، ترش و خامه‌ای با سس دست‌ساز",
        "Ingredients": ["مرغ مزه‌دار", "پنیر پارمسان", "کروتان", "سس رنچ", "کاهو", "گردو", "زیتون"],
        "Price": 259000
    },
    {
        "Drink Name": "Viande Salad",
        "Category": "سوپ و سالاد",
        "Flavor Description": "گوشت‌دار، مغذی و مدیترانه‌ای",
        "Ingredients": ["فیله گوساله", "کاهو", "زیتون", "کوجه", "هویج"],
        "Price": 293000
    },
    {
        "Drink Name": "Pomodoro Pasta",
        "Category": "پاستا",
        "Flavor Description": "پنه ریگاته با سس گوجه پومودورو، پنیری و ترش و تازه",
        "Ingredients": ["پنه", "سس گوجه پومودورو", "پنیر موزارلا", "ریحان"],
        "Price": 0
    },
    {
        "Drink Name": "Peanut Smoky Pasta",
        "Category": "پاستا",
        "Flavor Description": "کرم‌دار، دودی، مغذی و خاص با سس بادام زمینی",
        "Ingredients": ["پنه", "سس بادام زمینی", "کدو", "قارچ", "پنیر"],
        "Price": 0
    },
    {
        "Drink Name": "Solaire Smoothie",
        "Category": "شیک و اسموتی",
        "Flavor Description": "پروتئینی، استوایی و پرانرژی با طعم انبه و پرتقال",
        "Ingredients": ["پروتئین", "انبه", "پرتقال"],
        "Price": 172000
    },
    {
        "Drink Name": "Salé Sucré Shake",
        "Category": "شیک و اسموتی",
        "Flavor Description": "شیرین و شور با کرمی از بادام زمینی نمکی",
        "Ingredients": ["شیر", "بادام زمینی"],
        "Price": 179000
    },
    {
        "Drink Name": "Butternut Shake",
        "Category": "شیک و اسموتی",
        "Flavor Description": "خامه‌ای، مغذی و پرملات با مغزها و شیر یخ‌زده",
        "Ingredients": ["بستنی", "گردو", "فندق", "راده‌ی یخی"],
        "Price": 187000
    },
    {
        "Drink Name": "Inferno Smoothie",
        "Category": "شیک و اسموتی",
        "Flavor Description": "سیاه، شیرین و خاکی با چاشنی ماست و شلیل",
        "Ingredients": ["شلیل", "نمک جنگلی", "ماست"],
        "Price": 173000
    },
    {
        "Drink Name": "Ete Rouge Smoothie",
        "Category": "شیک و اسموتی",
        "Flavor Description": "توتی، ترش و پرتقالی با رایحه تازه میوه‌ای",
        "Ingredients": ["پرتقال", "توت فرنگی"],
        "Price": 183000
    },
    {
        "Drink Name": "Sang Sacré Smoothie",
        "Category": "شیک و اسموتی",
        "Flavor Description": "شیرین، میوه‌ای، با بافت یخی و طعم آلبالو",
        "Ingredients": ["توت فرنگی", "آلبالو", "ماست"],
        "Price": 178000
    },
    {
        "Drink Name": "Bacon Baguette",
        "Category": "باگت",
        "Flavor Description": "دودی، گوشتی، قارچی با نان فرانسوی و سس لذیذ",
        "Ingredients": ["بیکن", "فیله گوشت", "قارچ", "کاهو", "گوجه خشک مزه‌دار", "نان باگت"],
        "Price": 313000
    },
    {
        "Drink Name": "Sausage Baguette",
        "Category": "باگت",
        "Flavor Description": "ادویه‌دار، گوشتی و خامه‌ای با سوسیس دست‌ساز",
        "Ingredients": ["سوسیس دست‌ساز", "کاهو", "گوجه خشک", "پنیر گودا", "زیتون", "سس"],
        "Price": 341000
    },
    {
        "Drink Name": "Chicken Baguette",
        "Category": "باگت",
        "Flavor Description": "ملایم، مرغی، سبز با ترکیب اسفناج و بیبی اسفناج",
        "Ingredients": ["مرغ مزه‌دار", "بیبی اسفناج", "کاهو", "گوجه خشک", "نان باگت"],
        "Price": 293000
    },
    {
        "Drink Name": "Steak Baguette",
        "Category": "باگت",
        "Flavor Description": "کامل، گوشتی، پنیر‌دار با قارچ گریل و سس خاص",
        "Ingredients": ["فیله گوساله", "قارچ کاراملی", "کاهو", "گوجه خشک", "نان باگت"],
        "Price": 467000
    },
    {
        "Drink Name": "Mushroom Baguette",
        "Category": "باگت",
        "Flavor Description": "گیاهی، خامه‌ای با قارچ‌های اسفناجی و نان فرانسوی",
        "Ingredients": ["میکس قارچ", "اسفناج", "کاهو", "گوجه خشک", "نان باگت"],
        "Price": 254000
    },
    {
        "Drink Name": "Enjoy Toast",
        "Category": "صبحانه",
        "Flavor Description": "ترش، گوشتی و کلاسیک با بیکن و سوسیس صبحانه",
        "Ingredients": ["خمیر ترش", "سوسیس دست‌ساز", "پنیر لیته", "تخم مرغ", "تمرهندی", "کاهو"],
        "Price": 319000
    },
    {
        "Drink Name": "Bacon Toast",
        "Category": "صبحانه",
        "Flavor Description": "دودی و کره‌ای با بیکن و تخم مرغ اسکرمبل",
        "Ingredients": ["خمیر ترش", "بیکن", "پنیر لیته", "تخم مرغ اسکرمبل", "کاهو"],
        "Price": 287000
    },
    {
        "Drink Name": "Charmont Omelette",
        "Category": "صبحانه",
        "Flavor Description": "کلاسیک، اروپایی، با سس پومودورو و ریحان",
        "Ingredients": ["تخم مرغ", "سس پومودورو", "ریحان", "موتزارلا", "گوجه خشک"],
        "Price": 215000
    },
    {
        "Drink Name": "Oliva Omelette",
        "Category": "صبحانه",
        "Flavor Description": "تخم‌مرغی، زیتونی و مدیترانه‌ای با سبزیجات",
        "Ingredients": ["تخم مرغ", "زیتون", "سس پومودورو", "رب انار", "گردو", "گوجه خشک"],
        "Price": 228000
    },
    {
        "Drink Name": "Spaghetti Pancake",
        "Category": "صبحانه",
        "Flavor Description": "شیرین و رشته‌ای با موز، عسل و تاپینگ توتی",
        "Ingredients": ["پنکیک", "رشته", "موز", "عسل", "توت فرنگی", "بلوبری"],
        "Price": 219000
    },
    {
        "Drink Name": "PeanutButter Toast",
        "Category": "صبحانه",
        "Flavor Description": "کره‌ای، شیرین، مقوی با بافت خامه‌ای",
        "Ingredients": ["خمیر ترش", "کره بادام زمینی", "عسل", "موز", "خامه"],
        "Price": 199000
    },
    {
        "Drink Name": "Spinach Toast",
        "Category": "صبحانه",
        "Flavor Description": "سبز، خامه‌ای با اسفناج و قارچ کاراملی",
        "Ingredients": ["خمیر ترش", "تخم مرغ", "قارچ کاراملی", "اسفناج", "گوجه خشک"],
        "Price": 254000
    },
    {
        "Drink Name": "Stocky Toast",
        "Category": "صبحانه",
        "Flavor Description": "کامل، گوشت‌دار، با طعم کلاسیک و گرم",
        "Ingredients": ["خمیر ترش", "فیله گوساله", "تخم مرغ", "نیمرو", "گوجه خشک"],
        "Price": 378000
    },   
    {
        "Drink Name": "Emerald",
        "Category": "ماکتیل",
        "Flavor Description": "ترکیب میوه‌های ملس و تابستانه با پس طعم تلخی پرتقال",
        "Ingredients": ["میوه‌های ملس", "تابستانه", "پرتقال"],
        "Price": 143000,
    },
    {
        "Drink Name": "GummyCandy",
        "Category": "ماکتیل",
        "Flavor Description": "ترکیب ترش و شیرین میوه‌های استوایی با پس طعم پاستیلی",
        "Ingredients": ["میوه‌های استوایی"],
        "Price": 141000,
    },
    {
        "Drink Name": "Vin De Miel",
        "Category": "ماکتیل",
        "Flavor Description": "ترکیب مرکبات و انگور با پس طعم شهد عسل و چای ترش دست‌ساز",
        "Ingredients": ["مرکبات", "انگور", "شهد عسل", "چای ترش"],
        "Price": 139000,
    },
    {
        "Drink Name": "Lilin",
        "Category": "ماکتیل",
        "Flavor Description": "ترکیب ترش و شیرین میوه‌های قرمز با چاشنی نمک",
        "Ingredients": ["میوه‌های قرمز", "نمک"],
        "Price": 139000,
    },
    {
        "Drink Name": "Le Ventos",
        "Category": "ماکتیل",
        "Flavor Description": "ترکیب میوه‌های قرمز و مرکبات با هم آمیزی شهد صیفی جات دست‌ساز",
        "Ingredients": ["میوه‌های قرمز", "مرکبات", "شهد صیفی جات"],
        "Price": 131000,
    },
    {
        "Drink Name": "Charlotte",
        "Category": "ماکتیل",
        "Flavor Description": "ترکیب میوه‌های استوایی با هم آمیزی انار و ذغال اخته",
        "Ingredients": ["میوه‌های استوایی", "انار", "ذغال اخته"],
        "Price": 137000,
    },
    {
        "Drink Name": "Eté cool",
        "Category": "ماکتیل",
        "Flavor Description": "ترکیب بهشتی و خنک میوه‌های گرمسیری با پس طعم نعنا و لیمو",
        "Ingredients": ["میوه‌های گرمسیری", "نعنا", "لیمو"],
        "Price": 133000,
    },
    {
        "Drink Name": "Grenouille",
        "Category": "ماکتیل",
        "Flavor Description": "ترکیب سرحال کننده مرکبات و آلوها با مکمل انرژی زا",
        "Ingredients": ["مرکبات", "آلو", "مکمل انرژی زا"],
        "Price": 143000,
    },
    {
        "Drink Name": "Denis",
        "Category": "ماکتیل",
        "Flavor Description": "ترکیب سیب و پرتقال با چاشنی شهد زنجبیل دست‌ساز اسپایسی",
        "Ingredients": ["سیب", "پرتقال", "شهد زنجبیل"],
        "Price": 133000,
    },
    {
        "Drink Name": "Orange Cool up",
        "Category": "ماکتیل",
        "Flavor Description": "آب پرتقال طبیعی",
        "Ingredients": ["آب پرتقال"],
        "Price": 117000,
    },
    {
        "Drink Name": "Red Cool up",
        "Category": "ماکتیل",
        "Flavor Description": "آب هندوانه طبیعی",
        "Ingredients": ["آب هندوانه"],
        "Price": 87000,
    }
]





    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Regex("^🥼 نوشیدنی ابداعی$"), custom_drink_entry))
    app.add_handler(MessageHandler(filters.Regex("^📋 راهنمای منو$"), handle_menu_intro))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dynamic_handler))
    
    app.run_polling()

if __name__ == '__main__':
    main()
