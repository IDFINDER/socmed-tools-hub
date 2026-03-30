# -*- coding: utf-8 -*-
"""
Social Media Tools Hub Bot - Premium Central Hub
"""

import os
import logging
import threading
import secrets
from datetime import datetime, date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton, WebAppInfo
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from supabase import create_client, Client
from flask import Flask, render_template, request, redirect, url_for, session, render_template_string

# ========== متغيرات البيئة ==========
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_ANON_KEY')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'alshabany#772130900')
ADMIN_USERNAMES = os.environ.get('ADMIN_USERNAMES', 'E_Alshabany').split(',')
ADMIN_USERNAMES = [u.strip() for u in ADMIN_USERNAMES]
FREE_LIMIT = int(os.environ.get('FREE_LIMIT', '5'))
RENDER_URL = os.environ.get('RENDER_URL', 'socmed-tools-hub-xprw.onrender.com')
SYSTEM_BOT_NAME = os.environ.get('SYSTEM_BOT_NAME', 'system')
FLASK_SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', secrets.token_hex(32))

if not TELEGRAM_TOKEN or not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ خطأ: تأكد من تعيين المتغيرات المطلوبة")
    exit(1)

# ========== إعدادات logging ==========
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ========== Supabase Setup ==========
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========== بيانات البوتات ==========
BOTS = {
    "thumbnail": {
        "name": "📸 بوت تحميل صور يوتيوب",
        "username": "YouTube_photos_Extractor_bot",
        "icon": "📸",
        "order": 1
    },
    "playlist": {
        "name": "🎬 بوت استخراج روابط يوتيوب",
        "username": "YouTube_Playlist_Extractor_bot",
        "icon": "🎬",
        "order": 2
    },
    "analyzer": {
        "name": "📊 بوت تحليل يوتيوب",
        "username": "YouTube_data_analyzer_bot",
        "icon": "📊",
        "order": 3
    }
}

# ========== نموذج تسجيل الدخول المدمج ==========
LOGIN_FORM = """
<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - لوحة الإدارة</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', 'Tahoma', 'Arial', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .login-card {
            background: white;
            border-radius: 20px;
            padding: 40px;
            width: 100%;
            max-width: 400px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.2);
        }
        .login-card h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 30px;
            font-size: 1.8rem;
        }
        .login-card input {
            width: 100%;
            padding: 12px 15px;
            margin: 10px 0;
            border: 1px solid #e9ecef;
            border-radius: 10px;
            font-size: 1rem;
            font-family: inherit;
            transition: all 0.2s;
        }
        .login-card input:focus {
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
        }
        .login-card button {
            width: 100%;
            padding: 12px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 10px;
            font-size: 1rem;
            cursor: pointer;
            margin-top: 20px;
            transition: all 0.2s;
        }
        .login-card button:hover {
            background: #5a67d8;
            transform: scale(1.02);
        }
        .error {
            background: #fee;
            color: #dc3545;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 15px;
            text-align: center;
        }
        .footer {
            text-align: center;
            margin-top: 20px;
            font-size: 0.8rem;
            color: #6c757d;
        }
    </style>
</head>
<body>
    <div class="login-card">
        <h1>🔐 لوحة الإدارة</h1>
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        <form method="POST">
            <input type="text" name="username" placeholder="اسم المستخدم" required>
            <input type="password" name="password" placeholder="كلمة المرور" required>
            <button type="submit">🚪 دخول</button>
        </form>
        <div class="footer">
            🔒 فقط للمطورين المعتمدين
        </div>
    </div>
</body>
</html>
"""

# ========== دوال قاعدة البيانات ==========

