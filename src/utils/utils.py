import fitz 
import os
import time
import traceback
from pdf2image import convert_from_path
import json





def find_save_button(dlg):
    # 1. Buscar por nombre exacto (Windows inglés)
    try:
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
    
    except Exception as e:
        traceback.print_exc()
        return None


def rotate_pdf(pdf_path, output_path, degrees=90):
    """
    Rotate all the pages of a PDF.
    
    pdf_path: Original pdf path
    output_path: Path for rotated pdf
    degrees: 90, 180, 270
    """
    try:
        doc = fitz.open(pdf_path)
        
        for page in doc:
            page.set_rotation(degrees)  # rotate the page
        
        # Guardar de forma segura
        temp_path = pdf_path + ".tmp"
        doc.save(temp_path)
        doc.close()
        os.replace(temp_path, output_path)
        print(f"✔ Rotated PDF saved in: {output_path}")
    except Exception as e:
        traceback.print_exc()

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
        traceback.print_exc()
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
        traceback.print_exc()
        return None

    # --- save with safe options ---
    try:
        doc.save(new_path, garbage=4, deflate=True)
        doc.close()
        print(f"✔ PDF firmado guardado como: {new_path}")
        return new_path
    except Exception as e:
        print("❌ Error saving the signed PDF:", e)
        traceback.print_exc()
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
    except Exception as e:
        print("Error removing files in signature folder")
        traceback.print_exc()
  
# ===================== Wait for signature image ========================================
def wait_for_image(file_path = r"C:\Users\Jose A\Desktop\momook_signature\data\Techlogs\signature\signature.png", timeout=10):
    """
    Waits until image file exist.

    :param file_path: path ofh the file to check
    :param timeout: timeout in seconds
    :return: 1 if file exist, 0 if timeout reached
    """
    try:
        start_time = time.time()

        while True:
            if os.path.exists(file_path):
                return 1

            if time.time() - start_time > timeout:
                return 0

            time.sleep(0.05)  # pequeña pausa para no saturar CPU

    except Exception as e:
        traceback.print_exc()


# =============================== Wait for status txt to be available ===========================

def wait_for_status(file_path=r"C:\Users\Jose A\Desktop\momook_signature\data\Techlogs\signature\WacomStatus.txt", timeout=10):

    """
    Waits until 'status.txt' exists and has content.
    Returns first line as string
    If timeout reached returns None
    """
    try:
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
            
    except Exception as e:
        traceback.print_exc()


def load_paths():

    with open("config/paths.json") as f:
        paths = json.load(f)

    base_project = paths["base_dirs"]["projects"]
    user_dir = paths["base_dir"]["user_dir"]
    c_dir = paths["base_dir"]["c_dir"]

    return {
        "EDGE_PATH" : os.path.join(c_dir, paths["software"]["edge_exe"]),
        "FOLDER_PATH" : os.path.join(base_project, paths["techlog"]["input_pdf"]),
        "SUMATRA" : r"C:\Users\Jose A\AppData\Local\SumatraPDF",
        "WACOM_EXE_PATH" : os.path.join(base_project, paths["wacom"]["exe_path"]),
        "SIGNATURE_IMAGE" : os.path.join(base_project, paths["techlog"]["signature_image"]),
        "POPLER_PATH" : os.path.join(user_dir, paths["software"]["popler"])
    }
