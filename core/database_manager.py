import json
import os
import time
import re
import tempfile

DB_FILE = "master_data.json"

class DatabaseManager:
    def __init__(self):
        self.data = self.load_db()
        self.items = self.data.get('items', {})

     # [NEW] Helper Validasi Input
    def _get_input(self, prompt, valid_opts):
        while True:
            val = input(prompt).strip().lower()
            # Handle empty default (biasanya opsi pertama/terakhir tergantung konteks, disini strict)
            if val in valid_opts: return val
            print(f"   ❌ Pilihan tidak valid! Masukkan salah satu: {valid_opts}")

    def load_db(self):
        if not os.path.exists(DB_FILE):
            print("❌ Database tidak ditemukan!")
            return {"items": {}, "rules": {}}
        try:
            with open(DB_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading DB: {e}")
            return {"items": {}, "rules": {}}

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

    def save_db(self):
        self.data['items'] = self.items
        try:
            self.safe_save_json(self.data, DB_FILE)
            print("💾 Database berhasil disimpan!")
            time.sleep(0.5)
        except Exception as e:
            print(f"❌ Gagal menyimpan: {e}")

    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')

    def print_header(self):
        self.clear_screen()
        print("==========================================")
        print("🗄️  DATABASE MANAGER (CRUD SYSTEM)")
        print(f"📦 Total Items: {len(self.items)}")
        print("==========================================\n")

    def run(self):
        while True:
            self.print_header()
            print("MENU UTAMA:")
            print("   [1] 🔍 CARI & EDIT / HAPUS BARANG")
            print("   [2] ➕ TAMBAH BARANG BARU")
            print("   [3] 🔙 KEMBALI KE MENU UTAMA BOT")
            
            choice = input("\n👉 Pilih Menu [1-3]: ").strip()

            if choice == '1':
                self.search_ui()
            elif choice == '2':
                self.add_item_ui()
            elif choice == '3':
                break

    def search_ui(self):
        while True:
            self.print_header()
            print("Ketik kata kunci (Min 3 huruf) atau 'b' untuk batal.")
            keyword = input("🔍 Search: ").strip().upper()

            if keyword == 'B': break
            if len(keyword) < 3:
                print("⚠️ Kata kunci terlalu pendek!"); time.sleep(1); continue

            # Filter Logic
            results = [k for k in self.items.keys() if keyword in k]
            
            if not results:
                print("❌ Tidak ditemukan."); time.sleep(1); continue

            # Show Results
            print(f"\n🔎 Ditemukan {len(results)} barang:")
            for i, name in enumerate(results):
                price = self.items[name]['base_price']
                print(f"   [{i+1}] {name} (Rp {price:,.0f})")

            print("\n👉 Masukkan NOMOR untuk Edit/Hapus (atau 'b' batal)")
            try:
                sel = input("   Pilih: ").strip()
                if sel.lower() == 'b': continue
                
                idx = int(sel) - 1
                if 0 <= idx < len(results):
                    target_name = results[idx]
                    self.edit_item_ui(target_name)
                else:
                    print("❌ Nomor salah!")
            except ValueError:
                print("❌ Input harus angka!")
            time.sleep(0.5)

    def edit_item_ui(self, name):
        while True:
            item = self.items[name]
            self.clear_screen()
            print(f"✏️  EDIT MODE: {name}")
            print("-" * 50)
            print(f"   [1] Harga Dasar  : Rp {item['base_price']:,.0f}")
            
            disc_str = " + ".join([str(d) for d in item['default_discs'] if d > 0])
            if not disc_str: disc_str = "0 (Netto)"
            print(f"   [2] Diskon       : {disc_str}%")
            
            status = "✅ SERVICE/NETTO (No Footer Disc)" if item['is_netto'] else "❌ BARANG REGULER (Kena Footer Disc)"
            print(f"   [3] Status Netto : {status}")
            
            tax_status = "✅ KENA PPN" if item.get('is_taxable', True) else "❌ BEBAS PPN"
            print(f"   [7] Status PPN   : {tax_status}")
            
            # [NEW] Info Harga Alternatif
            alt_count = len(item.get('alternatives', []))
            print(f"   [8] Harga Alt    : {alt_count} Opsi Tersimpan")
            
            rule_info = item.get('custom_rule', 'Tidak ada')
            if isinstance(rule_info, dict): rule_info = f"{rule_info['logic']} -> Disc {rule_info['disc']}% ({rule_info.get('mode', 'NORMAL')})"
            print(f"   [6] Price Rule   : {rule_info}") # New Menu Display
            print("-" * 50)
            print("   [4] 🗑️  HAPUS BARANG INI")
            print("   [5] 💾 SELESAI & KEMBALI")

            choice = input("\n👉 Mau ubah apa? [1-8]: ").strip()

            if choice == '1':
                raw_val = input("   💰 Masukkan Harga Baru (Ketik 'b' untuk batal): ").strip()
                if raw_val.lower() == 'b': continue
                try:
                    val = float(raw_val.replace(',', '').replace('.', ''))
                    item['base_price'] = val
                    self.save_db()
                except: print("❌ Error input!")

            elif choice == '2':
                raw = input("   🏷️  Masukkan Diskon (Cth: 45+10) atau 'b' batal: ").strip()
                if raw.lower() == 'b': continue
                discs = [0.0]*4
                parts = raw.replace('%','').split('+')
                for i, p in enumerate(parts):
                    if i < 4:
                        try: discs[i] = float(p)
                        except: pass
                item['default_discs'] = discs
                # Auto update netto status logic
                if all(d == 0 for d in discs):
                    print("   ℹ️ Diskon 0, otomatis set ke Netto.")
                    item['is_netto'] = True
                else:
                    item['is_netto'] = False
                self.save_db()

            elif choice == '3':
                item['is_netto'] = not item['is_netto']
                self.save_db()

            elif choice == '7':
                item['is_taxable'] = not item.get('is_taxable', True)
                self.save_db()
                
            elif choice == '8': # [NEW] Menu Harga Alternatif
                alts = item.get('alternatives', [])
                print("\n🔀 DAFTAR HARGA ALTERNATIF:")
                if not alts: print("   (Kosong)")
                for i, alt in enumerate(alts):
                    tax_str = "Tax:ON" if alt.get('is_taxable', True) else "Tax:OFF"
                    print(f"   [{i+1}] Rp {alt['price']:,.0f} ({tax_str}) - {alt.get('note','-')}")
                
                print("\n   [A] Tambah Harga Baru")
                print("   [D] Hapus Semua")
                print("   [B] Kembali")
                sub = self._get_input("   Pilih: ", ['a', 'd', 'b']).upper()
                
                if sub == 'A':
                    raw_p = input("   💰 Harga Alt (Rp) atau 'b' batal: ").strip()
                    if raw_p.lower() == 'b': continue
                    try:
                        p = float(raw_p.replace(',', '').replace('.', ''))
                        t_in = self._get_input("   Kena PPN? (1=Ya, 0=Tdk): ", ['1', '0', 'y', 'n'])
                        t = (t_in in ['1', 'y'])
                        n = input("   Catatan (Opsional): ").strip()
                        alts.append({"price": p, "is_taxable": t, "note": n})
                        item['alternatives'] = alts
                        self.save_db()
                    except: print("❌ Input Error")
                
                elif sub == 'D':
                    item['alternatives'] = []
                    self.save_db()

            elif choice == '6': # New Menu for Rules
                print("\n📐 PRICE RULES EDITOR")
                print("   [A] Rule Matematika:")
                print("       Format: variable operator nilai")
                print("       Contoh: m2 <= 0.5  (Jika m2 kecil dari 0.5)")
                print("   [B] Rule Selalu Aktif (Upselling):")
                print("       Ketik: True")
                
                rule_str = input("   Logika (Kosongkan utk hapus, 'b' batal): ").strip()
                if rule_str.lower() == 'b': continue
                if not rule_str:
                    # Logic hapus rule existing untuk item ini (complex, skip for now or simple implementation)
                    print("   Rule dihapus/dikosongkan.")
                else:
                    disc_str = input("   Diskon % jika kena rule (cth: 50): ").strip()
                    # [NEW] Tanya Mode Hitung
                    print("   Mode Hitung saat Rule Kena:")
                    print("   [1] NORMAL  (Tetap dikali M2 asli)")
                    print("   [2] FLAT M2 (M2 dianggap 1 / Diabaikan)")
                    print("   [3] ALLOW UPS (Boleh Upselling / Harga > DB)")
                    mode_in = self._get_input("   Pilih [1/2/3]: ", ['1', '2', '3'])
                    
                    if mode_in == '2': calc_mode = "FLAT_M2"
                    elif mode_in == '3': calc_mode = "ALLOW_UPS"
                    else: calc_mode = "NORMAL"
                    try:
                        # Simple validation
                        is_math = re.match(r'([a-zA-Z0-9_]+)\s*(<=|>=|==|!=|<|>)\s*([0-9\.]+)', rule_str)
                        is_bool = (rule_str.lower() == 'true')

                        if not (is_math or is_bool):
                            print("❌ Format salah! Ketik 'True' atau rumus matematika (cth: m2 <= 0.5)")
                        else:
                            
                            item['custom_rule'] = {'logic': rule_str, 'disc': float(disc_str), 'mode': calc_mode}
                            self.save_db()
                            print("✅ Rule tersimpan!")
                            time.sleep(1)
                    except: print("❌ Input error")

            elif choice == '4':
                confirm = input(f"⚠️ YAKIN HAPUS '{name}'? [y/N]: ").lower()
                if confirm == 'y':
                    del self.items[name]
                    self.save_db()
                    return # Keluar dari menu edit karena barangnya ilang
            
            elif choice == '5':
                break

    def add_item_ui(self):
        self.clear_screen()
        print("➕ TAMBAH BARANG BARU")
        print("-" * 30)
        
        name = input("1. Nama Barang (Copy Paste dari Excel) atau 'b' batal: ").strip().upper()
        if not name: return
        if name == 'B': return
        if name in self.items:
            print("⚠️ Barang sudah ada! Masuk ke menu edit saja."); time.sleep(2); return

        raw_price = input("2. Harga (Rp) atau 'b' batal: ").strip()
        if raw_price.lower() == 'b': return
        try:
            price = float(raw_price.replace(',', '').replace('.', ''))
        except:
            print("❌ Harga salah!"); time.sleep(1); return

        print("3. Tipe Barang:")
        print("   [1] REGULER (Harga Fix, Kena Diskon Footer)")
        print("   [2] NETTO   (Harga Fix, NO Diskon Footer)")
        print("   [3] JASA    (Harga Bebas, NO Diskon Footer)")
        type_in = input("   Pilih [1/2/3]: ").strip()
        if type_in == 'B': return

        is_netto = (type_in in ['2', '3'])
        price_val = (type_in != '3') # Jasa (3) tidak divalidasi harganya

        is_tax_in = self._get_input("4. Apakah kena PPN? (1=Ya, 0=Tdk): ", ['1', '0', 'y', 'n'])
        is_taxable = (is_tax_in in ['1', 'y'])


        discs = [0.0]*4
        if type_in == '1': # Cuma Reguler yang punya diskon baris default
            raw_disc = input("5. Diskon (Cth: 45+10) atau 'b' batal: ").strip()
            if raw_disc.lower() == 'b': return
            parts = raw_disc.replace('%','').split('+')
            for i, p in enumerate(parts):
                if i < 4:
                    try: discs[i] = float(p)
                    except: pass

        self.items[name] = {
            "base_price": price,
            "default_discs": discs,
            "price_validation": price_val,
            "is_netto": is_netto,
            "is_taxable": is_taxable
        }
        self.save_db()
        print(f"✅ {name} berhasil ditambahkan!")
        time.sleep(1.5)

if __name__ == "__main__":
    db = DatabaseManager()
    db.run()