def get_or_create_user(user_id, first_name, username, language_code):
    """
    إنشاء أو تحديث مستخدم في جدول users.
    ينشئ سجل في bot_usage فقط للبوت الرئيسي (system)
    """
    try:
        response = supabase.table('users').select('*').eq('user_id', user_id).execute()
        
        if response.data:
            user = response.data[0]
            if user.get('first_name') != first_name or user.get('username') != username:
                supabase.table('users').update({
                    'first_name': first_name,
                    'username': username or '',
                    'language_code': language_code or ''
                }).eq('user_id', user_id).execute()
                user['first_name'] = first_name
                user['username'] = username
        else:
            new_user = {
                'user_id': user_id,
                'first_name': first_name,
                'username': username or '',
                'language_code': language_code or '',
                'status': 'free'
            }
            response = supabase.table('users').insert(new_user).execute()
            user = response.data[0]
        
        # إنشاء سجل للبوت الرئيسي (system) فقط إذا لم يكن موجوداً
        system_usage = supabase.table('bot_usage').select('*').eq('user_id', user_id).eq('bot_name', SYSTEM_BOT_NAME).execute()
        if not system_usage.data:
            supabase.table('bot_usage').insert({
                'user_id': user_id,
                'bot_name': SYSTEM_BOT_NAME,
                'daily_uses': 0,
                'total_uses': 0,
                'last_use_date': date.today().isoformat(),
                'username': username or '',
                'first_name': first_name
            }).execute()
        
        # جلب استخدامات البوتات الأخرى
        usage_data = {}
        for bot_id in BOTS.keys():
            usage = supabase.table('bot_usage').select('*').eq('user_id', user_id).eq('bot_name', bot_id).execute()
            if usage.data:
                usage_data[bot_id] = usage.data[0]
            else:
                usage_data[bot_id] = {'daily_uses': 0, 'total_uses': 0}
        
        # إضافة استخدام البوت الرئيسي
        system_usage_data = supabase.table('bot_usage').select('*').eq('user_id', user_id).eq('bot_name', SYSTEM_BOT_NAME).execute()
        usage_data[SYSTEM_BOT_NAME] = system_usage_data.data[0] if system_usage_data.data else {'daily_uses': 0, 'total_uses': 0}
        
        return {
            'user_id': user['user_id'],
            'first_name': user['first_name'],
            'username': user['username'],
            'status': user['status'],
            'premium_until': user.get('premium_until'),
            'usage': usage_data
        }
        
    except Exception as e:
        logger.error(f"Error in get_or_create_user: {e}")
        return None

def get_user_info(user_id):
    """جلب معلومات المستخدم مع استخداماته الموجودة فقط"""
    try:
        response = supabase.table('users').select('*').eq('user_id', user_id).execute()
        if response.data:
            user = response.data[0]
            usage_data = {}
            for bot_id in BOTS.keys():
                usage = supabase.table('bot_usage').select('*').eq('user_id', user_id).eq('bot_name', bot_id).execute()
                if usage.data:
                    usage_data[bot_id] = usage.data[0]
                else:
                    usage_data[bot_id] = {'daily_uses': 0, 'total_uses': 0}
            system_usage = supabase.table('bot_usage').select('*').eq('user_id', user_id).eq('bot_name', SYSTEM_BOT_NAME).execute()
            usage_data[SYSTEM_BOT_NAME] = system_usage.data[0] if system_usage.data else {'daily_uses': 0, 'total_uses': 0}
            return {**user, 'usage': usage_data}
        return None
    except Exception as e:
        logger.error(f"Error getting user info: {e}")
        return None

def get_remaining_for_bot(user_id, bot_id):
    """حساب الاستخدامات المتبقية للمستخدم لبوت معين"""
    if bot_id == SYSTEM_BOT_NAME:
        return -1
    user = get_user_info(user_id)
    if not user:
        return FREE_LIMIT
    if user['status'] == 'premium':
        return -1
    usage = user.get('usage', {}).get(bot_id, {})
    daily_uses = usage.get('daily_uses', 0)
    return FREE_LIMIT - daily_uses

# ========== لوحات المفاتيح ==========

