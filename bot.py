import os
import sqlite3
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

# =========================================================
# إعدادات البوت - Environment Variables & DB Path
# =========================================================

BOT_TOKEN = "8847079099:AAH_2MNnmSCwf0Fapmc2bHisjZNE496Lp7M"

if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is missing")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_NAME = os.path.join(BASE_DIR, "orders.db")

PAYMENT_METHOD = "E& Money"
WALLET_NUMBER = "01149818351"
WALLET_OWNER = "محمد"

WAITING_NAME = 1
WAITING_PLAYER_ID = 2
WAITING_RECEIPT = 3

# =========================================================
# قاعدة البيانات
# =========================================================

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_products_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            product_type TEXT NOT NULL DEFAULT 'game',
            description TEXT DEFAULT '',
            image TEXT DEFAULT '',
            active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS packages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            name TEXT NOT NULL,
            price REAL NOT NULL DEFAULT 0,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
        )
    """)

    # ضمان تفعيل جميع المنتجات والباقات الموجودة
    conn.execute("UPDATE products SET active = 1 WHERE active = 0")
    conn.execute("UPDATE packages SET active = 1 WHERE active = 0")

    conn.commit()
    conn.close()

def get_products():
    conn = get_db()
    products = conn.execute("""
        SELECT *
        FROM products
        WHERE active = 1
        ORDER BY id ASC
    """).fetchall()
    conn.close()
    return products

def get_product(product_id):
    conn = get_db()
    product = conn.execute("""
        SELECT *
        FROM products
        WHERE id = ? AND active = 1
    """, (product_id,)).fetchone()
    conn.close()
    return product

def get_packages(product_id):
    conn = get_db()
    packages = conn.execute("""
        SELECT *
        FROM packages
        WHERE product_id = ? AND active = 1
        ORDER BY id ASC
    """, (product_id,)).fetchall()
    conn.close()
    return packages

def get_package(package_id):
    conn = get_db()
    package = conn.execute("""
        SELECT packages.*, products.name AS product_name
        FROM packages
        JOIN products ON products.id = packages.product_id
        WHERE packages.id = ? AND packages.active = 1 AND products.active = 1
    """, (package_id,)).fetchone()
    conn.close()
    return package

def create_database():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL,
            username TEXT,
            customer_name TEXT NOT NULL,
            game TEXT NOT NULL,
            package TEXT NOT NULL,
            original_price REAL NOT NULL,
            final_price REAL NOT NULL,
            player_id TEXT NOT NULL,
            receipt_file_id TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER NOT NULL DEFAULT 0,
            order_id INTEGER,
            sender TEXT NOT NULL,
            message_type TEXT NOT NULL DEFAULT 'text',
            message_text TEXT,
            text TEXT,
            telegram_message_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()

def save_message(telegram_id, sender, message_type, message_text=None, telegram_message_id=None, order_id=None):
    conn = get_db()
    conn.execute(
        """
        INSERT INTO messages (telegram_id, order_id, sender, message_type, message_text, text, telegram_message_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            telegram_id,
            order_id,
            sender,
            message_type,
            message_text,
            message_text,
            telegram_message_id,
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )
    )
    conn.commit()
    conn.close()

def add_profit(price):
    price = float(price)
    if price < 50:
        profit = 10
    elif price < 100:
        profit = 15
    else:
        profit = 20
    return price + profit

# =========================================================
# الواجهات
# =========================================================

def main_menu():
    products = get_products()
    keyboard = []

    for product in products:
        keyboard.append([
            InlineKeyboardButton(product["name"], callback_data=f"game|{product['id']}")
        ])

    keyboard.append([InlineKeyboardButton("📋 سجل الشحن", callback_data="history")])
    keyboard.append([InlineKeyboardButton("🔜 المزيد قريبًا إن شاء الله", callback_data="soon")])

    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user

    if update.message:
        save_message(
            telegram_id=user.id,
            sender="customer",
            message_type="command",
            message_text="/start",
            telegram_message_id=update.message.message_id
        )

        await update.message.reply_text(
            "أهلاً بيك 👋\n\n🎮 اختار اللعبة اللي عايز تشحن لها:",
            reply_markup=main_menu()
        )

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.message:
        save_message(
            telegram_id=user.id,
            sender="customer",
            message_type="command",
            message_text="/info",
            telegram_message_id=update.message.message_id
        )
        text = (
            "RayyanElnahas\n"
            "Whatsapp : +201149818351\n"
            "Tiktok : priv_re1\n"
            "Instagram : mxr_911\n"
            "Telegram : @RayyanElnahas1\n"
        )
        await update.message.reply_text(text)

