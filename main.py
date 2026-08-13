# erp-automation/main.py
import time
import sys
import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
import codecs # [NEW] Import untuk fix encoding UTF-8
import threading
from pynput import keyboard
import pyautogui
import config.state as bot_state # [PENTING] Pakai State Global

# [FIX] Paksa terminal Windows pakai UTF-8 biar emoji / box drawing aman
if sys.platform == 'win32':
    os.system('chcp 65001 >nul 2>&1')
    try:
        sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    except Exception:
        pass

# --- IMPORT MODULES ---
try:
    from core.executor import Executor
    from core.auditor import ERP_Auditor
    from core.calibrator_v2 import CalibratorV2
    from core.batch_manager import BatchManager 
    from core.store_manager import StoreManager
    from core.database_manager import DatabaseManager # [NEW] Import DB Manager
    from core.ui_helper import ui  # [NEW] Christmas UI Helper
    from core.settings_manager import settings # [NEW] Settings
except ImportError as e:
    print(f"❌ Error Import Core: {e}")
    print("Pastikan struktur folder 'core' lengkap.")
    sys.exit(1)

# Import Generator (Opsional)
try:
    import generate_master
    HAS_GENERATOR = True
except ImportError:
    generate_master = None  # type: ignore
    HAS_GENERATOR = False

from config.speed_settings import SPEED_LEVELS

# --- GLOBAL CONTROL ---
CURRENT_SPEED = SPEED_LEVELS['1'] # Default Relax

def on_key_press(key):
    if key == keyboard.Key.f9:
        bot_state.STOP_REQUESTED = True
        print("\n\n🛑 PERINTAH STOP DITERIMA (F9). Bot akan berhenti setelah langkah ini selesai...\n")

def set_console_topmost():
    """
    Set terminal window to always on top (Windows Only).
    On Linux, this function does nothing safely.
    """
    if os.name == 'nt':
        try:
            import ctypes
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0003)
                print("✅ Terminal set to ALWAYS ON TOP.")
        except Exception as e:
            print(f"⚠️ Gagal set top most: {e}")
    else:
        # Linux/Mac logic (Optional, usually handled by Window Manager)
        print("ℹ️  Running on Linux: 'Always on Top' feature disabled (OS managed).")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def show_banner():
    clear_screen()
    ui.print_banner(
        title="ERP AUTOMATION SUITE V9.3 (ULTIMATE)",
        subtitle="Created By Bayu A.K.A Ryu - Merry Christmas! 🎅",
        speed_mode=CURRENT_SPEED['name']
    )

