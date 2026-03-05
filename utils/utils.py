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
def insert_signature(pdf_path, signature_path, coords):
    """
    Insert image signature inside the pdf
    
    pdf_path: string path to pdf
    signature_path: path to the signature, image file
    coords: coordinates where signature is to be inserted in pdf
    """
    printer_name = "ingeniero buena"
   

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
        return
     # --- 1. Creat automatic name ---
    base, ext = os.path.splitext(pdf_path)
    new_path = f"{base}_signed{ext}"

    # if it exists, use incremental one
    counter = 1
    while os.path.exists(new_path):
        new_path = f"{base}_signed_{counter}{ext}"
        counter += 1
    

    try:
        x, y, n, m = coords
        doc = fitz.open(pdf_path)
        page = doc[-1]
        rect = fitz.Rect(x, y, n, m)
        page.insert_image(rect, filename=signature_path, rotate=90)
    except:
        print("Error inserting the image")

    try:
        doc.save(new_path)
        doc.close()
        print(f"✔ PDF signed and saved in: {new_path}")
    except:
        print("Error saving the signed pdf")

    
"""
    try:
        print_pdf(pdf_path, PRINTER_NAME)
        print(f"PDF printed in {PRINTER_NAME}")
    except:
        print("PDF not printed")
"""

# ================Clean signature folder===============================

def clean_signature_folder():

    signaure_path = r"C:\Users\Jose A\Desktop\momook_signature\Techlogs\signature\signature.png"
    status_path = r"C:\Users\Jose A\Desktop\momook_signature\Techlogs\signature\WacomStatus.txt"
    try:
        if os.path.exists(signaure_path):
            os.remove(signaure_path)

        if os.path.exists(status_path):
            os.remove(status_path)   
    except:

        print("Error removing files in signature folder")
    
# ===================== Wait for signature image ========================================
def wait_for_image(file_path = r"C:\Users\Jose A\Desktop\momook_signature\Techlogs\signature\signature.png", timeout=10):
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

def wait_for_status(file_path=r"C:\Users\Jose A\Desktop\momook_signature\Techlogs\signature\WacomStatus.txt", timeout=10):


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

def generate_name_pdf(ruta_pdf):
        """
        Extrae Start y Finish de un PDF basado en imagen usando OCR.
        """
        texto_completo = ""

        # Convertir PDF a imágenes
        paginas = convert_from_path(ruta_pdf)
        
        for img in paginas:
            # Rotar horizontal automáticamente si ancho > alto
            if img.width > img.height:
                img = img.rotate(90, expand=True)
            texto = pytesseract.image_to_string(img)
            texto_completo += texto + "\n"

        texto_completo = re.sub(r'\s+', ' ', texto_completo)

         #Buscar cualquier hora tipo 0830, 08:30, 08.30, 08;30
        horas = re.findall(r"\b\d{1,2}[:.;]?\d{2}\b", texto_completo)

        print("Horas detectadas:", horas)

        hora_start = "SIN_START"
        hora_finish = "SIN_FINISH"

        if len(horas) >= 1:
            hora_start = horas[0]

        if len(horas) >= 2:
            hora_finish = horas[1]

        # Normalizar formato a HH-MM
        hora_start = hora_start.replace(":", "-").replace(".", "-").replace(";", "-")
        hora_finish = hora_finish.replace(":", "-").replace(".", "-").replace(";", "-")

        
        return f"Start_{hora_start}_Finish_{hora_finish}.pdf"


def rename_pdf(ruta_pdf):
    nuevo_nombre = generate_name_pdf(ruta_pdf)
    directorio = os.path.dirname(ruta_pdf)
    nueva_ruta = os.path.join(directorio, nuevo_nombre)

    # Evitar sobreescribir
    contador = 1
    nombre_base, extension = os.path.splitext(nuevo_nombre)
    while os.path.exists(nueva_ruta):
        nueva_ruta = os.path.join(directorio, f"{nombre_base}_{contador}{extension}")
        contador += 1

    os.rename(ruta_pdf, nueva_ruta)
    return nueva_ruta

