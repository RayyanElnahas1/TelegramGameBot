import os
import psycopg2
from psycopg2.extras import RealDictCursor
import requests
from flask import Flask, render_template, request, redirect, url_for, send_file

app = Flask(__name__, template_folder='templates', static_folder='static')

BOT_TOKEN = os.getenv("BOT_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn

def init_products_db():
    if not DATABASE_URL:
        return
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY,
        name VARCHAR(255) NOT NULL,
        product_type VARCHAR(50) NOT NULL DEFAULT 'game',
        description TEXT DEFAULT '',
        image TEXT DEFAULT '',
        active INT NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS packages (
        id SERIAL PRIMARY KEY,
        product_id INT NOT NULL,
        name VARCHAR(255) NOT NULL,
        price REAL NOT NULL DEFAULT 0,
        active INT NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY,
        telegram_id BIGINT NOT NULL DEFAULT 0,
        order_id INT,
        sender VARCHAR(50) NOT NULL,
        message_type VARCHAR(50) NOT NULL DEFAULT 'text',
        message_text TEXT,
        text TEXT,
        telegram_message_id BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    cursor.close()
    conn.close()

def send_telegram_notification(chat_id, text):
    if not BOT_TOKEN:
        print("BOT_TOKEN is missing. Notification not sent.")
        return
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send Telegram message: {e}")

def get_orders():
    conn = get_db()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT * FROM orders ORDER BY id DESC")
        orders = cursor.fetchall()
        return orders
    finally:
        cursor.close()
        conn.close()

@app.route("/")
def dashboard():
    orders = get_orders()
    return render_template("dashboard.html", orders=orders)

@app.route("/orders")
def orders():
    orders = get_orders()
    return render_template("orders.html", orders=orders)

@app.route('/order/<int:order_id>')
def order_details(order_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    if order is None:
        cursor.close()
        conn.close()
        return "الطلب غير موجود", 404

    cursor.execute("""
        SELECT * FROM messages 
        WHERE order_id = %s OR (telegram_id = %s AND telegram_id != 0)
        ORDER BY id ASC
    """, (order_id, order['telegram_id']))
    messages = cursor.fetchall()
    
    cursor.close()
    conn.close()
    return render_template('order_details.html', order=order, messages=messages)

@app.route('/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    new_status = request.form.get('status')
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT telegram_id FROM orders WHERE id = %s", (order_id,))
    order = cursor.fetchone()
    cursor.execute("UPDATE orders SET status = %s WHERE id = %s", (new_status, order_id))
    conn.commit()
    cursor.close()
    conn.close()

    if order and order['telegram_id']:
        status_text = {
            "paid": "💳 تم تأكيد دفع طلبك بنجاح!",
            "shipped": "✅ تم شحن طلبك بنجاح! شكراً لتعاملك معنا.",
            "rejected": "❌ معذرة، تم رفض طلبك. يرجى التواصل مع الدعم."
        }.get(new_status)
        if status_text:
            send_telegram_notification(order['telegram_id'], f"تحديث للطلب #{order_id}:\n{status_text}")

    return redirect(url_for('order_details', order_id=order_id))

@app.route('/order/<int:order_id>/receipt')
def order_receipt(order_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    cursor.close()
    conn.close()
    
    if not order:
        return "الطلب غير موجود", 404

    receipt_val = None
    for col in ['receipt_path', 'receipt_file_id', 'receipt', 'receipt_image']:
        if col in order.keys() and order[col]:
            receipt_val = order[col]
            break

    if not receipt_val:
        return "لا يوجد إيصال مرفق لهذا الطلب", 404

    if os.path.exists(str(receipt_val)):
        return send_file(str(receipt_val))

    if not BOT_TOKEN:
        return "تعذر تحميل الإيصال: BOT_TOKEN مفقود", 500

    try:
        file_info = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={receipt_val}").json()
        if file_info.get("ok"):
            file_path = file_info["result"]["file_path"]
            img_res = requests.get(f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}")
            
            os.makedirs("receipts", exist_ok=True)
            local_save = os.path.join("receipts", f"receipt_{order_id}.jpg")
            with open(local_save, "wb") as f:
                f.write(img_res.content)
            
            return send_file(local_save)
    except Exception as e:
        print(f"Error fetching receipt from telegram: {e}")

    return "تعذر تحميل الإيصال من السيرفر أو التليجرام", 404

@app.route('/order/<int:order_id>/message', methods=['POST'])
def send_order_message(order_id):
    message_text = request.form.get('message')
    if not message_text:
        return redirect(url_for('order_details', order_id=order_id))
    
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT telegram_id FROM orders WHERE id = %s', (order_id,))
    order = cursor.fetchone()
    if order:
        cursor.execute('''
            INSERT INTO messages (order_id, telegram_id, sender, text, message_text, message_type, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
        ''', (order_id, order['telegram_id'], 'admin', message_text, message_text, 'text'))
        conn.commit()
        
        send_telegram_notification(order['telegram_id'], f"💬 رسالة جديدة من الدعم:\n\n{message_text}")
        
    cursor.close()
    conn.close()
    return redirect(url_for('order_details', order_id=order_id))

@app.route("/products")
def products():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, COUNT(pa.id) AS package_count
        FROM products p
        LEFT JOIN packages pa ON pa.product_id = p.id
        GROUP BY p.id
        ORDER BY p.id DESC
    """)
    products = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("products.html", products=products)

@app.route("/products/add", methods=["POST"])
def add_product():
    name = request.form.get("name", "").strip()
    product_type = request.form.get("product_type", "game").strip()
    description = request.form.get("description", "").strip()
    if name:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO products (name, product_type, description, active) VALUES (%s, %s, %s, 1)",
            (name, product_type, description)
        )
        conn.commit()
        cursor.close()
        conn.close()
    return redirect(url_for("products"))

@app.route("/products/edit/<int:product_id>", methods=["GET", "POST"])
def edit_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()

    if product is None:
        cursor.close()
        conn.close()
        return redirect(url_for("products"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        product_type = request.form.get("product_type", "game").strip()
        description = request.form.get("description", "").strip()
        active = 1 if request.form.get("active") else 0
        
        if not name:
            cursor.close()
            conn.close()
            return render_template("product_edit.html", product=product, error="اسم المنتج مطلوب.")

        cursor.execute("""
            UPDATE products
            SET name = %s, product_type = %s, description = %s, active = %s
            WHERE id = %s
        """, (name, product_type, description, active, product_id))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("products"))

    cursor.close()
    conn.close()
    return render_template("product_edit.html", product=product)

@app.route("/products/delete/<int:product_id>", methods=["POST"])
def delete_product(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM packages WHERE product_id = %s", (product_id,))
    cursor.execute("DELETE FROM products WHERE id = %s", (product_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("products"))

@app.route("/products/<int:product_id>/packages")
def packages(product_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    if product is None:
        cursor.close()
        conn.close()
        return redirect(url_for("products"))

    cursor.execute(
        "SELECT * FROM packages WHERE product_id = %s ORDER BY id DESC",
        (product_id,)
    )
    packages = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("packages.html", product=product, packages=packages)

@app.route("/products/<int:product_id>/packages/add", methods=["POST"])
def add_package(product_id):
    name = request.form.get("name", "").strip()
    price_text = request.form.get("price", "0").strip()

    if not name:
        return redirect(url_for("packages", product_id=product_id))

    try:
        price = float(price_text)
    except ValueError:
        price = 0

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO packages (product_id, name, price, active)
        VALUES (%s, %s, %s, 1)
    """, (product_id, name, price))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("packages", product_id=product_id))

@app.route("/packages/edit/<int:package_id>", methods=["GET", "POST"])
def edit_package(package_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM packages WHERE id = %s", (package_id,))
    package = cursor.fetchone()

    if package is None:
        cursor.close()
        conn.close()
        return redirect(url_for("products"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        price_text = request.form.get("price", "0").strip()
        active = 1 if request.form.get("active") else 0

        if not name:
            cursor.close()
            conn.close()
            return render_template("packages_edit.html", package=package, error="اسم الباقة مطلوب.")

        try:
            price = float(price_text)
        except ValueError:
            cursor.close()
            conn.close()
            return render_template("packages_edit.html", package=package, error="السعر غير صحيح.")

        cursor.execute("""
            UPDATE packages
            SET name = %s, price = %s, active = %s
            WHERE id = %s
        """, (name, price, active, package_id))
        conn.commit()
        product_id = package["product_id"]
        cursor.close()
        conn.close()
        return redirect(url_for("packages", product_id=product_id))

    cursor.close()
    conn.close()
    return render_template("packages_edit.html", package=package)

@app.route("/packages/delete/<int:package_id>", methods=["POST"])
def delete_package(package_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id FROM packages WHERE id = %s", (package_id,))
    package = cursor.fetchone()

    if package is None:
        cursor.close()
        conn.close()
        return redirect(url_for("products"))

    product_id = package["product_id"]
    cursor.execute("DELETE FROM packages WHERE id = %s", (package_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("packages", product_id=product_id))

if __name__ == "__main__":
    init_products_db()
    app.run(host='0.0.0.0', port=5000)
