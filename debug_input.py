import json
import sys

print("🕵️‍♂️  MEMULAI INVESTIGASI NILAI INPUT...")
print("========================================")

# 1. CEK SOURCE CODE CONFIG
try:
    from config.steps_config import PHASE_1_STEPS
    print("✅ Berhasil import config/steps_config.py")
    
    found = False
    for step in PHASE_1_STEPS:
        if step['id'] == '2_cust_input_val': # ID input customer lu
            found = True
            val_in_code = step.get('value')
            print(f"👉 Nilai di file Python (steps_config.py): [{val_in_code}]")
            
            if val_in_code == 'n':
                print("   🚨 TERTANGKAP! File config lu isinya masih 'n' bro. Coba Save ulang!")
            elif val_in_code == 'b':
                print("   ✅ Oke, di file config isinya udah bener 'b'.")
            else:
                print(f"   ℹ️ Isinya: {val_in_code}")
            break
            
    if not found:
        print("❌ ID '2_cust_input_val' gak ketemu di config!")

except ImportError:
    print("❌ Gak bisa import config. Pastikan struktur folder bener.")

print("\n----------------------------------------")

# 2. CEK DATA JSON (SISA KALIBRASI)
try:
    with open('coordinates.json', 'r') as f:
        data = json.load(f)
        if '2_cust_input_val' in data:
            val_in_json = data['2_cust_input_val'].get('value')
            print(f"👉 Nilai di file JSON (coordinates.json)   : [{val_in_json}]")
            
            if val_in_json == 'n':
                print("   ℹ️ Nah! Di JSON isinya 'n'. Kalau Executor lu masih pake logic lama, dia bakal ambil ini.")
        else:
            print("❌ ID gak ketemu di JSON.")
except FileNotFoundError:
    print("❌ File coordinates.json gak ada.")

print("\n========================================")
print("KESIMPULAN:")

if val_in_code == 'b' and val_in_json == 'n':
    print("Masalahnya di Executor.py lu!")
    print("Script itu masih baca JSON (N) dan ngacangin Config Python (B).")
    print("SOLUSI: Pastikan lu udah copy-paste UPDATE kode executor.py yang gw kasih tadi.")
elif val_in_code == 'n':
    print("Masalahnya di File Config lu!")
    print("Lu belum save file, atau ngedit file yang salah.")