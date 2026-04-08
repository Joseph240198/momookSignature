from playwright.async_api import async_playwright, TimeoutError
import asyncio
from pathlib import Path
import time
from pywinauto import Application, Desktop, findwindows
import ctypes
import os
import win32print, win32api
import subprocess
from utils.utils import rotate_pdf, insert_signature, find_save_button, clean_signature_folder, wait_for_image, wait_for_status
import threading
from utils.ui_lib import UILibrary 
from utils.pdf_reader import generate_techlog_name, sort_techlog

#PRUEBA git 2
USERNAME = "j.soler@baatraining.com"
PASSWORD = "2401199883cCc"
EDGE_PATH = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
FOLDER_PATH = r"C:\Users\Jose A\Desktop\momook_signature\data\Techlogs\downloads"
SUMATRA = r"C:\Users\Jose A\AppData\Local\SumatraPDF"
PRINTER_NAME = "ingeniero buena"
WACOM_EXE_PATH = r"C:\Users\Jose A\Desktop\WacomSTU_Console\bin\Debug\WacomSTU_Console.exe"
SIGNATURE_IMAGE = r"C:\Users\Jose A\Desktop\momook_signature\data\Techlogs\signature\signature.png"
POPLER_PATH = r"C:\Users\Jose A\Desktop\poppler-25.12.0\Library\bin"
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

    ui = UILibrary()
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
            try:
                # Run wacom exe
                process = subprocess.Popen([WACOM_EXE_PATH],
                                stdin=subprocess.PIPE,
                                stdout=subprocess.PIPE,
                                text=True)
                

                # Runs in the background
                print("WacomSTU Console running in background")
            except:
                print("Error opening wacom tablet")
            
            ui.mostrar_mensaje("Please, sign on the tablet. Then click ok or cancel to continue.")
            status = wait_for_status(timeout=30)
            
            if status == "OK":
                print(status)
                signature_exists = wait_for_image(timeout = 30)
                if signature_exists:
                    techlog_name = generate_techlog_name(full_path)
                    new_path = insert_signature(full_path, SIGNATURE_IMAGE, (339.35, 547.49, 360.19, 678.42), techlog_name)
                    ui.cerrar_mensaje()
                    time.sleep(0.2)
                    clean_signature_folder()
                    sort_techlog(new_path)
                    return
                
                else:
                    print("Error: No signature found")
                    
            if status is None:
                print("No message received (timeout)")  
                #remove downloaded PDF
                os.remove(full_path)
                ui.cerrar_mensaje()
                process.terminate()
                #clean signature folder
                clean_signature_folder()
                

            if status == "CANCEL":
                #remove downloaded PDF
                os.remove(full_path)
                ui.cerrar_mensaje()
                #clean signature folder
                clean_signature_folder()

        except:
            print("❌ Error inserting signature")
            ui.cerrar_mensaje()
            clean_signature_folder()
        
        # ============ Rename techlogs =================
        

# ======================================================================================       
# =================================== MAIN =============================================
async def main():
    clean_signature_folder()
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