async def bs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if update.message:
        save_message(
            telegram_id=user.id,
            sender="customer",
            message_type="command",
            message_text="/bs",
            telegram_message_id=update.message.message_id
        )
        text = (
            "Mohamed Elashey\n"
            "Whatsapp : +201036359353\n"
            "Tiktok : elashry134"
        )
        await update.message.reply_text(text)

async def game_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    product_id = int(query.data.split("|", 1)[1])
    product = get_product(product_id)

    if not product:
        await query.edit_message_text("⚠️ المنتج غير موجود أو غير متاح حاليًا.")
        return

    context.user_data["product_id"] = product["id"]
    context.user_data["game_name"] = product["name"]

    packages = get_packages(product["id"])

    if not packages:
        await query.edit_message_text(
            f"{product['name']}\n\n⚠️ لا توجد باقات متاحة لهذا المنتج حاليًا.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back")]])
        )
        return

    buttons = []
    for package in packages:
        final_price = add_profit(package["price"])
        buttons.append([
            InlineKeyboardButton(
                f"{package['name']} — {final_price:g} جنيه",
                callback_data=f"package|{package['id']}"
            )
        ])

    buttons.append([InlineKeyboardButton("⬅️ رجوع", callback_data="back")])

    await query.edit_message_text(
        f"{product['name']}\n\nاختار الباقة اللي عايز تشحنها:",
        reply_markup=InlineKeyboardMarkup(buttons)
    )

async def package_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    package_id = int(query.data.split("|", 1)[1])
    package = get_package(package_id)

    if not package:
        await query.edit_message_text("⚠️ الباقة غير موجودة أو لم تعد متاحة.")
        return ConversationHandler.END

    original_price = float(package["price"])
    final_price = add_profit(original_price)

    context.user_data["package_id"] = package["id"]
    context.user_data["package"] = package["name"]
    context.user_data["original_price"] = original_price
    context.user_data["final_price"] = final_price

    await query.edit_message_text(
        f"✅ اخترت:\n"
        f"{package['product_name']}\n"
        f"📦 {package['name']}\n"
        f"💰 السعر: {final_price:g} جنيه\n\n"
        "👤 من فضلك اكتب اسمك."
    )
    return WAITING_NAME

async def receive_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text.strip()
    user = update.effective_user

    save_message(
        telegram_id=user.id,
        sender="customer",
        message_type="text",
        message_text=name,
        telegram_message_id=update.message.message_id
    )

    if len(name) < 2:
        await update.message.reply_text("⚠️ من فضلك اكتب اسمك بشكل صحيح.")
        return WAITING_NAME

    context.user_data["customer_name"] = name
    await update.message.reply_text(f"تمام يا {name} ❤️\n\n🎮 دلوقتي ابعتلي ID اللاعب بتاعك.")
    return WAITING_PLAYER_ID

async def receive_player_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    player_id = update.message.text.strip()
    user = update.effective_user

    save_message(
        telegram_id=user.id,
        sender="customer",
        message_type="text",
        message_text=player_id,
        telegram_message_id=update.message.message_id
    )

    if len(player_id) < 2:
        await update.message.reply_text("⚠️ الـID اللي كتبته قصير جدًا.\nمن فضلك ابعت ID اللاعب الصحيح.")
        return WAITING_PLAYER_ID

    context.user_data["player_id"] = player_id
    final_price = context.user_data["final_price"]

    await update.message.reply_text(
        "✅ تم استلام بيانات اللاعب.\n\n"
        "💳 مرحلة الدفع\n\n"
        f"🎮 اللعبة: {context.user_data['game_name']}\n"
        f"📦 الباقة: {context.user_data['package']}\n"
        f"🆔 ID اللاعب: {player_id}\n"
        f"💰 المبلغ المطلوب: {final_price:g} جنيه\n\n"
        f"🏦 طريقة الدفع: {PAYMENT_METHOD}\n"
        f"📱 رقم المحفظة: {WALLET_NUMBER}\n"
        f"👤 اسم صاحب المحفظة: {WALLET_OWNER}\n\n"
        "بعد التحويل، ابعت هنا صورة إيصال الدفع 📸"
    )
    return WAITING_RECEIPT

