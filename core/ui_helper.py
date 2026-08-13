import os
import sys
import time
import datetime
import threading
from math import ceil
from typing import Any, Optional 

# [FIX] Type Hinting biar Pylance gak bingung
pygame: Any = None 
HAS_AUDIO = False

try:
    import pygame  # type: ignore
    HAS_AUDIO = True
except ImportError:
    print("\n⚠️  WARNING: Library 'pygame' belum diinstall di PC ini! Audio dimatikan.")
    print("👉  Silakan buka terminal baru dan ketik: pip install pygame\n")
    time.sleep(2)
    HAS_AUDIO = False

class ThemeManager:
    def __init__(self):
        self.current_theme = self._detect_theme()
        self.music_thread = None
        self.stop_music_flag = False

    def _detect_theme(self):
        today = datetime.date.today()
        year = today.year
        
        # 1. IMLEK (Cth: 2025 Imlek tgl 29 Jan. Range: H-7 s/d H+7)
        if datetime.date(year, 1, 22) <= today <= datetime.date(year, 2, 5):
            return "IMLEK"
        
        # 2. RAMADHAN (Cth: 2025 Puasa mulai 1 Mar. Range: Sebulan)
        if datetime.date(year, 2, 18) <= today <= datetime.date(year, 3, 19):
            return "RAMADHAN"
            
        # 3. 17 AGUSTUS (Range: 1 - 31 Agustus)
        if today.month == 8:
            return "MERDEKA"
            
        # 4. HALLOWEEN (Range: 25 - 31 Oktober)
        if today.month == 10 and today.day >= 25:
            return "HALLOWEEN"
            
        # 5. NATAL & TAHUN BARU (Desember Full - Awal Jan)
        if today.month == 12 or (today.month == 1 and today.day <= 7):
            return "CHRISTMAS"
            
        return "DEFAULT"

    def get_header_art(self):
        """Return ASCII Art Keren sesuai tema"""
        if self.current_theme == "IMLEK":
            return [
                "🧧  GONG XI FA CAI  🧧",
                "🐉  YEAR OF SNAKE   🐉",
                "   (Bot Mode: Hoki)   "
            ]
        elif self.current_theme == "RAMADHAN":
            return [
                "🕌  MARHABAN YA RAMADHAN  🕌",
                "✨  SELAMAT MENUNAIKAN IBADAH PUASA  ✨",
                "       (Bot Mode: Berkah)       "
            ]
        elif self.current_theme == "MERDEKA":
            return [
                "🇮🇩  DIRGAHAYU INDONESIA  🇮🇩",
                "🦅  MERDEKA ATAU MATI!   🦅",
                "   (Bot Mode: Pejuang)    "
            ]
        elif self.current_theme == "HALLOWEEN":
            return [
                "🎃  TRICK OR TREAT  🎃",
                "👻  SPOOKY SEASON   👻",
                "  (Bot Mode: Horror)  "
            ]
        elif self.current_theme == "CHRISTMAS":
            return [
                "❄️ ❅ ❆ ✻ ✼ ❊ ❄️ ❅ ❆ ✻ ✼ ❊",
                "🎅  MERRY CHRISTMAS  🎄",
                "   (Bot Mode: Santa)   "
            ]
        else:
            # STANDARD MODE (Professional Look)
            return [
                "╔══════════════════════════════════════════════════════════╗",
                "║           🤖 ERP AUTOMATION SUITE V9.3 (ULTIMATE)        ║",
                "║           🚀 Created By Bayu A.K.A Ryu - 2025            ║",
                "╚══════════════════════════════════════════════════════════╝"
            ]

    def play_music(self):
        """Jalankan musik di background thread"""
        if not HAS_AUDIO or pygame is None: return
        
        self.stop_music_flag = False
        if self.music_thread and self.music_thread.is_alive():
            return
        
        # [FIX] Dapatkan absolute path ke folder aset biar bisa di-run dari mana aja
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        
        def _music_loop():
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
                
                music_files = {
                    "IMLEK": os.path.join(base_dir, "assets", "music", "imlek.mp3"),
                    "RAMADHAN": os.path.join(base_dir, "assets", "music", "ramadhan.mp3"),
                    "MERDEKA": os.path.join(base_dir, "assets", "music", "merdeka.mp3"),
                    "HALLOWEEN": os.path.join(base_dir, "assets", "music", "halloween.mp3"),
                    "CHRISTMAS": os.path.join(base_dir, "assets", "music", "christmas.mp3"),
                    "DEFAULT": os.path.join(base_dir, "assets", "music", "default.mp3")
                }
                
                target_file = music_files.get(self.current_theme, music_files["DEFAULT"])
                
                if not os.path.exists(target_file):
                    target_file = music_files["DEFAULT"]
                
                if os.path.exists(target_file):
                    pygame.mixer.music.load(target_file)
                    pygame.mixer.music.play(-1)
                    
                    while not self.stop_music_flag:
                        time.sleep(1)
                    
                    pygame.mixer.music.stop()
                else:
                    print(f"ℹ️  Lagu tidak ditemukan: {target_file} (Silent Mode)")
                    
            except Exception as e:
                print(f"⚠️ Audio Error: {e}")

        self.music_thread = threading.Thread(target=_music_loop, daemon=True)
        self.music_thread.start()

    def stop_music(self):
        self.stop_music_flag = True