def get_main_keyboard():
    keyboard = [
        [KeyboardButton("🎬 البوتات المتاحة"), KeyboardButton("💎 اشتراك مميز")],
        [KeyboardButton("📊 إحصائياتي"), KeyboardButton("❓ المساعدة")]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

def get_bots_inline_keyboard():
    keyboard = []
    for bot_id, bot_info in sorted(BOTS.items(), key=lambda x: x[1]['order']):
        keyboard.append([
            InlineKeyboardButton(
                f"{bot_info['icon']} {bot_info['name']}", 
                url=f"https://t.me/{bot_info['username']}"
            )
        ])
    return InlineKeyboardMarkup(keyboard)

def get_premium_inline_keyboard():
    payment_url = f"https://{RENDER_URL}/payment"
    keyboard = [[InlineKeyboardButton("💎 اشتراك مميز - 10 دولار مدى الحياة", web_app=WebAppInfo(url=payment_url))]]
    return InlineKeyboardMarkup(keyboard)

# ========== أوامر البوت ==========

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    first_name = user.first_name
    
    user_data = get_or_create_user(
        user.id,
        user.first_name,
        user.username or "",
        user.language_code or ""
    )
    
    if not user_data:
        await update.message.reply_text("❌ حدث خطأ، يرجى المحاولة لاحقاً")
        return
    
    status = user_data['status']
    
    if status == 'premium':
        status_text = "مميز"
        limit_text = "جميع البوتات: غير محدود"
    else:
        status_text = "مجاني"
        limit_text = f"الحد اليومي: {FREE_LIMIT} عملية لكل بوت"
    
    welcome_text = (
        f"🌐 مرحباً بك {first_name} في بوت الأدوات الاجتماعية! 🌐\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 حالتك: {status_text}\n"
        f"📊 {limit_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"🎯 ماذا يقدم هذا البوت؟\n"
        f"هو مركز التحكم الرئيسي لجميع بوتاتي المتخصصة في تحميل وتحليل محتوى يوتيوب.\n\n"
        f"📱 البوتات المتاحة:\n\n"
        f"📸 تحميل صور يوتيوب\n"
        f"🎬 استخراج روابط يوتيوب\n"
        f"📊 تحليل بيانات يوتيوب\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"💰 الخطة المجانية:\n"
        f"• {FREE_LIMIT} عملية يومياً لكل بوت\n\n"
        f"💎 الخطة المميزة (10 دولار مدى الحياة):\n"
        f"• استخدام غير محدود لجميع البوتات\n"
        f"• دعم أولوية في المعالجة\n"
        f"• تحديثات حصرية أولاً\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"📌 كيف تستخدم البوت؟\n"
        f"• اضغط على زر 🎬 البوتات المتاحة\n"
        f"• أو استخدم الأزرار أدناه للانتقال مباشرة\n\n"
        f"👨‍💻 المطور: @E_Alshabany"
    )
    await update.message.reply_text(welcome_text, reply_markup=get_main_keyboard())

async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """أمر مخصص للمطورين لفتح لوحة التحكم"""
    user = update.effective_user
    username = user.username
    
    if not username:
        await update.message.reply_text("❌ يرجى تعيين اسم مستخدم (Username) في حسابك أولاً")
        return
    
    if username in ADMIN_USERNAMES:
        keyboard = [[InlineKeyboardButton("🖥️ فتح لوحة التحكم", web_app=WebAppInfo(url=f"https://{RENDER_URL}/admin"))]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "🔐 مرحباً بك في لوحة التحكم\n\n"
            "📌 اضغط على الزر أدناه لفتح لوحة التحكم داخل التطبيق:",
            reply_markup=reply_markup
        )
    else:
        await update.message.reply_text("⛔ غير مصرح لك بالدخول إلى لوحة التحكم")

async def my_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = get_user_info(user_id)
    first_name = update.effective_user.first_name
    
    if not user_info:
        await update.message.reply_text("❌ لم أتمكن من العثور على معلوماتك")
        return
    
    status = user_info['status']
    
    if status == 'premium':
        status_text = "مميز"
        limit_text = "جميع البوتات: غير محدود"
    else:
        status_text = "مجاني"
        limit_text = f"الحد اليومي: {FREE_LIMIT} عملية لكل بوت"
    
    stats_text = (
        f"📊 إحصائياتك الشخصية\n\n"
        f"━━━━━━━━━━━━━━━━━━━━\n"
        f"👤 المستخدم: {first_name}\n"
        f"💎 نوع الخطة: {status_text}\n"
        f"📊 {limit_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━\n\n"
        f"📱 استخدامات اليوم:\n\n"
    )
    
    for bot_id, bot_info in sorted(BOTS.items(), key=lambda x: x[1]['order']):
        remaining = get_remaining_for_bot(user_id, bot_id)
        usage_data = user_info.get('usage', {}).get(bot_id, {})
        daily_uses = usage_data.get('daily_uses', 0)
        
        if remaining == -1:
            stats_text += f"{bot_info['icon']} {bot_info['name']}: غير محدود ✅\n"
        else:
            stats_text += f"{bot_info['icon']} {bot_info['name']}: {daily_uses}/{FREE_LIMIT} (متبقي {remaining})\n"
    
    stats_text += "\n━━━━━━━━━━━━━━━━━━━━\n💎 للاشتراك المميز: اضغط زر 💎 اشتراك مميز"
    await update.message.reply_text(stats_text, reply_markup=get_main_keyboard())

async def premium_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_info = get_user_info(user_id)
    
    if user_info and user_info['status'] == 'premium':
        premium_until = user_info.get('premium_until', '')
        if premium_until:
            expiry = datetime.strptime(premium_until, '%Y-%m-%d').strftime('%Y/%m/%d')
        else:
            expiry = "مدى الحياة"
        
        text = (
            f"👑 أنت مشترك في الخطة المميزة!\n\n"
            f"✅ مميزات الاشتراك المميز:\n"
            f"• استخدام غير محدود لجميع البوتات\n"
            f"• دعم أولوية في المعالجة\n"
            f"• تحديثات حصرية أولاً\n\n"
            f"📅 الاشتراك نشط حتى: {expiry}\n\n"
            f"شكراً لدعمك! 🙏"
        )
        await update.message.reply_text(text, reply_markup=get_main_keyboard())
    else:
        text = (
            f"💎 الاشتراك المميز\n\n"
            f"🎁 مميزات الخطة المميزة:\n"
            f"• ✅ استخدام غير محدود لجميع البوتات\n"
            f"• ✅ دعم أولوية في المعالجة\n"
            f"• ✅ تحديثات حصرية أولاً\n\n"
            f"💰 السعر:\n"
            f"• 10 دولار مدى الحياة\n\n"
            f"📊 حالتك الحالية:\n"
            f"• نوع الخطة: مجانية\n"
            f"• الحد اليومي: {FREE_LIMIT} عملية لكل بوت\n\n"
            f"🔽 للاشتراك، اضغط على الزر أدناه:"
        )
        await update.message.reply_text(text, reply_markup=get_premium_inline_keyboard())

async def available_bots_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "🎬 البوتات المتاحة\n\n📌 اضغط على أي بوت للانتقال مباشرة:"
    await update.message.reply_text(text, reply_markup=get_bots_inline_keyboard())

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        f"🆘 مساعدة بوت الأدوات الاجتماعية\n\n"
        f"🔹 ماذا يمكنني أن أفعل؟\n"
        f"• 🎬 عرض جميع البوتات المتاحة\n"
        f"• 📊 عرض إحصائياتي الشخصية\n"
        f"• 💎 الاشتراك المميز\n\n"
        f"🔹 نظام الاستخدام:\n"
        f"• الخطة المجانية: {FREE_LIMIT} عملية يومياً لكل بوت\n"
        f"• الخطة المميزة: استخدام غير محدود لجميع البوتات\n\n"
        f"🔹 كيف أستخدم البوتات؟\n"
        f"1. اضغط على زر 🎬 البوتات المتاحة\n"
        f"2. اختر البوت الذي تريده\n"
        f"3. استخدم البوت مباشرة\n\n"
        f"📋 الأوامر:\n"
        f"/start - بدء الاستخدام\n"
        f"/help - هذه المساعدة\n"
        f"/about - معلومات عن البوت\n"
        f"/mystats - إحصائياتي الشخصية\n"
        f"/premium - الاشتراك المميز\n\n"
        f"👨‍💻 المطور: @E_Alshabany"
    )
    await update.message.reply_text(help_text, reply_markup=get_main_keyboard())

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    about_text = (
        f"🌐 بوت الأدوات الاجتماعية - Social Media Tools Hub\n\n"
        f"🎯 الإصدار: 2.0 (مركز التحكم الرئيسي)\n\n"
        f"✨ الرؤية:\n"
        f"مركز واحد يجمع جميع أدوات تحميل وتحليل محتوى منصات التواصل الاجتماعي.\n\n"
        f"✅ المميزات:\n"
        f"• واجهة موحدة للوصول لجميع البوتات\n"
        f"• نظام اشتراك موحد لجميع البوتات\n"
        f"• إحصائيات شخصية لحالة استخدامك\n"
        f"• تحديثات مستمرة بإضافة بوتات جديدة\n\n"
        f"📱 البوتات الحالية:\n"
        f"• 📸 بوت تحميل صور يوتيوب\n"
        f"• 🎬 بوت استخراج روابط يوتيوب\n"
        f"• 📊 بوت تحليل يوتيوب\n\n"
        f"💰 نظام الاشتراك:\n"
        f"• مجاني: {FREE_LIMIT} عملية يومياً لكل بوت\n"
        f"• مميز: 10 دولار مدى الحياة - استخدام غير محدود\n\n"
        f"👨‍💻 المطور: @E_Alshabany\n"
        f"🚀 تم النشر على Render - 2026"
    )
    await update.message.reply_text(about_text, reply_markup=get_main_keyboard())

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "main_menu":
        await start_command(update, context)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if text == "🎬 البوتات المتاحة":
        await available_bots_command(update, context)
    elif text == "💎 اشتراك مميز":
        await premium_command(update, context)
    elif text == "📊 إحصائياتي":
        await my_stats_command(update, context)
    elif text == "❓ المساعدة":
        await help_command(update, context)
    else:
        await update.message.reply_text(
            "❓ عذراً، لم أتعرف على طلبك.\n\n"
            "📌 يمكنك استخدام الأزرار أدناه أو إرسال /help للمساعدة.",
            reply_markup=get_main_keyboard()
        )

