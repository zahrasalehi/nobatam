# نوبت بگیر (نوبتم)
i did some vibe-coding...sorry not sorry!
 این سایت قراره برای وقت هایی که در زمان خاصی باید نوبت بگیریم به ما کمک کنه که بطور اتوماتیک نوبت خودمونو بگیریم.
سایت هایی که فعلا اضافه شده اند:

1. پذیرش۲۴

## راه‌اندازی

1. محیط مجازی و وابستگی‌ها:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # یا در ویندوز: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. متغیرهای محیط (یا کپی از `.env.example` به `.env`):
   - `PAZIRESH24_CLIENT_ID` و `PAZIRESH24_CLIENT_SECRET` را از پذیرش۲۴ (مثلاً از طریق تلگرام) دریافت کنید.
   - `PAZIRESH24_REDIRECT_URI` باید دقیقاً همان آدرسی باشد که در ثبت کلاینت در پذیرش۲۴ وارد کرده‌اید (مثلاً `http://127.0.0.1:8000/auth/callback/`).

3. مایگریشن و اجرا:
   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

4. در مرورگر به `http://127.0.0.1:8000/` بروید؛ با «ورود با پذیرش۲۴» وارد شوید، سپس جستجوی پزشک و «رزرو اولین نوبت موجود» را انجام دهید.
5. لازم به ذکر است که کاربران لاگینی در سایت انجام نمیدهند و فقط لازم است که یکبار با پذیرش۲۴ لاگین بشوند

6. docs : https://developers.paziresh24.com/authorization
