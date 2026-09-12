import time
from playwright.sync_api import sync_playwright
from config import CHROME_USER_DATA_DIR, CHROME_PROFILES, BROWSER_ARGS

def main():
    print(f"\n📁 حزمة بيانات المتصفح الجديدة: {CHROME_USER_DATA_DIR}\n")
    print("سنقوم الآن بإعداد الحسابات. سيفتح متصفح لكل لغة لتسجيل الدخول.")
    print("بمجرد الدخول بنجاح لـ YouTube Studio، ارجع هنا واضغط Enter.\n")
    
    with sync_playwright() as p:
        for lang, profile in CHROME_PROFILES.items():
            print(f"=== 🟡 جاري تجهيز بروفايل: {lang} ({profile}) ===")
            try:
                context = p.chromium.launch_persistent_context(
                    user_data_dir=CHROME_USER_DATA_DIR,
                    channel="chrome",
                    headless=False,
                    args=[f"--profile-directory={profile}"] + BROWSER_ARGS,
                    ignore_default_args=["--enable-automation"],
                    no_viewport=True,
                )
                page = context.pages[0] if context.pages else context.new_page()
                page.goto("https://studio.youtube.com")
                
                print(f"⌛ برجاء تسجيل الدخول لحساب [{lang}] في المتصفح المفتوح...")
                input(f"➤ بعد تسجيل الدخول وفتح YouTube Studio بنجاح، اضغط Enter هنا للاستمرار...")
                
                context.close()
                print(f"✅ تم حفظ بروفايل: {lang}\n")
            except Exception as e:
                print(f"❌ حدث خطأ أثناء تجهيز {lang}: {e}")
                
    print("🎉 اكتمل تسجيل الدخول لجميع اللغات! يمكنك الآن تشغيل python main.py")

if __name__ == "__main__":
    main()
