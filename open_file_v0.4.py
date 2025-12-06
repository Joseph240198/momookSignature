from playwright.async_api import async_playwright, TimeoutError
import asyncio
from pathlib import Path
import time
from pywinauto import Application, Desktop, findwindows
import fitz   

USERNAME = "j.soler@baatraining.com"
PASSWORD = "2401199883$cC"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FOLDER_PATH = r"C:\Users\Jose A\Desktop\momook_signature\Techlogs"
Path(FOLDER_PATH).mkdir(exist_ok=True)


# =================================== UTILITIES =====================================

def find_save_button(dlg):
    # 1. Buscar por nombre exacto (Windows inglés)
    for name in ["Save", "&Save", "Guardar", "&Guardar"]:
        try:
            btn = dlg.child_window(title=name, control_type="Button")
            return btn.wrapper_object()
        except:
            pass

    # 2. Buscar por regex
    try:
        btn = dlg.child_window(title_re=".*Save.*", control_type="Button")
        return btn.wrapper_object()
    except:
        pass

    # 3. Buscar cualquier botón visible en el diálogo
    buttons = dlg.descendants(control_type="Button")
    if buttons:
        return buttons[0]  # normalmente el primero es Save

    # 4. Buscar dentro de DirectUIHWND (diálogos modernos)
    duis = dlg.descendants(class_name="DirectUIHWND")
    for ui in duis:
        try:
            btns = ui.descendants(control_type="Button")
            if btns:
                return btns[0]
        except:
            pass

    return None


# =================================== PLAYWRIGHT SETUP ================================
async def create_instance():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,
        channel="chrome",
        args=["--kiosk-printing"]
    )
    context = await browser.new_context(accept_downloads=True)
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

        # Esperar a que aparezca Save As
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
        edit = dlg.child_window(class_name="Edit")

        edit.set_edit_text(filename)

        # Wait for text to be fully applied
        for _ in range(10):
            if edit.window_text() == filename:
                break

        # ---- Find Save button ----
        btn = find_save_button(dlg)
       
        if btn is None:
            print("❌ Save button not found")
            dlg.print_control_identifiers()
            return
        
        btn.click_input()
        print(f"💾 Saved file: {filename}")


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