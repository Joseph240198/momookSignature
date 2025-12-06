from playwright.async_api import async_playwright, TimeoutError
import asyncio
from pathlib import Path
from pywinauto import Desktop

USERNAME = "j.soler@baatraining.com"
PASSWORD = "2401199883$cC"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FOLDER_PATH = r"C:\Users\Jose A\Desktop\momook_signature\Techlogs"
Path(FOLDER_PATH).mkdir(exist_ok=True)

async def create_instance():
    """Crea el navegador y el contexto"""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=False,
        channel="chrome",
        args=["--kiosk-printing",  f'--download.default_directory={FOLDER_PATH}',
        "--disable-prompt-on-repost"]      
        
        
    )
    context = await browser.new_context()
    page = await context.new_page()
    return page, context, browser, playwright

async def login(page):
    await page.fill('input[name="username"]', USERNAME)
    await page.fill('input[name="password"]', PASSWORD)
    await page.click("button:has-text('Login')")
    print("✅ Logged in")

# =================================== ENTER PATH TO SAVE FILE =====================================
def _fill_save_dialog(filepath: str, timeout: int):
    """Interact with Windows 'Save As' dialog to fill filename and click Save."""
    dialog = Desktop(backend="uia").window(title_re=".*(Guardar|Save|Save print output as).*")
    dialog.wait("visible", timeout=timeout)

    file_edit = dialog.child_window(auto_id="1001", control_type="Edit")
    file_edit.wait("enabled", timeout=timeout)
    file_edit.type_keys(str(filepath), with_spaces=True)

    save_btn = dialog.child_window(title="Save", control_type="Button")
    save_btn.wait("enabled", timeout=timeout)
    save_btn.click()

# ==================================== ASYNC WRAPPER ===========================================
async def save_pdf_dialog(filepath: str, timeout: int = 10):
    """Runs the blocking pywinauto code in a separate thread."""
    await asyncio.to_thread(_fill_save_dialog, filepath, timeout)


# ========================================= MAIN ============================================
async def main():
    main_page, context, browser, playwright = await create_instance()
    print("🌐 Main page created.")
    await main_page.goto("https://my.momook.com/react-ui/login")
    print("🌐 Main page loaded:", await main_page.title())

    await login(main_page)
    print("✅ Logged in")
    print("🕒 Waiting for user actions (press ESC to exit)...")

    # Detecta cualquier solicitud de impresión
    async def handle_request(request):
        url = request.url
        if "/ffs/logs/" in url and url.endswith("/print"):
            print(f"🖨 Print URL intercepted: {url}")
             # Create unique file name
            filename = Path(FOLDER_PATH) / f"document_{int(asyncio.get_event_loop().time() * 1000)}.pdf"
            await save_pdf_dialog(filename, timeout=10)
    main_page.on("request", lambda req: asyncio.create_task(handle_request(req)))

    # Mantiene el navegador abierto hasta que cierres la ventana
    while not main_page.is_closed():
        await asyncio.sleep(0.5)

    print("🛑 Browser closing...")
    await browser.close()
    await playwright.stop()
    print("✅ Browser closed successfully.")


# ====================================== RUN ======================================

asyncio.run(main())