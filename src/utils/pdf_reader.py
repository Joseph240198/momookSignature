import pytesseract
from pdf2image import convert_from_path
import re
import cv2
import numpy as np
import os


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPLER_PATH = r"C:\Users\Jose A\Desktop\momook_signature\src\utils\poppler-25.12.0\Library\bin"
FILE_PATH = r"C:\Users\Jose A\Desktop\momook_signature\data\Techlogs\document_1773235104435.pdf"
OUTPUT_IMAGE_PATH = r"C:\Users\Jose A\Desktop\momook_signature\data\images\debug_images\image.png"

# DATE ZONE
x1_date, y1_date = 1735, 1565
x2_date, y2_date = 2007, 1621

# START HOUR ZONE
x1_start, y1_start = 3165, 1489
x2_start, y2_start = 3663, 1550

# FINISH HOUR ZONE
x1_finish, y1_finish = 3167, 1569
x2_finish, y2_finish = 3670, 1626

#SIMULATOR ID ZONE
x1_sim, y1_sim = 3875, 568
x2_sim, y2_sim = 4506, 641

def rotate_pdf_and_convert_to_image(pdf_path, output_image_path, poppler_path):
    """
    Rota un PDF de una sola página -90 grados y lo convierte a imagen PNG.
    Guarda la imagen en output_image_path.
    """

    # Convertir PDF a imagen (solo 1 página)
    pages = convert_from_path(pdf_path, dpi=400, poppler_path=poppler_path)

    if len(pages) == 0:
        print("❌ Can not convert PDF to image.")
        return None

    # Primera (y única) página
    img = pages[0]

    # Rotar -90 grados
    rotated = img.rotate(-90, expand=True)

    # Guardar imagen
    rotated.save(output_image_path, "PNG")

    print("✅ Imagen generada en:", output_image_path)
    return rotated

def generate_crops(rotated_image):
   
    if rotated_image is not None:
        rotated_np = np.array(rotated_image)
        # Recortes
        date_crop   = rotated_np[y1_date:y2_date, x1_date:x2_date]
        start_crop  = rotated_np[y1_start:y2_start, x1_start:x2_start]
        finish_crop = rotated_np[y1_finish:y2_finish, x1_finish:x2_finish]
        sim_crop = rotated_np[y1_sim:y2_sim, x1_sim:x2_sim]

        # Guardar crops originales
        save_crop(date_crop,   "date_raw.png")
        save_crop(start_crop,  "start_raw.png")
        save_crop(finish_crop, "finish_raw.png")
        save_crop(sim_crop, "sim_raw.png")
        return date_crop, start_crop, finish_crop, sim_crop
        
    else:
        print("image is none")
    

def preprocess(img):
    img = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2GRAY)
    img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    img = cv2.GaussianBlur(img, (5, 5), 0)
    _, img = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    kernel = np.ones((3, 3), np.uint8)
    img = cv2.dilate(img, kernel, iterations=1)
    return img

def ocr_text(img):
    config = "--psm 6 -c tessedit_char_whitelist=0123456789:-"
    return pytesseract.image_to_string(img, config=config)

def save_crop(img, name, folder="crops"):
    os.makedirs(folder, exist_ok=True)
    path = os.path.join(folder, name)
    cv2.imwrite(path, img)
    return path

def extract_fields_from_crops(date_crop, start_crop, finish_crop, sim_crop):
    # Preprocesado
    date_img   = preprocess(date_crop)
    start_img  = preprocess(start_crop)
    finish_img = preprocess(finish_crop)
    sim_img = preprocess(sim_crop)

    # OCR
    date_text   = ocr_text(date_img)
    start_text  = ocr_text(start_img)
    finish_text = ocr_text(finish_img)
    sim_text = ocr_text(sim_img)

    # Extracción
    date_match   = re.search(r"\d{4}-\d{2}-\d{2}", date_text)
    start_match  = re.search(r"\d{1,2}:\d{2}", start_text)
    finish_match = re.search(r"\d{1,2}:\d{2}", finish_text)
    sim_match = re.search(r"[A-Za-z0-9.]+", sim_text)

    return {
        "date": date_match.group(0) if date_match else None,
        "start": start_match.group(0) if start_match else None,
        "finish": finish_match.group(0) if finish_match else None,
        "sim": sim_match.group(0) if sim_match else None,

        # Raw text para depuración
        "raw_date": date_text,
        "raw_start": start_text,
        "raw_finish": finish_text,
        "raw_sim": sim_text
    }

    
def generate_techlog_name(file_path):
    image = rotate_pdf_and_convert_to_image(file_path, OUTPUT_IMAGE_PATH, POPLER_PATH)
    date_crop, start_crop, finish_crop, sim_crop = generate_crops(image)
    result = extract_fields_from_crops(date_crop, start_crop, finish_crop, sim_crop)
    sim    = result.get("sim", "")
    date   = result.get("date", "")
    start  = result.get("start", "")
    finish = result.get("finish", "")

    # Construir nombre final
    techlog_name = f"{sim}_{date}_{start}_{finish}"

    return techlog_name

















