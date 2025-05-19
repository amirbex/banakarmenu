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
GOOGLE_API_KEY = 'AIzaSyDOwvn30o1OdXf2KFxZPkYwXSqBqerpQ3A'
genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")

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
    response = await model.generate_content(prompt)  # با await
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
    # پرامپت مشخص برای مسیر منو
    prompt = f"کاربر دنبال نوشیدنی با این مشخصاته: {request}\nبا توجه به لیست منو زیر، فقط اسم و ویژگی آیتم‌های مناسب رو بگو:\n" + '\n'.join([f"- {item['Drink Name']} ({item['Flavor Description']})" for item in sample_menu])
    thinking_msg = await send_typing_thinking(update)
    try:
        response = model.generate_content(prompt)
        result = response.candidates[0].content.parts[0].text
        await thinking_msg.delete()
        await send_chunked_text(result, update)
    except:
        await thinking_msg.delete()
        await update.message.reply_text("متأسفم، نتونستم پیشنهادی از منو پیدا کنم.")

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
        {"Drink Name": "Iced Americano", "Flavor Description": "تلخ، خنک، انرژی‌بخش"},
        {"Drink Name": "CocoMoco Frappe", "Flavor Description": "شیرین، شکلاتی، خامه‌ای"},
        {"Drink Name": "Passion Mojito", "Flavor Description": "ترش، شیرین، پَشن‌فروتی"},
    ]

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Regex("^🥼 نوشیدنی ابداعی$"), custom_drink_entry))
    app.add_handler(MessageHandler(filters.Regex("^📋 راهنمای منو$"), handle_menu_intro))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, dynamic_handler))
    
    app.run_polling()

if __name__ == '__main__':
    main()
