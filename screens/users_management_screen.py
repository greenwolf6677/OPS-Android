"""
OPS Users Management Screen
شاشة إدارة المستخدمين والإعدادات
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.filechooser import FileChooserListView
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ListProperty, ObjectProperty
from kivy.clock import Clock
from kivy.logger import Logger
from kivy.utils import platform
from kivy.core.image import Image as CoreImage
from kivy.core.clipboard import Clipboard

import sqlite3
import os
import json
import shutil
import threading
import zipfile
from datetime import datetime
from database import get_db_connection

# استيراد إعدادات المحل
from utils.settings import load_settings, save_settings, DEFAULT_SETTINGS, IMAGES_DIR

# تحديد المسار الأساسي
if platform == 'android':
    from android.storage import primary_external_storage_path
    from android.permissions import request_permissions, Permission
    BASE_PATH = primary_external_storage_path()
    request_permissions([Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])
else:
    BASE_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class UserItem(BoxLayout):
    """عنصر مستخدم في قائمة العرض"""
    user_id = NumericProperty(0)
    username = StringProperty("")
    full_name = StringProperty("")
    role = StringProperty("")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = 50
        self.padding = [5, 5]
        self.spacing = 5


class UsersRecycleView(RecycleView):
    """عرض قائمة المستخدمين"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []
        self.layout_manager = RecycleBoxLayout(
            default_size=(None, 50),
            default_size_hint=(1, None),
            size_hint_y=None,
            height=self.minimum_height,
            orientation='vertical'
        )
        self.add_widget(self.layout_manager)


