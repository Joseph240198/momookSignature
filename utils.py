import fitz 
import os
import time
import asyncio


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
async def insert_signature(pdf_path, signature_path, coords):
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
        await asyncio.sleep(0.3)
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

    x, y, n, m = coords
    doc = fitz.open(pdf_path)
    page = doc[-1]
    rect = fitz.Rect(x, y, n, m)
    page.insert_image(rect, filename=signature_path, rotate=90)
    doc.save(new_path)
    doc.close()
    print(f"✔ PDF signed and saved in: {new_path}")
"""
    try:
        print_pdf(pdf_path, PRINTER_NAME)
        print(f"PDF printed in {PRINTER_NAME}")
    except:
        print("PDF not printed")
"""