class UIHelper:
    def __init__(self):
        self.theme = ThemeManager()
        self.width = 64 

        global HAS_AUDIO
        if HAS_AUDIO and pygame is not None:
            try:
                if not pygame.mixer.get_init():
                    pygame.mixer.init()
            except Exception as e:
                print(f"\n⚠️  WARNING: Gagal menyalakan Audio Device! (Speaker belum dicolok?): {e}")
                print("👉  Audio bot akan dimatikan sementara.\n")
                time.sleep(2)
                HAS_AUDIO = False

    def start_music(self):
        from core.settings_manager import settings
        if settings.get('audio', 'bgm_enabled'):
            self.theme.play_music()

    def play_sfx(self, sfx_name="alert"):
        from core.settings_manager import settings
        
        if not settings.get('audio', 'sfx_enabled'): return
        if not HAS_AUDIO or pygame is None: 
            print("\a", end="")
            return

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()

            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            sfx_path = os.path.join(base_dir, "assets", "music", f"{sfx_name}.mp3")
            
            if os.path.exists(sfx_path):
                sound = pygame.mixer.Sound(sfx_path)
                sound.play()
            else:
                print("\a", end="")
        except Exception as e: 
            print(f"   ⚠️ [Debug] Gagal play SFX: {e}")

    def _truncate(self, text, max_len):
        text = str(text)
        if len(text) > max_len:
            return text[:max_len-3] + "..."
        return text

    def _center(self, text, width):
        if len(text) >= width: return text[:width]
        pad = (width - len(text)) // 2
        return " " * pad + text + " " * (width - len(text) - pad)

    def print_banner(self, title, subtitle="", speed_mode=""):
        art = self.theme.get_header_art()
        
        if self.theme.current_theme == "DEFAULT":
            print("\n")
            for line in art:
                print(self._center(line, self.width))
            if speed_mode:
                print(self._center(f"⚡ Speed Mode: {speed_mode}", self.width))
            return

        print("\n" + "╔" + "═" * (self.width - 2) + "╗")
        
        for line in art:
            print(f"║{self._center(line, self.width - 2)}║")
            
        print("╠" + "═" * (self.width - 2) + "╣")
        print(f"║{self._center(title, self.width - 2)}║")
        if subtitle:
            print(f"║{self._center(subtitle, self.width - 2)}║")
        if speed_mode:
            print(f"║{self._center(f'⚡ Speed: {speed_mode}', self.width - 2)}║")
        print("╚" + "═" * (self.width - 2) + "╝")

    def print_row_card(self, idx, name, line_no, qty, m2, price, discs, total_row, master_data, type_str):
        s_name = self._truncate(name, 58)
        s_qty = f"{qty:.2f}"
        s_m2 = f"{m2:.2f}"
        s_price = f"Rp {price:,.0f}"
        d_str = " + ".join([f"{d:.0f}%" for d in discs if d > 0]) or "0%"
        s_disc = self._truncate(d_str, 25)
        
        if master_data:
            s_status = "✅ TERDAFTAR"
            s_ref_price = f"Rp {master_data['base_price']:,.0f}"
        else:
            s_status = "⚠️ UNKNOWN"
            s_ref_price = "-"

        print("\n" + "┌" + "─" * (self.width - 2) + "┐")
        header = f"🔍 ROW #{idx} | LINE: {line_no}"
        print(f"│ {header:<{self.width - 4}} │")
        print("├" + "─" * (self.width - 2) + "┤")
        print(f"│ 📦 {s_name:<{self.width - 6}} │")
        print("├" + "─"*30 + "┬" + "─"*31 + "┤")
        print(f"│ Qty   : {s_qty:<20} │ Status   : {s_status:<18} │")
        print(f"│ M2    : {s_m2:<20} │ Ref Harga: {s_ref_price:<18} │")
        print(f"│ Harga : {s_price:<20} │ Disc     : {s_disc:<18} │")
        print("├" + "─" * (self.width - 2) + "┤")
        s_total = f"Rp {total_row:,.0f} ({type_str})"
        print(f"│ 💰 NETTO : {s_total:<{self.width - 13}} │")
        print("└" + "─" * (self.width - 2) + "┘")

    def print_price_mismatch(self, item_name, db_price, screen_price, diff, tolerance):
        self.play_sfx("alert")
        print("\n" + "┏" + "━" * (self.width - 2) + "┓")
        print(f"┃ 🚨 PRICE MISMATCH DETECTED! {' '*(self.width-30)} ┃")
        print("┣" + "━" * (self.width - 2) + "┫")
        s_name = self._truncate(item_name, self.width - 6)
        print(f"┃ {s_name:<{self.width - 4}} ┃")
        print("┣" + "━" * (self.width - 2) + "┫")
        print(f"┃ 💾 Database : Rp {db_price:,.0f}".ljust(self.width - 2) + "┃")
        print(f"┃ 🖥️  Screen   : Rp {screen_price:,.0f}".ljust(self.width - 2) + "┃")
        diff_pct = (diff / db_price * 100) if db_price > 0 else 0
        print(f"┃ ⚖️  Diff     : Rp {diff:,.0f} ({diff_pct:.1f}%)".ljust(self.width - 2) + "┃")
        print("┗" + "━" * (self.width - 2) + "┛")

    def print_audit_summary(self, items_count, gross_total, netto_total, bot_total, screen_total, diff, is_valid):
        print("\n" + "╭" + "─" * (self.width - 2) + "╮")
        print(f"│ 🧾 TRANSACTION SUMMARY {' '*(self.width-26)} │")
        print("├" + "─" * (self.width - 2) + "┤")
        print(f"│ 📦 Items    : {items_count:<48} │")
        print(f"│ 💵 Gross    : Rp {gross_total:,.0f}".ljust(self.width - 2) + "│")
        print(f"│ 💰 Netto    : Rp {netto_total:,.0f}".ljust(self.width - 2) + "│")
        print("│" + " " * (self.width - 2) + "│")
        print(f"│ 🤖 Bot Calc : Rp {bot_total:,.0f}".ljust(self.width - 2) + "│")
        print(f"│ 🖥️  Screen   : Rp {screen_total:,.0f}".ljust(self.width - 2) + "│")
        diff_pct = (diff / screen_total * 100) if screen_total > 0 else 0
        print(f"│ ⚖️  Diff     : Rp {diff:,.0f} ({diff_pct:.4f}%)".ljust(self.width - 2) + "│")
        print("├" + "─" * (self.width - 2) + "┤")
        status = "✅ VALID - MATCHED" if is_valid else "❌ INVALID - REJECTED"
        print(f"│ 🎯 STATUS   : {status:<{self.width - 16}} │")
        print("╰" + "─" * (self.width - 2) + "╯")

    def print_menu(self, options):
        print("\n" + "╭" + "─" * (self.width - 2) + "╮")
        print(f"│ 🎁 MENU UTAMA {' '*(self.width-17)} │")
        print("├" + "─" * (self.width - 2) + "┤")
        for opt in options:
            s_opt = self._truncate(opt, self.width - 6)
            print(f"│ {s_opt:<{self.width - 4}} │")
        print("╰" + "─" * (self.width - 2) + "╯")

    def print_success(self, msg):
        print(f"✅ {msg}")

    def print_error(self, msg):
        print(f"❌ {msg}")

# Instance Global
ui = UIHelper()