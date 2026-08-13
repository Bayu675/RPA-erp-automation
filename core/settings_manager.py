import json
import os

SETTINGS_FILE = "config/user_settings.json"

DEFAULT_SETTINGS = {
    "timeout_mismatch": {"enabled": True, "seconds": 10},
    "timeout_unknown": {"enabled": True, "seconds": 5},
    "audio": {
        "bgm_enabled": True,
        "sfx_enabled": True
    },
    "fuzzy_threshold": 0.9,
    "max_strikes": 3
}

class SettingsManager:
    def __init__(self):
        self.settings = self.load_settings()

    def load_settings(self):
        if not os.path.exists(SETTINGS_FILE):
            self.save_settings(DEFAULT_SETTINGS)
            return DEFAULT_SETTINGS
        try:
            with open(SETTINGS_FILE, 'r') as f:
                return json.load(f)
        except:
            return DEFAULT_SETTINGS

    def save_settings(self, data=None):
        if data: self.settings = data
        # Ensure directory exists
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def get(self, key, subkey=None):
        if subkey:
            return self.settings.get(key, {}).get(subkey)
        return self.settings.get(key)

    def set(self, key, value, subkey=None):
        if subkey:
            self.settings[key][subkey] = value
        else:
            self.settings[key] = value
        self.save_settings()

    def run_menu(self):
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("⚙️  PENGATURAN (SETTINGS)")
            print("========================")
            
            # 1. Mismatch Timeout
            mm = self.settings['timeout_mismatch']
            mm_str = f"{mm['seconds']}s" if mm['enabled'] else "OFF (Infinite)"
            print(f"[1] Timeout Mismatch : {mm_str}")
            
            # 2. Unknown Timeout
            un = self.settings['timeout_unknown']
            un_str = f"{un['seconds']}s" if un['enabled'] else "OFF (Infinite)"
            print(f"[2] Timeout Unknown  : {un_str}")
            
            # 3. Audio
            au = self.settings['audio']
            bgm = "ON" if au['bgm_enabled'] else "OFF"
            sfx = "ON" if au['sfx_enabled'] else "OFF"
            print(f"[3] Background Music : {bgm}")
            print(f"[4] SFX Alert        : {sfx}")

            # 5. Fuzzy Threshold
            fz = self.settings.get('fuzzy_threshold', 0.9)
            print(f"[5] Fuzzy Threshold  : {fz}")

            # --- [NEW] Tampilan Menu Max Strike ---
            ms = self.settings.get('max_strikes', 3)
            ms_str = "∞ (INFINITE)" if ms == 0 else f"{ms} Kali"
            print(f"[6] Max Strike Batch : {ms_str}")
            
            print("-" * 25)
            print("[0] KEMBALI")
            
            choice = input("\n👉 Ubah Setting [0-6]: ").strip()
            
            if choice == '0': break
            
            elif choice == '1':
                self._toggle_timeout('timeout_mismatch', "Mismatch")
            elif choice == '2':
                self._toggle_timeout('timeout_unknown', "Unknown Item")
            elif choice == '3':
                curr = self.get('audio', 'bgm_enabled')
                new_val = not curr
                self.set('audio', new_val, 'bgm_enabled')
                # Langsung efektif tanpa restart
                from core.ui_helper import ui
                if new_val:
                    ui.start_music()
                    print("   🎵 Background music DINYALAKAN.")
                else:
                    ui.theme.stop_music()
                    print("   🔇 Background music DIMATIKAN.")
                input("   Tekan Enter...")
            elif choice == '4':
                curr = self.get('audio', 'sfx_enabled')
                self.set('audio', not curr, 'sfx_enabled')
            elif choice == '5':
                self._set_fuzzy_threshold()
            elif choice == '6':
                self._set_max_strikes()

    def _toggle_timeout(self, key, label):
        curr = self.settings[key]
        print(f"\n🔧 Setting {label}")
        print(f"   Status saat ini: {'ON' if curr['enabled'] else 'OFF'}")
        print("   [1] ON (Set Waktu)")
        print("   [2] OFF (Tunggu Selamanya)")
        print("   [b] Batal")
        
        ch = input("   Pilih: ").strip()
        if ch.lower() == 'b': return
        if ch == '1':
            try:
                sec = int(input("   ⏱️  Durasi (detik): ").strip())
                self.settings[key] = {"enabled": True, "seconds": sec}
            except: print("   ❌ Input error!")
        elif ch == '2':
            self.settings[key]['enabled'] = False
        
        self.save_settings()

    def _set_fuzzy_threshold(self):
        curr = self.settings.get('fuzzy_threshold', 0.9)
        print(f"\n🔧 Fuzzy Threshold (Kemiripan Nama Item)")
        print(f"   Nilai saat ini: {curr}")
        print("   Range: 0.1 (longgar) - 1.0 (harus persis)")
        print("   Rekomendasi: 0.8 - 0.9")
        raw_val = input("   Masukkan nilai baru (atau 'b' batal): ").strip()
        if raw_val.lower() == 'b': return
        try:
            val = float(raw_val)
            if 0.1 <= val <= 1.0:
                self.settings['fuzzy_threshold'] = round(val, 2)
                self.save_settings()
                print(f"   ✅ Fuzzy threshold diset ke {val}")
            else:
                print("   ❌ Nilai harus antara 0.1 dan 1.0")
        except ValueError:
            print("   ❌ Input tidak valid!")
        input("   Tekan Enter...")
    def _set_max_strikes(self):
        curr = self.settings.get('max_strikes', 3)
        print(f"\n🔧 Max Strike Batch Mode")
        print(f"   Nilai saat ini: {'∞ (INFINITE)' if curr == 0 else curr}")
        print("   👉 Ketik angka (contoh: 3, 5, 10)")
        print("   👉 Ketik '00' untuk INFINITE (Tanpa batas strike)")
        
        val = input("   Masukkan nilai baru (atau 'b' batal): ").strip()
        if val.lower() == 'b': return
        
        if val == '00':
            self.settings['max_strikes'] = 0
            self.save_settings()
            print("   ✅ Max Strike diset ke INFINITE (00)")
        else:
            try:
                num = int(val)
                if num > 0:
                    self.settings['max_strikes'] = num
                    self.save_settings()
                    print(f"   ✅ Max Strike diset ke {num}")
                else:
                    print("   ❌ Harus lebih dari 0, atau ketik '00' untuk infinite.")
            except ValueError:
                print("   ❌ Input harus berupa angka!")
        input("   Tekan Enter...")

# Global Instance
settings = SettingsManager()