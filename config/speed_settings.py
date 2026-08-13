# erp-automation/config/speed_settings.py
from typing import TypedDict

class SpeedProfile(TypedDict):
    name: str
    mouse_duration: float   # Kecepatan gerak mouse (detik)
    action_delay: float     # Jeda setelah klik/ngetik
    phase_gap: float        # Jeda perpindahan Phase 1 ke 2
    audit_scroll: float     # Jeda scroll per baris di audit
    start_buffer: float     # Jeda awal pas switch window

SPEED_LEVELS = {
    '1': {
        "name": "🐢 RELAX (Default)",
        "mouse_duration": 0.5,  # Gerak santai
        "action_delay": 1.0,    # Nunggu 1 detik abis klik
        "phase_gap": 3.0,       # Napas panjang antar fase
        "audit_scroll": 0.5,    # Scroll pelan
        "start_buffer": 5.0     # Waktu siap-siap lama
    },
    '2': {
        "name": "🐇 FAST (Balanced)",
        "mouse_duration": 0.2,  # Gerak cepet
        "action_delay": 0.4,    # Sat set
        "phase_gap": 1.5,       # Napas pendek
        "audit_scroll": 0.2,    # Scroll cepet
        "start_buffer": 3.0     # Cukup buat Alt+Tab
    },
    '3': {
        "name": "⚡ EXTREME (No Limit)",
        "mouse_duration": 0.0,  # Teleport!
        "action_delay": 0.1,    # Nyaris instan (bahaya kalo PC kentang)
        "phase_gap": 0.5,       # Gak pake napas
        "audit_scroll": 0.05,   # Scroll kilat
        "start_buffer": 2.0     # Mode pro
    }
}