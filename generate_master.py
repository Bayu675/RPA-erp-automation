import json
import os
import shutil
import pandas as pd
from datetime import datetime

MASTER_FILE = 'master_data.json'
BACKUP_DIR = 'backups'

def get_mode(series):
    """Mencari nilai mayoritas (modus), jika kosong kembalikan 0.0"""
    mode_vals = series.mode()
    return float(mode_vals.iloc[0]) if not mode_vals.empty else 0.0

def generate_from_excel(excel_path):
    print(f"🔄 Membaca file Excel: {excel_path}...")
    try:
        df = pd.read_excel(excel_path)
    except Exception as e:
        print(f"❌ Gagal membaca Excel: {e}")
        return

    # Pastikan kolom yang dibutuhkan ada, jika tidak buat dengan nilai 0
    required_cols = ['@ Harga', 'Disc-1 (%)', 'Disc-2 (%)', 'Disc-3 (%)', 'Disc-4 (%)']
    for col in required_cols:
        if col not in df.columns:
            df[col] = 0.0

    # Isi NaN dengan 0.0
    df[required_cols] = df[required_cols].fillna(0.0)

    print("📊 Memproses data dan mencari nilai mayoritas (Modus) untuk duplikat...")
    # Group by Nama Barang dan cari Modus
    grouped = df.groupby('Nama Barang').agg({
        '@ Harga': get_mode,
        'Disc-1 (%)': get_mode,
        'Disc-2 (%)': get_mode,
        'Disc-3 (%)': get_mode,
        'Disc-4 (%)': get_mode
    }).reset_index()

    master_db = {}
    keywords_no_val = ["BIAYA", "ONGKOS", "PACKING", "SERVICE"]

    for _, row in grouped.iterrows():
        name = str(row['Nama Barang']).strip().upper()
        if not name or name == 'NAN': continue

        price = float(row['@ Harga'])
        discs = [
            float(row['Disc-1 (%)']),
            float(row['Disc-2 (%)']),
            float(row['Disc-3 (%)']),
            float(row['Disc-4 (%)'])
        ]

        # Logika Data
        #is_netto = all(d == 0.0 for d in discs)
        is_netto = False
        price_validation = not any(kw in name for kw in keywords_no_val)

        master_db[name] = {
            "base_price": price,
            "default_discs": discs,
            "price_validation": price_validation,
            "is_netto": is_netto,
            "is_taxable": True # Default
        }

    final_db = {"items": master_db, "rules": {}}

    # --- SAFETY NET (BACKUP) ---
    if os.path.exists(MASTER_FILE):
        os.makedirs(BACKUP_DIR, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = os.path.join(BACKUP_DIR, f"master_data_{timestamp}.json")
        
        print(f"\n⚠️ File {MASTER_FILE} sudah ada.")
        confirm = input("Apakah Anda yakin ingin menimpanya? (y/n): ").strip().lower()
        
        if confirm == 'y':
            shutil.copy(MASTER_FILE, backup_path)
            print(f"💾 Backup berhasil dibuat: {backup_path}")
        else:
            print("❌ Operasi dibatalkan.")
            return

    # Save ke JSON
    with open(MASTER_FILE, 'w') as f:
        json.dump(final_db, f, indent=4)
    
    print(f"✅ Selesai! {len(master_db)} barang tersimpan ke {MASTER_FILE}.")

if __name__ == "__main__":
    excel_file = input("Masukkan nama file Excel (contoh: data.xlsx): ").strip()
    if os.path.exists(excel_file):
        generate_from_excel(excel_file)
    else:
        print("❌ File tidak ditemukan!")

def generate():
    excel_file = input("Masukkan nama file Excel (contoh: data.xlsx): ").strip()
    if os.path.exists(excel_file):
        generate_from_excel(excel_file)
    else:
        print("❌ File tidak ditemukan!")

if __name__ == "__main__":
    generate()