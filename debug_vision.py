import cv2
import numpy as np
import pyautogui
import json
import os

# Load Config
try:
    with open("coordinates_phase2.json", "r") as f:
        coords = json.load(f)
        table = coords['table_area']
except:
    print("❌ File coordinates_phase2.json gak ada/rusak!")
    exit()

print("📸 CHEESEEE! Mengambil screenshot dalam 3 detik...")
print("   (Pastikan ERP terbuka dan ada baris biru terpilih)")
import time; time.sleep(3)

# 1. Screenshot Full
full_ss = pyautogui.screenshot()
full_np = np.array(full_ss)
full_bgr = cv2.cvtColor(full_np, cv2.COLOR_RGB2BGR)

# 2. Crop Area Tabel (Sesuai Phase 1)
tl, tt, tw, th = table['left'], table['top'], table['width'], table['height']
table_crop = full_bgr[tt:tt+th, tl:tl+tw]

# 3. Proses Deteksi Biru (Logic sama persis dengan auditor.py)
hsv = cv2.cvtColor(table_crop, cv2.COLOR_BGR2HSV)
# Range Biru Standar
mask = cv2.inRange(hsv, np.array([90, 20, 20]), np.array([130, 255, 255]))

contours, _ = cv2.findContours(mask, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
best_row = None
max_w = 0

debug_img = table_crop.copy()

print(f"\n🔍 Menganalisa area tabel ({tw}x{th})...")

for c in contours:
    x, y, w, h = cv2.boundingRect(c)
    
    # Visualisasi SEMUA kandidat (Kotak Hijau Tipis)
    cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 255, 0), 1)
    
    # Filter Logic (Sesuai auditor.py)
    # Kita perketat filter debug biar keliatan dia lolos atau enggak
    passes_filter = (18 < h < 65) and (w > 100)
    
    if passes_filter:
        print(f"   ✅ Kandidat Valid: y={y}, h={h}, w={w}")
        if w > max_w:
            max_w = w
            best_row = {'top': y, 'bottom': y+h, 'height': h, 'width': w}
            # Visualisasi PEMENANG (Kotak Merah Tebal)
            cv2.rectangle(debug_img, (x, y), (x+w, y+h), (0, 0, 255), 3)
    else:
        # Debug: Kenapa gagal?
        pass # (Optional: Print alasan gagal)

# 4. Simpan Hasil
if not os.path.exists("debug_images"): os.makedirs("debug_images")
cv2.imwrite("debug_images/VISION_CHECK.png", debug_img)
cv2.imwrite("debug_images/VISION_MASK.png", mask) # Liat apa yang dianggap biru

if best_row:
    print(f"\n🎉 KETEMU! Baris Biru di Y: {best_row['top']} - {best_row['bottom']} (Tinggi: {best_row['height']}px)")
    print("👉 Cek file 'debug_images/VISION_CHECK.png'. Kotak MERAH harus pas di baris data, JANGAN kena Header.")
else:
    print("\n❌ Gak nemu baris biru yang valid. Cek 'debug_images/VISION_MASK.png'")