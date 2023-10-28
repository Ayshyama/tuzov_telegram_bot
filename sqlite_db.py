import sqlite3


async def db_connect() -> None:
    global db, cur

    db = sqlite3.connect('db.db')
    cur = db.cursor()

    cur.execute("""CREATE TABLE IF NOT EXISTS products (
        product_id INTEGER PRIMARY KEY,
        title TEXT, 
        media TEXT,
        category TEXT DEFAULT 'free')""")
    db.commit()

    cur.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        is_subscribed INTEGER DEFAULT 0,
        has_premium INTEGER DEFAULT 0)""")

    db.commit()


def add_new_user(user_id, username, first_name, last_name):
    cur.execute("""INSERT OR IGNORE INTO users (user_id, username, first_name, last_name) 
                   VALUES (?, ?, ?, ?)""", (user_id, username, first_name, last_name))
    db.commit()


def user_exists(user_id):
    user = cur.execute("""SELECT * FROM users WHERE user_id = ?""", (user_id,)).fetchone()
    return user is not None


def get_user_status(user_id):
    user = cur.execute("""SELECT is_subscribed, has_premium FROM users WHERE user_id = ?""", (user_id,)).fetchone()
    return user if user else (0, 0)


def set_subscription_status(user_id, status):
    cur.execute("""UPDATE users SET is_subscribed = ? WHERE user_id = ?""", (status, user_id))
    db.commit()


def set_premium_status(user_id, status):
    cur.execute("""UPDATE users SET has_premium = ? WHERE user_id = ?""", (status, user_id))
    db.commit()


async def get_all_products() -> list:
    products = cur.execute("""SELECT * FROM products""").fetchall()
    return products


async def create_new_product(data):
    cur.execute("""INSERT INTO "products" (title, media, category) VALUES (?, ?, ?)""",
                (data['title'], data['media'], data['category']))
    db.commit()
    return cur.lastrowid


async def delete_product(product_id: int) -> None:
    cur.execute("""DELETE FROM products WHERE product_id = ?""", (product_id,))
    db.commit()


async def edit_product(product_id: int, title: str) -> None:
    cur.execute("""UPDATE products SET title = ? WHERE product_id = ?""", (title, product_id,))
    db.commit()


def set_user_subscribed(user_id: int):
    cur.execute("UPDATE users SET is_subscribed = 1 WHERE user_id = ?", (user_id,))
    db.commit()


def get_products_by_category(category: str):
    return cur.execute("""SELECT * FROM products WHERE category = ?""", (category,)).fetchall()


def get_product_by_id(product_id: int):
    product = cur.execute("""SELECT * FROM products WHERE product_id = ?""", (product_id,)).fetchone()
    return product


def get_all_users():
    return cur.execute("""SELECT * FROM users""").fetchall()


def update_user(user_id, is_subscribed, has_premium):
    cur.execute("""UPDATE users SET is_subscribed = ?, has_premium = ? WHERE user_id = ?""", (is_subscribed, has_premium, user_id))
    db.commit()
