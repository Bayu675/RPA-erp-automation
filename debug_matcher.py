import json
from rapidfuzz import process, fuzz

def normalize(text):
    # Logic sama persis dengan auditor.py (Updated)
    text = text.upper()
    text = text.replace('8', 'B').replace('0', 'O')
    text = text.replace('(', 'C').replace('[', 'I').replace('|', 'I')
    return "".join(e for e in text if e.isalnum())

def debug():
    print("🕵️‍♂️ DEBUGGER PENCARI JODOH (STRING MATCHER - V2)")
    print("==========================================")
    
    try:
        with open('master_data.json', 'r') as f:
            data = json.load(f)
            items = list(data.get('items', {}).keys())
            print(f"✅ Database dimuat: {len(items)} items.")
    except Exception as e:
        print(f"❌ Gagal baca database: {e}")
        return

    while True:
        ocr_input = input("\n👉 Paste Teks OCR dari Terminal (atau 'q' keluar): ").strip()
        if ocr_input.lower() == 'q': break
        
        print(f"\n🔍 Menganalisa: '{ocr_input}'")
        
        # 1. Cek Exact Match
        if ocr_input in items:
            print("   ✅ EXACT MATCH DITEMUKAN! (Harusnya aman)")
            continue
            
        # 2. Cek Normalized
        norm_input = normalize(ocr_input)
        print(f"   🛠️  Normalized Input: '{norm_input}'")
        
        found_norm = False
        for db_item in items:
            norm_db = normalize(db_item)
            if norm_input == norm_db:
                print(f"   ✅ NORMALIZED MATCH DITEMUKAN!")
                print(f"      Asli Database: '{db_item}'")
                print(f"      Norm Database: '{norm_db}'")
                found_norm = True
                break
        
        if not found_norm:
            print("   ❌ GAGAL MATCHING NORMAL.")
            
            # 3. Cari Kandidat Terdekat (Difflib)
            print("   🔎 Mencari kembaran terdekat...")
            matches = process.extract(ocr_input, items, scorer=fuzz.WRatio, limit=3, score_cutoff=40.0)
            
            if matches:
                best = matches[0][0]
                print(f"      Did you mean: '{best}'?")
                
                # Compare Char by Char
                print("\n      ⚔️  PERBANDINGAN KARAKTER:")
                print(f"      OCR: {ocr_input}")
                print(f"      DB : {best}")
                
                # Show Diff
                norm_best = normalize(best)
                print(f"      Norm OCR: {norm_input}")
                print(f"      Norm DB : {norm_best}")
                
                if norm_input != norm_best:
                    print("      ⚠️  BEDA DI NORMALIZED STRING!")
            else:
                print("      ⚠️  Tidak ada item yang mirip sama sekali. Cek Database!")

if __name__ == "__main__":
    debug()