import json
import os
import sys
try:
    import questionary
    from questionary import Choice, Separator
except ImportError:
    print("❌ Library 'questionary' belum diinstall!")
    print("👉 Silahkan run: pip install questionary")
    sys.exit(1)

DB_FILE = "stores.json"

class StoreManager:
    def __init__(self):
        self.stores = self.load_stores()

    def load_stores(self):
        if not os.path.exists(DB_FILE):
            # Init default kalo file gak ada
            default_data = [{"name": "CONTOH TOKO", "selected": False}]
            with open(DB_FILE, 'w') as f:
                json.dump(default_data, f, indent=4)
            return default_data
        
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error baca database: {e}")
            return []

    def save_stores(self):
        try:
            with open(DB_FILE, 'w') as f:
                json.dump(self.stores, f, indent=4)
            # print("💾 Database Toko tersimpan.") # Silent save biar terminal bersih
        except Exception as e:
            print(f"❌ Gagal simpan database: {e}")

    def run_ui(self):
        while True:
            # 1. Siapkan Pilihan (Choices) untuk Checkbox Utama
            choices = []
            for store in self.stores:
                choices.append(Choice(
                    title=store['name'],
                    value=store['name'],
                    checked=store.get('selected', False)
                ))
            
            # Tambah Menu Operasional
            choices.append(Separator())
            choices.append(Choice(title="➕ TAMBAH TOKO BARU", value="ADD_NEW_STORE"))
            choices.append(Choice(title="🗑️  HAPUS TOKO", value="DELETE_STORE")) # [NEW] Fitur Hapus
            choices.append(Separator())
            choices.append(Choice(title="✅ SELESAI & SIMPAN", value="EXIT_MENU"))

            # 2. Tampilkan UI
            print("\n========================================")
            print("   🏪 STORE MANAGER (Kelola Database)")
            print("   [Spasi] = Centang untuk Batch Mode")
            print("   [Enter] = Eksekusi Menu")
            print("========================================")
            
            # Note: questionary.checkbox mengembalikan LIST value yang dicentang
            # Kita perlu handle kalau user mencentang menu "ADD/DELETE"
            
            selected_values = questionary.checkbox(
                "Pilih Toko untuk Batch Mode ATAU Menu Kelola:",
                choices=choices,
                style=questionary.Style([
                    ('qmark', 'fg:#E91E63 bold'),
                    ('question', 'bold'),
                    ('answer', 'fg:#2196f3 bold'),
                    ('pointer', 'fg:#673ab7 bold'),
                    ('highlighted', 'fg:#673ab7 bold'),
                    ('selected', 'fg:#4caf50 bold'),
                    ('separator', 'fg:#cc5454'),
                    ('instruction', ''),
                    ('text', ''),
                    ('disabled', 'fg:#858585 italic')
                ])
            ).ask()

            # Handle Cancel/Ctrl+C
            if selected_values is None:
                return

            # --- LOGIC HANDLING ---
            
            # A. TAMBAH TOKO
            if "ADD_NEW_STORE" in selected_values:
                new_name = questionary.text("👉 Masukkan Nama Toko Baru:").ask()
                if new_name:
                    clean_name = new_name.strip().upper()
                    # Cek duplikat
                    if any(s['name'] == clean_name for s in self.stores):
                        print(f"⚠️ Toko '{clean_name}' sudah ada!")
                        time.sleep(1)
                    else:
                        self.stores.append({"name": clean_name, "selected": True})
                        self.save_stores()
                        print(f"✅ Toko '{clean_name}' ditambahkan.")
                
                # Update status toko lain yang mungkin diubah user sebelum klik Add
                self._sync_selection_state(selected_values, ignore_cmds=True)
                continue 

            # B. HAPUS TOKO (Fitur Baru)
            if "DELETE_STORE" in selected_values:
                # Ambil list nama toko buat dropdown hapus
                delete_choices = [s['name'] for s in self.stores]
                if not delete_choices:
                    print("⚠️ Daftar toko kosong, gak ada yang bisa dihapus.")
                else:
                    target_delete = questionary.select(
                        "❌ Pilih Toko yang mau DIHAPUS PERMANEN:",
                        choices=delete_choices
                    ).ask()
                    
                    if target_delete:
                        confirm = questionary.confirm(f"Yakin mau hapus '{target_delete}'?").ask()
                        if confirm:
                            self.stores = [s for s in self.stores if s['name'] != target_delete]
                            self.save_stores()
                            print(f"🗑️ Toko '{target_delete}' berhasil dihapus.")
                
                # Sync selection sisa
                self._sync_selection_state(selected_values, ignore_cmds=True)
                continue

            # C. SELESAI / SAVE
            if "EXIT_MENU" in selected_values:
                # Simpan status checkbox terakhir
                self._sync_selection_state(selected_values, ignore_cmds=True)
                print(f"✅ Database diupdate.")
                return

            # D. Kalau cuma centang toko doang tanpa klik menu Exit
            # (Looping terus sampe user klik EXIT_MENU biar UX-nya jelas)
            self._sync_selection_state(selected_values, ignore_cmds=True)

    def _sync_selection_state(self, selected_values, ignore_cmds=False):
        """Update status True/False di database memory & file berdasarkan checklist user"""
        cmd_list = ["ADD_NEW_STORE", "DELETE_STORE", "EXIT_MENU"]
        
        # Bersihkan list dari command menu, ambil nama tokonya aja
        active_stores = [x for x in selected_values if x not in cmd_list]
        
        for store in self.stores:
            if store['name'] in active_stores:
                store['selected'] = True
            else:
                store['selected'] = False
        self.save_stores()

    def get_active_stores(self):
        """Helper buat BatchManager ambil toko yg dicentang doang"""
        self.stores = self.load_stores() 
        return [s['name'] for s in self.stores if s.get('selected', True)]

if __name__ == "__main__":
    import time # Buat delay dikit pas notif
    mgr = StoreManager()
    mgr.run_ui()