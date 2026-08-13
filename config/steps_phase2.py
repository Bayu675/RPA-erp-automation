from typing import List, TypedDict, Literal

class StepConfig(TypedDict):
    id: str
    action: Literal['click_point', 'define_column', 'define_box', 'input_text']
    msg: str

# Daftar Target Kalibrasi Phase 2 (FINAL INTEGRATION VERSION)
PHASE_2_STEPS: List[StepConfig] = [
    # --- A. PEMBATASAN AREA (KACAMATA KUDA) ---
    {
        "id": "table_area",
        "action": "define_box",
        "msg": "PENTING: Buat KOTAK AREA TABEL SAJA (Batasi area scan biar gak liat Header)"
    },
    
    # --- B. TRIGGER & ANCHOR ---
    {
        "id": "anchor_item_name",
        "action": "click_point",
        "msg": "KLIK di tengah teks 'Nama Barang' pada BARIS PERTAMA (Untuk pancingan warna biru)"
    },

    # --- C. MAPPING KOLOM TABEL (Sumbu X) ---
    # [BARU] Wajib baca nama barang buat cek Master Data (Netto/Biaya)
    {
        "id": "col_item_name",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ Nama Barang ]"
    },

    {
        "id": "col_m2",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ M2 ]"
    },
    {
        "id": "col_qty",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ Qty ]"
    },
    {
        "id": "col_price",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ @Harga ]"
    },
    
    # --- DISKON BARIS (1 s.d 4) ---
    {
        "id": "col_disc_row_1",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ Disc-1 (Baris) ]"
    },
    {
        "id": "col_disc_row_2",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ Disc-2 (Baris) ]"
    },
    {
        "id": "col_disc_row_3",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ Disc-3 (Baris) ]"
    },
    {
        "id": "col_disc_row_4",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ Disc-4 (Baris) ]"
    },
    
    # --- KOLOM DATA LAIN ---
    {
        "id": "col_amount",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ Jumlah ]"
    },
    {
        "id": "col_line_no",
        "action": "define_column",
        "msg": "Definisikan Batas Kiri & Kanan Kolom [ No. / Nomor Urut ] (Pojok Kanan)"
    },

    # --- D. MAPPING FOOTER (Kotak Tetap) ---
    {
        "id": "footer_disc_1",
        "action": "define_box",
        "msg": "Buat Kotak Area pada angka [ % Diskon Footer 1 ]"
    },
    {
        "id": "footer_disc_2",
        "action": "define_box",
        "msg": "Buat Kotak Area pada angka [ % Diskon Footer 2 ]"
    },
    {
        "id": "footer_disc_3",
        "action": "define_box",
        "msg": "Buat Kotak Area pada angka [ % Diskon Footer 3 ]"
    },
    {
        "id": "footer_disc_4",
        "action": "define_box",
        "msg": "Buat Kotak Area pada angka [ % Diskon Footer 4 ]"
    },
    
    # --- E. PPN & GRAND TOTAL ---
    { 
        "id": "footer_ppn_pct", 
        "action": "define_box", 
        "msg": "Buat Kotak Area pada angka [ % Ppn ] (Contoh: 11.00)" 
    },
    { 
        "id": "footer_grand_total", 
        "action": "define_box", 
        "msg": "Buat Kotak Area pada angka [ Netto / Grand Total ] (Target Validasi Akhir)" 
    },

    # --- F. ACTION BUTTONS (SUCCESS FLOW) ---
    {
        "id": "btn_action_1",
        "action": "click_point",
        "msg": "KLIK KOORDINAT PERTAMA setelah Match (Misal: Surat Jalan)"
    },
    # [BARU] Input Text buat Hotkey
    {
        "id": "save_hotkey",
        "action": "input_text", 
        "msg": "KETIK Tombol Shortcut untuk Save (Contoh: f3, f10, enter)"
    },
    # Tombol SAVE_KEY (F3) nanti di-handle via keyboard, gak butuh koordinat mouse
    {
        "id": "btn_action_2",
        "action": "click_point",
        "msg": "KLIK KOORDINAT TERAKHIR (Misal: Tombol Simpan/Confirm)"
    },

    # --- G. ERROR CAPTURE (AUTO REPORT) ---
    {
        "id": "error_so_box",
        "action": "define_box",
        "msg": "Buat Kotak Area pada [ NOMOR SO / SURAT JALAN ] (Untuk bukti screenshot jika REJECT)"
    },
    
    # --- H. BATCH PROCESSING (SMART SELECTOR) ---
    {
        "id": "header_customer_name_box",
        "action": "define_box",
        "msg": "Buat Kotak Area PAS di teks [ NAMA CUSTOMER TERPILIH ] (Untuk Bot Validasi Toko)"
    }
 ]
