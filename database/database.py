"""
OPS Database Module
وحدة قاعدة البيانات لنظام OPS
المعدلة لتعمل على أندرويد 11 فما فوق
"""

import sqlite3
import os
from datetime import datetime
from kivy.utils import platform
from kivy.logger import Logger
from kivy.app import App

# ==================== تحديد مسار قاعدة البيانات ====================
if platform == 'android':
    # استخدام المسار الخاص بالتطبيق لضمان الصلاحيات في الإصدارات الحديثة
    try:
        DB_DIR = App.get_running_app().user_data_dir
        DB_PATH = os.path.join(DB_DIR, 'ops.db')
        if not os.path.exists(DB_DIR):
            os.makedirs(DB_DIR, exist_ok=True)
    except Exception as e:
        # حل احتياطي في حال استدعاء الملف قبل تشغيل App
        DB_PATH = "ops.db" 
else:
    # المسار لنسخة الويندوز أو الماك
    DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ops.db')

Logger.info(f"OPS Database: Using database at {DB_PATH}")


def get_db_connection():
    """الحصول على اتصال بقاعدة البيانات"""
    conn = sqlite3.connect(DB_PATH)
    # تفعيل العلاقات الخارجية لضمان عمل الـ FOREIGN KEY
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """تهيئة قاعدة البيانات"""
    conn = get_db_connection()
    c = conn.cursor()
    
    # ==================== الجداول الأساسية ====================
    
    # جدول المستخدمين
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'employee')),
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول التصنيفات
    c.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            description TEXT
        )
    ''')
    
    # جدول المنتجات
    c.execute('''
        CREATE TABLE IF NOT EXISTS products (
            barcode TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            buy_price REAL NOT NULL DEFAULT 0,
            sell_price REAL NOT NULL DEFAULT 0,
            quantity INTEGER NOT NULL DEFAULT 0,
            unit TEXT DEFAULT 'قطعة',
            category_id INTEGER DEFAULT 1,
            image_path TEXT,
            is_quick INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories(id)
        )
    ''')
    
    # جدول الزبائن
    c.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            address TEXT,
            notes TEXT,
            balance REAL DEFAULT 0.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # جدول الموردين
    c.execute('''
        CREATE TABLE IF NOT EXISTS suppliers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            address TEXT,
            phone TEXT,
            mobile TEXT,
            notes TEXT,
            balance REAL DEFAULT 0.0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # ==================== جدول المبيعات ====================
    c.execute('''
        CREATE TABLE IF NOT EXISTS sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            customer_id INTEGER DEFAULT 0,
            barcode TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            total REAL NOT NULL,
            discount REAL DEFAULT 0,
            payment_method TEXT NOT NULL,
            date TEXT NOT NULL,
            returned_qty INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )
    ''')
    
    # ==================== جدول المرتجعات ====================
    c.execute('''
        CREATE TABLE IF NOT EXISTS returns (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_invoice_id TEXT NOT NULL,
            barcode TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            return_amount REAL NOT NULL,
            reason TEXT,
            return_date TEXT NOT NULL,
            user_id INTEGER NOT NULL,
            customer_id INTEGER DEFAULT 0,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (customer_id) REFERENCES customers(id),
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )
    ''')
    
    # ==================== جدول الطلبيات ====================
    c.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_date TEXT NOT NULL,
            customer_id INTEGER DEFAULT 0,
            total REAL DEFAULT 0,
            discount REAL DEFAULT 0,
            net_total REAL DEFAULT 0,
            payment_method TEXT,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # جدول تفاصيل الطلبيات
    c.execute('''
        CREATE TABLE IF NOT EXISTS order_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            barcode TEXT,
            name TEXT,
            price REAL,
            quantity INTEGER,
            subtotal REAL,
            FOREIGN KEY (order_id) REFERENCES orders(id),
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )
    ''')
    
    # ==================== جدول المشتريات ====================
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            supplier_id INTEGER NOT NULL,
            total REAL NOT NULL,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    ''')
    
    # جدول تفاصيل المشتريات
    c.execute('''
        CREATE TABLE IF NOT EXISTS purchase_items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            purchase_id INTEGER NOT NULL,
            barcode TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            buy_price REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (purchase_id) REFERENCES purchases(id),
            FOREIGN KEY (barcode) REFERENCES products(barcode)
        )
    ''')
    
    # ==================== جداول المدفوعات ====================
    
    # جدول مدفوعات الزبائن
    c.execute('''
        CREATE TABLE IF NOT EXISTS customer_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (customer_id) REFERENCES customers(id)
        )
    ''')
    
    # جدول مدفوعات الموردين
    c.execute('''
        CREATE TABLE IF NOT EXISTS supplier_payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            supplier_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            payment_date TEXT NOT NULL,
            notes TEXT,
            FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
        )
    ''')
    
    # ==================== جدول الشيكات ====================
    c.execute('''
        CREATE TABLE IF NOT EXISTS checks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id INTEGER,
            check_number TEXT,
            owner_name TEXT,
            bank_name TEXT,
            due_date TEXT,
            amount REAL,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            FOREIGN KEY (order_id) REFERENCES orders(id)
        )
    ''')
    
    # ==================== إضافة البيانات الافتراضية ====================
    
    # إضافة المستخدمين الافتراضيين
    c.execute("SELECT COUNT(*) FROM users")
    if c.fetchone()[0] == 0:
        c.execute("""
            INSERT INTO users (username, password, full_name, role)
            VALUES (?, ?, ?, ?)
        """, ('admin', '1234', 'مدير النظام', 'admin'))
        c.execute("""
            INSERT INTO users (username, password, full_name, role)
            VALUES (?, ?, ?, ?)
        """, ('employee', '5678', 'موظف مبيعات', 'employee'))
        Logger.info("OPS Database: Default users created")
    
    # إضافة التصنيفات الافتراضية
    c.execute("SELECT COUNT(*) FROM categories")
    if c.fetchone()[0] == 0:
        default_categories = [
            (1, "مخبوزات", "الخبز والمعجنات"),
            (2, "ألبان", "الحليب ومشتقاته"),
            (3, "معلبات", "المواد المعلبة"),
            (4, "مشروبات", "المشروبات الساخنة والباردة"),
            (5, "منظفات", "مواد التنظيف"),
            (6, "خضروات", "الخضروات الطازجة"),
            (7, "فواكه", "الفواكه الطازجة"),
            (8, "لحوم", "اللحوم والدواجن")
        ]
        for cat in default_categories:
            c.execute("INSERT INTO categories (id, name, description) VALUES (?, ?, ?)", cat)
        Logger.info("OPS Database: Default categories created")
    
    # إضافة منتجات تجريبية إذا لم توجد
    c.execute("SELECT COUNT(*) FROM products")
    if c.fetchone()[0] == 0:
        sample_products = [
            ("123456", "خبز عربي", 1.50, 2.50, 100, "قطعة", 1, None, 0),
            ("234567", "حليب طازج", 3.00, 4.50, 50, "لتر", 2, None, 0),
            ("345678", "جبنة بيضاء", 8.00, 12.00, 30, "كيلو", 2, None, 0),
            ("456789", "زيت زيتون", 15.00, 22.00, 25, "لتر", 3, None, 0),
            ("567890", "أرز بسمتي", 10.00, 15.00, 40, "كيلو", 3, None, 0),
            ("678901", "سكر", 4.00, 6.50, 60, "كيلو", 3, None, 0),
        ]
        for prod in sample_products:
            c.execute("""
                INSERT INTO products (barcode, name, buy_price, sell_price, quantity, unit, category_id, image_path, is_quick)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, prod)
        Logger.info("OPS Database: Sample products created")
    
    conn.commit()
    conn.close()
    Logger.info("OPS Database: Initialization completed")


def get_user_permissions(user_id):
    """الحصول على صلاحيات المستخدم"""
    try:
        conn = get_db_connection()
        user = conn.execute("SELECT role FROM users WHERE id = ?", (user_id,)).fetchone()
        conn.close()
        
        if user and user['role'] == 'admin':
            return {
                'sales': True,
                'customers': True,
                'returns': True,
                'products': True,
                'suppliers': True,
                'purchases': True,
                'reports': True,
                'settings': True,
                'users': True
            }
        else:
            return {
                'sales': True,
                'customers': True,
                'returns': True,
                'products': False,
                'suppliers': False,
                'purchases': False,
                'reports': False,
                'settings': False,
                'users': False
            }
    except Exception as e:
        Logger.error(f"OPS Database: Error getting permissions - {e}")
        return {
            'sales': True,
            'customers': True,
            'returns': True,
            'products': False,
            'suppliers': False,
            'purchases': False,
            'reports': False,
            'settings': False,
            'users': False
        }