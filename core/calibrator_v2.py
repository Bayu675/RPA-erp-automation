# erp-automation/core/calibrator_v2.py
import json
import time
import os
import pyautogui
import numpy as np
import cv2 
from pynput import mouse, keyboard
from config.steps_phase2 import PHASE_2_STEPS
from core.logger import BotLogger

COORD_FILE_V2 = "coordinates_phase2.json"

class CalibratorV2:
    def __init__(self):
        self.captured_data = {}
        self.temp_clicks = [] 
        self.old_data = {}

        # Load data lama biar gak ilang pas partial update
        try:
            with open(COORD_FILE_V2, 'r') as f:
                self.old_data = json.load(f)
                self.captured_data = self.old_data.copy()
        except:
            self.old_data = {}

    def get_click(self):
        click_pos = []
        
        def on_click(x, y, button, pressed):
            if pressed and button == mouse.Button.left:
                click_pos.append((int(x), int(y)))
                return False # Stop listener

        def on_key_press(key):
           try:
               if key == keyboard.Key.up:
                   pyautogui.move(0, -1, duration=0)
               elif key == keyboard.Key.down:
                   pyautogui.move(0, 1, duration=0)
               elif key == keyboard.Key.left:
                   pyautogui.move(-1, 0, duration=0)
               elif key == keyboard.Key.right:
                   pyautogui.move(1, 0, duration=0)
               elif key == keyboard.Key.enter:
                   mx, my = pyautogui.position()
                   click_pos.append((int(mx), int(my)))
           except Exception:
               pass

        m_listener = mouse.Listener(on_click=on_click)
        k_listener = keyboard.Listener(on_press=on_key_press)
        m_listener.start()
        k_listener.start()

        # Setup Jendela OpenCV
        window_name = "🔍 SNIPER MODE (Klik Kiri untuk Pilih)"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1) # Always on top
        cv2.resizeWindow(window_name, 250, 250)

        zoom_factor = 5
        capture_size = 50 # Ambil area 50x50 pixel di sekitar mouse


        try:
            while m_listener.is_alive() and k_listener.is_alive() and not click_pos:
                # Ambil posisi mouse saat ini
                mx, my = pyautogui.position()
                
                # Hitung kotak area yang mau di-screenshot
                left = max(0, mx - capture_size // 2)
                top = max(0, my - capture_size // 2)
                
                # Screenshot area kecil di sekitar mouse
                img = pyautogui.screenshot(region=(left, top, capture_size, capture_size))
                frame = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
                
                # Zoom in (Pakai INTER_NEAREST biar pixelnya kotak-kotak tajam, gak blur)
                zoomed = cv2.resize(frame, (capture_size * zoom_factor, capture_size * zoom_factor), interpolation=cv2.INTER_NEAREST)
                
                # Gambar Crosshair (Garis Bidik Merah) di tengah
                h, w = zoomed.shape[:2]
                cx, cy = w // 2, h // 2
                cv2.line(zoomed, (cx, 0), (cx, h), (0, 0, 255), 1) # Garis Vertikal
                cv2.line(zoomed, (0, cy), (w, cy), (0, 0, 255), 1) # Garis Horizontal
                
                # Tampilkan ke layar
                cv2.imshow(window_name, zoomed)
                cv2.waitKey(30) # Refresh rate ~30 FPS
                
        except Exception as e:
            print(f"   ⚠️ Magnifier Error: {e}")
        finally:
            cv2.destroyWindow(window_name)
            if m_listener.is_alive(): m_listener.stop()
            if k_listener.is_alive(): k_listener.stop()

        if click_pos:
            return click_pos[0]
        return (0, 0)

    def _save_preview(self, region, tag="preview"):
        """Simpan screenshot area buat dicek user."""
        try:
            if not os.path.exists("debug_images"):
                os.makedirs("debug_images")
            
            x, y, w, h = region
            if w < 1: w = 1
            if h < 1: h = 1
            
            img = pyautogui.screenshot(region=(x, y, w, h))
            filename = f"debug_images/CHECK_{tag}.png"
            img.save(filename)
            print(f"   📸 Cek Gambar: '{filename}' (Buka folder debug_images)")
        except Exception as e:
            print(f"   ⚠️ Gagal Preview: {e}")

    def run_wizard(self):
        print("\n🦅 MATA ELANG - KALIBRASI PHASE 2 (V2 + CUSTOM PADDING)")
        print("=========================================================")
        
        print("MODE KALIBRASI:")
        print("   [1] Full Wizard (Semua Langkah)")
        print("   [2] Select Step (Pilih Langkah Tertentu)")
        print("   [b] 🔙 Batal")
        mode = input("👉 Pilih Mode [1/2/b]: ").strip()
        
        if mode.lower() == 'b':
            return

        steps_to_run = PHASE_2_STEPS 

        if mode == '2':
            print("\nDAFTAR TARGET:")
            for idx, step in enumerate(PHASE_2_STEPS):
                status = "✅" if step['id'] in self.old_data else "❌"
                print(f"   [{idx+1}] {status} {step['id']} - {step['msg'][:40]}...")
            
            try:
                raw_in = input("\n👉 Masukkan NOMOR langkah: ")
                pilih = int(raw_in) - 1
                if 0 <= pilih < len(PHASE_2_STEPS):
                    steps_to_run = [PHASE_2_STEPS[pilih]]
                    print(f"🔧 Mode Edit: {steps_to_run[0]['id']}")
                else:
                    print("❌ Nomor salah."); return
            except ValueError:
                print("❌ Input harus angka."); return

        print("\nPastikan Window ERP Terbuka & Tampilan Tabel Siap.")
        print("Tekan Ctrl+C untuk Cancel kapan saja.\n")
        
        try:
            for step in steps_to_run:
                # Reset data capture & padding
                captured_step_data = None
                current_padding = 0
                
                # Cek apakah ada data lama buat padding default
                if step['id'] in self.old_data:
                    current_padding = self.old_data[step['id']].get('ocr_padding', 0)

                while True: # RETRY / CONFIG LOOP
                    print(f"\n🔹 {step['msg']}", flush=True)
                    self.temp_clicks = [] 
                    preview_msg = ""
                    region_preview = None 

                    # Cek kalau data sudah dicapture (misal abis set Config), jangan minta klik lagi
                    if captured_step_data is None:
                        
                        # --- ACTION 1: KLIK TITIK ---
                        if step['action'] == 'click_point':
                            print("   👉 Klik 1 titik target...", flush=True)
                            pt = self.get_click()
                            captured_step_data = {"type": "point", "x": pt[0], "y": pt[1]}
                            preview_msg = f"Titik: ({pt[0]}, {pt[1]})"
                            region_preview = (pt[0]-25, pt[1]-25, 50, 50)

                        # --- ACTION 2: DEFINISI KOLOM ---
                        elif step['action'] == 'define_column':
                            print("   👉 Klik BATAS KIRI (Pojok Kiri Atas)...", flush=True); p1 = self.get_click(); time.sleep(0.3)
                            print("   👉 Klik BATAS KANAN (Pojok Kanan Bawah)...", flush=True); p2 = self.get_click()
                            
                            x_start = min(p1[0], p2[0]); x_end = max(p1[0], p2[0])
                            width = x_end - x_start
                            y_start = min(p1[1], p2[1]); height_click = abs(p1[1] - p2[1])
                            
                            # Logic Adaptive Preview
                            if height_click > 5: h_prev = height_click; note = "User"
                            else: h_prev = 30; note = "Auto"
                            
                            region_preview = (x_start, y_start, width, h_prev)
                            captured_step_data = {"type": "column", "x_start": x_start, "x_end": x_end}
                            preview_msg = f"W:{width}px | H:{h_prev}px ({note})"

                        # --- ACTION 3: DEFINISI BOX ---
                        elif step['action'] == 'define_box':
                            print("   👉 Klik POJOK KIRI-ATAS...", flush=True); p1 = self.get_click(); time.sleep(0.3)
                            print("   👉 Klik POJOK KANAN-BAWAH...", flush=True); p2 = self.get_click()
                            
                            l = min(p1[0], p2[0]); t = min(p1[1], p2[1])
                            w = abs(p2[0] - p1[0]); h = abs(p2[1] - p1[1])
                            
                            captured_step_data = {"type": "box", "left": l, "top": t, "width": w, "height": h}
                            region_preview = (l, t, w, h)
                            preview_msg = f"Box: {w}x{h} px"

                        # --- ACTION 4: INPUT TEXT ---
                        elif step['action'] == 'input_text':
                            curr = self.old_data.get(step['id'], {}).get('value', 'f3')
                            val = input(f"   ⌨️  Input Key (Default '{curr}'): ").strip().lower()
                            if not val: val = curr
                            captured_step_data = {"type": "text", "value": val}
                            preview_msg = f"Key: '{val}'"

                        # Apply padding yang tersimpan ke data sementara
                        if captured_step_data:
                            captured_step_data['ocr_padding'] = current_padding

                        # Generate Preview
                        if region_preview:
                            x, y, w, h = region_preview
                            if x < 0: x = 0; 
                            if y < 0: y = 0
                            self._save_preview((x, y, w, h), tag=step['id'])

                    else:
                        print("   (Data koordinat sudah ada, menunggu konfirmasi/config)")

                    # --- KONFIRMASI DENGAN OPSI [C] ---
                    print(f"   🔎 Info: {preview_msg} | Padding: {current_padding}px")
                    confirm = input("   Simpan? [Y/n/retry/c]: ").lower()

                    if confirm == 'c':
                        try:
                            raw_pad = input("   👉 Masukkan nilai Padding (px, misal 10): ").strip()
                            current_padding = int(raw_pad)
                            if captured_step_data:
                                captured_step_data['ocr_padding'] = current_padding
                            print(f"   🔧 Padding di-set ke: {current_padding}px")
                        except:
                            print("   ❌ Input harus angka!")
                        continue # Loop lagi buat konfirmasi

                    elif confirm == 'retry':
                        print("   🔄 Ulangi ambil titik...")
                        captured_step_data = None # Reset capture
                        continue 
                    
                    elif confirm == 'n':
                        print("   ⚠️ Skipped.")
                        break 
                    
                    else: 
                        # Save
                        self.captured_data[step['id']] = captured_step_data
                        self.old_data[step['id']] = captured_step_data
                        print("   ✅ Tersimpan.")
                        time.sleep(0.5)
                        break 

            if self.captured_data:
                with open(COORD_FILE_V2, 'w') as f:
                    json.dump(self.captured_data, f, indent=4)
                print(f"\n💾 CONFIG PHASE 2 DISIMPAN: {COORD_FILE_V2}")
            else:
                print("\n⚠️ Tidak ada perubahan.")
            import sys
            if sys.platform == 'win32':
                import msvcrt
                while msvcrt.kbhit():
                    msvcrt.getch()

        except KeyboardInterrupt:
            print("\n❌ Batal.")

if __name__ == "__main__":
    app = CalibratorV2()
    app.run_wizard()