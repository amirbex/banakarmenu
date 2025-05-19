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
    "Available": true
  },
  {
    "Drink Name": "Doppio (Commercial)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه عصاره گیری شده تحت فشار، طعمی متعادل‌تر و ملایم‌تر",
    "Ingredients": ["قهوه عصاره گیری شده"],
    "Price": 128000,
    "Available": true
  },

  {
    "Drink Name": "Americano (Single Origin)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو با مقدار دلخواه آب، طعمی قوی و تلخ",
    "Ingredients": ["قهوه دپویو", "آب"],
    "Price": 141000,
    "Available": true
  },
  {
    "Drink Name": "Americano (Commercial)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو با مقدار دلخواه آب، طعمی ملایم‌تر و متعادل‌تر",
    "Ingredients": ["قهوه دپویو", "آب"],
    "Price": 128000,
    "Available": true
  },

  {
    "Drink Name": "Cappuccino (Single Origin)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با شیر و فوم شیر حجیم، طعمی غنی و کرمی",
    "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
    "Price": 150000,
    "Available": true
  },
  {
    "Drink Name": "Cappuccino (Commercial)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با شیر و فوم شیر، طعمی ملایم‌تر و متعادل‌تر",
    "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
    "Price": 137000,
    "Available": true
  },

  {
    "Drink Name": "Caffè Latte (Single Origin)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با شیر و فوم شیر اندک، طعمی ملایم و کرمی",
    "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
    "Price": 152000,
    "Available": true
  },
  {
    "Drink Name": "Caffè Latte (Commercial)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با شیر و فوم شیر اندک، طعمی متعادل‌تر",
    "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
    "Price": 139000,
    "Available": true
  },

  {
    "Drink Name": "Affogato (Single Origin)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با دو اسکوپ بستنی وانیلی، طعمی شیرین و دلچسب",
    "Ingredients": ["قهوه دپویو", "بستنی وانیلی"],
    "Price": 154000,
    "Available": true
  },
  {
    "Drink Name": "Affogato (Commercial)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با دو اسکوپ بستنی وانیلی، طعمی ملایم‌تر و شیرین",
    "Ingredients": ["قهوه دپویو", "بستنی وانیلی"],
    "Price": 141000,
    "Available": true
  },

  {
    "Drink Name": "Caffè Macchiato (Single Origin)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با شیر و فوم اندک، طعمی قوی و صاف",
    "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
    "Price": 148000,
    "Available": true
  },
  {
    "Drink Name": "Caffè Macchiato (Commercial)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با شیر و فوم اندک، طعمی ملایم‌تر و صاف",
    "Ingredients": ["قهوه دپویو", "شیر", "فوم شیر"],
    "Price": 135000,
    "Available": true
  },

  {
    "Drink Name": "Caffè Mocha (Single Origin)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با سس شکلات و شیر و فوم شیر اندک، طعمی شکلاتی و ملایم",
    "Ingredients": ["قهوه دپویو", "سس شکلات", "شیر", "فوم شیر"],
    "Price": 159000,
    "Available": true
  },
  {
    "Drink Name": "Caffè Mocha (Commercial)",
    "Category": "نوشیدنی بر پایه اسپرسو",
    "Flavor Description": "قهوه دپویو همراه با سس شکلات و شیر و فوم شیر اندک، طعمی ملایم‌تر و متعادل‌تر",
    "Ingredients": ["قهوه دپویو", "سس شکلات", "شیر", "فوم شیر"],
    "Price": 147000,
    "Available": true
  },
{
    "Drink Name": "Mont Parnasse",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب ترش میوه‌های قرمز با پس طعم شیرینی فندق",
    "Ingredients": ["میوه‌های قرمز", "فندق"],
    "Price": 147000,
    "Available": true
  },
  {
    "Drink Name": "Emerald",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب میوه‌های ملس و تابستانه با پس طعم تلخی پرتقال",
    "Ingredients": ["میوه‌های ملس", "تابستانه", "پرتقال"],
    "Price": 143000,
    "Available": true
  },
  {
    "Drink Name": "GummyCandy",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب ترش و شیرین میوه‌های استوایی با پس طعم پاستیلی",
    "Ingredients": ["میوه‌های استوایی"],
    "Price": 141000,
    "Available": true
  },
  {
    "Drink Name": "Vin De Miel",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب مرکبات و انگور با پس طعم شهد عسل و چای ترش دست‌ساز",
    "Ingredients": ["مرکبات", "انگور", "شهد عسل", "چای ترش"],
    "Price": 139000,
    "Available": true
  },
  {
    "Drink Name": "Lilin",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب ترش و شیرین میوه‌های قرمز با چاشنی نمک",
    "Ingredients": ["میوه‌های قرمز", "نمک"],
    "Price": 139000,
    "Available": true
  },
  {
    "Drink Name": "Le Ventos",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب میوه‌های قرمز و مرکبات با هم آمیزی شهد صیفی جات دست‌ساز",
    "Ingredients": ["میوه‌های قرمز", "مرکبات", "شهد صیفی جات"],
    "Price": 131000,
    "Available": true
  },
  {
    "Drink Name": "Charlotte",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب میوه‌های استوایی با هم آمیزی انار و ذغال اخته",
    "Ingredients": ["میوه‌های استوایی", "انار", "ذغال اخته"],
    "Price": 137000,
    "Available": true
  },
  {
    "Drink Name": "Eté cool",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب بهشتی و خنک میوه‌های گرمسیری با پس طعم نعنا و لیمو",
    "Ingredients": ["میوه‌های گرمسیری", "نعنا", "لیمو"],
    "Price": 133000,
    "Available": true
  },
  {
    "Drink Name": "Grenouille",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب سرحال کننده مرکبات و آلوها با مکمل انرژی زا",
    "Ingredients": ["مرکبات", "آلو", "مکمل انرژی زا"],
    "Price": 143000,
    "Available": true
  },
  {
    "Drink Name": "Denis",
    "Category": "ماکتیل",
    "Flavor Description": "ترکیب سیب و پرتقال با چاشنی شهد زنجبیل دست‌ساز اسپایسی",
    "Ingredients": ["سیب", "پرتقال", "شهد زنجبیل"],
    "Price": 133000,
    "Available": true
  },
  {
    "Drink Name": "Orange Cool up",
    "Category": "ماکتیل",
    "Flavor Description": "آب پرتقال طبیعی",
    "Ingredients": ["آب پرتقال"],
    "Price": 117000,
    "Available": true
  },
  {
    "Drink Name": "Red Cool up",
    "Category": "ماکتیل",
    "Flavor Description": "آب هندوانه طبیعی",
    "Ingredients": ["آب هندوانه"],
    "Price": 87000,
    "Available": true
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
