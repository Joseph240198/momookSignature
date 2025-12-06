from playwright.async_api import async_playwright, TimeoutError
import asyncio
from pathlib import Path
import time
from pywinauto import Application, Desktop, findwindows

USERNAME = "j.soler@baatraining.com"
PASSWORD = "2401199883$cC"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FOLDER_PATH = r"C:\Users\Jose A\Desktop\momook_signature\Techlogs"
Path(FOLDER_PATH).mkdir(exist_ok=True)



# =================================== PLAYWRIGHT SETUP ========================================
async def create_instance():
    """Create Edge browser instance with kiosk printing."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,
        channel="chrome",
        args=["--kiosk-printing"]  # triggers automatic print
        
    )
    context = await browser.new_context()
    page = await context.new_page()
    return page, context, browser, playwright

# =================================== LOGIN ================================================
async def login(page):
    await page.fill('input[name="username"]', USERNAME)
    await page.fill('input[name="password"]', PASSWORD)
    await page.click("button:has-text('Login')")
    print("✅ Logged in")

# =================================== HANDLE PRINT REQUEST =================================
async def handle_request(context, request):
    url = request.url
    if "/ffs/logs/" in url and url.endswith("/print"):
        print(f"🖨 Print URL intercepted: {url}")

        # Esperar hasta 10 segundos a que aparezca el diálogo
        dlg = None
        start_time = time.time()
        while time.time() - start_time < 10:
            try:
                windows = findwindows.find_windows(title_re=".*Guardar como.*|.*Save As.*|.*Save Print Output As.*")
                if windows:
                    app = Application(backend="win32").connect(handle=windows[0])
                    dlg = app.window(handle=windows[0])
                    break
            except findwindows.ElementNotFoundError:
                pass
            await asyncio.sleep(0.5)  # espera no bloqueante

        if dlg is None:
            print("❌ No se encontró el diálogo 'Save As / Print Output As'")
            return

        dlg.wait('visible', timeout=5)
        dlg.print_control_identifiers()

        # Guardar el archivo automáticamente
        filename = f"document_{int(asyncio.get_event_loop().time() * 1000)}.pdf"
        dlg['Edit'].set_edit_text(str(filename))
        # Esperar hasta que el campo contenga el filename
        for _ in range(10):
            current_text = dlg['File name:Edit'].texts()[0]
            if current_text == str(filename):
                break
            await asyncio.sleep(0.2)
        dlg['Save'].click()  # botón Guardar
        print(f"✅ Archivo guardado en: {filename}")
        

# =================================== MAIN ================================================
async def main():
    main_page, context, browser, playwright = await create_instance()
    print("🌐 Main page created.")
    await main_page.goto("https://my.momook.com/react-ui/login")
    print("🌐 Main page loaded:", await main_page.title())

    await login(main_page)
    print("🕒 Waiting for user actions (press ESC to exit)...")

    # Attach request handler
    main_page.on("request", lambda req: asyncio.create_task(handle_request(context, req)))

    # Keep browser open until manually closed
    while not main_page.is_closed():
        await asyncio.sleep(0.5)

    print("🛑 Browser closing...")
    await browser.close()
    await playwright.stop()
    print("✅ Browser closed successfully.")

# =================================== RUN ================================================
asyncio.run(main())