# ========== Flask Routes ==========

app = Flask(__name__)
app.secret_key = FLASK_SECRET_KEY

@app.route('/')
@app.route('/health')
@app.route('/healthcheck')
def health():
    return "OK", 200

@app.route('/payment')
def payment_page():
    return render_template('payment.html', free_limit=FREE_LIMIT)

@app.route('/admin', methods=['GET', 'POST'])
def admin_panel():
    # التحقق من تسجيل الدخول عبر النموذج المدمج
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if password == ADMIN_PASSWORD and username in ADMIN_USERNAMES:
            session['admin_logged_in'] = True
            session['admin_username'] = username
            return redirect(url_for('admin_panel'))
        else:
            return render_template_string(LOGIN_FORM, error="❌ اسم المستخدم أو كلمة المرور غير صحيحة")
    
    # التحقق من وجود جلسة نشطة
    if not session.get('admin_logged_in'):
        return render_template_string(LOGIN_FORM)
    
    try:
        users = supabase.table('users').select('*').execute()
        
        bot_usage_thumbnail = supabase.table('bot_usage').select('*').eq('bot_name', 'thumbnail').execute()
        bot_usage_playlist = supabase.table('bot_usage').select('*').eq('bot_name', 'playlist').execute()
        bot_usage_analyzer = supabase.table('bot_usage').select('*').eq('bot_name', 'analyzer').execute()
        
        usage_thumbnail_dict = {u['user_id']: u for u in bot_usage_thumbnail.data}
        usage_playlist_dict = {u['user_id']: u for u in bot_usage_playlist.data}
        usage_analyzer_dict = {u['user_id']: u for u in bot_usage_analyzer.data}
        
        total_uses_photos = sum(u.get('total_uses', 0) for u in bot_usage_thumbnail.data)
        total_uses_playlist = sum(u.get('total_uses', 0) for u in bot_usage_playlist.data)
        total_uses_analyzer = sum(u.get('total_uses', 0) for u in bot_usage_analyzer.data)
        
        today = date.today()
        daily_stats = []
        for i in range(6, -1, -1):
            target_date = today - timedelta(days=i)
            date_str = target_date.strftime('%Y-%m-%d')
            
            thumbnail_daily = sum(1 for u in bot_usage_thumbnail.data if u.get('last_use_date') == date_str)
            playlist_daily = sum(1 for u in bot_usage_playlist.data if u.get('last_use_date') == date_str)
            analyzer_daily = sum(1 for u in bot_usage_analyzer.data if u.get('last_use_date') == date_str)
            
            daily_stats.append({
                'date': target_date.strftime('%d/%m/%Y'),
                'thumbnail': thumbnail_daily,
                'playlist': playlist_daily,
                'analyzer': analyzer_daily,
                'total': thumbnail_daily + playlist_daily + analyzer_daily
            })
        
        users_list = []
        premium_count = 0
        free_count = 0
        
        for user in users.data:
            usage_thumbnail = usage_thumbnail_dict.get(user['user_id'], {})
            usage_playlist = usage_playlist_dict.get(user['user_id'], {})
            usage_analyzer = usage_analyzer_dict.get(user['user_id'], {})
            
            first_name = user.get('first_name', '-')
            username = user.get('username', '-')
            
            daily_thumbnail = usage_thumbnail.get('daily_uses', 0)
            daily_playlist = usage_playlist.get('daily_uses', 0)
            daily_analyzer = usage_analyzer.get('daily_uses', 0)
            
            if user['status'] == 'premium':
                premium_count += 1
            else:
                free_count += 1
            
            users_list.append({
                'user_id': user['user_id'],
                'first_name': first_name,
                'username': username,
                'status': user['status'],
                'premium_until': user.get('premium_until', '-'),
                'usage': {
                    'thumbnail': daily_thumbnail,
                    'playlist': daily_playlist,
                    'analyzer': daily_analyzer
                }
            })
        
        today_str = str(date.today())
        active_users = set()
        for u in bot_usage_thumbnail.data:
            if u.get('last_use_date') == today_str:
                active_users.add(u['user_id'])
        for u in bot_usage_playlist.data:
            if u.get('last_use_date') == today_str:
                active_users.add(u['user_id'])
        for u in bot_usage_analyzer.data:
            if u.get('last_use_date') == today_str:
                active_users.add(u['user_id'])
        
        stats = {
            'total_users': len(users.data),
            'premium_users': premium_count,
            'free_users': free_count,
            'total_uses': total_uses_photos + total_uses_playlist + total_uses_analyzer,
            'total_uses_photos': total_uses_photos,
            'total_uses_playlist': total_uses_playlist,
            'total_uses_analyzer': total_uses_analyzer,
            'active_today': len(active_users),
            'last_update': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return render_template('admin.html', users=users_list, stats=stats, daily_stats=daily_stats, free_limit=FREE_LIMIT)
    
    except Exception as e:
        logger.error(f"Admin panel error: {e}")
        return f"خطأ في لوحة التحكم: {str(e)}", 500

@app.route('/upgrade-user', methods=['POST'])
def upgrade_user():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))
    
    try:
        user_id = int(request.form.get('user_id'))
        until_date = date.today() + timedelta(days=3650)
        
        supabase.table('users').update({
            'status': 'premium',
            'premium_until': until_date.isoformat()
        }).eq('user_id', user_id).execute()
        
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"خطأ: {e}", 500

