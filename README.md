# Typing Master Pro - Deployment Guide

هذا التطبيق مهيأ للعمل على منصة **Render** باستخدام إطار العمل **FastAPI**.

## خطوات النشر على Render:

### 1. رفع الكود إلى GitHub
1. أنشئ مستودعاً (Repository) جديداً على [GitHub](https://github.com).
2. ارفع الملفات الأربعة التالية إلى المستودع:
   - `main.py`
   - `requirements.txt`
   - `Procfile`
   - `README.md`

### 2. النشر على Render
1. اذهب إلى [Render.com](https://render.com) وأنشئ حساباً.
2. اضغط على **New +** واختر **Web Service**.
3. اربط حسابك بـ GitHub واختر المستودع الذي أنشأته.
4. في إعدادات الخدمة (Settings):
   - **Name:** typing-master-pro (أو أي اسم تختاره)
   - **Region:** اختر الأقرب لك (مثلاً: Frankfurt)
   - **Branch:** main
   - **Runtime:** Python 3
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** سيقرأ Render أمر التشغيل تلقائياً من ملف `Procfile`.
5. اختر **Free Plan** (الخطة المجانية).
6. اضغط **Create Web Service**.

### 3. بعد النشر
- سيستغرق البناء بضع دقائق.
- بعد الانتهاء، ستحصل على رابط مثل: `https://typing-master-pro.onrender.com`.
- **ملاحظة:** الخطة المجانية في Render تجعل التطبيق "ينام" (Sleep) بعد 15 دقيقة من عدم النشاط. عند فتح الرابط بعد فترة خمول، قد يستغرق 30 ثانية ليستيقظ. إذا أردت أن يعمل 24/7 بدون توقف، يمكنك الترقية للخطة المدفوعة ($7/شهر).

## حساب الأدمن (Admin)
للدخول كأدمن، استخدم:
- **اسم المستخدم:** `bos`
- **كلمة المرور:** `Bader@12`