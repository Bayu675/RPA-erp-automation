import json
import time
import numpy as np
import cv2
import pyautogui
from typing import Dict, Any, Optional
from pynput import mouse, keyboard
from config.steps_config import PHASE_1_STEPS, RESET_STEPS

# File path for saving the coordinates
COORD_FILE = "coordinates.json"

class Calibrator:
    def __init__(self):
        self.captured_coords: Dict[str, Any] = {}
        self.current_x = 0
        self.current_y = 0
        self.old_data: Dict[str, Any] = {}

        # [PENTING] Load data lama biar gak ilang pas partial update
        try:
            with open(COORD_FILE, 'r') as f:
                self.old_data = json.load(f)
                # Mulai dengan data lama, nanti kita timpa yang diedit aja
                self.captured_coords = self.old_data.copy() 
        except:
            self.old_data = {}

    def get_user_click(self) -> Dict[str, int]:
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

        print("   ⏳ Menunggu input... (Arahkan mouse)", flush=True)
        print("   🔎 [SNIPER] Geser: Mouse/Panah Keyboard | Pilih: Klik Kiri/Enter", flush=True)

        # Mulai listener mouse & keyboard di background
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
            self.current_x, self.current_y = click_pos[0]
            return {"x": self.current_x, "y": self.current_y}
        
        return {"x": 0, "y": 0}

    def run_calibration_wizard(self):
        print("\n🖱️  KALIBRASI PHASE 1 (INPUT LOGIC)")
        print("====================================")

        ALL_STEPS = PHASE_1_STEPS + RESET_STEPS
        
        # --- MENU SELEKSI LANGKAH ---
        print("MODE KALIBRASI:")
        print("   [1] Full Wizard (Semua Langkah dari Awal)")
        print("   [2] Select Step (Pilih Langkah Tertentu)")
        print("   [b] 🔙 Batal")
        mode = input("👉 Pilih Mode [1/2/b]: ").strip()
        
        if mode.lower() == 'b':
            return

        steps_to_run = ALL_STEPS # Default: Semua (Pakai list gabungan)

        if mode == '2':
            print("\nDAFTAR LANGKAH:")
            for idx, step in enumerate(ALL_STEPS):
                # Tampilkan nilai saat ini dari JSON lama
                curr_val = "Belum ada"
                if step['id'] in self.old_data:
                    if step['action'] == 'type':
                        curr_val = str(self.old_data[step['id']].get('value', '-'))
                    else:
                        curr_val = "OK (Koordinat Tersimpan)"
                
                print(f"   [{idx+1}] {step['msg']} [Current: {curr_val}]")
            
            try:
                raw_in = input("\n👉 Masukkan NOMOR langkah yang mau diedit: ")
                pilih = int(raw_in) - 1
                if 0 <= pilih < len(ALL_STEPS):
                    steps_to_run = [ALL_STEPS[pilih]] # Filter jadi 1 langkah
                    print(f"🔧 Mode Edit: {steps_to_run[0]['msg']}")
                else:
                    print("❌ Nomor salah. Batal."); return
            except ValueError:
                print("❌ Input harus angka."); return
        # ----------------------------

        print("\nPastikan layar input ERP sudah siap.")
        print("Tekan Ctrl+C jika ingin batal.\n")

        try:
            for step in steps_to_run:
                print(f"\n🔹 STEP: {step['msg']}", flush=True)
                
                step_data: Dict[str, Any] = {
                    "action": step['action'],
                    "id": step['id']
                }
        # --- [NEW] MENU KHUSUS UNTUK ADD SO & ROW HEIGHT ---
                if step['id'] == '5_checkbox_add_so':
                    print("\n   ⚙️  PENGATURAN KHUSUS: ADD SO & ROW HEIGHT")
                    print("   [1] Set Koordinat Checkbox 'Add SO' (Normal)")
                    print("   [2] Set Manual Nilai Jarak Baris (Row Height)")
                    print("   [3] 📏 Alat Bantu Hitung Jarak Baris (Otomatis)")
                    sub_choice = input("   👉 Pilih [1/2/3]: ").strip()

                    if sub_choice == '2':
                        curr_rh = self.old_data.get('GLOBAL_ROW_HEIGHT', 18)
                        try:
                            new_rh = int(input(f"   Masukkan nilai Row Height (Current: {curr_rh}px): "))
                            self.captured_coords['GLOBAL_ROW_HEIGHT'] = new_rh
                            print(f"   ✅ Row Height diset ke {new_rh}px")
                        except ValueError:
                            print("   ❌ Input tidak valid. Batal.")
                        continue # Skip ambil koordinat, lanjut ke step berikutnya

                    elif sub_choice == '3':
                        print("\n   📏 ALAT BANTU HITUNG JARAK BARIS")
                        print("   👉 Klik pada baris PERTAMA (Tengah-tengah baris)...")
                        pt1 = self.get_user_click()
                        print("   👉 Klik pada baris KEDUA (Tepat di bawahnya)...")
                        pt2 = self.get_user_click()
                        calc_rh = abs(pt2['y'] - pt1['y'])
                        print(f"   ✅ Terhitung jarak antar baris: {calc_rh}px")
                        self.captured_coords['GLOBAL_ROW_HEIGHT'] = calc_rh
                        continue # Skip ambil koordinat, lanjut ke step berikutnya

                # --- LOGIC KLIK ---
                if step['action'] == 'click':
                    coords = self.get_user_click()
                    print(f"   ✅ Captured: X={coords['x']}, Y={coords['y']}")
                    
                    # Konfirmasi
                    confirm = input("   Simpan posisi ini? [Y/n/retry]: ").lower()
                    while confirm == 'retry':
                        coords = self.get_user_click()
                        print(f"   ✅ Captured (Retry): X={coords['x']}, Y={coords['y']}")
                        confirm = input("   Simpan posisi ini? [Y/n/retry]: ").lower()
                    
                    if confirm == 'n':
                        print("   ⚠️ Skipped (Data lama tetap dipakai jika ada).")
                        continue 

                    step_data.update(coords)

                # --- LOGIC KETIK ---
                elif step['action'] == 'type':
                    # Cek nilai default (Prioritas: JSON Lama -> Config Python)
                    # [FIX] Ensure default_val is always a string for type safety
                    default_val: str = str(step.get('value') or '') 
                    
                    if step['id'] in self.old_data:
                        old_val = self.old_data[step['id']].get('value')
                        if old_val is not None:
                            default_val = str(old_val)

                    print(f"   ⌨️  Input Keyboard (Default saat ini: '{default_val}')")
                    user_input = input(f"   Ketik nilai baru (atau TEKAN ENTER untuk pakai default): ").strip()
                    
                    final_val: str = ""
                    if user_input:
                        final_val = user_input
                        print(f"   ✅ Diupdate jadi: '{final_val}'")
                    else:
                        final_val = default_val
                        print(f"   ✅ Tetap pakai: '{final_val}'")
                    
                    step_data['value'] = final_val

                # Update memory (Timpa data lama dengan yang baru)
                self.captured_coords[step['id']] = step_data
                time.sleep(0.5)

            # SAVE FINAL
            self.save_to_file()

        except KeyboardInterrupt:
            print("\n❌ Kalibrasi dibatalkan user.")

    def save_to_file(self):
        try:
            with open(COORD_FILE, 'w') as f:
                json.dump(self.captured_coords, f, indent=4)
            print(f"\n💾 SUKSES! Konfigurasi disimpan ke '{COORD_FILE}'")
        except Exception as e:
            print(f"\n⛔ Gagal menyimpan file: {e}")

if __name__ == "__main__":
    app = Calibrator()
    app.run_calibration_wizard()