@app.route('/downgrade-user', methods=['POST'])
def downgrade_user():
    if not session.get('admin_logged_in'):
        return redirect(url_for('admin_panel'))
    
    try:
        user_id = int(request.form.get('user_id'))
        
        supabase.table('users').update({
            'status': 'free',
            'premium_until': None
        }).eq('user_id', user_id).execute()
        
        return redirect(url_for('admin_panel'))
    except Exception as e:
        return f"خطأ: {e}", 500

@app.route('/reset-daily')
def reset_daily_endpoint():
    try:
        supabase.rpc('reset_daily_usage').execute()
        return "Daily usage reset completed", 200
    except Exception as e:
        logger.error(f"Reset daily error: {e}")
        return f"Error: {e}", 500

# ========== تشغيل Flask ==========
PORT = int(os.environ.get('PORT', 10000))

def run_flask():
    app.run(host='0.0.0.0', port=PORT, debug=False)

threading.Thread(target=run_flask, daemon=True).start()

# ========== الدالة الرئيسية ==========

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("about", about_command))
    application.add_handler(CommandHandler("mystats", my_stats_command))
    application.add_handler(CommandHandler("premium", premium_command))
    application.add_handler(CommandHandler("admin", admin_command))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_callback))
    
    print("="*60)
    print("🌐 Social Media Tools Hub Bot - Premium Central Hub")
    print("🤖 @SocMed_tools_bot")
    print("✅ أوامر: /start /help /about /mystats /premium /admin")
    print(f"✅ نظام الاشتراك: مجاني {FREE_LIMIT} عملية/بوت - مميز غير محدود")
    print("✅ صفحة الدفع: /payment")
    print("✅ لوحة الإدارة: /admin (نموذج تسجيل دخول مدمج)")
    print(f"✅ المطورين المسموح لهم: {', '.join(ADMIN_USERNAMES)}")
    print("="*60)
    
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
