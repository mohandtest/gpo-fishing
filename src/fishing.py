import threading
import time
import mss
import numpy as np
import win32api
import win32con
import keyboard

class FishingBot:
    def __init__(self, app):
        self.app = app
        self.recovery_in_progress = False
        self.watchdog_active = False
        self.watchdog_thread = None
        self.last_loop_heartbeat = time.time()
        self.force_stop_flag = False
        self.last_fruit_spawn_time = 0                                            
        self.fruit_spawn_cooldown = 15 * 60                                             
    
    def check_recovery_needed(self):
        """Smart recovery check - detects genuinely stuck states"""
        if not self.app.recovery_enabled or not self.app.main_loop_active or self.recovery_in_progress:
            return False
            
        current_time = time.time()
        
                                
        if current_time - self.app.last_smart_check < 20.0:
            return False
            
        self.app.last_smart_check = current_time
        
                                                          
        state_duration = current_time - self.app.state_start_time
        
                                            
        max_durations = {
            "idle": 45.0,                                   
            "fishing": 90.0,                                          
            "casting": 20.0,                          
            "menu_opening": 15.0,                          
            "typing": 10.0,                                 
            "clicking": 8.0,                           
            "purchasing": 60.0                              
        }
        
        max_duration = max_durations.get(self.app.current_state, 60.0)
        
        if state_duration > max_duration:
            self.app.log(f'🚨 State "{self.app.current_state}" stuck for {state_duration:.0f}s (max: {max_duration}s)', "error")
            return True
            
                                            
        time_since_activity = current_time - self.app.last_activity_time
        if time_since_activity > 120:                            
            self.app.log(f'⚠️ No activity for {time_since_activity:.0f}s - loop may be frozen', "error")
            return True
            
        return False
    
    def start_watchdog(self):
        """Start aggressive watchdog that monitors from OUTSIDE the main loop"""
        if self.watchdog_active:
            return
            
        self.watchdog_active = True
        self.last_loop_heartbeat = time.time()
        self.watchdog_thread = threading.Thread(target=self._watchdog_monitor, daemon=True)
        self.watchdog_thread.start()
        self.app.log('🐕 Watchdog started - monitoring for stuck states', "verbose")
    
    def stop_watchdog(self):
        """Stop the watchdog"""
        self.watchdog_active = False
        if self.watchdog_thread and self.watchdog_thread.is_alive():
            self.watchdog_thread.join(timeout=2.0)
    
    def _watchdog_monitor(self):
        """Smart watchdog that monitors for stuck states and restarts the loop"""
        while self.watchdog_active and self.app.main_loop_active:
            try:
                current_time = time.time()
                
                                                
                heartbeat_age = current_time - self.last_loop_heartbeat
                
                                                                 
                if heartbeat_age > 30.0:
                    self.app.log(f'🚨 WATCHDOG: No heartbeat for {heartbeat_age:.0f}s - Loop appears stuck', "error")
                    self._restart_fishing_loop()
                    break
                
                                        
                if self.check_recovery_needed():
                    self.app.log('🚨 WATCHDOG: Stuck state detected - Restarting loop', "error")
                    self._restart_fishing_loop()
                    break
                
                time.sleep(10.0)                          
                
            except Exception as e:
                self.app.log(f'⚠️ Watchdog error: {e}', "error")
                time.sleep(10.0)
        
        self.app.log('🐕 Watchdog stopped', "verbose")
    
    def update_heartbeat(self):
        """Update heartbeat from main loop"""
        self.last_loop_heartbeat = time.time()
    
    def _restart_fishing_loop(self):
        """Restart the fishing loop when it gets stuck"""
        if self.recovery_in_progress:
            return
            
        current_time = time.time()
        
                                
        if self.app.recovery_count >= 5:
            self.app.log(f'🛑 TOO MANY RESTARTS: {self.app.recovery_count} attempts. Stopping fishing.', "error")
            self.app.main_loop_active = False
            self.watchdog_active = False
            return
        
        self.recovery_in_progress = True
        self.app.recovery_count += 1
        self.app.last_recovery_time = current_time
        
        self.app.log(f'🔄 RESTARTING LOOP #{self.app.recovery_count}/5 - Fishing got stuck', "important")
        
                                          
        try:
            if self.app.is_clicking:
                win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                self.app.is_clicking = False
        except:
            pass
        
                                                  
        self.force_stop_flag = True
        
                     
        self.app.last_activity_time = current_time
        self.app.last_fish_time = current_time
        self.app.set_recovery_state("idle", {"action": "loop_restart"})
        
                                                
        time.sleep(2.0)
        
                                 
        self.force_stop_flag = False
        self.last_loop_heartbeat = time.time()
        
                          
        self.app.log('🎣 Starting fresh fishing loop...', "important")
        self.app.main_loop_thread = threading.Thread(target=lambda: self.run_main_loop(skip_initial_setup=True), daemon=True)
        self.app.main_loop_thread.start()
        
        self.recovery_in_progress = False

    def _force_recovery(self):
        """NUCLEAR OPTION: Force recovery when system is truly stuck"""
        if self.recovery_in_progress:
            return
            
        current_time = time.time()
        
                        
        if self.app.recovery_count >= 3:
            self.app.log(f'🛑 RECOVERY LIMIT REACHED: {self.app.recovery_count} attempts failed. STOPPING EVERYTHING.', "error")
            self.app.main_loop_active = False
            self.watchdog_active = False
            return
        
        self.recovery_in_progress = True
        self.app.recovery_count += 1
        self.app.last_recovery_time = current_time
        
        self.app.log(f'💥 FORCE RECOVERY #{self.app.recovery_count}/3 - NUKING EVERYTHING', "error")
        
                      
        if hasattr(self.app, 'webhook_manager'):
            recovery_info = {
                "recovery_number": self.app.recovery_count,
                "stuck_state": self.app.current_state,
                "timestamp": current_time,
                "recovery_type": "FORCE_RECOVERY"
            }
            self.app.webhook_manager.send_recovery(recovery_info)
        
                               
        self.force_stop_flag = True
        self.app.main_loop_active = False
        
                                   
        try:
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
            self.app.is_clicking = False
        except:
            pass
        
                         
        self.app.last_activity_time = current_time
        self.app.last_fish_time = current_time
        self.app.set_recovery_state("idle", {"action": "force_recovery_reset"})
        
                                                       
        self.app.log('💥 FORCE KILLING main loop thread...', "verbose")
        time.sleep(1.0)                                                  
        
                                                    
        try:
            if hasattr(self.app, 'main_loop_thread') and self.app.main_loop_thread and self.app.main_loop_thread.is_alive():
                self.app.main_loop_thread.join(timeout=3.0)
                if self.app.main_loop_thread.is_alive():
                    self.app.log('⚠️ Thread refused to die - continuing anyway', "error")
        except:
            pass
        
                              
        if self.app.recovery_count < 3:
            self.app.log('💥 RESTARTING FROM SCRATCH...', "important")
            
                         
            self.force_stop_flag = False
            self.last_loop_heartbeat = time.time()
            
                         
            self.app.main_loop_active = True
            self.app.main_loop_thread = threading.Thread(target=lambda: self.run_main_loop(skip_initial_setup=True), daemon=True)
            self.app.main_loop_thread.start()
            
            self.app.log('✅ FORCE RECOVERY COMPLETE - Fresh start initiated', "important")
        
        self.recovery_in_progress = False
    
    def perform_recovery(self):
        """Legacy recovery method - now just calls force recovery"""
        self._force_recovery()
    
    def cast_line(self):
        """Cast fishing line"""
                                                                
        self.move_to_fishing_position()
        
                                                       
        try:
            import win32api
            print(f"🖱️ Right-clicking at fishing position")
            current_pos = win32api.GetCursorPos()
            self.app._right_click_at(current_pos)
            time.sleep(0.3)
        except Exception as e:
            print(f"❌ Right-click failed: {e}")
        
                       
        print("Casting line...")
        self.app.cast_line()
    
    def store_fruit(self):
        """Complete fruit storage and rod switching workflow with reliable delays - stores 2 fruits"""
        fruit_storage_enabled = getattr(self.app, 'fruit_storage_enabled', False)
        print(f"🔍 Fruit storage enabled: {fruit_storage_enabled}")
        
        if not fruit_storage_enabled:
            print("⏭️ Fruit storage disabled - skipping")
            return
            
        try:
            import keyboard
            import time
            
                                                   
            fruit_key_1 = getattr(self.app, 'fruit_storage_key', '2')
            fruit_key_2 = getattr(self.app, 'fruit_storage_key_2', '3')
            rod_key = getattr(self.app, 'rod_key', '1')
            
            print(f"🍎 Starting fruit storage workflow for 2 fruits...")
            
                                                      
                                                                                             
                                                                                                                
            print(f"📷 Step 0: Resetting player camera position...")
            
                                              
            if hasattr(self.app, 'fishing_location') and self.app.fishing_location:
                fishing_x, fishing_y = self.app.fishing_location
            else:
                                               
                import win32api
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                fishing_x = screen_width // 2
                fishing_y = screen_height // 3
            
                                    
            print(f"🎣 Step 0a: Casting rod at ({fishing_x}, {fishing_y}) to reset camera...")
            self.app._click_at((fishing_x, fishing_y))
            time.sleep(1.0)                           
            
                                        
            print(f"🎣 Step 0b: Retrieving rod to complete camera reset...")
            self.app._click_at((fishing_x, fishing_y))
            time.sleep(1.0)                               
            
            print(f"✅ Camera position reset - player now facing water")
            
                                                      
                                                       
            print(f"📦 Step 1: Pressing fruit storage key 1 '{fruit_key_1}'")
            keyboard.press_and_release(fruit_key_1)
            time.sleep(0.5)                                               
            
                                                           
            if hasattr(self.app, 'fruit_coords') and 'fruit_point' in self.app.fruit_coords:
                fruit_x, fruit_y = self.app.fruit_coords['fruit_point']
                print(f"🎯 Step 2: Clicking fruit point 1 at ({fruit_x}, {fruit_y})")
                self.app._click_at((fruit_x, fruit_y))
                time.sleep(0.5)                               
            else:
                print("❌ Fruit point coordinates not configured - skipping fruit storage")
                return
            
                                                                                     
            if hasattr(self.app, 'fruit_coords') and 'fruit_point_2' in self.app.fruit_coords:
                fruit_x2, fruit_y2 = self.app.fruit_coords['fruit_point_2']
                print(f"🎯 Step 3: Clicking fruit point 2 (backup) at ({fruit_x2}, {fruit_y2})")
                self.app._click_at((fruit_x2, fruit_y2))
                time.sleep(0.5)                                          
                
                                                     
                print(f"🎯 Step 4: Clicking back at fruit point 1 at ({fruit_x}, {fruit_y})")
                self.app._click_at((fruit_x, fruit_y))
                time.sleep(0.5)                              
            else:
                print("ℹ️ Fruit point 2 not configured - skipping backup clicks")
            
                                                       
            print(f"📦 Step 5: Waiting for storage dialog...")
            time.sleep(0.8)                                           
            
                                               
            print(f"⬇️ Step 6: Pressing backspace to drop/store first fruit...")
            time.sleep(0.3)                                
            keyboard.press('backspace')
            time.sleep(0.1)                
            keyboard.release('backspace')
            time.sleep(1.2)                                               
            
                                                       
                                                        
            print(f"📦 Step 7: Pressing fruit storage key 2 '{fruit_key_2}'")
            keyboard.press_and_release(fruit_key_2)
            time.sleep(0.5)                               
            
                                                           
            print(f"🎯 Step 8: Clicking fruit point 1 at ({fruit_x}, {fruit_y})")
            self.app._click_at((fruit_x, fruit_y))
            time.sleep(0.5)                               
            
                                                          
            if hasattr(self.app, 'fruit_coords') and 'fruit_point_2' in self.app.fruit_coords:
                print(f"🎯 Step 9: Clicking fruit point 2 (backup) at ({fruit_x2}, {fruit_y2})")
                self.app._click_at((fruit_x2, fruit_y2))
                time.sleep(0.5)                                          
                
                                                      
                print(f"🎯 Step 10: Clicking back at fruit point 1 at ({fruit_x}, {fruit_y})")
                self.app._click_at((fruit_x, fruit_y))
                time.sleep(0.5)                              
            
                                              
            print(f"📦 Step 11: Waiting for storage dialog...")
            time.sleep(0.8)                                           
            
                                                       
            print(f"⬇️ Step 12: Pressing backspace to drop/store second fruit...")
            time.sleep(0.3)                                
            keyboard.press('backspace')
            time.sleep(0.1)                
            keyboard.release('backspace')
            time.sleep(1.2)                                               
            
                                       
                                    
            print(f"🎣 Step 13: Returning to rod...")
            
                                                       
            time.sleep(1.0)                                                
            
                                                                         
            print(f"🎣 Step 13: Pressing rod key '{rod_key}' once")
            keyboard.press_and_release(rod_key)
            time.sleep(0.8)                                              
            
                                                                                  
            auto_bait_enabled = getattr(self.app, 'auto_bait_enabled', False)
            if auto_bait_enabled and hasattr(self.app, 'top_bait_coords') and self.app.top_bait_coords:
                bait_x, bait_y = self.app.top_bait_coords
                print(f"🎯 Step 14a: Clicking top bait point 1 at ({bait_x}, {bait_y})")
                self.app._click_at((bait_x, bait_y))
                time.sleep(0.3)                                
                
                                                       
                if hasattr(self.app, 'top_bait_coords_2') and self.app.top_bait_coords_2:
                    bait_x2, bait_y2 = self.app.top_bait_coords_2
                    print(f"🎯 Step 14b: Clicking top bait point 2 (backup) at ({bait_x2}, {bait_y2})")
                    self.app._click_at((bait_x2, bait_y2))
                    time.sleep(0.3)                            
                    
                                               
                    print(f"🎯 Step 14c: Clicking back at bait point 1 at ({bait_x}, {bait_y})")
                    self.app._click_at((bait_x, bait_y))
                    time.sleep(0.3)               
                    
            elif not auto_bait_enabled:
                print("ℹ️ Step 14: Auto-bait disabled - skipping bait selection")
            else:
                print("❌ Top bait point not configured - skipping bait selection")
            
                                                              
            print(f"🎯 Step 15: Final preparation for next cast...")
            time.sleep(0.3)                        
            self.move_to_fishing_position()
            
            print(f"✅ Fruit storage sequence completed: Fruit Key 1 → Sequence → Fruit Key 2 → Sequence → Rod Key → Bait Point → Fishing Position")
            
        except Exception as e:
            print(f"❌ Fruit storage workflow failed: {e}")
    
    def move_to_fishing_position(self):
        """Move mouse to fishing position (custom or default center-top)"""
        try:
            import win32api
            import win32gui
            import time
            
                                                                       
            auto_mouse_enabled = getattr(self.app, 'auto_mouse_position_enabled', False)
            if auto_mouse_enabled:
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                fishing_x = screen_width // 2
                fishing_y = screen_height // 3
                print(f"🎯 Auto mouse position enabled - using default position: ({fishing_x}, {fishing_y})")
            elif hasattr(self.app, 'fishing_location') and self.app.fishing_location:
                fishing_x, fishing_y = self.app.fishing_location
                print(f"🎯 Moving mouse to custom fishing position: ({fishing_x}, {fishing_y})")
            else:
                screen_width = win32api.GetSystemMetrics(0)
                screen_height = win32api.GetSystemMetrics(1)
                fishing_x = screen_width // 2
                fishing_y = screen_height // 3
                print(f"🎯 Moving mouse to default fishing position: ({fishing_x}, {fishing_y})")
            
                                                          
            win32api.SetCursorPos((fishing_x, fishing_y))
            time.sleep(0.1)
            
        except Exception as e:
            print(f"❌ Failed to move to fishing position: {e}")
    
    def check_and_purchase(self):
        """Check if auto-purchase is needed"""
        if getattr(self.app, 'auto_purchase_var', None) and self.app.auto_purchase_var.get():
            self.app.purchase_counter += 1
            loops_needed = int(getattr(self.app, 'loops_per_purchase', 1)) if getattr(self.app, 'loops_per_purchase', None) is not None else 1
            print(f'🛒 Purchase counter: {self.app.purchase_counter}/{loops_needed}')
            if self.app.purchase_counter >= max(1, loops_needed):
                try:
                    print('🛒 Performing auto-purchase...')
                    self.perform_auto_purchase()
                    self.app.purchase_counter = 0
                    print('🛒 Auto-purchase complete')
                except Exception as e:
                    print(f'❌ AUTO-PURCHASE ERROR: {e}')
                                                                     
                    self.app.purchase_counter = 0
                                         
                    self.app.set_recovery_state("idle", {"action": "purchase_error_recovery"})
    
    def perform_auto_purchase(self):
        """Perform auto-purchase sequence"""
        pts = self.app.point_coords
        
                                                               
        for key in [1, 2, 3]:
            if key in pts and pts[key] and isinstance(pts[key], list):
                pts[key] = tuple(pts[key])
        
        if not pts or not pts.get(1) or not pts.get(2) or not pts.get(3):
            print("❌ Auto-purchase failed: Missing point coordinates (need points 1-3)")
            return
        
        if not self.app.main_loop_active:
            return
        
        print(f"🛒 Starting auto-purchase sequence for {self.app.auto_purchase_amount} items...")
        
        amount = str(self.app.auto_purchase_amount)
        
                                               
        self.app.set_recovery_state("menu_opening", {"action": "pressing_e_key"})
        keyboard.press('e')
        time.sleep(3.0)
        keyboard.release('e')
        time.sleep(self.app.purchase_delay_after_key)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "click_point_1"})
        self._click_at(pts[1])
        time.sleep(self.app.purchase_click_delay)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "click_point_2"})
        self._click_at(pts[2])
                                                     
        time.sleep(self.app.purchase_click_delay + 0.3)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("typing", {"action": "typing_amount"})
                                                         
        keyboard.press_and_release('ctrl+a')
        time.sleep(0.1)
        keyboard.press_and_release('delete')
        time.sleep(0.1)
        
                                                              
        for char in amount:
            keyboard.write(char)
            time.sleep(0.05)
        
                                                  
        time.sleep(self.app.purchase_after_type_delay + 0.5)
        print(f"🛒 Typed amount: {amount}")
        
        if not self.app.main_loop_active:
            return
        
                                    
        self.app.set_recovery_state("clicking", {"action": "click_point_1_confirm"})
        self._click_at(pts[1])
        time.sleep(self.app.purchase_click_delay)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "click_point_3"})
        self._click_at(pts[3])
        time.sleep(self.app.purchase_click_delay)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "click_point_2_final"})
        self._click_at(pts[2])
        time.sleep(self.app.purchase_click_delay)
        
        if not self.app.main_loop_active:
            return
        
        self.app.set_recovery_state("clicking", {"action": "right_click_fishing_location"})
                                                           
        if hasattr(self.app, 'fishing_location') and self.app.fishing_location:
            fishing_coords = self.app.fishing_location
            print(f"🎯 Right-clicking at custom fishing location: {fishing_coords}")
        else:
                                                     
            import win32api
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
            fishing_coords = (screen_width // 2, screen_height // 3)
            print(f"🎯 Right-clicking at default fishing location: {fishing_coords}")
        
        self._right_click_at(fishing_coords)
        time.sleep(self.app.purchase_click_delay)
        
        if hasattr(self.app, 'webhook_manager'):
            self.app.webhook_manager.send_purchase(amount)
        
                                           
        if not hasattr(self.app, 'bait_purchased'):
            self.app.bait_purchased = 0
        self.app.bait_purchased += self.app.auto_purchase_amount
        
                                  
        try:
            self.app.root.after(0, lambda: self.app.update_stats_display())
        except:
            pass
        
        print(f"✅ Auto-purchase sequence completed for {amount} items")
        
                                                       
        self.app.set_recovery_state("idle", {"action": "purchase_complete"})
    
    def _click_at(self, coords):
        """Click at coordinates"""
        try:
            x, y = (int(coords[0]), int(coords[1]))
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, 1, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        except Exception as e:
            pass
    
    def _right_click_at(self, coords):
        """Right click at coordinates"""
        try:
            x, y = (int(coords[0]), int(coords[1]))
            win32api.SetCursorPos((x, y))
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, 0, 1, 0, 0)
            threading.Event().wait(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0, 0, 0)
            threading.Event().wait(0.05)
            win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0, 0, 0)
        except Exception as e:
            pass
    
    def validate_fishing_detection(self, img, real_area, target_color, dark_color, white_color):
        """Enhanced validation of fishing bar detection with confidence scoring"""
        try:
            real_height = real_area['height']
            real_width = real_area['width']
            
                                               
            blue_pixels = 0
            dark_pixels = 0
            white_pixels = 0
            total_pixels = real_height * real_width
            
            for row_idx in range(real_height):
                for col_idx in range(real_width):
                    b, g, r = img[row_idx, col_idx, 0:3]
                    
                                                   
                    if r == target_color[0] and g == target_color[1] and b == target_color[2]:
                        blue_pixels += 1
                                                   
                    elif r == dark_color[0] and g == dark_color[1] and b == dark_color[2]:
                        dark_pixels += 1
                                                   
                    elif r == white_color[0] and g == white_color[1] and b == white_color[2]:
                        white_pixels += 1
            
                                          
            blue_ratio = blue_pixels / total_pixels
            dark_ratio = dark_pixels / total_pixels
            white_ratio = white_pixels / total_pixels
            
                                 
            has_sufficient_blue = blue_ratio > 0.05                                  
            has_sufficient_dark = dark_ratio > 0.1                                  
            has_white_indicator = white_ratio > 0.02                                 
            
                                      
            confidence = 0.0
            if has_sufficient_blue:
                confidence += 0.3
            if has_sufficient_dark:
                confidence += 0.4
            if has_white_indicator:
                confidence += 0.3
            
                                                                                        
            if 0.1 < dark_ratio < 0.6 and 0.02 < white_ratio < 0.2:
                confidence += 0.1
            
            validation_result = {
                'is_valid': confidence > 0.6,
                'confidence': confidence,
                'blue_ratio': blue_ratio,
                'dark_ratio': dark_ratio,
                'white_ratio': white_ratio,
                'metrics': {
                    'sufficient_blue': has_sufficient_blue,
                    'sufficient_dark': has_sufficient_dark,
                    'has_white': has_white_indicator
                }
            }
            
            return validation_result
            
        except Exception as e:
            print(f"❌ Detection validation error: {e}")
            return {'is_valid': False, 'confidence': 0.0}
    
    def calculate_smart_control_zones(self, dark_sections, white_top_y, real_height):
        """Calculate smart control zones with weighted scoring"""
        if not dark_sections or white_top_y is None:
            return None
        
                                   
        for section in dark_sections:
            section['size'] = section['end'] - section['start'] + 1
            section['relative_size'] = section['size'] / real_height
            
                                                                    
            section['distance_to_white'] = abs(section['middle'] - white_top_y)
            section['relative_distance'] = section['distance_to_white'] / real_height
            
                                                                                       
            size_score = min(1.0, section['relative_size'] / 0.2)                              
            distance_score = max(0.1, 1.0 - (section['relative_distance'] * 2))                    
            
            section['confidence'] = (size_score * 0.6) + (distance_score * 0.4)
            section['control_weight'] = section['confidence'] * section['size']
        
                                                       
        best_section = max(dark_sections, key=lambda s: s['control_weight'])
        
        return {
            'target_section': best_section,
            'all_sections': dark_sections,
            'section_count': len(dark_sections),
            'total_dark_area': sum(s['size'] for s in dark_sections),
            'confidence': best_section['confidence']
        }
    
    def run_main_loop(self, skip_initial_setup=False):
        """Main fishing loop with enhanced smart detection and control"""
        print('🎣 Main loop started with enhanced smart detection')
        target_color = (85, 170, 255)
        dark_color = (25, 25, 25)
        white_color = (255, 255, 255)
        
                                       
        self.error_smoothing = []                                     
        self.fishing_success_rate = 0.8                                            
        self.recent_catches = []                                 
        
                                             
        if not self.recovery_in_progress:
            self.app.recovery_count = 0
        
        try:
            with mss.mss() as sct:
                                                           
                if not skip_initial_setup:
                    self.perform_initial_setup()
                else:
                    print("🔧 Skipping initial setup - resuming from current state")
                
                                                                            
                if not self.watchdog_active:
                    self.start_watchdog()
                
                                   
                while self.app.main_loop_active and not self.force_stop_flag:
                                                   
                    self.update_heartbeat()
                    
                                                   
                    if not self.app.main_loop_active:
                        print('🛑 Main loop stopped - main_loop_active is False')
                        break
                    if self.force_stop_flag:
                        print('🛑 Main loop stopped - force_stop_flag is True')
                        break
                    
                    try:
                        print(f'🎣 Fishing cycle #{self.app.fish_count + 1}')
                        
                                                                                  
                        self.app.set_recovery_state("casting", {"action": "initial_cast"})
                        self.cast_line()
                        cast_time = time.time()
                        
                                                                    
                        time.sleep(0.5)
                        
                                               
                        self.app.set_recovery_state("fishing", {"action": "blue_bar_detection"})
                        detected = False
                        was_detecting = False
                        print('Scanning for blue fishing bar...')
                        
                        detection_start_time = time.time()
                        last_spawn_check = time.time()
                        last_click_time = time.time()  # For timer-based click control
                        spawn_check_interval = 4.0                                                  
                        
                        while self.app.main_loop_active and not self.force_stop_flag:
                                                                          
                            self.update_heartbeat()
                            
                                                                                       
                                                                                                             
                            current_time = time.time()
                            time_since_last_spawn = current_time - self.last_fruit_spawn_time
                            
                                                                                                             
                            if not detected and current_time - last_spawn_check > spawn_check_interval and time_since_last_spawn > self.fruit_spawn_cooldown:
                                try:
                                                                    
                                    if hasattr(self.app, 'ocr_manager') and self.app.ocr_manager.is_available():
                                                                                           
                                        original_cooldown = self.app.ocr_manager.capture_cooldown
                                        self.app.ocr_manager.capture_cooldown = 0.1                                           
                                        
                                        spawn_text = self.app.ocr_manager.extract_text()
                                        
                                                                   
                                        self.app.ocr_manager.capture_cooldown = original_cooldown
                                        
                                        if spawn_text:
                                            print(f"🔍 Spawn check OCR result: {spawn_text}")
                                            fruit_name = self.app.ocr_manager.detect_fruit_spawn(spawn_text)
                                            if fruit_name:
                                                print(f"🌟 Devil fruit spawn detected: {fruit_name}")
                                                                                    
                                                self.last_fruit_spawn_time = current_time
                                                print(f"⏰ Fruit spawn cooldown activated - won't check again for 15 minutes")
                                                              
                                                if hasattr(self.app, 'webhook_manager') and getattr(self.app, 'fruit_spawn_webhook_enabled', True):
                                                    self.app.webhook_manager.send_fruit_spawn(fruit_name)
                                    
                                    last_spawn_check = current_time
                                except Exception as spawn_error:
                                    print(f"⚠️ Spawn check error: {spawn_error}")
                            elif time_since_last_spawn <= self.fruit_spawn_cooldown:
                                                                         
                                pass
                            
                                                           
                            current_time = time.time()
                            
                                                                              
                            base_timeout = self.app.scan_timeout
                            if self.fishing_success_rate > 0.7:
                                                                              
                                adaptive_timeout = base_timeout * 1.3
                            elif self.fishing_success_rate < 0.4:
                                                                                           
                                adaptive_timeout = base_timeout * 0.7
                            else:
                                adaptive_timeout = base_timeout
                            
                            if current_time - detection_start_time > adaptive_timeout:
                                if not detected:
                                    print(f'⏰ No fish detected after {adaptive_timeout:.1f}s (adaptive), recasting...')
                                                          
                                    self.recent_catches.append(False)
                                    if len(self.recent_catches) > 10:
                                        self.recent_catches.pop(0)
                                    self.fishing_success_rate = sum(self.recent_catches) / len(self.recent_catches)
                                    break
                                elif current_time - detection_start_time > adaptive_timeout + 15:
                                    print(f'⏰ Fish control timeout after {adaptive_timeout + 15:.1f}s, recasting...')
                                                                           
                                    if self.app.is_clicking:
                                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                                        self.app.is_clicking = False
                                                          
                                    self.recent_catches.append(False)
                                    if len(self.recent_catches) > 10:
                                        self.recent_catches.pop(0)
                                    self.fishing_success_rate = sum(self.recent_catches) / len(self.recent_catches)
                                    break
                            
                                                                
                            try:
                                                                           
                                bar_area = self.app.layout_manager.get_layout_area('bar')
                                if not bar_area:
                                                                 
                                    bar_area = {'x': 700, 'y': 400, 'width': 200, 'height': 100}
                                x = bar_area['x']
                                y = bar_area['y']
                                width = bar_area['width']
                                height = bar_area['height']
                                monitor = {'left': x, 'top': y, 'width': width, 'height': height}
                                screenshot = sct.grab(monitor)
                                img = np.array(screenshot)
                            except Exception as screenshot_error:
                                print(f'❌ Screenshot error: {screenshot_error}')
                                time.sleep(0.1)
                                continue
                            
                                                                                  
                            try:
                                point1_x = None
                                point1_y = None
                                found_first = False
                                for row_idx in range(height):
                                    for col_idx in range(width):
                                        b, g, r = img[row_idx, col_idx, 0:3]
                                        if r == target_color[0] and g == target_color[1] and b == target_color[2]:
                                            point1_x = x + col_idx
                                            point1_y = y + row_idx
                                            found_first = True
                                            break
                                    if found_first:
                                        break
                            except Exception as detection_error:
                                print(f'❌ Blue bar detection error: {detection_error}')
                                time.sleep(0.1)
                                continue
                            
                            if found_first:
                                detected = True
                            else:
                                                   
                                if not detected and time.time() - cast_time > self.app.scan_timeout:
                                    print(f'Cast timeout after {self.app.scan_timeout}s, recasting...')
                                                                                         
                                    if hasattr(self.app, 'bait_manager') and self.app.bait_manager.is_enabled():
                                        print("🔄 Reselecting bait (may have run out)")
                                        self.app.bait_manager.select_top_bait()
                                    break
                                
                                if was_detecting:
                                    print('Fish caught! Processing...')
                                    
                                                                      
                                    if self.app.is_clicking:
                                        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                                        self.app.is_clicking = False
                                    
                                                                                  
                                    self.recent_catches.append(True)
                                    if len(self.recent_catches) > 10:
                                        self.recent_catches.pop(0)
                                    self.fishing_success_rate = sum(self.recent_catches) / len(self.recent_catches)
                                    
                                                                                         
                                    self.app.increment_fish_counter()
                                    
                                                                  
                                    self.process_post_catch_workflow()
                                    
                                    time.sleep(self.app.wait_after_loss)
                                    was_detecting = False
                                    self.check_and_purchase()
                                                                    
                                    success_pct = int(self.fishing_success_rate * 100)
                                    print(f'🐟 Fish processing complete | Success Rate: {success_pct}%')
                                    break
                                
                                time.sleep(0.1)
                                continue
                            
                                                         
                            point2_x = None
                            row_idx = point1_y - y
                            for col_idx in range(width - 1, -1, -1):
                                b, g, r = img[row_idx, col_idx, 0:3]
                                if r == target_color[0] and g == target_color[1] and b == target_color[2]:
                                    point2_x = x + col_idx
                                    break
                            
                            if point2_x is None:
                                time.sleep(0.1)
                                continue
                            
                                                      
                            temp_area_x = point1_x
                            temp_area_width = point2_x - point1_x + 1
                            temp_monitor = {'left': temp_area_x, 'top': y, 'width': temp_area_width, 'height': height}
                            temp_screenshot = sct.grab(temp_monitor)
                            temp_img = np.array(temp_screenshot)
                            
                                                              
                            top_y = None
                            for row_idx in range(height):
                                found_dark = False
                                for col_idx in range(temp_area_width):
                                    b, g, r = temp_img[row_idx, col_idx, 0:3]
                                    if r == dark_color[0] and g == dark_color[1] and b == dark_color[2]:
                                        top_y = y + row_idx
                                        found_dark = True
                                        break
                                if found_dark:
                                    break
                            
                            bottom_y = None
                            for row_idx in range(height - 1, -1, -1):
                                found_dark = False
                                for col_idx in range(temp_area_width):
                                    b, g, r = temp_img[row_idx, col_idx, 0:3]
                                    if r == dark_color[0] and g == dark_color[1] and b == dark_color[2]:
                                        bottom_y = y + row_idx
                                        found_dark = True
                                        break
                                if found_dark:
                                    break
                            
                            if top_y is None or bottom_y is None:
                                time.sleep(0.1)
                                continue
                            
                                                       
                            self.app.real_area = {'x': temp_area_x, 'y': top_y, 'width': temp_area_width, 'height': bottom_y - top_y + 1}
                            real_x = self.app.real_area['x']
                            real_y = self.app.real_area['y']
                            real_width = self.app.real_area['width']
                            real_height = self.app.real_area['height']
                            real_monitor = {'left': real_x, 'top': real_y, 'width': real_width, 'height': real_height}
                            real_screenshot = sct.grab(real_monitor)
                            real_img = np.array(real_screenshot)
                            
                                                                      
                            
                                                  
                            white_top_y = None
                            white_bottom_y = None
                            for row_idx in range(real_height):
                                for col_idx in range(real_width):
                                    b, g, r = real_img[row_idx, col_idx, 0:3]
                                    if r == white_color[0] and g == white_color[1] and b == white_color[2]:
                                        white_top_y = real_y + row_idx
                                        break
                                if white_top_y is not None:
                                    break
                            
                            for row_idx in range(real_height - 1, -1, -1):
                                for col_idx in range(real_width):
                                    b, g, r = real_img[row_idx, col_idx, 0:3]
                                    if r == white_color[0] and g == white_color[1] and b == white_color[2]:
                                        white_bottom_y = real_y + row_idx
                                        break
                                if white_bottom_y is not None:
                                    break
                            
                            if white_top_y is not None and white_bottom_y is not None:
                                white_height = white_bottom_y - white_top_y + 1
                                max_gap = white_height * 2
                                white_center_y = (white_top_y + white_bottom_y) // 2  # Target center of white bar
                            
                                                                
                            dark_sections = []
                            current_section_start = None
                            gap_counter = 0
                            for row_idx in range(real_height):
                                has_dark = False
                                for col_idx in range(real_width):
                                    b, g, r = real_img[row_idx, col_idx, 0:3]
                                    if r == dark_color[0] and g == dark_color[1] and b == dark_color[2]:
                                        has_dark = True
                                        break
                                if has_dark:
                                    gap_counter = 0
                                    if current_section_start is None:
                                        current_section_start = real_y + row_idx
                                else:
                                    if current_section_start is not None:
                                        gap_counter += 1
                                        if gap_counter > max_gap:
                                            section_end = real_y + row_idx - gap_counter
                                            dark_sections.append({'start': current_section_start, 'end': section_end, 'middle': (current_section_start + section_end) // 2})
                                            current_section_start = None
                                            gap_counter = 0
                            
                            if current_section_start is not None:
                                section_end = real_y + real_height - 1 - gap_counter
                                dark_sections.append({'start': current_section_start, 'end': section_end, 'middle': (current_section_start + section_end) // 2})
                            
                                                            
                            if dark_sections and white_top_y is not None:
                                if not was_detecting:
                                                                                             
                                    print('Fish detected! Starting control...')
                                    self.app.set_recovery_state("fishing", {"action": "fish_control_active"})
                                was_detecting = True
                                
                                                                                         
                                for section in dark_sections:
                                    section['size'] = section['end'] - section['start'] + 1
                                largest_section = max(dark_sections, key=lambda s: s['size'])
                                
                                # Control target: keep fish center at the white bar center
                                raw_error = largest_section['middle'] - white_center_y
                                normalized_error = raw_error / real_height if real_height > 0 else raw_error
                                derivative = normalized_error - self.app.previous_error
                                self.app.previous_error = normalized_error
                                pd_output = self.app.kp * normalized_error + self.app.kd * derivative
                                
                                print(f'Error: {raw_error}px, PD: {pd_output:.2f}, Fish: {largest_section["middle"]}, Center Target: {white_center_y}, Clicking: {self.app.is_clicking}')
                                
                                # Simple timer-based control for stability
                                # When fish is near center: single click every 0.4s to hold it steady
                                # When fish is far: continuous hold/release for momentum correction
                                center_threshold = 0.02  # Zone for timer-based clicks
                                aggressive_threshold = 0.06  # Zone for continuous control
                                click_interval = 0.4  # Click every 0.4 seconds to hold
                                
                                current_time = time.time()
                                
                                if abs(normalized_error) < center_threshold:
                                    # Fish is stable near center - use single click every 0.4s
                                    if pd_output > 0.005:  # Fish needs to be held down
                                        if current_time - last_click_time > click_interval:
                                            # Single click to hold
                                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                                            time.sleep(0.05)  # 50ms click
                                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                                            last_click_time = current_time
                                            self.app.is_clicking = False
                                    else:
                                        # Fish is above center or at center - just release and wait
                                        if self.app.is_clicking:
                                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                                            self.app.is_clicking = False
                                else:
                                    # Fish is far from center - use continuous hold/release for momentum correction
                                    if self.app.is_clicking:
                                        # Currently holding - release if fish is above center
                                        if pd_output < -aggressive_threshold:
                                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                                            self.app.is_clicking = False
                                    else:
                                        # Currently releasing - hold if fish is below center
                                        if pd_output > aggressive_threshold:
                                            win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
                                            self.app.is_clicking = True
                            
                            time.sleep(0.1)
                        
                        self.app.set_recovery_state("idle", {"action": "detection_complete"})
                        
                    except Exception as e:
                        print(f'🚨 Main loop error: {e}')
                        import traceback
                        traceback.print_exc()
                        self.app.log(f'Main loop error: {e}', "error")
                        if not self.force_stop_flag:
                            time.sleep(1.0)
                        else:
                            break                                  
        
        except Exception as e:
            self.app.log(f'🚨 Critical main loop error: {e}', "error")
        
        finally:
                             
            print('🛑 Main loop stopped - cleaning up')
            
                           
            self.stop_watchdog()
            
                                  
            if self.app.is_clicking:
                try:
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
                    self.app.is_clicking = False
                except:
                    pass
    
    def perform_initial_setup(self):
        """Perform initial setup: zoom out, specific zoom in, auto buy if enabled"""
        print("🔧 Performing initial setup...")
        
                                                    
        self.app.set_recovery_state("initial_setup", {"action": "starting_setup"})
        
                                                                           
        self.update_heartbeat()
        
                                             
        auto_zoom_enabled = getattr(self.app, 'auto_zoom_enabled', False)
        if not auto_zoom_enabled and hasattr(self.app, 'auto_zoom_var'):
            try:
                auto_zoom_enabled = self.app.auto_zoom_var.get()
            except Exception:
                pass
        
        if auto_zoom_enabled:
            if hasattr(self.app, 'zoom_controller'):
                if self.app.zoom_controller.is_available():
                    self.app.set_recovery_state("initial_setup", {"action": "zoom_out"})
                    print("🔍 Step 1: Full zoom out...")
                    success_out = self.app.zoom_controller.reset_zoom()
                    print(f"Zoom out result: {success_out}")
                    self.update_heartbeat()                         
                    time.sleep(1.0)                                         
                    
                                              
                    self.app.set_recovery_state("initial_setup", {"action": "zoom_in"})
                    print("🔍 Step 2: Specific zoom in...")
                    success_in = self.app.zoom_controller.zoom_in()
                    print(f"Zoom in result: {success_in}")
                    self.update_heartbeat()                        
                    time.sleep(1.0)                                         
                else:
                    print("🔍 Zoom controller not available (missing pywin32)")
            else:
                print("🔍 Zoom controller not initialized")
        else:
            print("🔍 Auto zoom disabled - skipping zoom sequence")
        
                                          
        if getattr(self.app, 'auto_purchase_var', None) and self.app.auto_purchase_var.get():
            print("🛒 Step 3: Auto purchase...")
            self.app.set_recovery_state("purchasing", {"sequence": "initial_auto_purchase"})
            self.perform_auto_purchase()
                                                                  
            time.sleep(1.0)
        
                                                                      
        auto_bait_enabled = getattr(self.app, 'auto_bait_enabled', False)
        if auto_bait_enabled and hasattr(self.app, 'top_bait_coords') and self.app.top_bait_coords:
            print("🎣 Step 4: Selecting initial bait...")
            self.app.set_recovery_state("initial_setup", {"action": "bait_selection"})
            
            import keyboard
            
                                                     
            rod_key = getattr(self.app, 'rod_key', '1')
            print(f"  → Pressing rod key '{rod_key}'")
            keyboard.press_and_release(rod_key)
            time.sleep(0.5)
            
                                    
            bait_x, bait_y = self.app.top_bait_coords
            print(f"  → Clicking top bait point 1 at ({bait_x}, {bait_y})")
            self.app._click_at((bait_x, bait_y))
            time.sleep(0.3)
            
                                                   
            if hasattr(self.app, 'top_bait_coords_2') and self.app.top_bait_coords_2:
                bait_x2, bait_y2 = self.app.top_bait_coords_2
                print(f"  → Clicking top bait point 2 (backup) at ({bait_x2}, {bait_y2})")
                self.app._click_at((bait_x2, bait_y2))
                time.sleep(0.3)
                
                                           
                print(f"  → Clicking back at bait point 1")
                self.app._click_at((bait_x, bait_y))
                time.sleep(0.3)
            
            print("  ✓ Initial bait selected")
        elif auto_bait_enabled:
            print("⚠️ Auto-bait enabled but coordinates not set - skipping bait selection")
        else:
            print("ℹ️ Auto-bait disabled - skipping initial bait selection")
        
                                                                                
        self.app.set_recovery_state("initial_setup", {"action": "finalizing"})
        print("⏳ Waiting for setup to stabilize...")
        time.sleep(1.5)
        
                                                     
        self.app.set_recovery_state("idle", {"action": "setup_complete"})
        self.update_heartbeat()                          
        print("✅ Initial setup complete")
    
    def process_post_catch_workflow(self):
        """Complete post-catch workflow: search for drops, find text, log to webhook and dev mode"""
        print("🎣 Processing post-catch workflow...")
        
                                                            
        original_layout = self.app.layout_manager.current_layout
        if original_layout != 'drop':
            print("📍 Switching to drop layout for text recognition...")
            self.app.layout_manager.toggle_layout()
            if hasattr(self.app, 'overlay_manager'):
                self.app.overlay_manager.update_layout()
        
                                                   
        drop_info = self.search_for_drops()
        
                                                                       
        if drop_info and drop_info.get('has_fruit', False):
            print("🍎 Fruit detected in catch - running fruit storage sequence")
            
                                                   
            if not hasattr(self.app, 'devil_fruits_caught'):
                self.app.devil_fruits_caught = []
            self.app.devil_fruits_caught.append(drop_info.get('drop_text', 'Unknown Fruit'))
            
                                  
            try:
                self.app.root.after(0, lambda: self.app.update_stats_display())
            except:
                pass
            
                                                       
            if (hasattr(self.app, 'webhook_manager') and 
                getattr(self.app, 'devil_fruit_webhook_enabled', True)):
                self.app.webhook_manager.send_devil_fruit_drop(drop_info)
            
            self.store_fruit()
        elif getattr(self.app, 'fruit_storage_enabled', False):
            print("⏭️ No fruit detected - skipping fruit storage sequence")
        else:
            print("⏭️ Fruit storage disabled - skipping sequence")
        
                                                     
        if original_layout != 'drop':
            print("📍 Switching back to bar layout...")
            self.app.layout_manager.toggle_layout()
            if hasattr(self.app, 'overlay_manager'):
                self.app.overlay_manager.update_layout()
        
        print("✅ Post-catch workflow complete")
    
    def check_legendary_pity(self, drop_text):
        """
        Check if devil fruit drop is legendary by detecting pity counters
        Legendary drops show: 0/37, 0/40, 0/92, 0/100
        Non-legendary show: 1/37, 2/40, etc.
        """
        import re
        
                                                                            
        pity_patterns = []
                                                 
        for i in range(1, 101):
            pity_patterns.append(f'0/{i}')
        
                                   
        pity_patterns = [re.escape(pattern) for pattern in pity_patterns]
        
        text_lower = drop_text.lower()
        
                                                                               
        legendary_keywords = ['legendary']
        has_legendary_keyword = any(keyword in text_lower for keyword in legendary_keywords)
        
                                                                    
        has_legendary_pity = any(re.search(pattern, drop_text) for pattern in pity_patterns)
        
                                                                            
        is_legendary = has_legendary_keyword or has_legendary_pity
        
        if is_legendary:
            print(f"🔍 Legendary detection: keyword={has_legendary_keyword}, pity={has_legendary_pity}")
            print(f"📝 Drop text: {drop_text}")
        
        return is_legendary

    def search_for_drops(self):
        """Search for drops in the drop layout area and extract text"""
        drop_info = {'has_fruit': False, 'drop_text': '', 'is_legendary': False}
        
        try:
                                              
            if not hasattr(self.app, 'ocr_manager') or not self.app.ocr_manager.get_stats()['available']:
                print("📝 OCR not available, skipping drop search")
                return drop_info
            
                                  
            drop_area = self.app.layout_manager.get_layout_area('drop')
            if not drop_area:
                print("📝 No drop area configured, skipping drop search")
                return drop_info
            
            print("🔍 Searching for drops in drop area...")
            
                                             
            import mss
            with mss.mss() as sct:
                monitor = {
                    'left': drop_area['x'],
                    'top': drop_area['y'],
                    'width': drop_area['width'],
                    'height': drop_area['height']
                }
                screenshot = sct.grab(monitor)
                img = np.array(screenshot)
            
                                                          
            if hasattr(self.app, 'ocr_manager'):
                drop_text = self.app.ocr_manager.extract_text()                                                
                if drop_text:
                    drop_info['drop_text'] = drop_text
                    
                    if drop_text == "TEXT_DETECTED_NO_OCR":
                        print("📝 Text-like content detected in drop area (install Tesseract OCR for full text recognition)")
                                                                           
                        drop_info['has_fruit'] = True
                    else:
                        print(f"📝 Drop detected: {drop_text}")
                        
                                                                               
                        devil_fruit_keywords = ['devil', 'fruit', 'backpack', 'drop', 'got', 'fished up']
                        drop_text_lower = drop_text.lower()
                        
                                                              
                        devil_fruit_phrases = [
                            'devil fruit',
                            'fished up a devil',
                            'got a devil fruit',
                            'devil fruit drop',
                            'check your backpack'
                        ]
                        
                                                          
                        for phrase in devil_fruit_phrases:
                            if phrase in drop_text_lower:
                                drop_info['has_fruit'] = True
                                print(f"🍎 Devil fruit detected in drop: '{phrase}'")
                                break
                        
                                                                                             
                        if not drop_info['has_fruit']:
                            keyword_matches = sum(1 for keyword in devil_fruit_keywords if keyword in drop_text_lower)
                            if keyword_matches >= 2:
                                drop_info['has_fruit'] = True
                                print(f"🍎 Devil fruit detected (keyword match count: {keyword_matches})")
                        
                                                     
                        if 'devil fruit' in drop_text_lower:
                            drop_info['has_fruit'] = True
                            print(f"🍎 Devil fruit detected!")
                        
                                                                   
                        fruit_name = self.app.ocr_manager.detect_fruit_spawn(drop_text)
                        if fruit_name:
                            print(f"🌟 Devil fruit spawn detected: {fruit_name}")
                                                       
                            if hasattr(self.app, 'webhook_manager'):
                                self.app.webhook_manager.send_fruit_spawn(fruit_name)
                        
                                                 
                        if hasattr(self.app, 'overlay_manager_drop') and self.app.overlay_manager_drop.window:
                            self.app.overlay_manager_drop.display_captured_text(drop_text)
                        
                                                   
                        if getattr(self.app, 'dev_mode', False):
                            print(f"🔧 [DEV MODE] Drop details: {drop_text}")
                        
                else:
                    print("📝 No text found in drop area")
                        
        except Exception as e:
            print(f"❌ Drop search error: {e}")
        
        return drop_info
    
    def process_auto_zoom(self):
        """Process automatic zoom control (DISABLED - handled in perform_initial_setup)"""
                                                                                  
                                                                  
        return