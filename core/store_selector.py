# erp-automation/core/store_selector.py
import time
from core.logger import BotLogger

class StoreSelector:
    def __init__(self, executor, auditor):
        self.exec = executor
        self.audit = auditor
        self.max_attempts = 25 # Batas maksimal muter biar gak infinite loop
    
    def normalize_store_name(self, name):
        """Normalize store name: Hapus SEMUA spasi dan simbol (Pure Alphanumeric)"""
        if not name: return ""
        name = name.upper()
        # Ide Jenius: Buang semua karakter kecuali huruf dan angka
        return "".join(e for e in name if e.isalnum())

    def select_store(self, target_name: str):
        import config.state as bot_state
        
        target_name_norm = self.normalize_store_name(target_name)
        first_char = target_name[0]
        
        # [LOGIC BARU] PEEK BEFORE CLICK (Intip dulu)
        # Cek apakah toko yang terpilih SEKARANG sudah benar?
        current_header = self.audit.read_customer_header()
        current_header_norm = self.normalize_store_name(current_header)
        
        if target_name_norm in current_header_norm:
            print(f"   ✅ Toko sudah sesuai: {current_header} (Skip Selection)")
            return True
            
        # Kalau belum sesuai, baru kita cari
        print(f"\n🔍 MENCARI TOKO: [{target_name}] (Current: {current_header})")

        # 1. Buka Dropdown (Pake koordinat Phase 1)
        # ID: 1_cust_dropdown_open
        self.exec.execute_step("1_cust_dropdown_open", "Buka Dropdown Customer", delay=0.5)

        found = False
        attempt = 0
        seen_stores = set()  # [NEW] Track untuk early bailout

        while attempt < self.max_attempts:
            # [FIX] Check F9 stop request
            if bot_state.STOP_REQUESTED:
                print("\n🛑 Store selection stopped by user (F9)")
                return False
            attempt += 1
            
            # 2. Ketik Huruf Depan (Cycling)
            # Kita inject manual perintah ketik tanpa lewat JSON config biar cepat
            # Tapi kita butuh akses ke executor buat ngetik doang
            import pyautogui
            pyautogui.write(first_char)
            time.sleep(0.2)  # [OPTIMIZED] Reduced for batch speed
            
            # 3. Tutup Dropdown (Klik Sembarang)
            # ID: 3_cust_dropdown_close
            self.exec.execute_step("3_cust_dropdown_close", "Tutup Dropdown (Cek Posisi)", delay=0.3)  # [OPTIMIZED]

            # 4. INTIP: Apakah sudah benar?
            current_text = self.audit.read_customer_header()
            current_text_norm = self.normalize_store_name(current_text)
            print(f"   👁️ Percobaan #{attempt}: Terbaca '{current_text}'")

            # Check match dengan normalization
            if target_name_norm in current_text_norm:
                print(f"   ✅ MATCH! Toko ditemukan: {current_text}")
                found = True
                break
            
            # [NEW] Early bailout - detect cycling
            seen_stores.add(current_text_norm)
            if len(seen_stores) >= 5 and attempt >= 10:
                # Udah lihat 5+ toko berbeda dan 10+ attempt = toko gak ada
                print(f"\n⚠️ EARLY BAILOUT: Toko '{target_name}' tidak ditemukan setelah cycling.")
                print(f"   Toko yang terdeteksi: {list(seen_stores)[:5]}")
                break
            
            # Kalau salah, Buka lagi dropdown buat putaran selanjutnya
            print(f"   ❌ Mismatch (Target: {target_name}). Ulangi...")
            self.exec.execute_step("1_cust_dropdown_open", "Buka Dropdown Lagi", delay=0.3)
        
        if not found:
            BotLogger.error(f"GAGAL MENEMUKAN TOKO '{target_name}' setelah {self.max_attempts}x percobaan.")
            return False
            
        return True