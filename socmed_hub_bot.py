# -*- coding: utf-8 -*-
"""
Social Media Tools Hub Bot
Main hub for all social media tools and bots
"""

import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ========== إعدادات Flask للـ Health Check ==========
from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
@app.route('/health')
@app.route('/healthcheck')
def health():
    return "OK", 200

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))

threading.Thread(target=run_flask, daemon=True).start()
# ==================================================

# ========== متغيرات البيئة ==========
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
YOUTUBE_API_KEY = os.environ.get('YOUTUBE_API_KEY')  # للاستخدام المستقبلي

if not TELEGRAM_TOKEN:
    print("❌ خطأ: تأكد من تعيين متغير البيئة TELEGRAM_TOKEN")
    exit(1)
# ==================================

# إعدادات logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ==================== بيانات البوتات ====================
# يمكن إضافة بوتات جديدة هنا بسهولة
BOTS = {
    "youtube_playlist": {
        "name": "🎬 بوت استخراج روابط يوتيوب",
        "username": "YouTube_Playlist_Extractor_bot",
        "description": "استخراج جميع روابط قوائم التشغيل والقنوات مع إرسال ملف نصي منظم",
        "features": [
            "✅ استخراج روابط قوائم التشغيل",
            "✅ جلب فيديوهات القنوات كاملة",
            "✅ عرض عناوين الفيديوهات",
            "✅ إرسال ملف نصي بالنتائج"
        ],
        "icon": "🎬",
        "order": 1
    },
    "youtube_thumbnail": {
        "name": "📸 بوت تحميل صور يوتيوب",
        "username": "YouTube_photos_Extractor_bot",
        "description": "تحميل صور الفيديوهات (Thumbnails) بأعلى جودة متاحة",
        "features": [
            "✅ تحميل صور بدقة تصل إلى 1080p",
            "✅ دعم الروابط المتعددة",
            "✅ عرض عنوان الفيديو مع الصورة",
            "✅ معالجة متسلسلة مع عرض التقدم"
        ],
        "icon": "📸",
        "order": 2
    },
    "youtube_analyzer": {
        "name": "📊 بوت تحليل يوتيوب",
        "username": "YouTube_data_analyzer_bot",
        "description": "تحليل إحصائيات الفيديوهات والقنوات بشكل متقدم",
        "features": [
            "✅ تحليل كامل للفيديوهات",
            "✅ إحصائيات القنوات الشاملة",
            "✅ عرض أفضل التعليقات",
            "✅ إرسال ملف نصي بالتحليل"
        ],
        "icon": "📊",
        "order": 3
    }
    # يمكن إضافة بوتات جديدة هنا مستقبلاً:
    # "instagram": {
    #     "name": "📷 بوت تحميل انستقرام",
    #     "username": "Instagram_Downloader_bot",
    #     "description": "تحميل فيديوهات وصور انستقرام",
    #     "features": ["✅ تحميل فيديوهات", "✅ تحميل صور", "✅ دعم الـ Reels"],
    #     "icon": "📷",
    #     "order": 4
    # },
    # "twitter": {
    #     "name": "🐦 بوت تحميل تويتر",
    #     "username": "Twitter_Downloader_bot",
    #     "description": "تحميل فيديوهات وصور تويتر",
    #     "features": ["✅ تحميل فيديوهات", "✅ تحميل صور", "✅ دعم التغريدات"],
    #     "icon": "🐦",
    #     "order": 5
    # }
}

# ==================== لوحة المفاتيح السريعة ====================

