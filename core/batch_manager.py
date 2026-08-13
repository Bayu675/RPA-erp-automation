# erp-automation/core/batch_manager.py
import time
from core.executor import Executor
from core.auditor import ERP_Auditor
from core.store_selector import StoreSelector
from core.logger import BotLogger
from config.speed_settings import SPEED_LEVELS
from core.store_manager import StoreManager
import config.state as bot_state 
from core.settings_manager import settings

class BatchManager:
    def __init__(self, speed_profile=None):
        self.spd = speed_profile if speed_profile else SPEED_LEVELS['2'] 
        
        self.exec = Executor(speed_profile=self.spd)
        self.audit = ERP_Auditor(speed_profile=self.spd, auto_skip_unknown=True)  # [FIX] Auto-skip for batch
        self.selector = StoreSelector(self.exec, self.audit)
        self.store_mgr = StoreManager()
        
    def run_batch(self):
        target_stores = self.store_mgr.get_active_stores()
        print("\n🏭 STARTING BATCH MODE (MULTI-STORE - STRIKE SYSTEM)")
        print("====================================================")
        print(f"📋 Antrian: {len(target_stores)} Toko Terpilih")
        
        # [FIX] Validasi empty list
        if len(target_stores) == 0:
            print("\n❌ ERROR: Tidak ada toko yang dipilih!")
            print("👉 Gunakan Menu [6] untuk mengelola database toko.")
            print("👉 Centang toko yang ingin diproses di batch mode.")
            input("\nTekan Enter untuk kembali ke menu...")
            return  # Abort batch

        print("\n⏳ JEDA 3 DETIK! Silahkan pindah ke window ERP sekarang...")
        for i in range(3, 0, -1):
            print(f"   {i}...", end="\r", flush=True)
            time.sleep(1)
        print("🚀 GAS! Memulai operasi...")
        
        while True:
            work_done_in_cycle = False 
            
            for i, store_name in enumerate(target_stores):
                if bot_state.STOP_REQUESTED: break

                print(f"\n🏢 [TOKO {i+1}/{len(target_stores)}] Processing: {store_name}")
                
                if not self._ensure_store_ready(store_name):
                    print(f"⏩ SKIP {store_name}: Gagal dipilih setelah 3x percobaan.")
                    continue
                
                store_had_success = self.process_store_transactions(store_name)
                if store_had_success:
                    work_done_in_cycle = True
            
            if bot_state.STOP_REQUESTED:
                print("\n🛑 BATCH STOPPED BY USER.")
                break

            if not work_done_in_cycle:
                print("\n💤 RONDA SELESAI. Tidak ada transaksi baru di SEMUA toko.")
                break 
            
            print("\n🔄 SATU PUTARAN SELESAI. Ada transaksi sukses tadi, jadi kita MUTER LAGI...")
            time.sleep(0.5)  # [OPTIMIZED] Reduced from 2.0s
        print("\n🏁 PROGRAM FINISHED (AUTO STOP).")

    def _ensure_store_ready(self, store_name):
        for attempt in range(1, 4):
            if bot_state.STOP_REQUESTED: return False
            print(f"   🔍 Seleksi Toko '{store_name}' (Percobaan {attempt}/3)...")
            found = self.selector.select_store(store_name)
            if found:
                return True
            time.sleep(0.3)  # [OPTIMIZED] Reduced from 1.0s 
        return False

    def process_store_transactions(self, store_name):
        skipped_count = 0
        idle_strikes = 0   
        
        # [FIX PYLANCE] Pastikan MAX_STRIKES selalu integer
        raw_strikes = settings.get('max_strikes')
        MAX_STRIKES: int = int(raw_strikes) if raw_strikes is not None else 3
        
        any_success = False
        
        while (MAX_STRIKES == 0) or (idle_strikes < MAX_STRIKES):
            cursor_index = skipped_count
            
            strike_display = "∞" if MAX_STRIKES == 0 else str(MAX_STRIKES)
            print(f"\n🔄 {store_name} | Row Offset: {cursor_index} | Strike: {idle_strikes}/{strike_display}")
            
            if bot_state.STOP_REQUESTED:
                return any_success
            
            if not self._ensure_store_ready(store_name):
                print("❌ Dropdown berubah dan gagal dikembalikan. Abort toko ini.")
                break

            # PHASE 1: INPUT
            # [OPTIMIZATION] Skip startup wait kecuali di attempt pertama
            is_first_attempt = (cursor_index == 0 and idle_strikes == 0)
            try:
                has_input = self.exec.run_phase_1(
                    retry_idx=cursor_index, 
                    skip_customer_selection=True,
                    initial_wait=is_first_attempt  # Hanya wait di attempt pertama
                )
            except KeyboardInterrupt:
                return any_success

            if not has_input:
                print("   ⚠️ Tabel Kosong / Gagal Klik Baris.")
                idle_strikes += 1
                time.sleep(1)
                continue

            # PHASE 2: AUDIT
            is_valid = self.audit.run_audit(skip_startup_wait=True)
            
            if is_valid:
                print(f"✅ SUKSES! {store_name} Data tersimpan.")
                print(f"   👉 Reset Strike Counter (0). Telunjuk tetap di {cursor_index}.")
                
                # [FIX] LOGIC RESET
                # Kalau sukses, baris itu hilang/naik. Jadi skipped_count JANGAN ditambah.
                # Kita tetap klik di posisi yang sama (karena baris bawahnya udah naik).
                idle_strikes = 0 
                any_success = True
                time.sleep(0.5)  # [OPTIMIZED] Reduced from 2.0s for batch speed
                
            else:
                # [FIX] Beri info yang lebih jelas di Batch Mode
                print(f"❌ REJECT/SKIP pada baris ke-{cursor_index + 1}.")
                print(f"   (Cek log di atas untuk detail: Harga beda / Barang tidak dikenal / Total selisih)")
                print(f"   👉 STRIKE {idle_strikes+1}! Telunjuk TURUN ke baris {cursor_index + 1}.")
                
                self.exec.run_reset_sequence()
                
                # [FIX] LOGIC SKIP
                # Kalau gagal, baris itu masih ada di sana (batu).
                # Kita harus tambah skipped_count biar next loop kita klik bawahnya.
                skipped_count += 1
                idle_strikes += 1
                
        if MAX_STRIKES > 0:
            print(f"🛑 Toko '{store_name}' Selesai (Kena {MAX_STRIKES} Strike Out). Pindah ke toko selanjutnya.")
        else:
            print(f"🛑 Toko '{store_name}' Selesai (Dihentikan Manual / Tabel Habis). Pindah ke toko selanjutnya.")
            
        return any_success