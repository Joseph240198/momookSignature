from playwright.async_api import async_playwright, TimeoutError
import asyncio
from pathlib import Path
import time
from pywinauto import Application, Desktop, findwindows
import fitz 
import os
import win32print, win32api
import subprocess
from utils import rotate_pdf, insert_signature, find_save_button

#PRUEBA git 2
USERNAME = "j.soler@baatraining.com"
PASSWORD = "2401199883$cC"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FOLDER_PATH = r"C:\Users\Jose A\Desktop\momook_signature\Techlogs"
SUMATRA = r"C:\Users\Jose A\AppData\Local\SumatraPDF"
PRINTER_NAME = "ingeniero buena"
Path(FOLDER_PATH).mkdir(exist_ok=True)



#====================================PRINT PDF=========================================
def print_pdf(pdf_path, printer_name):
    try:
        subprocess.run([
            SUMATRA,
            "-print-to", printer_name,
            pdf_path
        ])
        return 1
    except:
        return 0

# =================================== PLAYWRIGHT SETUP ================================
async def create_instance():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,
        channel="chrome",
        args=["--kiosk-printing", "--start-maximized"]
    )
    context = await browser.new_context(accept_downloads=True , no_viewport=True)
    page = await context.new_page()
    return page, context, browser, playwright

# =================================== LOGIN ===========================================
async def login(page):
    await page.fill('input[name="username"]', USERNAME)
    await page.fill('input[name="password"]', PASSWORD)
    await page.click("button:has-text('Login')")
    print("✅ Logged in")

# =================================== HANDLE PRINT ====================================

async def handle_request(context, request):
    url = request.url

    if "/ffs/logs/" in url and url.endswith("/print"):
        print(f"🖨 Print URL intercepted: {url}")

        # Wait until Save print output as shows
        dlg = None
        start = time.time()

        while time.time() - start < 12:
            try:
                wins = findwindows.find_windows(
                    title_re=".*Guardar.*|.*Save.*|.*Print Output.*"
                )
                if wins:
                    app = Application(backend="uia").connect(handle=wins[0])
                    dlg = app.window(handle=wins[0])
                    break
            except:
                pass

            await asyncio.sleep(0.3)

        if dlg is None:
            print("❌ Save dialog NOT FOUND")
            return

        dlg.wait('visible', timeout=5)

        # ----- Set filename -----
        filename = f"document_{int(time.time() * 1000)}.pdf"
        full_path = os.path.join(FOLDER_PATH, filename)

        edit = dlg.child_window(class_name="Edit")

        edit.set_edit_text(full_path)

        # ------- Wait for text to be fully applied ----------
        try:
            for _ in range(10):
                if edit.window_text() == full_path:
                    break
        except:
            print("❌ Path not written correctly")

        # ---- Find Save button ----
        try:
            btn = find_save_button(dlg)
            if btn is None:
                print("❌ Save button not found")
                dlg.print_control_identifiers()
                return
            else:
                btn.invoke()
                print(f"💾 Saved file: {filename}")
        except:
            print("❌ Save button error")

        # --------Insert signature in pdf ----------
        try:
            await insert_signature(full_path, r"C:\Users\Jose A\Desktop\momook_signature\Techlogs\signature.png", (339.35, 547.49, 360.19, 678.42))
        except:
            print("❌ Error inserting signature")


# =================================== MAIN =============================================
async def main():
    main_page, context, browser, playwright = await create_instance()
    print("🌐 Browser launched")

    await main_page.goto("https://my.momook.com/react-ui/login")

    await login(main_page)

    # Attach handler
    main_page.on("request", lambda req: asyncio.create_task(handle_request(context, req)))

    print("👀 Waiting for user actions...")

    # Keep running
    while True:
        if main_page.is_closed():
            break
        await asyncio.sleep(0.5)

    await browser.close()
    await playwright.stop()


asyncio.run(main())