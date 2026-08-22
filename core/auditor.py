# erp-automation/core/auditor.py

import os
import sys
import importlib.util
import logging

# Supaya pesan WARNING dari PaddleOCR (`ppocr`) tidak muncul saat module di-import,
# set level logger lebih awal sebelum `paddleocr` di-import atau dipanggil.
logging.getLogger("ppocr").setLevel(logging.ERROR)

# Atasi bug C++ PaddlePaddle pada CPU
os.environ["FLAGS_enable_pir_api"] = "0"
os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

# --- START: BONGKAR ERROR ASLI PADDLEOCR ---
spec = importlib.util.find_spec("paddleocr")
if spec and spec.submodule_search_locations:
    paddleocr_dir = spec.submodule_search_locations[0]
    sys.path.insert(0, paddleocr_dir)
    try:
        from tools.infer import predict_system
        print("✅ Mesin PaddleOCR sehat dan berhasil di-load!")
    except Exception as e:
        print("\n" + "🔥"*25)
        print("🚨 INI DIA PENYAKIT ASLINYA:")
        import traceback
        traceback.print_exc()
        print("🔥"*25 + "\n")
        sys.exit(1)
    sys.path.pop(0)
# --- END: BONGKAR ERROR ASLI PADDLEOCR ---

import json
import time
import tempfile
import cv2
import numpy as np
import pyautogui
from PIL import Image, ImageOps
from rapidfuzz import process, fuzz
import threading
from core.logger import BotLogger
from config.speed_settings import SPEED_LEVELS
import config.state as bot_state
from core.ui_helper import ui 
from core.settings_manager import settings

# Import PaddleOCR 
from paddleocr import PaddleOCR

COORD_FILE = "coordinates_phase2.json"
MASTER_FILE = "master_data.json"
MAX_TOLERANCE_RP = 100.0

class TimeoutInput:
    """Helper untuk input dengan countdown timer (Non-Blocking OS Level)"""
    
    @staticmethod
    def wait_for_input(timeout_sec):
        print(f"   ⏳ Menunggu respon... (Auto-Reject dalam {timeout_sec}s)")
        print("   👉 Tekan [ENTER] untuk Input Data, atau diamkan untuk Reject.")
        
        if sys.platform == 'win32':
            import msvcrt
            # Bersihkan sisa ketikan sebelumnya (Flush buffer)
            while msvcrt.kbhit():
                msvcrt.getch()
                
            start_time = time.time()
            while time.time() - start_time < timeout_sec:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch in [b'\r', b'\n']:
                        print() # Turun baris biar rapi
                        return True
                time.sleep(0.1)
            return False
        else:
            import select
            r, _, _ = select.select([sys.stdin], [], [], timeout_sec)
            if r:
                sys.stdin.readline()
                return True
            return False

    @staticmethod
    def get_choice_with_timeout(timeout_sec, default_choice='2'):
        print(f"   ⏳ Auto-Reject dalam {timeout_sec}s...")
        
        if sys.platform == 'win32':
            import msvcrt
            # Bersihkan sisa ketikan sebelumnya
            while msvcrt.kbhit():
                msvcrt.getch()
                
            start_time = time.time()
            input_str = ""
            
            while time.time() - start_time < timeout_sec:
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    if ch in [b'\r', b'\n']:
                        print()
                        return input_str.strip() if input_str.strip() else default_choice
                    elif ch == b'\x08': # Handle tombol Backspace
                        if len(input_str) > 0:
                            input_str = input_str[:-1]
                            sys.stdout.write('\b \b')
                            sys.stdout.flush()
                    else:
                        try:
                            char = ch.decode('utf-8')
                            input_str += char
                            sys.stdout.write(char)
                            sys.stdout.flush()
                        except:
                            pass
                time.sleep(0.05)
            print() # Turun baris kalau timeout
            return default_choice
        else:
            import select
            r, _, _ = select.select([sys.stdin], [], [], timeout_sec)
            if r:
                val = sys.stdin.readline().strip()
                return val if val else default_choice
            return default_choice
    
    @staticmethod
    def get_valid_input(prompt, valid_opts):
        while True:
            val = input(prompt).strip().lower()
            if val in valid_opts: return val
            print(f"   ❌ Pilihan tidak valid! Masukkan salah satu: {valid_opts}")  