class UsersManagementScreen(Screen):
    """شاشة إدارة المستخدمين والإعدادات"""
    
    # متغيرات الإعدادات
    store_name = StringProperty("")
    store_phone = StringProperty("")
    store_address = StringProperty("")
    tax_number = StringProperty("")
    receipt_footer = StringProperty("")
    currency = StringProperty("₪")
    logo_path = StringProperty("")
    
    # متغيرات المستخدم
    selected_user_id = NumericProperty(0)
    full_name = StringProperty("")
    username = StringProperty("")
    password = StringProperty("")
    is_admin = BooleanProperty(False)
    
    # متغيرات الصلاحيات
    sales_perm = BooleanProperty(True)
    reports_perm = BooleanProperty(False)
    stock_perm = BooleanProperty(False)
    
    # حالة التحميل
    loading = BooleanProperty(False)
    
    # قائمة المستخدمين
    users_list = ListProperty([])
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.load_settings()
        self.load_users()
    
    def on_enter(self):
        """عند دخول الشاشة"""
        self.load_users()
        Logger.info("OPS Users Management: Screen entered")
    
    def load_settings(self):
        """تحميل إعدادات المحل"""
        settings = load_settings()
        self.store_name = settings.get("store_name", DEFAULT_SETTINGS["store_name"])
        self.store_phone = settings.get("store_phone", "")
        self.store_address = settings.get("store_address", "")
        self.tax_number = settings.get("tax_number", "")
        self.receipt_footer = settings.get("receipt_footer", DEFAULT_SETTINGS["receipt_footer"])
        self.currency = settings.get("currency", DEFAULT_SETTINGS["currency"])
        self.logo_path = settings.get("store_logo", "")
        
        # تحديث عرض الشعار
        if self.logo_path and os.path.exists(self.logo_path):
            self.update_logo_display()
    
    def save_store_settings(self):
        """حفظ إعدادات المحل"""
        settings = {
            "store_name": self.store_name.strip(),
            "store_phone": self.store_phone.strip(),
            "store_address": self.store_address.strip(),
            "tax_number": self.tax_number.strip(),
            "receipt_footer": self.receipt_footer.strip(),
            "currency": self.currency,
            "store_logo": self.logo_path
        }
        save_settings(settings)
        self.show_popup("نجاح", "✅ تم حفظ إعدادات المحل بنجاح")
    
    def load_users(self):
        """تحميل قائمة المستخدمين"""
        self.loading = True
        try:
            conn = get_db_connection()
            conn.row_factory = sqlite3.Row
            users = conn.execute("SELECT id, username, full_name, role FROM users").fetchall()
            conn.close()
            
            data = []
            for u in users:
                data.append({
                    'user_id': u['id'],
                    'username': u['username'],
                    'full_name': u['full_name'] or u['username'],
                    'role': u['role']
                })
            
            self.users_list = data
            Logger.info(f"OPS Users Management: Loaded {len(data)} users")
            
        except Exception as e:
            Logger.error(f"OPS Users Management: Error loading users - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
        finally:
            self.loading = False
    
    def select_user(self, user_id, username, full_name, role):
        """تحديد مستخدم للتعديل"""
        self.selected_user_id = user_id
        self.username = username
        self.full_name = full_name
        self.password = ""  # لا نعرض كلمة المرور
        self.is_admin = (role == 'admin')
        self.sales_perm = True
        self.reports_perm = self.is_admin
        self.stock_perm = self.is_admin
    
    def clear_user_fields(self):
        """مسح حقول المستخدم"""
        self.selected_user_id = 0
        self.username = ""
        self.full_name = ""
        self.password = ""
        self.is_admin = False
        self.sales_perm = True
        self.reports_perm = False
        self.stock_perm = False
    
    def add_user(self):
        """إضافة مستخدم جديد"""
        if not self.username or not self.password:
            self.show_popup("تنبيه", "يرجى تعبئة اسم المستخدم وكلمة المرور")
            return
        
        role = "admin" if self.is_admin else "employee"
        
        try:
            conn = get_db_connection()
            conn.execute("""
                INSERT INTO users (username, password, role, full_name)
                VALUES (?, ?, ?, ?)
            """, (self.username, self.password, role, self.full_name))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", f"تمت إضافة {self.full_name or self.username} بنجاح")
            self.clear_user_fields()
            self.load_users()
            
        except sqlite3.IntegrityError:
            self.show_popup("خطأ", "اسم المستخدم موجود مسبقاً")
        except Exception as e:
            Logger.error(f"OPS Users Management: Error adding user - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def update_user(self):
        """تحديث بيانات المستخدم"""
        if not self.selected_user_id:
            self.show_popup("تنبيه", "اختر مستخدماً من الجدول أولاً")
            return
        
        role = "admin" if self.is_admin else "employee"
        
        try:
            conn = get_db_connection()
            if self.password:
                conn.execute("""
                    UPDATE users SET username=?, password=?, role=?, full_name=?
                    WHERE id=?
                """, (self.username, self.password, role, self.full_name, self.selected_user_id))
            else:
                conn.execute("""
                    UPDATE users SET username=?, role=?, full_name=?
                    WHERE id=?
                """, (self.username, role, self.full_name, self.selected_user_id))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", "تم تحديث بيانات المستخدم")
            self.clear_user_fields()
            self.load_users()
            
        except Exception as e:
            Logger.error(f"OPS Users Management: Error updating user - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def delete_user(self):
        """حذف مستخدم"""
        if not self.selected_user_id:
            self.show_popup("تنبيه", "اختر مستخدماً من الجدول أولاً")
            return
        
        self.show_confirmation_popup(
            "تأكيد الحذف",
            f"هل أنت متأكد من حذف المستخدم '{self.full_name or self.username}'؟",
            self._delete_user_confirm
        )
    
    def _delete_user_confirm(self):
        """تأكيد حذف المستخدم"""
        try:
            conn = get_db_connection()
            conn.execute("DELETE FROM users WHERE id=?", (self.selected_user_id,))
            conn.commit()
            conn.close()
            
            self.show_popup("نجاح", "تم حذف المستخدم بنجاح")
            self.clear_user_fields()
            self.load_users()
            
        except Exception as e:
            Logger.error(f"OPS Users Management: Error deleting user - {e}")
            self.show_popup("خطأ", f"حدث خطأ: {str(e)}")
    
    def select_logo(self):
        """اختيار شعار المحل"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        filechooser = FileChooserListView(
            path='/sdcard' if platform == 'android' else '/',
            filters=['*.png', '*.jpg', '*.jpeg', '*.gif', '*.bmp']
        )
        content.add_widget(filechooser)
        
        buttons = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_ok = Button(text="اختيار", font_name='ArabicFont', background_color=(0.2, 0.6, 0.2, 1))
        btn_cancel = Button(text="إلغاء", font_name='ArabicFont', background_color=(0.6, 0.2, 0.2, 1))
        buttons.add_widget(btn_ok)
        buttons.add_widget(btn_cancel)
        content.add_widget(buttons)
        
        popup = Popup(title="اختر شعار المحل", content=content, size_hint=(0.9, 0.9))
        
        def select(instance):
            if filechooser.selection:
                file_path = filechooser.selection[0]
                # نسخ الصورة إلى مجلد الصور
                ext = os.path.splitext(file_path)[1]
                new_filename = f"logo_{datetime.now().strftime('%Y%m%d%H%M%S')}{ext}"
                new_path = os.path.join(IMAGES_DIR, new_filename)
                shutil.copy2(file_path, new_path)
                self.logo_path = new_path
                self.update_logo_display()
                popup.dismiss()
        
        btn_ok.bind(on_press=select)
        btn_cancel.bind(on_press=popup.dismiss)
        
        popup.open()
    
    def clear_logo(self):
        """إزالة الشعار"""
        self.logo_path = ""
        self.update_logo_display()
    
    def update_logo_display(self):
        """تحديث عرض الشعار"""
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                self.logo_image.source = self.logo_path
                self.logo_label.text = ""
            except:
                self.logo_label.text = "لا يمكن عرض الصورة"
        else:
            self.logo_label.text = "لا يوجد شعار"
    
    def create_backup(self):
        """إنشاء نسخة احتياطية"""
        backup_dir = self.select_directory()
        if not backup_dir:
            return
        
        self.show_loading_popup("جاري إنشاء النسخة الاحتياطية...")
        
        def run_backup():
            try:
                app_dir = os.path.dirname(os.path.abspath(__file__)) if not getattr(sys, 'frozen', False) else os.path.dirname(sys.executable)
                
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                backup_name = f"ManualBackup_{timestamp}.zip"
                backup_path = os.path.join(backup_dir, backup_name)
                
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(app_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, app_dir)
                            zipf.write(file_path, arcname)
                
                Clock.schedule_once(lambda dt: self.show_popup("نجاح", f"تم إنشاء النسخة الاحتياطية بنجاح:\n{backup_path}"), 0)
                
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_popup("خطأ", str(e)), 0)
            finally:
                Clock.schedule_once(lambda dt: self.dismiss_loading_popup(), 0)
        
        threading.Thread(target=run_backup, daemon=True).start()
    
    def restore_backup(self):
        """استرجاع نسخة احتياطية"""
        backup_file = self.select_file()
        if not backup_file:
            return
        
        self.show_confirmation_popup(
            "تأكيد الاسترجاع",
            "سيتم استبدال ملفات البرنامج بالنسخة الاحتياطية.\nهل تريد المتابعة؟",
            self._restore_backup_confirm
        )
    
    def _restore_backup_confirm(self):
        """تأكيد استرجاع النسخة الاحتياطية"""
        backup_file = self.selected_file
        self.show_loading_popup("جاري استرجاع النسخة الاحتياطية...")
        
        def run_restore():
            try:
                app_dir = os.path.dirname(os.path.abspath(__file__)) if not getattr(sys, 'frozen', False) else os.path.dirname(sys.executable)
                
                with zipfile.ZipFile(backup_file, 'r') as zip_ref:
                    zip_ref.extractall(app_dir)
                
                Clock.schedule_once(lambda dt: self.show_popup("تم", "تم استرجاع النسخة الاحتياطية بنجاح.\nيرجى إعادة تشغيل البرنامج."), 0)
                
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_popup("خطأ", str(e)), 0)
            finally:
                Clock.schedule_once(lambda dt: self.dismiss_loading_popup(), 0)
        
        threading.Thread(target=run_restore, daemon=True).start()
    
    def manual_update(self):
        """التحديث اليدوي"""
        update_file = self.select_file()
        if not update_file or not update_file.lower().endswith(".zip"):
            self.show_popup("إلغاء", "لم يتم اختيار ملف تحديث صالح")
            return
        
        self.show_confirmation_popup(
            "تأكيد التحديث",
            "هل تريد عمل نسخة احتياطية كاملة قبل التحديث؟\n(موصى به بشدة)",
            self._update_with_backup
        )
    
    def _update_with_backup(self):
        """التحديث مع النسخ الاحتياطي"""
        backup_dir = self.select_directory()
        if not backup_dir:
            self.show_popup("إلغاء", "تم إلغاء التحديث")
            return
        
        self.show_loading_popup("جاري التحديث...")
        
        def run_update():
            try:
                app_dir = os.path.dirname(os.path.abspath(__file__)) if not getattr(sys, 'frozen', False) else os.path.dirname(sys.executable)
                
                # عمل نسخة احتياطية
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
                backup_name = f"Backup_{timestamp}.zip"
                backup_path = os.path.join(backup_dir, backup_name)
                
                with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(app_dir):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, app_dir)
                            zipf.write(file_path, arcname)
                
                # تطبيق التحديث
                temp_extract = os.path.join(app_dir, "update_temp")
                os.makedirs(temp_extract, exist_ok=True)
                
                with zipfile.ZipFile(self.selected_file, 'r') as zip_ref:
                    zip_ref.extractall(temp_extract)
                
                updated_count = 0
                for root, dirs, files in os.walk(temp_extract):
                    for file in files:
                        src = os.path.join(root, file)
                        rel_path = os.path.relpath(src, temp_extract)
                        dst = os.path.join(app_dir, rel_path)
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                        updated_count += 1
                
                shutil.rmtree(temp_extract)
                
                Clock.schedule_once(lambda dt: self.show_popup("نجاح", f"تم التحديث بنجاح!\nتم تحديث {updated_count} ملف/مجلد.\nيرجى إعادة تشغيل البرنامج."), 0)
                
            except Exception as e:
                Clock.schedule_once(lambda dt: self.show_popup("خطأ", f"حدث خطأ أثناء التحديث:\n{str(e)}"), 0)
            finally:
                Clock.schedule_once(lambda dt: self.dismiss_loading_popup(), 0)
        
        threading.Thread(target=run_update, daemon=True).start()
    
    def select_directory(self):
        """اختيار مجلد"""
        # على Android، نستخدم مجلد المستندات
        if platform == 'android':
            import os
            from android.storage import primary_external_storage_path
            path = primary_external_storage_path()
            return os.path.join(path, 'Documents')
        else:
            from tkinter import filedialog
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            return filedialog.askdirectory()
    
    def select_file(self):
        """اختيار ملف"""
        if platform == 'android':
            from android.storage import primary_external_storage_path
            path = primary_external_storage_path()
            # هنا يمكن فتح نافذة اختيار الملف
            return None
        else:
            from tkinter import filedialog
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            return filedialog.askopenfilename()
    
    def show_loading_popup(self, message):
        """عرض نافذة تحميل"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont'))
        
        self.loading_popup = Popup(title="جاري التنفيذ", content=content, size_hint=(0.6, 0.3))
        self.loading_popup.open()
    
    def dismiss_loading_popup(self):
        """إغلاق نافذة التحميل"""
        if hasattr(self, 'loading_popup'):
            self.loading_popup.dismiss()
    
    def go_back(self):
        """العودة للشاشة الرئيسية"""
        self.manager.current = 'dashboard'
    
    def show_popup(self, title, message):
        """عرض نافذة منبثقة"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        btn = Button(text="موافق", size_hint_y=0.3, font_name='ArabicFont')
        popup = Popup(title=title, content=content, size_hint=(0.8, 0.5))
        btn.bind(on_press=popup.dismiss)
        content.add_widget(btn)
        
        popup.open()
    
    def show_confirmation_popup(self, title, message, on_confirm):
        """عرض نافذة تأكيد"""
        content = BoxLayout(orientation='vertical', padding=10, spacing=10)
        content.add_widget(Label(text=message, font_name='ArabicFont', halign='center', text_size=(400, None)))
        
        buttons = BoxLayout(size_hint_y=0.3, spacing=10)
        btn_yes = Button(text="نعم", font_name='ArabicFont', background_color=(0.2, 0.6, 0.2, 1))
        btn_no = Button(text="لا", font_name='ArabicFont', background_color=(0.6, 0.2, 0.2, 1))
        buttons.add_widget(btn_yes)
        buttons.add_widget(btn_no)
        content.add_widget(buttons)
        
        popup = Popup(title=title, content=content, size_hint=(0.7, 0.4))
        
        def yes_action(instance):
            popup.dismiss()
            on_confirm()
        
        btn_yes.bind(on_press=yes_action)
        btn_no.bind(on_press=popup.dismiss)
        
        popup.open()