def mostrar_pdf_en_terminal(ruta_pdf, poppler_path=None):
    paginas = convert_from_path(ruta_pdf, dpi=300, poppler_path=poppler_path)

    # Indicar ruta de Tesseract si es necesario
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    for i, img in enumerate(paginas, start=1):
        # Girar 90° a la derecha
        img = img.rotate(-90, expand=True)

        # OCR
        texto = pytesseract.image_to_string(img)
        print(f"\n--- Página {i} ---\n")
        print(texto)
        print("\n------------------\n")

def ocr_preprocesado(ruta_pdf, poppler_path):
    """
    Convierte PDF a imágenes y muestra en terminal todo el texto detectado por OCR.
    Incluye rotación 90° a la derecha y preprocesamiento de imagen.
    """
    # Configurar Tesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Convertir PDF a imágenes de alta resolución
    paginas = convert_from_path(ruta_pdf, dpi=400, poppler_path=poppler_path)

    for i, img in enumerate(paginas, start=1):
        # Girar 90° a la derecha
        img = img.rotate(-90, expand=True)

        # Preprocesamiento
        img = img.convert("L")  # escala de grises
        img = ImageEnhance.Contrast(img).enhance(2)  # mejorar contraste
        img = img.point(lambda x: 0 if x < 140 else 255, '1')  # binarización
        img = img.filter(ImageFilter.MedianFilter())  # reducir ruido

        # OCR
        texto = pytesseract.image_to_string(img)

        print(f"\n--- Página {i} ---\n")
        print(texto)
        print("\n------------------\n")

def preprocess_image(pil_image):
    """Mejora la imagen para que Tesseract lea mejor."""
    img = np.array(pil_image)

    # Escala de grises
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Binarización
    gray = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)[1]

    # Suavizado
    gray = cv2.medianBlur(gray, 3)

    return gray



def create_searchable_pdf(input_pdf_path, output_pdf_path, poppler_path):
    """
    Convierte un PDF en un PDF searchable (OCR) y lo guarda SIEMPRE en output_pdf_path.
    """

    # Asegurar ruta absoluta
    input_pdf_path = os.path.abspath(input_pdf_path)
    output_pdf_path = os.path.abspath(output_pdf_path)

    # Configurar Tesseract
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    # Convertir PDF a imágenes
    try:
        pages = convert_from_path(input_pdf_path, dpi=300, poppler_path=poppler_path)
    except Exception as e:
        print("❌ Error convirtiendo PDF a imágenes:", e)
        return False

    pdf_bytes_total = b""

    # Procesar cada página
    for page in pages:
        processed = preprocess_image(page)

        try:
            pdf_bytes = pytesseract.image_to_pdf_or_hocr(
                processed,
                extension='pdf',
                lang='eng'
            )
        except Exception as e:
            print("❌ Error en OCR:", e)
            return False

        pdf_bytes_total += pdf_bytes

    # Guardar el PDF searchable
    try:
        with open(output_pdf_path, "wb") as f:
            f.write(pdf_bytes_total)
    except Exception as e:
        print("❌ Error guardando el PDF searchable:", e)
        return False

    print("✅ PDF searchable creado en:", output_pdf_path)
    print("📄 Existe el archivo:", os.path.exists(output_pdf_path))

    return True



def read_pdf_and_print(pdf_path):
    """
    Reads a searchable PDF and prints detected text to console.
    """

    extracted_text = ""

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            extracted_text += page.extract_text() or ""

    print("\n----- EXTRACTED TEXT -----\n")
    print(extracted_text)
    print("\n--------------------------\n")

def get_searchable_pdf_path(original_path):
    """
    Returns a new path adding '_searchable' before the file extension.
    """

    directory = os.path.dirname(original_path)
    filename = os.path.basename(original_path)

    name, extension = os.path.splitext(filename)

    new_filename = f"{name}_searchable{extension}"

    return os.path.join(directory, new_filename)