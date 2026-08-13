# erp-automation/config/steps_config.py
from typing import List, TypedDict, Literal, Optional
try:
    from typing import NotRequired # Python 3.11
except ImportError:
    from typing_extensions import NotRequired # Fallback untuk Python lama

# --- TYPE DEFINITIONS (Strict Mode) ---
class StepConfig(TypedDict):
    id: str
    action: Literal['click', 'type']  # Restrict to only these values
    msg: str
    value: Optional[str] # Only needed if action is 'type'
    custom_delay: NotRequired[Optional[float]]

# --- DATA SOURCE ---
PHASE_1_STEPS: List[StepConfig] = [
    # --- BLOCK 1: CUSTOMER SELECTION ---
    {
        "id": "1_cust_dropdown_open",
        "action": "click",
        "msg": "Tentukan Kordinat Field Dropdown Costumer (Single Left Click)",
        "value": None
    },
    {
        "id": "2_cust_input_val",
        "action": "type",
        "value": "b", 
        "msg": "Tentukan Huruf Awal Costumer"
    },
    {
        "id": "3_cust_dropdown_close",
        "action": "click",
        "msg": "Tentukan Kordinat Sembarang Untuk Menutup Dropdown List Costumer (Single Left Click)",
        "value": None
    },

    # --- BLOCK 2: SO / TRANSACTION PROCESSING ---
    {
        "id": "4_btn_add_customer",
        "action": "click",
        "msg": "Tentukan Kordinat Tombol Add Costumer (Single Left Click)",
        "value": None
    },
    {
        "id": "5_checkbox_add_so",
        "action": "click",
        "msg": "Tentukan Kordinat Checkbox Add SO (Single Left Click)",
        "value": None
    },
    {
        "id": "6_checklist_confirm_so",
        "action": "click",
        "msg": "Tentukan Kordinat Checklist SO (Single Left Click)",
        "value": None
    },

    # --- BLOCK 3: PAYMENT & DATING ---
    {
        "id": "7_pay_dropdown_open",
        "action": "click",
        "msg": "Tentukan kordinat Field Dropdown Pembayaran Ditunjukan (Single Left Click)",
        "value": None
    },
    {
        "id": "8_pay_input_val",
        "action": "type",
        "value": "b", 
        "msg": "Tentukan Huruf Awal Pembayaran"
    },
    {
        "id": "9_pay_dropdown_close",
        "action": "click",
        "msg": "Tentukan Kordinat Sembarang Untuk Menutup Dropdown List Pembayaran (Single Left Click)",
        "value": None
    },
    {
        "id": "10_date_field",
        "action": "click",
        "msg": "Tentukan Kordinat Field Tanggal (Single Left Click)",
        "value": None
    },
    {
        "id": "11_item_row",
        "action": "click",
        "msg": "Tentukan Kordinat Field Item Barang (Single Left Click)",
        "value": None
    }
    ]

# --- BLOCK 4: RESET RITUAL (ERROR RECOVERY) ---
RESET_STEPS: List[StepConfig] = [
    {
        "id": "reset_click_surat_jalan",
        "action": "click",
        "msg": "Tentukan Kordinat Field 'Surat Jalan' (Untuk Reset Posisi jika Audit Gagal)",
        "value": None
    },
    {
        "id": "reset_click_clear",
        "action": "click",
        "msg": "Tentukan Kordinat Tombol 'Clear' / 'Bersihkan' (Untuk Reset Form)",
        "value": None
    }
]