def main_loop():
    global CURRENT_SPEED 

    ui.start_music()

    while True:
        show_banner()
        
        menu_options = [
            "[1] 🚀 START FULL TRANSACTION (Input -> Audit -> Save)",
            "[2] 🛡️ START AUDIT ONLY (Cek Validasi & Save)",
            "------------------------------------------------",
            "INFO: Tekan [F9] saat bot jalan untuk STOP (Balik ke Menu).",
            "INFO: Banting Mouse ke (0,0) untuk EMERGENCY KILL.",
            "[3] 🔧 KALIBRASI (Setting Koordinat)",
            "[s] ⚡ SET SPEED (Relax/Fast/Extreme)",
            "[4] 🧠 UPDATE MASTER DATA (Generate JSON from Raw Text)",
            "------------------------------------------------",
            "[5] 🏭 START BATCH MODE (Multi-Toko)",
            "[6] 🏪 KELOLA TOKO (Store Database UI)",
            "[7] 🗄️  DATABASE MANAGER (Cari, Edit, Hapus Barang)",
            "[8] ⚙️  PENGATURAN (Timeout & Audio)",
            "[9] 🌐 BUKA WEB DASHBOARD (UI Manager)",
            "[q] 🚪 KELUAR"
        ]
        
        ui.print_menu(menu_options)
        
        choice = input("\n👉 Pilih Menu [1-7/s/q]: ").lower().strip()
        
        if choice == 'q':
            print("\n👋 See ya, Bro! Happy Coding.")
            break

        elif choice == 's':
            print("\nPILIH KECEPATAN BOT:")
            print("   [1] 🐢 RELAX   (Aman, Stabil)")
            print("   [2] 🐇 FAST    (Recommended)")
            print("   [3] ⚡ EXTREME (Resiko Tinggi, Butuh PC Kenceng)")
            print("   [b] 🔙 Batal")
            sp = input("👉 Pilih [1/2/3/b]: ").strip()
            
            if sp.lower() == 'b':
                continue
                
            if sp in SPEED_LEVELS:
                CURRENT_SPEED = SPEED_LEVELS[sp]
                print(f"✅ Speed set to: {CURRENT_SPEED['name']}")
                time.sleep(1)
            else:
                print("❌ Pilihan salah.")
                time.sleep(1)
            
        elif choice == '1':
            # --- FULL CYCLE ---
            bot_state.STOP_REQUESTED = False 

            listener = keyboard.Listener(on_press=on_key_press)
            listener.start()

            print("\n🚀 MASUK MODE AUTO-LOOP. Tekan F9 untuk Stop.")
            counter = 1

            try:
                while not bot_state.STOP_REQUESTED:
                    print(f"\n🔄 --- TRANSAKSI KE-{counter} ---")
                    
                    retry_count = 0
                    max_retries = 20
                    transaction_success = False

                    while retry_count < max_retries:
                        if bot_state.STOP_REQUESTED: break

                        bot_exec = Executor(speed_profile=CURRENT_SPEED)
                        try:
                            bot_exec.run_phase_1(retry_idx=retry_count)
                        except KeyboardInterrupt:
                            break 
            
                        print(f"\n⏳ Transisi Phase {CURRENT_SPEED['phase_gap']}s...")
                        time.sleep(CURRENT_SPEED['phase_gap'])

                        # PHASE 2 (Audit)
                        bot_audit = ERP_Auditor(speed_profile=CURRENT_SPEED)
                        is_valid = bot_audit.run_audit()
                       
                        if is_valid:
                            print(f"✅ Transaksi #{counter} SUKSES di percobaan ke-{retry_count+1}.")
                            transaction_success = True
                            break 
                        else:
                            print(f"\n⚠️ AUDIT GAGAL (Percobaan {retry_count+1}/{max_retries})")
                            print("   ➡️ Melakukan Reset & Geser Baris...")

                            bot_exec.run_reset_sequence()
                            retry_count += 1
                            time.sleep(1)
                    
                    if bot_state.STOP_REQUESTED:
                        print("🛑 Loop dihentikan oleh user (F9).")
                        break

                    if transaction_success:
                        counter += 1
                    else:
                        print(f"\n❌ GAGAL TOTAL setelah {max_retries}x percobaan. Stop Loop.")
                        break
                    
                    print(f"⏳ Next transaction in {CURRENT_SPEED['phase_gap']}s...")
                    time.sleep(CURRENT_SPEED['phase_gap'])

            except pyautogui.FailSafeException:
                print("\n\n🚨 EMERGENCY STOP TERDETEKSI! (Mouse Slam)")
            except Exception as e:
                print(f"\n❌ CRASH REPORT: {e}")
            finally:
                if 'listener' in locals() and listener.running:
                    listener.stop()
            
            input("\n✅ Transaksi Selesai. Tekan Enter untuk kembali ke menu...")

        elif choice == '2':
            # --- AUDIT ONLY ---
            print("\n🛡️ Memulai PHASE 2: AUDIT ONLY...")
            try:
                bot_audit = ERP_Auditor(speed_profile=CURRENT_SPEED)
                bot_audit.run_audit()
            except Exception as e:
                print(f"\n❌ CRASH REPORT: {e}")
            input("\nTekan Enter untuk kembali ke menu...")
        
        elif choice == '3':
            # --- MENU KALIBRASI ---
            print("\n🔧 PILIH MODE KALIBRASI:")
            print("   [1] 🖱️  PHASE 1 (Input Logic)")
            print("   [2] 🦅 PHASE 2 (Audit Logic)")
            print("   [b] 🔙 Kembali")
            cal_mode = input("\n👉 Pilih Phase [1/2]: ").strip()
            
            if cal_mode == '1':
                try:
                    cmd = f'"{sys.executable}" -m core.calibrator'
                    os.system(cmd)
                except Exception as e: print(f"❌ Error: {e}")
            elif cal_mode == '2':
                try:
                    cal = CalibratorV2()
                    cal.run_wizard()
                except Exception as e: print(f"❌ Error: {e}")
            input("\nTekan Enter untuk kembali ke menu...")

        elif choice == '4':
            # --- GENERATE MASTER DATA ---
            if HAS_GENERATOR:
                assert generate_master is not None
                try:
                    import importlib
                    importlib.reload(generate_master)
                    generate_master.generate()
                except Exception as e: print(f"\n❌ Error Generator: {e}")
            else:
                print("\n❌ File 'generate_master.py' gak ketemu.")
            input("\nTekan Enter untuk kembali ke menu...")

        elif choice == '5':
            # --- BATCH MODE ---
            bot_state.STOP_REQUESTED = False 
            listener = keyboard.Listener(on_press=on_key_press)
            listener.start()
            try:
                manager = BatchManager(speed_profile=CURRENT_SPEED)
                manager.run_batch()
            except Exception as e:
                print(f"\n❌ BATCH ERROR: {e}")
            finally:
                if 'listener' in locals() and listener.running:
                    listener.stop()
            input("\n✅ Batch Selesai. Tekan Enter untuk kembali...")

        elif choice == '6':
            # --- STORE MANAGER ---
            try:
                mgr = StoreManager()
                mgr.run_ui()
            except Exception as e: print(f"❌ Error UI: {e}")

        elif choice == '7':
            # --- DATABASE MANAGER (NEW) ---
            try:
                db_mgr = DatabaseManager()
                db_mgr.run()
            except Exception as e:
                print(f"❌ Error DB Manager: {e}")
                input("Enter untuk lanjut...")
        elif choice == '8':
            # --- SETTINGS MENU ---
            settings.run_menu()
        elif choice == '9':
            # --- WEB DASHBOARD ---
            from core.web_server import start_server, stop_server
            import webbrowser
            
            print("\n🌐 Memulai Web Server di background...")
            start_server()
            time.sleep(1) # Tunggu server siap
            
            print("✅ Server berjalan di http://127.0.0.1:5000")
            print("Membuka browser otomatis...")
            webbrowser.open('http://127.0.0.1:5000')
            
            input("\n🛑 TEKAN [ENTER] DI SINI UNTUK MEMATIKAN SERVER DAN KEMBALI KE MENU...")
            stop_server()
            print("Server dimatikan.")

        else:
            print("\n⚠️ Pilihan gak valid bro.")
            time.sleep(1)

if __name__ == "__main__":
    set_console_topmost()
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\n\n🛑 Force Stop. Keluar...")
        sys.exit(0) 