async def receive_receipt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not update.message.photo:
        save_message(
            telegram_id=user.id,
            sender="customer",
            message_type="other",
            message_text="رسالة غير صورة أثناء انتظار الإيصال",
            telegram_message_id=update.message.message_id
        )
        await update.message.reply_text("⚠️ من فضلك ابعت صورة إيصال الدفع.")
        return WAITING_RECEIPT

    photo = update.message.photo[-1]
    telegram_id = user.id
    username = user.username or ""

    customer_name = context.user_data["customer_name"]
    game_name = context.user_data["game_name"]
    package = context.user_data["package"]
    original_price = context.user_data["original_price"]
    final_price = context.user_data["final_price"]
    player_id = context.user_data["player_id"]
    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    conn = get_db()
    cursor = conn.execute(
        """
        INSERT INTO orders (telegram_id, username, customer_name, game, package, original_price, final_price, player_id, receipt_file_id, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (telegram_id, username, customer_name, game_name, package, original_price, final_price, player_id, photo.file_id, "pending", created_at)
    )
    order_id = cursor.lastrowid
    conn.commit()
    conn.close()

    save_message(
        telegram_id=telegram_id,
        sender="customer",
        message_type="photo",
        message_text="صورة إيصال الدفع",
        telegram_message_id=update.message.message_id,
        order_id=order_id
    )

    await update.message.reply_text(
        f"✅ تم استلام طلبك بنجاح.\n\n"
        f"🧾 رقم الطلب: #{order_id}\n"
        f"🎮 اللعبة: {game_name}\n"
        f"📦 الباقة: {package}\n"
        f"🆔 ID اللاعب: {player_id}\n"
        f"💰 المبلغ: {final_price:g} جنيه\n\n"
        "⏳ طلبك الآن قيد المراجعة.\n"
        "من فضلك انتظر تأكيد الدفع."
    )

    context.user_data.clear()
    return ConversationHandler.END

async def history(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = query.from_user.id
    conn = get_db()
    orders = conn.execute(
        "SELECT * FROM orders WHERE telegram_id = ? ORDER BY id DESC",
        (telegram_id,)
    ).fetchall()
    conn.close()

    if not orders:
        await query.edit_message_text(
            "📋 سجل الشحن\n\nلسه مفيش طلبات شحن مسجلة عندك.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back")]])
        )
        return

    total_spent = sum(order["final_price"] for order in orders)
    text = f"📋 سجل الشحن الخاص بك\n\n🔢 عدد الطلبات: {len(orders)}\n💰 إجمالي المبالغ: {total_spent:g} جنيه\n\n"

    status_names = {
        "pending": "⏳ قيد المراجعة",
        "paid": "💳 تم تأكيد الدفع",
        "shipped": "✅ تم الشحن",
        "rejected": "❌ مرفوض",
    }

    for order in orders[:10]:
        status = status_names.get(order["status"], order["status"])
        text += (
            f"🧾 الطلب #{order['id']}\n"
            f"🎮 {order['game']}\n"
            f"📦 {order['package']}\n"
            f"💰 {order['final_price']:g} جنيه\n"
            f"📅 {order['created_at']}\n"
            f"📌 الحالة: {status}\n\n"
        )

    await query.edit_message_text(
        text,
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back")]])
    )

async def soon(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🔜 المزيد من الألعاب قريبًا إن شاء الله ❤️",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ رجوع", callback_data="back")]])
    )

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🎮 اختار اللعبة اللي عايز تشحن لها:",
        reply_markup=main_menu()
    )

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ تم إلغاء الطلب.\n\nاكتب /start لو عايز تبدأ طلب جديد.")
    return ConversationHandler.END

def main():
    create_database()
    init_products_db()

    application = Application.builder().token(BOT_TOKEN).build()

    conversation_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(package_selected, pattern=r"^package\|")],
        states={
            WAITING_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name)],
            WAITING_PLAYER_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_player_id)],
            WAITING_RECEIPT: [MessageHandler(filters.PHOTO, receive_receipt)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_message=False,
    )

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("bs", bs_command))

    application.add_handler(CallbackQueryHandler(game_selected, pattern=r"^game\|"))
    application.add_handler(CallbackQueryHandler(history, pattern=r"^history$"))
    application.add_handler(CallbackQueryHandler(soon, pattern=r"^soon$"))
    application.add_handler(CallbackQueryHandler(back, pattern=r"^back$"))

    application.add_handler(conversation_handler)

    print("Bot is starting via Polling...")
    application.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()