class ERP_Auditor:
    def __init__(self, speed_profile=None, auto_skip_unknown=False):
        self.coords = self.load_json(COORD_FILE)
        self.load_database()
        
        self.spd = speed_profile if speed_profile else SPEED_LEVELS['1']
        self.auto_skip_unknown = auto_skip_unknown
        
        # --- [FIX] BUNGKAM WARNING "ANGLE CLASSIFIER" PADDLEOCR ---
        class SuppressOCRWarnings(logging.Filter):
            def filter(self, record):
                # Cegat pesan yang mengandung kata "angle classifier"
                return "angle classifier" not in record.getMessage().lower()
                
        ppocr_logger = logging.getLogger("ppocr")
        ppocr_logger.setLevel(logging.ERROR)
        ppocr_logger.addFilter(SuppressOCRWarnings())
        self.ocr_engine = PaddleOCR(use_angle_cls=False, lang='en', use_space_char=True, show_log=False)
        ppocr_logger.setLevel(logging.ERROR)
        
        self.consecutive_empty_rows = 0
        self.last_line_image = None
        self.stuck_counter = 0
        self.last_line_no = -1
        
        self.bucket_eligible_for_footer = 0.0 
        self.bucket_netto_items = 0.0         
        self.bucket_non_taxable = 0.0 
        self.total_gross_items = 0.0          

        hk_config = self.coords.get('save_hotkey')
        self.save_key = hk_config['value'] if hk_config else 'f3'

    def load_json(self, filepath):
        try:
            with open(filepath, 'r') as f: return json.load(f)
        except FileNotFoundError:
            BotLogger.error(f"Error: {filepath} gak ada!")
            sys.exit(1)

    def load_database(self):
        """Load DB dan handle struktur items/rules"""
        raw = self.load_json(MASTER_FILE)
        if 'items' in raw:
            self.master_data = raw
        else:
            self.master_data = {'items': raw, 'rules': {}}
        
        self.rules = self.master_data.get('rules', {})
        self.reload_normalization_cache()

    def reload_normalization_cache(self):
        self.master_keys_norm = {}
        if 'items' in self.master_data:
            for k in self.master_data['items']:
                norm = self.normalize_string(k)
                self.master_keys_norm[norm] = k

    def normalize_string(self, text):
        text = text.upper()
        # 1. Hapus spasi dulu biar simbol yang kepisah (contoh: / \) bisa nyambung
        text = text.replace(' ', '')
        return "".join(e for e in text if e.isalnum())

    def safe_save_json(self, data, filepath):
        dir_name = os.path.dirname(filepath) or '.'
        fd, temp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
        try:
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=4)
            os.replace(temp_path, filepath)
        except Exception as e:
            os.remove(temp_path)
            raise e

    def handle_unknown_item_interactive(self, ocr_name):
        ui.play_sfx("alert")
        print("\n" + "!"*60)
        print(f"🚨 UNKNOWN ITEM: [{ocr_name}]")
        
        # [FIX] Use Settings
        cfg = settings.get('timeout_unknown')
        if cfg is not None and cfg['enabled']:
            if not TimeoutInput.wait_for_input(cfg['seconds']):
                return False # Timeout -> Reject
        else:
            print("   👉 Tekan [ENTER] untuk Input Data")
            print("   👉 Ketik 's' lalu [ENTER] untuk SKIP/REJECT SO ini")
            ans = input("   Pilihan: ").strip().lower()
            if ans == 's':
                print("   ⏩ Skipping SO by user request...")
                return False # Langsung reject
            
        # [NEW] Smart Suggestion Logic
        print("\n💡 MENCARI KEMIRIPAN...")
        keys = list(self.master_data.get('items', {}).keys())
        matches = process.extract(ocr_name, keys, scorer=fuzz.WRatio, limit=3, score_cutoff=60.0)
        
        suggestions = []
        if matches:
            print("   Ditemukan barang serupa:")
            for i, match_tuple in enumerate(matches):
                m = match_tuple[0] # Ambil string namanya saja
                data = self.master_data['items'][m]
                p = data['base_price']
                d = "+".join([str(x) for x in data['default_discs'] if x > 0]) or "0"
                print(f"   [{i+1}] {m} (Rp {p:,.0f}) | Disc: {d}%")
                suggestions.append(data)
        else:
            print("   (Tidak ada barang mirip)")

        print("\n📝 MODE INPUT DATA BARU")
        final_name = input(f"   Nama Barang (Enter='{ocr_name}', 'b' batal): ").strip() or ocr_name
        if final_name.lower() == 'b':
            print("   ⏩ Dibatalkan. Skipping SO...")
            return False
        
        # Init variables to avoid 'undefined' error
        price = 0.0
        discs = [0.0]*4
        is_netto = False
        price_val = True
        is_taxable = True
        goto_save = False

        while True:
            try:
                raw_p = input("   💰 Harga (Rp) / Pilih [1-3] atau 'b' batal: ").strip()
                if raw_p.lower() == 'b':
                    print("   ⏩ Dibatalkan. Skipping SO...")
                    return False
                
                # Cek apakah user milih nomor saran?
                if raw_p.isdigit() and 1 <= int(raw_p) <= len(suggestions):
                    # AUTO-FILL DARI SARAN
                    chosen = suggestions[int(raw_p)-1]
                    price = chosen['base_price']
                    discs = chosen['default_discs']
                    is_netto = chosen['is_netto']
                    price_val = chosen.get('price_validation', True)
                    is_taxable = chosen.get('is_taxable', True)
                    
                    print(f"   ✅ Auto-Fill: Rp {price:,.0f} | Netto: {is_netto}")
                    goto_save = True 
                    break
                
                price = float(raw_p.replace(',', '').replace('.', ''))
                goto_save = False
                break
            except: print("   ❌ Angka woy!")
            
        if not goto_save:
            print("   Tipe: [1] Reguler  [2] Netto  [3] Jasa")
            type_in = TimeoutInput.get_valid_input("   Pilih: ", ['1', '2', '3'])
            
            is_netto = (type_in in ['2', '3'])
            price_val = (type_in != '3')
            tax_in = TimeoutInput.get_valid_input("   Kena PPN? (1=Ya, 0=Tdk): ", ['1', '0', 'y', 'n'])
            is_taxable = (tax_in in ['1', 'y'])

            if type_in == '1':
                raw_disc = input("   🏷️  Diskon (Cth: 45+10): ").strip()
                parts = raw_disc.replace('%','').split('+')
                for i, p in enumerate(parts):
                    if i < 4:
                        try: discs[i] = float(p)
                        except: pass
        
        # Input Rule Baru (Opsional)
        new_rule = None
        rule_in = TimeoutInput.get_valid_input("   📐 Ada Price Rule? (1=Ya, 0=Tdk): ", ['1', '0', 'y', 'n'])
        has_rule = (rule_in in ['1', 'y'])
        if has_rule:
            print("   👉 Format: variable operator nilai (cth: m2 <= 0.5)")
            rule_str = input("   Logika: ").strip()
            disc_str = input("   Diskon %: ").strip()
            
            print("   Mode: [1] NORMAL  [2] FLAT M2  [3] ALLOW UPS")
            mode_in = TimeoutInput.get_valid_input("   Pilih [1/2/3]: ", ['1', '2', '3'])
            if mode_in == '2': calc_mode = "FLAT_M2"
            elif mode_in == '3': calc_mode = "ALLOW_UPS"
            else: calc_mode = "NORMAL"

            try:
                new_rule = {'logic': rule_str, 'disc': float(disc_str), 'mode': calc_mode}
            except: print("   ❌ Rule invalid, skip.")

        # Input Harga Alternatif (Opsional)
        alternatives = []
        alt_in = TimeoutInput.get_valid_input("   🔀 Ada Harga Alt? (1=Ya, 0=Tdk): ", ['1', '0', 'y', 'n'])
        has_alt = (alt_in in ['1', 'y'])
        if has_alt:
            print("   👉 Masukkan harga alternatif (Ketik 'q' untuk selesai)")
            while True:
                raw_alt = input("   💰 Harga Alt (Rp): ").strip()
                if raw_alt.lower() == 'q' or not raw_alt: break
                try:
                    p_alt = float(raw_alt.replace(',', '').replace('.', ''))
                    t_in = TimeoutInput.get_valid_input("      Kena PPN? (1=Ya, 0=Tdk): ", ['1', '0', 'y', 'n'])
                    t_alt = (t_in in ['1', 'y'])
                    n_alt = input("      Catatan: ").strip()
                    alternatives.append({"price": p_alt, "is_taxable": t_alt, "note": n_alt})
                except: print("      ❌ Angka woy!")

        # Save logic
        new_entry = {
            "base_price": price, "default_discs": discs,
            "price_validation": price_val, "is_netto": is_netto, "is_taxable": is_taxable
        }
        if new_rule: new_entry['custom_rule'] = new_rule
        if alternatives: new_entry['alternatives'] = alternatives

        self.master_data['items'][final_name] = new_entry
        
        try:
            self.safe_save_json(self.master_data, MASTER_FILE)
            self.reload_normalization_cache()
            print("💾 Database Updated! Melanjutkan audit...")
            return True
        except Exception as e: 
            BotLogger.error(f"Gagal simpan JSON: {e}")
            return False

    def preprocess_image(self, img_pil, mode='standard', padding=0):
        img_np = np.array(img_pil.convert('L'))
        h_raw, w_raw = img_np.shape
        bg_color = int(np.median(img_np))

        if h_raw > 4 and w_raw > 4:
            img_np[0:1, :] = bg_color
            img_np[h_raw-1:h_raw, :] = bg_color

        if mode == 'repair_broken_font':
            img_np = cv2.resize(img_np, None, fx=5, fy=5, interpolation=cv2.INTER_CUBIC)
            _, thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
            h_t, w_t = thresh.shape
            border_cut = int(h_t * 0.25)
            thresh[0:border_cut, :] = 0
            thresh[h_t-border_cut:h_t, :] = 0
            kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3,3))
            thresh = cv2.dilate(thresh, kernel, iterations=1)
            coords = cv2.findNonZero(thresh)
            if coords is not None:
                x, y, w, h = cv2.boundingRect(coords)
                thresh = thresh[y:y+h, x:x+w]
            result = cv2.bitwise_not(thresh)
            img_final = cv2.copyMakeBorder(result, 20, 20, 20, 20, cv2.BORDER_CONSTANT, value=255)
            img_final = Image.fromarray(img_final)
        elif mode == 'name_safe':
            height, width = img_np.shape
            img_np = cv2.resize(img_np, (width * 3, height * 3), interpolation=cv2.INTER_LINEAR)
            _, thresh = cv2.threshold(img_np, 120, 255, cv2.THRESH_BINARY)
            img_final = Image.fromarray(thresh)
        else:
            height, width = img_np.shape
            img_np = cv2.resize(img_np, (width * 3, height * 3), interpolation=cv2.INTER_CUBIC)
            _, thresh = cv2.threshold(img_np, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
            
            if mode == 'standard':
                if np.mean(thresh) < 127: thresh = cv2.bitwise_not(thresh)
            elif mode == 'remove_vertical':
                if np.mean(thresh) > 127: thresh = cv2.bitwise_not(thresh)
                cnts, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                for c in cnts:
                    x,y,w,h = cv2.boundingRect(c)
                    if (h > w*5) and (h > height*0.85): cv2.drawContours(thresh, [c], -1, 0, -1)
                thresh = cv2.bitwise_not(thresh)
            
            img_final = Image.fromarray(thresh)

        if padding > 0:
            img_final = ImageOps.expand(img_final, border=padding, fill=255)
        return img_final

    def _run_paddle_ocr(self, img_pil, debug_name="unknown"):
        """Wrapper PaddleOCR yang dioptimalkan"""
        try:
            # Convert PIL Image ke format BGR Numpy Array (Warna Asli)
            img_np = cv2.cvtColor(np.array(img_pil.convert('RGB')), cv2.COLOR_RGB2BGR)
            
            # Zoom 2x saja
            h, w = img_np.shape[:2]
            img_np = cv2.resize(img_np, (w * 2, h * 2), interpolation=cv2.INTER_CUBIC)
 
            # Gunakan BORDER_CONSTANT (Putih) agar huruf di pinggir tidak terseret/rusak
            img_np = cv2.copyMakeBorder(img_np, 15, 15, 15, 15, cv2.BORDER_CONSTANT, value=[255, 255, 255])

            # Debugging
            debug_dir = "debug_ocr_images"
            if not os.path.exists(debug_dir):
                os.makedirs(debug_dir)
                
            timestamp = int(time.time() * 1000)
            filepath = os.path.join(debug_dir, f"{timestamp}_{debug_name}.png")
            cv2.imwrite(filepath, img_np)

            # Jalankan OCR
            result = self.ocr_engine.ocr(img_np)
            
            if not result or result[0] is None:
                return ""
            
            # Urutkan hasil bacaan dari kiri ke kanan (Sumbu X)
            lines = result[0]
            lines.sort(key=lambda item: item[0][0][0])

            extracted_texts = []
            for line in lines:
                if isinstance(line, list) and len(line) == 2:
                    text_data = line[1]
                    if isinstance(text_data, tuple) or isinstance(text_data, list):
                        extracted_texts.append(str(text_data[0]))
            
            return " ".join(extracted_texts).strip()
            
        except Exception as e:
            BotLogger.warn(f"PaddleOCR Error: {e}")
            return ""

    def clean_number(self, text):
        if not text: return 0.0
        text = text.replace('Rp', '').replace('rp', '').replace('RP', '')
        text = text.replace(' ', '').replace(',', '')
        if any(c.isalpha() and c not in 'lIO' for c in text): return None
        
        text = text.replace('|', '1').replace('l', '1').replace('I', '1')
        text = text.replace('O', '0').replace('o', '0')
        
        clean_txt = "".join([c for c in text if c.isdigit() or c == '.'])
        if clean_txt.count('.') > 1:
            parts = clean_txt.split('.')
            clean_txt = "".join(parts[:-1]) + '.' + parts[-1]
        try: return float(clean_txt)
        except: return 0.0

    def clean_number_with_raw(self, text):
        val = self.clean_number(text)
        if val is None: val = 0.0
        return val, text

    def clean_percentage(self, val):
        if val is None: return 0.0
        if val > 100: return 0.0 
        return val

    def clean_text(self, text):
        return " ".join(text.split()).upper()

    def get_master_item(self, ocr_name):
        clean_name = self.clean_text(ocr_name)
        if clean_name in self.master_data.get('items', {}): 
            return self.master_data['items'][clean_name], clean_name
        
        norm_ocr = self.normalize_string(ocr_name)
        if norm_ocr in self.master_keys_norm:
            real_key = self.master_keys_norm[norm_ocr]
            return self.master_data['items'][real_key], real_key

        keys = list(self.master_data.get('items', {}).keys())
        threshold = settings.get('fuzzy_threshold') or 0.9
        rf_threshold = threshold * 100
        match = process.extractOne(clean_name, keys, scorer=fuzz.WRatio, score_cutoff=rf_threshold)
        if match: return self.master_data['items'][match[0]], match[0]
        return None, ocr_name

    def get_blue_row_relative(self, table_crop_cv):
        hsv = cv2.cvtColor(table_crop_cv, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, np.array([90, 20, 20]), np.array([130, 255, 255]))
        contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        valid = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if 8 < h < 75 and w > 100:
                valid.append({'top': y, 'bottom': y + h, 'height': h, 'width': w})
        return max(valid, key=lambda r: r['width']) if valid else None

    def ocr_column(self, full_screenshot, col_config, yt, yb, custom_config='--psm 7', mode='remove_vertical', debug_name=None):
        x1, x2 = col_config['x_start'], col_config['x_end']
        pad_val = col_config.get('ocr_padding', 0)
        
        crop = full_screenshot.crop((max(0, x1-pad_val), max(0, yt-pad_val), x2+pad_val, yb+pad_val))
        return self._run_paddle_ocr(crop, debug_name=debug_name or "column")

    def ocr_static_box(self, full_screenshot, box_config, custom_config='--psm 7', mode='standard', debug_name="static_box"):
        l, t, w, h = box_config['left'], box_config['top'], box_config['width'], box_config['height']
        pad_val = box_config.get('ocr_padding', 0)
        
        crop = full_screenshot.crop((max(0, l-pad_val), max(0, t-pad_val), l+w+pad_val, t+h+pad_val))
        return self._run_paddle_ocr(crop, debug_name=debug_name)

    def print_row_card(self, idx, name, line_no, qty, m2, price, discs, total_row, master_data, type_str):
        ui.print_row_card(idx, name, line_no, qty, m2, price, discs, total_row, master_data, type_str)

    def print_receipt(self, total_gross, total_netto_items, footer_discs, ppn_pct, bot_final, screen_final):
        print("\n\n" + "="*50)
        print("🧾 FINAL SUMMARY (STRUK BELANJA)")
        print("="*50)
        print(f"1. Total Barang (Gross)      : Rp {total_gross:,.0f}")
        print(f"2. Total Netto Item          : Rp {total_netto_items:,.0f}")
        
        dpp = self.bucket_eligible_for_footer
        disc_info = []
        for fd in footer_discs:
            if fd > 0:
                dpp -= dpp * (fd/100)
                disc_info.append(f"{fd}%")
        
        dpp += self.bucket_netto_items
        disc_str = " + ".join(disc_info) or "0%"
        print(f"3. Diskon Footer ({disc_str:<8}) : (Applied)")
        print(f"   -> DPP (Dasar Pajak)      : Rp {dpp:,.0f}")
        
        ppn_nominal = dpp * (ppn_pct/100)
        print(f"4. PPN ({ppn_pct}%)                 : Rp {ppn_nominal:,.0f}")
        print("-" * 50)
        print(f"💰 GRAND TOTAL (BOT)         : Rp {bot_final:,.0f}")
        print(f"🖥️ GRAND TOTAL (LAYAR)       : Rp {screen_final:,.0f}")
        print("="*50 + "\n")

    def apply_price_rules(self, item_config, val_m2, val_qty, current_price):
        """Apply math rules from DB"""
        default_res = (current_price, "NORMAL")
        rule = item_config.get('custom_rule')
        if not rule: return default_res
        
        try:
            logic = rule['logic']
            disc = rule['disc']
            mode = rule.get('mode', 'NORMAL')
            
            logic = logic.replace('true', 'True').replace('false', 'False')

            context = {'m2': val_m2, 'qty': val_qty}
            
            if eval(logic, {}, context):
                print(f"   ⚡ Rule Hit: {logic} -> Mode: {mode}")
                if mode == 'ALLOW_UPS': return current_price, mode
                new_price = current_price * (1 - (disc/100))
                return new_price, mode
        except Exception as e:
            print(f"   ⚠️ Rule Error: {e}")
            
        return default_res

    def run_audit(self, skip_startup_wait: bool = False) -> bool:
        BotLogger.info("STARTING PHASE 2: AUDIT SESSION")
        wait_time = 0.2 if skip_startup_wait else self.spd['start_buffer']
        if wait_time > 0: 
            print(f"   ⏳ Menunggu {wait_time} detik (Switch Window)...", flush=True)
            time.sleep(wait_time)

        # Refresh configs to get any runtime changes from dashboard
        self.coords = self.load_json(COORD_FILE)
        anchor = self.coords['anchor_item_name']
        pyautogui.click(anchor['x'], anchor['y'])
        
        # Anchor click delay
        anchor_delay = float(anchor['custom_delay']) if anchor.get('custom_delay') is not None and str(anchor.get('custom_delay')).strip() != "" else (0.2 if skip_startup_wait else 0.5)
        time.sleep(anchor_delay)
        
        pyautogui.press('home')
        time.sleep(0.3 if skip_startup_wait else 1.0)

        table = self.coords.get('table_area')
        if not table: return False
        tl, tt, tw, th = table['left'], table['top'], table['width'], table['height']

        row_index = 1
        self.bucket_eligible_for_footer = 0.0 
        self.bucket_netto_items = 0.0
        self.bucket_non_taxable = 0.0
        self.total_gross_items = 0.0
        self.last_line_image = None
        self.stuck_counter = 0
        self.last_line_no = -1
        
        list_service = self.rules.get('service_items', [])
        list_no_disc = self.rules.get('no_discount_items', [])
        
        print("   ⚙️  Membaca area Footer di awal untuk cek Diskon Global...", flush=True)
        init_ss = pyautogui.screenshot()
        global_f_discs = []
        num_cfg = '--psm 7 -c tessedit_char_whitelist=0123456789.,'
        for i in range(1, 5):
            k = f'footer_disc_{i}'
            val = 0.0
            if k in self.coords:
                raw_disc = self.ocr_static_box(init_ss, self.coords[k], custom_config=num_cfg, mode='remove_vertical')
                val = self.clean_percentage(self.clean_number(raw_disc))
            global_f_discs.append(val)
        print(f"   ℹ️  Diskon Global (Footer) terdeteksi: {global_f_discs}")

        while True:
            if bot_state.STOP_REQUESTED: return False

            try:
                print(f"\r   👀 Mencari baris data ke-{row_index}...", end="", flush=True)
                
                time.sleep(0.1)
                full_ss = pyautogui.screenshot()
                table_pil = full_ss.crop((tl, tt, tl+tw, tt+th))
                crop_cv = cv2.cvtColor(np.array(table_pil), cv2.COLOR_RGB2BGR)
                rel = self.get_blue_row_relative(crop_cv)
                
                if not rel:
                    if self.consecutive_empty_rows > 1: break
                    else:
                        print(f"\r   ⬇️  Scroll ke bawah mencari data...       ", end="", flush=True)
                        pyautogui.press('up'); time.sleep(0.2)
                        pyautogui.press('down'); time.sleep(1.0)
                        self.consecutive_empty_rows += 1; continue
                
                self.consecutive_empty_rows = 0
                gy_top, gy_bot = tt + rel['top'], tt + rel['bottom']

                print(f"\r   ⚙️  Membaca teks (OCR) baris ke-{row_index}...    ", end="", flush=True)

                x1_line = self.coords['col_line_no']['x_start']
                x2_line = self.coords['col_line_no']['x_end']
                line_crop = full_ss.crop((x1_line, gy_top, x2_line, gy_bot))
                current_line_img = cv2.cvtColor(np.array(line_crop), cv2.COLOR_RGB2GRAY)

                is_duplicate = False
                if self.last_line_image is not None:
                    if current_line_img.shape != self.last_line_image.shape:
                        self.last_line_image = cv2.resize(self.last_line_image, (current_line_img.shape[1], current_line_img.shape[0]))
                    
                    blur_curr = cv2.GaussianBlur(current_line_img, (3, 3), 0)
                    blur_last = cv2.GaussianBlur(self.last_line_image, (3, 3), 0)
                    
                    diff_matrix = cv2.absdiff(blur_curr, blur_last)
                    _, thresh_diff = cv2.threshold(diff_matrix, 20, 255, cv2.THRESH_BINARY)
                    changed_px = cv2.countNonZero(thresh_diff)
                    if changed_px < 15:
                        is_duplicate = True

                raw_line = self.ocr_column(full_ss, self.coords['col_line_no'], gy_top, gy_bot, custom_config='--psm 10', mode='repair_broken_font')
                val_line, _ = self.clean_number_with_raw(raw_line)

                if val_line > 0:
                    if val_line == self.last_line_no: 
                        is_duplicate = True
                    self.last_line_no = val_line

                raw_name = self.ocr_column(full_ss, self.coords['col_item_name'], gy_top, gy_bot, custom_config='--psm 6', mode='name_safe', debug_name="col_item_name")
                
                item_config, matched_name = self.get_master_item(raw_name)
                if item_config: raw_name = matched_name
                
                if len(self.clean_text(raw_name)) < 3:
                    print("\r   ⚠️ OCR terhalang blok biru. Mencoba filter alternatif...  ", end="", flush=True)
                    x1, x2 = self.coords['col_item_name']['x_start'], self.coords['col_item_name']['x_end']
                    crop = full_ss.crop((x1, gy_top, x2, gy_bot))
                    img_np = np.array(crop.convert('L'))
                    img_np = cv2.resize(img_np, (img_np.shape[1] * 3, img_np.shape[0] * 3), interpolation=cv2.INTER_CUBIC)
                    _, thresh = cv2.threshold(img_np, 160, 255, cv2.THRESH_BINARY)
                    raw_name = self._run_paddle_ocr(Image.fromarray(thresh), debug_name="fallback_item_name")
                    
                    item_config, matched_name = self.get_master_item(raw_name)
                    if item_config: raw_name = matched_name
                
                if not item_config:
                    if self.handle_unknown_item_interactive(raw_name):
                        item_config, matched_name = self.get_master_item(raw_name)
                        if item_config: raw_name = matched_name
                        anc = self.coords['anchor_item_name']
                        pyautogui.click(anc['x'], anc['y'])
                        time.sleep(0.5)
                    else:
                        BotLogger.warn(f"⛔ REJECTED: Barang tidak dikenal / di-skip user -> [{raw_name}]")
                        return False

                if item_config is None: return False
                
                num_cfg = '--psm 7 -c tessedit_char_whitelist=0123456789.,'
                
                raw_qty = self.ocr_column(full_ss, self.coords['col_qty'], gy_top, gy_bot, custom_config=num_cfg, mode='remove_vertical', debug_name="col_qty")
                val_qty = self.clean_number(raw_qty)
                if val_qty is None: val_qty = 0.0
                
                raw_price = self.ocr_column(full_ss, self.coords['col_price'], gy_top, gy_bot, custom_config=num_cfg, mode='remove_vertical', debug_name="col_price")
                val_price_screen = self.clean_number(raw_price)
                if val_price_screen is None: val_price_screen = 0.0
                
                raw_m2 = self.ocr_column(full_ss, self.coords['col_m2'], gy_top, gy_bot, custom_config=num_cfg, mode='remove_vertical', debug_name="col_m2")
                val_m2 = self.clean_number(raw_m2)
                if val_m2 is None or val_m2 == 0.0: val_m2 = 1.0

                should_validate_price = item_config.get('price_validation', True)
                
                if should_validate_price:
                    val_price_db = item_config.get('base_price', 0)
                    
                    alternatives = item_config.get('alternatives', [])
                    base_diff = abs(val_price_screen - val_price_db)
                    tolerance = val_price_db * 0.05
                    
                    if base_diff > tolerance and alternatives:
                        for alt in alternatives:
                            alt_price = alt['price']
                            if abs(val_price_screen - alt_price) < (alt_price * 0.05):
                                val_price_db = alt_price
                                print(f"\n   🔀 Match Alternative Price: Rp {alt_price:,.0f} ({alt.get('note','')})")
                                item_config['temp_tax_override'] = alt.get('is_taxable', True)
                                break
                else:
                    val_price_db = val_price_screen
                
                val_price_db, calc_mode = self.apply_price_rules(item_config, val_m2, val_qty, val_price_db)
                
                if calc_mode == 'ALLOW_UPS' and val_price_screen >= val_price_db:
                    val_price_db = val_price_screen
                    print(f"\n   📈 Upselling Allowed: Rp {val_price_screen:,.0f}")

                val_price = val_price_db

                price_diff = abs(val_price_screen - val_price_db)
                max_price_diff = 100.0 
                
                if should_validate_price and price_diff > max_price_diff and val_price_db > 0:
                    ui.print_price_mismatch(raw_name, val_price_db, val_price_screen, price_diff, max_price_diff)
                    
                    print("\n👉 OPSI TINDAKAN:")
                    print("   [1] UPDATE DATABASE (Ikut Harga Layar)")
                    print("   [2] REJECT / SKIP Transaksi Ini")
                    print("   [3] STOP BOT (Exit)")
                    
                    print("\n👉 Pilih [1/2/3]: ", end='', flush=True)
                    
                    cfg = settings.get('timeout_mismatch')
                    if cfg is not None and cfg['enabled']:
                        user_choice = TimeoutInput.get_choice_with_timeout(cfg['seconds'], default_choice='2')
                    else:
                        user_choice = input().strip() 

                    if user_choice == '1':
                        item_config['base_price'] = val_price_screen
                        self.master_data['items'][raw_name] = item_config
                        try:
                            self.safe_save_json(self.master_data, MASTER_FILE)
                            ui.print_success("Database update!")
                            val_price_db = val_price_screen
                        except: pass
                    elif user_choice == '2': 
                        BotLogger.warn(f"⛔ REJECTED: Selisih harga ditolak user -> [{raw_name}]")
                        return False
                    elif user_choice == '3': 
                        BotLogger.warn(f"⛔ REJECTED: Bot dihentikan user (Exit) saat cek harga -> [{raw_name}]")
                        bot_state.STOP_REQUESTED = True
                        return False
                    else:
                        BotLogger.warn(f"⛔ REJECTED: Timeout / Input tidak valid saat cek harga -> [{raw_name}]")
                        return False 

                if is_duplicate:
                    self.stuck_counter += 1
                    print(f"\n   ⚠️ UI Frame Statis ({self.stuck_counter}/2). Verifikasi scroll...")
                    if self.stuck_counter >= 2: 
                        print("   🛑 Table End Reached (EOF). Mengakhiri audit tabel.")
                        break
                    pyautogui.press('down')
                    time.sleep(0.5) 
                    time.sleep(self.spd['audit_scroll'])
                    continue 
                else:
                    self.stuck_counter = 0 
                    self.last_line_image = current_line_img.copy()

                is_service = any(k in raw_name for k in list_service) or "BIAYA" in raw_name
                is_no_disc = any(k in raw_name for k in list_no_disc)

                d_rows = []
                for i in range(1, 5):
                    k = f'col_disc_row_{i}'
                    v = 0.0
                    if not is_no_disc and k in self.coords:
                        v = self.clean_percentage(self.clean_number(
                            self.ocr_column(full_ss, self.coords[k], gy_top, gy_bot, custom_config=num_cfg, mode='remove_vertical')
                        ))
                    d_rows.append(v)

                is_moved_to_footer = False
                if should_validate_price and item_config:
                    db_discs = item_config.get('default_discs', [0.0, 0.0, 0.0, 0.0])
                    
                    disc_mismatch = False
                    
                    match_line = True
                    for i in range(4):
                        if abs(d_rows[i] - db_discs[i]) > 0.1:
                            match_line = False
                            break
                            
                    if not match_line:
                        is_line_zero = all(d < 0.1 for d in d_rows)
                        match_footer = True
                        for i in range(4):
                            if abs(global_f_discs[i] - db_discs[i]) > 0.1:
                                match_footer = False
                                break
                                
                        if is_line_zero and match_footer:
                            is_moved_to_footer = True 
                        else:
                            disc_mismatch = True 
                    
                    if disc_mismatch:
                        ui.play_sfx("alert")
                        print("\n" + "┏" + "━"*60 + "┓")
                        print(f"┃ 🚨 DISCOUNT MISMATCH DETECTED: {raw_name[:25]:<25} ┃")
                        print("┣" + "━"*60 + "┫")
                        db_disc_str = " + ".join([f"{d}%" for d in db_discs if d > 0]) or "0%"
                        scr_disc_str = " + ".join([f"{d}%" for d in d_rows if d > 0]) or "0%"
                        ftr_disc_str = " + ".join([f"{d}%" for d in global_f_discs if d > 0]) or "0%"
                        print(f"┃ 💾 Database (Expected) : {db_disc_str}".ljust(61) + "┃")
                        print(f"┃ 🖥️  Screen Line (Row)   : {scr_disc_str}".ljust(61) + "┃")
                        print(f"┃ 🖥️  Screen Footer       : {ftr_disc_str}".ljust(61) + "┃")
                        print("┗" + "━"*60 + "┛")
                        
                        print("\n👉 OPSI TINDAKAN:")
                        print("   [1] UPDATE DATABASE (Ikut Diskon Layar)")
                        print("   [2] REJECT / SKIP Transaksi Ini")
                        print("   [3] STOP BOT (Exit)")
                        
                        print("\n👉 Pilih [1/2/3]: ", end='', flush=True)
                        
                        cfg = settings.get('timeout_mismatch')
                        if cfg is not None and cfg['enabled']:
                            user_choice = TimeoutInput.get_choice_with_timeout(cfg['seconds'], default_choice='2')
                        else:
                            user_choice = input().strip()

                        if user_choice == '1':
                            item_config['default_discs'] = d_rows
                            self.master_data['items'][raw_name] = item_config
                            try:
                                self.safe_save_json(self.master_data, MASTER_FILE)
                                ui.print_success("Database Diskon diupdate!")
                            except: pass
                        elif user_choice == '2': 
                            BotLogger.warn(f"⛔ REJECTED: Selisih diskon ditolak user -> [{raw_name}]")
                            return False
                        elif user_choice == '3': 
                            BotLogger.warn(f"⛔ REJECTED: Bot dihentikan user (Exit) saat cek diskon -> [{raw_name}]")
                            bot_state.STOP_REQUESTED = True
                            return False
                        else:
                            BotLogger.warn(f"⛔ REJECTED: Timeout / Input tidak valid saat cek diskon -> [{raw_name}]")
                            return False
                
                if calc_mode == 'FLAT_M2':
                    gross_row = val_price * val_qty * 1.0
                else:
                    gross_row = val_price * val_qty * val_m2
                self.total_gross_items += gross_row
                
                net_calc = gross_row
                if is_service:
                    if 'col_amount' in self.coords:
                        net_calc = self.clean_number(self.ocr_column(full_ss, self.coords['col_amount'], gy_top, gy_bot, custom_config=num_cfg, mode='remove_vertical'))
                        if net_calc is None: net_calc = 0.0
                    else: net_calc = 0.0
                    self.bucket_netto_items += net_calc
                    type_str = "SERV (NET)"
                else:
                    for d in d_rows: 
                        if d > 0: net_calc *= (1 - (d/100))
                    
                    is_netto = item_config.get('is_netto', False) if item_config else False
                    if is_netto: 
                        is_tax = item_config.get('is_taxable', True)
                        if 'temp_tax_override' in item_config:
                            is_tax = item_config.pop('temp_tax_override')
                            
                        if is_tax:
                            self.bucket_netto_items += net_calc
                        else:
                            self.bucket_non_taxable += net_calc
                        type_str = "NET"
                    else: 
                        self.bucket_eligible_for_footer += net_calc
                        type_str = "DISC (FOOTER)" if is_moved_to_footer else "DISC"

                print("\r" + " "*60 + "\r", end="", flush=True)

                self.print_row_card(row_index, raw_name, val_line, val_qty, val_m2, val_price, d_rows, net_calc, item_config, type_str)
                pyautogui.press('down')
                time.sleep(self.spd['audit_scroll']) 
                row_index += 1

            except Exception as e:
                BotLogger.error(f"CRASH ROW: {e}")
                return False

        try:
            print("\n   ⚙️  Membaca area Footer (Diskon, PPN, Total)...", flush=True)
            full_ss = pyautogui.screenshot()
            f_discs = []
            num_cfg = '--psm 7 -c tessedit_char_whitelist=0123456789.,'
            
            for i in range(1, 5):
                k = f'footer_disc_{i}'
                val = 0.0
                if k in self.coords:
                    raw_disc = self.ocr_static_box(full_ss, self.coords[k], custom_config=num_cfg, mode='remove_vertical')
                    val = self.clean_percentage(self.clean_number(raw_disc))
                f_discs.append(val)
            
            raw_ppn = self.ocr_static_box(full_ss, self.coords['footer_ppn_pct'], custom_config=num_cfg, mode='remove_vertical')
            val_ppn = self.clean_number(raw_ppn)
            if val_ppn is None: val_ppn = 0.0
            
            raw_total = self.ocr_static_box(full_ss, self.coords['footer_grand_total'], custom_config=num_cfg, mode='remove_vertical')
            screen_total = self.clean_number(raw_total)
            if screen_total is None: screen_total = 0.0

            dpp = self.bucket_eligible_for_footer
            for fd in f_discs:
                if fd > 0: dpp *= (1 - (fd/100))
            
            taxable_base = dpp + self.bucket_netto_items
            ppn_nominal = taxable_base * (val_ppn/100)
            
            final_calc = taxable_base + ppn_nominal + self.bucket_non_taxable
            
            total_netto = self.bucket_eligible_for_footer + self.bucket_netto_items
            self.print_receipt(self.total_gross_items, total_netto, f_discs, val_ppn, final_calc, screen_total)

            diff = abs(final_calc - screen_total)
            is_valid = diff < MAX_TOLERANCE_RP
            
            ui.print_audit_summary(
                items_count=row_index - 1,
                gross_total=self.total_gross_items,
                netto_total=total_netto,
                bot_total=final_calc,
                screen_total=screen_total,
                diff=diff,
                is_valid=is_valid
            )
            
            if is_valid:
                BotLogger.info("🎉 INVOICE VALID! EXECUTING SAVE...")
                
                # Dynamic Save Execution Delays via Dashboard
                b1 = self.coords.get('btn_action_1')
                if b1:
                    pyautogui.click(b1['x'], b1['y'])
                    d_b1 = float(b1['custom_delay']) if b1.get('custom_delay') is not None and str(b1.get('custom_delay')).strip() != "" else self.spd.get('action_delay', 1.5)
                    time.sleep(d_b1)

                pyautogui.press(self.save_key)
                hk_cfg = self.coords.get('save_hotkey') or {}
                d_save = float(hk_cfg['custom_delay']) if hk_cfg.get('custom_delay') is not None and str(hk_cfg.get('custom_delay')).strip() != "" else self.spd.get('action_delay', 1.5)
                time.sleep(d_save)

                b2 = self.coords.get('btn_action_2')
                if b2:
                    pyautogui.click(b2['x'], b2['y'])
                    d_b2 = float(b2['custom_delay']) if b2.get('custom_delay') is not None and str(b2.get('custom_delay')).strip() != "" else self.spd.get('action_delay', 0.5)
                    time.sleep(d_b2)

                return True
            else:
                BotLogger.warn(f"⛔ REJECTED: Grand Total selisih Rp {diff:,.0f} (Maks toleransi Rp {MAX_TOLERANCE_RP})")
                so_box = self.coords.get('error_so_box') 
                so_num = self.ocr_static_box(full_ss, so_box, mode='standard') if so_box else "UNKNOWN"
                BotLogger.log_reject_to_csv({
                    'so_number': so_num, 'bot_total': final_calc,
                    'screen_total': screen_total, 'diff': diff, 'reason': f'Diff > {MAX_TOLERANCE_RP}'
                })
                return False

        except Exception as e:
            BotLogger.error(f"CRASH FOOTER: {e}")
            return False

    def read_customer_header(self):
        box = self.coords.get('header_customer_name_box')
        if not box: return ""
        return self.ocr_static_box(pyautogui.screenshot(), box, mode='standard').strip().upper()

if __name__ == "__main__":
    bot = ERP_Auditor()
    bot.run_audit()