# erp-automation/core/executor.py
import json
import time
import sys
import pyautogui
from typing import Dict, Any, List, Optional
from config.steps_config import PHASE_1_STEPS, RESET_STEPS
from config.speed_settings import SPEED_LEVELS 
import config.state as bot_state

COORD_FILE = "coordinates.json"
pyautogui.FAILSAFE = True 
VFP_ROW_HEIGHT = 18

class Executor:
    def __init__(self, speed_profile=None):
        self.coords: Dict[str, Any] = {}
        self.spd = speed_profile if speed_profile else SPEED_LEVELS['1']
        self.load_config()

    def load_config(self):
        try:
            with open(COORD_FILE, 'r') as f:
                self.coords = json.load(f)
        except FileNotFoundError:
            print(f"❌ Error: File '{COORD_FILE}' gak ada! Kalibrasi dulu bro.")
            sys.exit(1)

    def execute_step(self, step_id: str, step_msg: str, default_val_from_code: Optional[str] = None, delay: Optional[float] = None, y_offset: int = 0):
        # [FIX] Cek Stop Request di awal setiap langkah
        if bot_state.STOP_REQUESTED:
            print("\n🛑 STOP REQUESTED (Executor).")
            raise KeyboardInterrupt("User requested stop") # [FIX] Raise Exception, jangan sys.exit

        if step_id not in self.coords:
            print(f"⚠️  SKIP: Data '{step_msg}' gak ada di JSON.")
            return

        step_data = self.coords[step_id]
        action = step_data.get('action')

        try:
            if action == 'click':
                x = step_data['x']
                y = step_data['y']
                
                # APPLY OFFSET (Khusus Logic Turun Baris / Retry)
                if y_offset > 0:
                    y += y_offset
                    # print(f"[Offset +{y_offset}px]...", end=" ") # Silent offset
                
                pyautogui.moveTo(x, y, duration=self.spd['mouse_duration']) 
                pyautogui.click()
                # print(f"✅ Typed '{final_val}'") # Silent type

            elif action == 'type':
                # [FIX] Strict Type Handling for Pylance
                val_from_json: Optional[str] = step_data.get('value')
                
                # Prioritas: JSON > Code Default > Empty String (Safety)
                final_val: str = ""
                
                if val_from_json is not None:
                    final_val = str(val_from_json)
                elif default_val_from_code is not None:
                    final_val = str(default_val_from_code)
                
                if final_val:
                    pyautogui.write(final_val, interval=0.1)
                    print(f"✅ Typed '{final_val}'")
                else:
                    pass

                        # --- LOGIKA CUSTOM DELAY BARU ---
            custom_delay = step_data.get('custom_delay')
            if custom_delay is not None:
                final_delay = custom_delay
            elif delay is not None:
                final_delay = delay
            else:
                final_delay = self.spd['action_delay']
            time.sleep(final_delay)

        except Exception as e:
            print(f"\n❌ Error: {e}")
            raise e # Lempar error ke atas biar ditangkap main loop

    def run_reset_sequence(self):
        print("\n🧹 JALANIN RITUAL RESET (Cuci Piring)...")
        for step in RESET_STEPS:
            self.execute_step(step['id'], step['msg'], delay=0.8)
        print("✅ Reset Selesai. Form bersih.")

    def run_phase_1(self, retry_idx: int = 0, skip_customer_selection: bool = False, initial_wait: bool = True):
        print(f"\n🤖 STARTING AUTOMATION (PHASE 1) - Attempt #{retry_idx + 1}")
        print("==================================")
        
        if retry_idx == 0 and initial_wait:
            wait_time = self.spd['start_buffer']
            print("⚠️  GESER MOUSE KE POJOK KIRI-ATAS UNTUK STOP!")
            print(f"   Mulai dalam {wait_time} detik...")
            time.sleep(wait_time)
        
        print("🚀 GO!")

        for step_schema in PHASE_1_STEPS:
            s_id = step_schema['id']
            s_msg = step_schema['msg']
            s_val_default: Optional[str] = step_schema.get('value') 

            if skip_customer_selection and s_id in ["1_cust_dropdown_open", "2_cust_input_val", "3_cust_dropdown_close"]:
                continue
            
            dynamic_row_height = self.coords.get('GLOBAL_ROW_HEIGHT', 18)
            current_offset = 0
            if s_id in ["5_checkbox_add_so"] and retry_idx > 0:
                current_offset = retry_idx * dynamic_row_height  # 18px per row
            
            self.execute_step(s_id, s_msg, default_val_from_code=s_val_default, delay=None, y_offset=current_offset)
        
        print("\n✅ PHASE 1 SELESAI.")
        return True