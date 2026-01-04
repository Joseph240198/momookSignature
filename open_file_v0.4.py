from playwright.async_api import async_playwright, TimeoutError
import asyncio
from pathlib import Path
import time
from pywinauto import Application, Desktop, findwindows
import fitz 
import os
import win32print, win32api
import subprocess

#PRUEBA git 2
USERNAME = "j.soler@baatraining.com"
PASSWORD = "2401199883$cC"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FOLDER_PATH = r"C:\Users\Jose A\Desktop\momook_signature\Techlogs"
SUMATRA = r"C:\Users\Jose A\AppData\Local\SumatraPDF"
PRINTER_NAME = "ingeniero buena"
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

#==================================== INSERT SIGNATURE ================================
async def insert_signature(pdf_path, signature_path, coords):
    """
    Insert image signature inside the pdf
    
    pdf_path: string path to pdf
    signature_path: path to the signature, image file
    coords: coordinates where signature is to be inserted in pdf
    """
    printer_name = "ingeniero buena"
    # ---- 1) ESPERAR A QUE EL PDF EXISTA ----
    timeout = 10
    start = time.time()
    print(f"⏳ Esperando a que el PDF exista: {pdf_path}")

    while time.time() - start < timeout:
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            print("✅ PDF encontrado, abriendo...")
            break
        await asyncio.sleep(0.3)
    else:
        print("❌ ERROR: El PDF no apareció a tiempo, no se puede firmar.")
        return
     # --- 1. Crear nombre automático ---
    base, ext = os.path.splitext(pdf_path)
    new_path = f"{base}_signed{ext}"

    # Si ya existe, crear uno incremental
    counter = 1
    while os.path.exists(new_path):
        new_path = f"{base}_signed_{counter}{ext}"
        counter += 1

    x, y, n, m = coords
    doc = fitz.open(pdf_path)
    page = doc[-1]
    rect = fitz.Rect(x, y, n, m)
    page.insert_image(rect, filename=signature_path, rotate=90)
    doc.save(new_path)
    doc.close()
    print(f"✔ PDF signed and saved in: {new_path}")

    try:
        print_pdf(pdf_path, PRINTER_NAME)
        print(f"PDF printed in {PRINTER_NAME}")
    except:
        print("PDF not printed")


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

        full_pdf_path = os.path.join(r"C:\Users\Jose A\Desktop\momook_signature\Techlogs", filename)
        await insert_signature(full_pdf_path, r"C:\Users\Jose A\Desktop\momook_signature\Techlogs\signature.png", (339.35, 547.49, 360.19, 678.42))


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