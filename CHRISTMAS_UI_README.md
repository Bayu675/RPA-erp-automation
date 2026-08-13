# 🎄 CHRISTMAS UI UPDATE - Installation Guide

## 🎁 What's New?

Your ERP Automation Suite now has a **Christmas-themed Rich UI**!

Features:
- 🎅 Christmas decorations (snow, santa, trees)
- 📊 Beautiful tables and panels
- 🎨 Color-coded status (green=success, red=error, yellow=warning)
- 📈 Better visual hierarchy
- 🎯 Easier to read logs and summaries

## 📦 Installation

### Step 1: Install Rich Library

```bash
cd /home/ryu/Desktop/TOOLS/erp-automation/erp-automation
pip install rich
```

Or install all requirements:
```bash
pip install -r requirement
```

### Step 2: Run the Program

```bash
python main.py
```

## ✨ What You'll See

### Main Menu (Before vs After)

**BEFORE:**
```
================================================
      🤖 ERP AUTOMATION SUITE V9.2 (ULTIMATE)   
------------------------------------------------
   SPEED MODE: 🐇 FAST (Balanced)
          Created By Bayu A.K.A Ryu             
================================================

MENU UTAMA:
   [1] 🚀 START FULL TRANSACTION
   [2] 🛡️ START AUDIT ONLY
   ...
```

**AFTER (Christmas Theme!):**
```
╔═══════════════════════════════════════════════════════════════════╗
║  ❄ ❅ ❆ ✻ ✼ ❊ ❄ ❅ ❆ ✻ ✼ ❊ ❄ ❅ ❆ ✻ ✼ ❊ ❄ ❅                    ║
║                                                                   ║
║  🎅  ERP AUTOMATION SUITE V9.3 (ULTIMATE)  🎄                   ║
║  Created By Bayu A.K.A Ryu - Merry Christmas! 🎅                ║
║  ⚡ Speed Mode: 🐇 FAST (Balanced)                              ║
║                                                                   ║
║  ❄ ❅ ❆ ✻ ✼ ❊ ❄ ❅ ❆ ✻ ✼ ❊ ❄ ❅ ❆ ✻ ✼ ❊ ❄ ❅                    ║
╚═══════════════════════════════════════════════════════════════════╝

╭─ 🎁 MENU UTAMA ────────────────────────────────────────────────╮
│   [1] 🚀 START FULL TRANSACTION (Input -> Audit -> Save)       │
│   [2] 🛡️ START AUDIT ONLY (Cek Validasi & Save)               │
│   ------------------------------------------------              │
│   INFO: Tekan [F9] saat bot jalan untuk STOP                   │
│   [3] 🔧 KALIBRASI (Setting Koordinat)                         │
│   ...                                                           │
╰─────────────────────────────────────────────────────────────────╯
```

### Price Mismatch Alert (New!)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                🚨 PRICE MISMATCH: ROLLER BLIND 2.0           ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┌──────────────────────────┬──────────────┬──────────┐
│ Source                   │        Price │  Status  │
├──────────────────────────┼──────────────┼──────────┤
│ 💾 Database (Expected)   │  Rp 350,000  │    ✅    │
│ 🖥️  Screen (Detected)    │  Rp 380,000  │    ❌    │
│ ⚖️  Difference            │   Rp 30,000  │ Over 5%  │
│                          │      (8.6%)  │          │
└──────────────────────────┴──────────────┴──────────┘

👉 Action: Update database atau perbaiki harga di ERP.
```

### Transaction Summary (New!)

```
╭───────────────────────────────────────────────────────────────╮
│               🧾 TRANSACTION SUMMARY                          │
├───────────────────────────────────────────────────────────────┤
│ 📦 Items Processed          11                                │
│ 💵 Gross Total              Rp 5,230,000                      │
│ 💰 Netto Total              Rp 3,450,000                      │
│                                                               │
│ 🤖 Bot Calculated           Rp 3,638,025                      │
│ 🖥️  Screen Display          Rp 3,638,000                      │
│ ⚖️  Difference               Rp 25 (0.0007%)                  │
│                                                               │
│ 🎯 Status                   ✅ VALID - TRANSACTION SAVED      │
╰───────────────────────────────────────────────────────────────╯
```

## 🔄 Fallback Mode

If `rich` library is not installed, the program will automatically fallback to **plain terminal mode** (your current UI). No errors, no crashes!

You'll see this message:
```
⚠️  Rich library not installed. Using plain terminal.
   Install: pip install rich
```

## ⚙️ Customization

Want to disable Christmas theme? Edit `core/ui_helper.py`:

```python
# Line 35:
def _check_christmas_season(self):
    # Change to always False:
    return False  # Disable Christmas theme
```

## 🎅 Enjoy!

Merry Christmas & Happy Automating! 🎄

---
Created by Bayu A.K.A Ryu - 2025
