import fitz 
import os
import time
import asyncio
import subprocess
import threading
import re
import pytesseract
from pdf2image import convert_from_path
from PIL import Image, ImageEnhance, ImageFilter
import cv2
import numpy as np
import pdfplumber




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

def rotate_pdf(pdf_path, output_path, degrees=90):
    """
    Rotate all the pages of a PDF.
    
    pdf_path: Original pdf path
    output_path: Path for rotated pdf
    degrees: 90, 180, 270
    """
    doc = fitz.open(pdf_path)
    
    for page in doc:
        page.set_rotation(degrees)  # rota la página
    
    # Guardar de forma segura
    temp_path = pdf_path + ".tmp"
    doc.save(temp_path)
    doc.close()
    os.replace(temp_path, output_path)
    print(f"✔ Rotated PDF saved in: {output_path}")

#==================================== INSERT SIGNATURE ================================
def insert_signature(pdf_path, signature_path, coords, techlog_name):
    import time
    import fitz
    import os

    # ---- sanitize filename ----
    safe_name = techlog_name.replace(":", "-")

    # ---- wait until pdf exists ----
    timeout = 10
    start = time.time()
    print(f"⏳ Esperando a que el PDF exista: {pdf_path}")

    while time.time() - start < timeout:
        if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0:
            print("✅ PDF encontrado, abriendo...")
            break
        time.sleep(0.3)
    else:
        print("❌ ERROR: El PDF no apareció a tiempo, no se puede firmar.")
        return None

    # --- build final path ---
    folder = os.path.dirname(pdf_path)
    new_path = os.path.join(folder, f"{safe_name}.pdf")

    counter = 1
    while os.path.exists(new_path):
        new_path = os.path.join(folder, f"{safe_name}_{counter}.pdf")
        counter += 1

    # --- ensure original PDF is not locked ---
    try:
        tmp = fitz.open(pdf_path)
        tmp.close()
        time.sleep(0.2)
    except:
        print("⚠ El PDF está bloqueado por otro proceso.")
        return None

    # --- insert signature ---
    try:
        x, y, n, m = coords
        doc = fitz.open(pdf_path)
        page = doc[-1]
        rect = fitz.Rect(x, y, n, m)
        page.insert_image(rect, filename=signature_path, rotate=90)
    except Exception as e:
        print("❌ Error inserting the image:", e)
        return None

    # --- save with safe options ---
    try:
        doc.save(new_path, garbage=4, deflate=True)
        doc.close()
        print(f"✔ PDF firmado guardado como: {new_path}")
        return new_path
    except Exception as e:
        print("❌ Error saving the signed PDF:", e)
        return None


# ================Clean signature folder===============================

def clean_signature_folder():

    signaure_path = r"C:\Users\Jose A\Desktop\momook_signature\data\Techlogs\signature\signature.png"
    status_path = r"C:\Users\Jose A\Desktop\momook_signature\data\Techlogs\signature\WacomStatus.txt"
    try:
        if os.path.exists(signaure_path):
            os.remove(signaure_path)

        if os.path.exists(status_path):
            os.remove(status_path)   
    except:

        print("Error removing files in signature folder")
    
# ===================== Wait for signature image ========================================
def wait_for_image(file_path = r"C:\Users\Jose A\Desktop\momook_signature\data\Techlogs\signature\signature.png", timeout=10):
    """
    Espera hasta que exista el archivo de imagen.

    :param file_path: Ruta del archivo a comprobar
    :param timeout: Tiempo máximo de espera en segundos
    :return: 1 si el archivo aparece, 0 si se alcanza el timeout
    """
    start_time = time.time()

    while True:
        if os.path.exists(file_path):
            return 1

        if time.time() - start_time > timeout:
            return 0

        time.sleep(0.05)  # pequeña pausa para no saturar CPU


# =============================== Wait for status txt to be available ===========================

def wait_for_status(file_path=r"C:\Users\Jose A\Desktop\momook_signature\data\Techlogs\signature\WacomStatus.txt", timeout=10):


    """
    Espera hasta que el archivo `status.txt` exista y tenga contenido.
    Devuelve la primera línea como string.
    Si se alcanza el timeout (segundos), devuelve None.
    """
    start_time = time.time()
    
    while True:
        if os.path.exists(file_path):
            with open(file_path, "r") as f:
                line = f.readline().strip()
                if line:  # Si hay algo escrito
                    return line
        # Timeout
        if time.time() - start_time > timeout:
            return None
        time.sleep(0.1)  # evitar consumir CPU


