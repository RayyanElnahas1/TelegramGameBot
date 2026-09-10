import sqlite3
import urllib.parse
import pg8000.native

# 1. اسم ملف SQLite على جهازك
SQLITE_DB = 'orders.db'

# 2. رابط External Database URL من Render
POSTGRES_URL = "postgresql://orders_db_nyhy_user:7wxU2EPicOWG58evkyoSmRDKqGUT9k8n@dpg-da5o558jo6nc73d6ffo0-a.frankfurt-postgres.render.com/orders_db_nyhy"

def run_migration():
    print("جاري نقل البيانات إلى PostgreSQL عبر pg8000...")
    
    # تفكيك رابط الاتصال
    url = urllib.parse.urlparse(POSTGRES_URL)
    
    sqlite_conn = sqlite3.connect(SQLITE_DB)
    sqlite_cursor = sqlite_conn.cursor()

    # الاتصال بـ PostgreSQL
    pg = pg8000.native.Connection(
        user=url.username,
        password=url.password,
        host=url.hostname,
        port=url.port or 5432,
        database=url.path[1:],
        ssl_context=True
    )

    # 1. إنشاء الجداول
    pg.run("""
    CREATE TABLE IF NOT EXISTS products (
        id SERIAL PRIMARY KEY, name TEXT NOT NULL, product_type TEXT NOT NULL DEFAULT 'game',
        description TEXT DEFAULT '', image TEXT DEFAULT '', active INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    pg.run("""
    CREATE TABLE IF NOT EXISTS packages (
        id SERIAL PRIMARY KEY, product_id INTEGER NOT NULL, name TEXT NOT NULL,
        price REAL NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
    );
    """)
    pg.run("""
    CREATE TABLE IF NOT EXISTS orders (
        id SERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL, username TEXT,
        customer_name TEXT NOT NULL, game TEXT NOT NULL, package TEXT NOT NULL,
        original_price REAL NOT NULL, final_price REAL NOT NULL, player_id TEXT NOT NULL,
        receipt_file_id TEXT, status TEXT NOT NULL DEFAULT 'pending', created_at TEXT NOT NULL
    );
    """)
    pg.run("""
    CREATE TABLE IF NOT EXISTS messages (
        id SERIAL PRIMARY KEY, telegram_id BIGINT NOT NULL, order_id INTEGER,
        sender TEXT NOT NULL, message_type TEXT NOT NULL, message_text TEXT,
        telegram_message_id BIGINT, created_at TEXT NOT NULL, text TEXT NOT NULL DEFAULT ''
    );
    """)

    tables = ['products', 'packages', 'orders', 'messages']

    for table in tables:
        sqlite_cursor.execute(f"SELECT * FROM {table}")
        rows = sqlite_cursor.fetchall()

        if not rows:
            print(f"جدول {table} فارغ.")
            continue

        sqlite_cursor.execute(f"PRAGMA table_info({table})")
        columns = [col[1] for col in sqlite_cursor.fetchall()]
        col_names = ", ".join(columns)
        placeholders = ", ".join([f":{i}" for i in range(len(columns))])

        query = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"

        for row in rows:
            params = {str(i): row[i] for i in range(len(row))}
            pg.run(query, **params)

        pg.run(f"SELECT setval(pg_get_serial_sequence('{table}', 'id'), COALESCE(MAX(id), 1)) FROM {table};")
        print(f"تم نقل {len(rows)} صف في جدول {table}")

    sqlite_conn.close()
    pg.close()
    print("\nتمت عملية النقل بنجاح إلى PostgreSQL!")

if __name__ == '__main__':
    run_migration()