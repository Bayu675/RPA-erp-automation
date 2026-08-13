# debug_exact_match.py
import json

def string_to_hex(s):
    return " ".join("{:02x}".format(ord(c)) for c in s)

def debug():
    print("🕵️‍♂️ DEBUGGER EXACT MATCH (HEX LEVEL)")
    print("=====================================")
    
    # 1. LOAD JSON
    try:
        with open('master_data.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Handle struktur items atau root
            items = data.get('items', data) 
            keys = list(items.keys())
            print(f"✅ Database Loaded: {len(keys)} items")
    except Exception as e:
        print(f"❌ Gagal load JSON: {e}")
        return

    # 2. INPUT STRING YANG ANDA COPY DARI CONSOLE
    print("\n👉 Paste String Produk 'A' (yang tadi gagal) di bawah ini:")
    target_input = input("INPUT: ").strip() # Kita strip manual buat test
    
    print(f"\n🔍 Menganalisa: '{target_input}'")
    print(f"   HEX Input : {string_to_hex(target_input)}")

    # 3. CARI DI DATABASE (MANUAL LOOP)
    found_visual = False
    
    for db_key in keys:
        # Cek apakah secara visual sama (case insensitive)
        if db_key.upper() == target_input.upper():
            found_visual = True
            print(f"\n⚠️  DITEMUKAN SECARA VISUAL TAPI GAGAL DI CODE!")
            print(f"   DB Key (Asli) : '{db_key}'")
            print(f"   HEX DB Key    : {string_to_hex(db_key)}")
            
            # Analisa Perbedaan
            if db_key != target_input:
                print("\n   ❌ PENYEBAB: Perbedaan Case/Spasi/Karakter!")
                if len(db_key) != len(target_input):
                    print(f"      Panjang String Beda! (Input: {len(target_input)} vs DB: {len(db_key)})")
                
                # Cek Spasi
                if "  " in db_key and "  " not in target_input:
                    print("      👉 DB punya SPASI GANDA, Input cuma satu!")
                elif "  " in target_input and "  " not in db_key:
                    print("      👉 Input punya SPASI GANDA, DB cuma satu!")
            else:
                print("\n   ✅ ANEH! String sama persis 100%. Cek struktur JSON ['items'].")
            break
            
    if not found_visual:
        print("\n❌ TIDAK DITEMUKAN SAMA SEKALI DI DATABASE.")
        print("   Coba cek apakah ada typo atau karakter aneh.")

if __name__ == "__main__":
    debug()