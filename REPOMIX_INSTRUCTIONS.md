# Catatan Proyek untuk AI / LLM

Beberapa file berikut **sengaja dikecualikan** dari bundle Repomix untuk menghemat penggunaan token dan menjaga konteks tetap fokus pada *core logic*:

**1. File Data & Output:**
- `master_data.json` (Daftar master item, harga dasar, diskon bawaan, rules, dll.)
- `stores.json` (Daftar toko/store untuk batch mode)
- `coordinates.json` & `coordinates_phase2.json` (Koordinat UI/klik untuk otomatisasi)
- `audit_rejects.xlsx` / `*.csv` (File Excel/CSV output log audit)

**2. File Debugging & Setup:**
- `debug_*.py` (Script testing sementara untuk vision, matcher, dll.)
- `setup_win_auto.bat` (Installer environment)

> **Catatan Penting:**
> File-file di atas ada di dalam repositori lokal. Jika kamu (LLM) memerlukan struktur skema/contoh isi dari file JSON tersebut untuk memahami logika pemrosesan data di script Python, beri tahu saya agar saya sediakan file `.example.json` atau cuplikan kodenya.