def get_main_keyboard():
    """لوحة المفاتيح الرئيسية"""
    keyboard = [
        [KeyboardButton("🎬 البوتات المتاحة"), KeyboardButton("ℹ️ عن البوت")],
        [KeyboardButton("❓ المساعدة"), KeyboardButton("📊 الإحصائيات")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_bots_inline_keyboard():
    """أزرار مضمنة للبوتات"""
    keyboard = []
    # ترتيب البوتات حسب order
    sorted_bots = sorted(BOTS.items(), key=lambda x: x[1]['order'])
    for bot_id, bot_info in sorted_bots:
        keyboard.append([
            InlineKeyboardButton(
                f"{bot_info['icon']} {bot_info['name']}", 
                url=f"https://t.me/{bot_info['username']}"
            )
        ])
    return InlineKeyboardMarkup(keyboard)

def get_bot_details_inline(bot_id):
    """أزرار مضمنة لبوت معين"""
    bot_info = BOTS.get(bot_id)
    if not bot_info:
        return None
    keyboard = [
        [InlineKeyboardButton("🚀 فتح البوت", url=f"https://t.me/{bot_info['username']}")],
        [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)

# ==================== الإحصائيات ====================

def get_stats():
    """إحصائيات البوت الرئيسي"""
    total_bots = len(BOTS)
    youtube_bots = sum(1 for b in BOTS.values() if 'يوتيوب' in b['name'] or 'YouTube' in b['name'])
    
    stats_text = f"""
📊 **إحصائيات بوت الأدوات الاجتماعية**

━━━━━━━━━━━━━━━━━━━━
🤖 **عدد البوتات:** {total_bots}
🎬 **بوتات يوتيوب:** {youtube_bots}
🚀 **قيد التطوير:** {0}

━━━━━━━━━━━━━━━━━━━━
✅ **البوتات المتاحة:**
"""
    for bot_id, bot_info in sorted(BOTS.items(), key=lambda x: x[1]['order']):
        stats_text += f"\n{bot_info['icon']} {bot_info['name']}\n   👤 @{bot_info['username']}"
    
    stats_text += "\n\n━━━━━━━━━━━━━━━━━━━━\n🔄 **آخر تحديث:** مارس 2026\n👨‍💻 **المطور:** @alshabany8"
    
    return stats_text

# ==================== أوامر البوت ====================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """رسالة الترحيب"""
    welcome_text = """
🌐 **مرحباً بك في بوت الأدوات الاجتماعية!** 🌐

🎯 **ماذا يقدم هذا البوت؟**
هو مركز التحكم الرئيسي لجميع بوتاتي المتخصصة في تحميل وتحليل محتوى منصات التواصل الاجتماعي.

📱 **البوتات المتاحة حالياً:**

🎬 **يوتيوب - استخراج روابط**
`@YouTube_Playlist_Extractor_bot`
استخراج روابط قوائم التشغيل والقنوات مع ملف نصي منظم

📸 **يوتيوب - تحميل الصور**
`@YouTube_photos_Extractor_bot`
تحميل صور الفيديوهات بأعلى جودة (حتى 1080p)

📊 **يوتيوب - تحليل البيانات**
`@YouTube_data_analyzer_bot`
تحليل إحصائيات الفيديوهات والقنوات بشكل متقدم

━━━━━━━━━━━━━━━━━━━━
🚀 **قريباً:**
• 📷 بوت تحميل انستقرام
• 🐦 بوت تحميل تويتر
• 📘 بوت تحميل فيسبوك

━━━━━━━━━━━━━━━━━━━━
📌 **كيف تستخدم البوت؟**
• اضغط على زر 🎬 البوتات المتاحة
• أو استخدم الأزرار أدناه للانتقال مباشرة

👨‍💻 **المطور:** @alshabany8
"""
    await update.message.reply_text(welcome_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """تعليمات المساعدة"""
    help_text = """
🆘 **مساعدة بوت الأدوات الاجتماعية**

🔹 **ماذا يمكنني أن أفعل؟**
• 🎬 عرض جميع البوتات المتاحة
• 📊 عرض إحصائيات البوتات
• ℹ️ معلومات عن البوت الرئيسي

🔹 **كيف أستخدم البوتات؟**
1. اضغط على زر 🎬 البوتات المتاحة
2. اختر البوت الذي تريده
3. اضغط على الزر للانتقال مباشرة

🔹 **البوتات المتاحة حالياً:**
• 🎬 بوت استخراج روابط يوتيوب
• 📸 بوت تحميل صور يوتيوب
• 📊 بوت تحليل يوتيوب

📋 **الأوامر:**
/start - بدء الاستخدام
/help - هذه المساعدة
/about - معلومات عن البوت
/stats - إحصائيات البوتات

👨‍💻 **المطور:** @alshabany8
"""
    await update.message.reply_text(help_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معلومات عن البوت"""
    about_text = """
🌐 **بوت الأدوات الاجتماعية - Social Media Tools Hub**

🎯 **الإصدار:** 1.0 (مركز التحكم الرئيسي)

✨ **الرؤية:**
مركز واحد يجمع جميع أدوات تحميل وتحليل محتوى منصات التواصل الاجتماعي.

✅ **المميزات:**
• واجهة موحدة للوصول لجميع البوتات
• تحديثات مستمرة بإضافة بوتات جديدة
• سهولة التنقل بين الأدوات المختلفة

📱 **البوتات الحالية:**
• 🎬 استخراج روابط يوتيوب
• 📸 تحميل صور يوتيوب
• 📊 تحليل إحصائيات يوتيوب

🚀 **قيد التطوير:**
• 📷 بوت انستقرام (قريباً)
• 🐦 بوت تويتر (قريباً)
• 📘 بوت فيسبوك (قريباً)

👨‍💻 **المطور:** Ibrahim Alshabany
📧 **البريد:** central.app.ye@gmail.com
📱 **إنستغرام:** @ebrahim_alshabany

🚀 **تم النشر على Render - 2026**
"""
    await update.message.reply_text(about_text, parse_mode='Markdown', reply_markup=get_main_keyboard())

async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """إحصائيات البوتات"""
    await update.message.reply_text(get_stats(), parse_mode='Markdown', reply_markup=get_main_keyboard())

async def available_bots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """عرض البوتات المتاحة"""
    text = """
🎬 **البوتات المتاحة**

📌 اضغط على أي بوت للانتقال مباشرة:
"""
    await update.message.reply_text(text, parse_mode='Markdown', reply_markup=get_bots_inline_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة الأزرار المضمنة"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "main_menu":
        text = """
🌐 **القائمة الرئيسية**

📌 اختر ما تريد:
• 🎬 البوتات المتاحة - لعرض جميع البوتات
• ℹ️ عن البوت - معلومات عن المشروع
• 📊 الإحصائيات - عدد البوتات المتاحة
• ❓ المساعدة - تعليمات الاستخدام
"""
        await query.edit_message_text(text, parse_mode='Markdown', reply_markup=get_main_keyboard())
        return
    
    # عرض تفاصيل بوت معين إذا كان المعرف موجوداً
    for bot_id, bot_info in BOTS.items():
        if data == f"bot_{bot_id}":
            details = f"""
{bot_info['icon']} **{bot_info['name']}**

📝 **الوصف:**
{bot_info['description']}

✨ **المميزات:**
{chr(10).join(bot_info['features'])}

👤 **المعرف:** @{bot_info['username']}

━━━━━━━━━━━━━━━━━━━━
🚀 اضغط الزر أدناه لفتح البوت مباشرة
"""
            await query.edit_message_text(details, parse_mode='Markdown', reply_markup=get_bot_details_inline(bot_id))
            return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة رسائل المستخدم"""
    text = update.message.text.strip()
    
    # معالجة الأزرار
    if text == "🎬 البوتات المتاحة":
        await available_bots_command(update, context)
    elif text == "ℹ️ عن البوت":
        await about_command(update, context)
    elif text == "❓ المساعدة":
        await help_command(update, context)
    elif text == "📊 الإحصائيات":
        await stats_command(update, context)
    else:
        await update.message.reply_text(
            "❓ **عذراً، لم أتعرف على طلبك.**\n\n"
            "📌 يمكنك استخدام الأزرار أدناه أو إرسال /help للمساعدة.",
            parse_mode='Markdown',
            reply_markup=get_main_keyboard()
        )

# ==================== الدالة الرئيسية ====================

def main():
    """تشغيل البوت"""
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # إضافة المعالجات
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("="*60)
    print("🌐 Social Media Tools Hub Bot")
    print("🤖 @SocMed_tools_bot")
    print("✅ أوامر: /start /help /about /stats")
    print("✅ البوتات المتاحة: " + ", ".join([b['name'] for b in BOTS.values()]))
    print("✅ تم النشر على Render مع Health Check")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()