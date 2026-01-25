import tkinter as tk
from tkinter import ttk

class ToolTip:
    """Simple tooltip for overlay point indicators"""
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tooltip = None
        self.widget.bind("<Enter>", self.show)
        self.widget.bind("<Leave>", self.hide)
    
    def show(self, event=None):
        if self.tooltip:
            return
                             
        x = self.widget.winfo_rootx() + 25
        y = self.widget.winfo_rooty() + 25
        
        self.tooltip = tk.Toplevel(self.widget)
        self.tooltip.wm_overrideredirect(True)
        self.tooltip.wm_geometry(f"+{x}+{y}")
        
        label = tk.Label(self.tooltip, text=self.text, background="#ffffe0",
                        relief=tk.SOLID, borderwidth=1, font=("Arial", 9))
        label.pack()
    
    def hide(self, event=None):
        if self.tooltip:
            self.tooltip.destroy()
            self.tooltip = None

class OverlayManager:
    def __init__(self, app, fixed_layout=None):
        self.app = app
        self.fixed_layout = fixed_layout                                                     
        self.window = None
        self.frame = None
        self.label = None
        self.point_indicators = []                                 
        self.drag_data = {'x': 0, 'y': 0, 'resize_edge': None, 'start_width': 0, 
                         'start_height': 0, 'start_x': 0, 'start_y': 0}
    
    def create(self):
        if self.window is not None:
            return
        
        self.window = tk.Toplevel(self.app.root)
        self.window.overrideredirect(True)
        self.window.attributes('-alpha', 0.6)
        self.window.attributes('-topmost', True)
        self.window.minsize(1, 1)
        
                                 
        current_area = self.get_current_area()
        x = current_area['x']
        y = current_area['y']
        width = current_area['width']
        height = current_area['height']
        geometry = f"{width}x{height}+{x}+{y}"
        self.window.geometry(geometry)
        
                                                  
        current_layout = self.get_current_layout()
        layout_config = self.app.layout_manager.layouts[current_layout]
        bg_color = self._rgb_to_hex(layout_config['color'])
        border_color = self._rgb_to_hex(layout_config['border_color'])
        
        self.frame = tk.Frame(self.window, bg=bg_color, highlightthickness=3, 
                             highlightbackground=border_color)
        self.frame.pack(fill=tk.BOTH, expand=True)
        
                                                                             
        self.label = tk.Label(self.frame, text=layout_config['name'], 
                             bg=bg_color, fg='white', font=('Arial', 12, 'bold'))
                                     
        self.label.place(relx=0.5, y=5, anchor='n')
        
                                                                      
        self.text_display = None
        current_layout = self.get_current_layout()
        if current_layout == 'drop':
                                                                                        
            self.text_display = tk.Text(self.frame, height=4, width=30, 
                                      bg=bg_color, fg='white', font=('Courier', 9),
                                      wrap=tk.WORD, state=tk.DISABLED, bd=0, 
                                      highlightthickness=0, relief='flat')
                                                           
            self.text_display.pack(pady=(30, 5), padx=5, fill=tk.BOTH, expand=True)
        
                                     
        self.draw_click_points()
        
                     
        self.window.bind("<ButtonPress-1>", self._start_action)
        self.window.bind("<B1-Motion>", self._motion)
        self.window.bind("<Motion>", self._update_cursor)
        self.window.bind("<Configure>", self._on_configure)
        
        self.frame.bind("<ButtonPress-1>", self._start_action)
        self.frame.bind("<B1-Motion>", self._motion)
        self.frame.bind("<Motion>", self._update_cursor)
        
                                            
        self.label.bind("<ButtonPress-1>", self._start_action)
        self.label.bind("<B1-Motion>", self._motion)
        self.label.bind("<Motion>", self._update_cursor)
    
    def draw_click_points(self):
        """Draw visual indicators for all configured click points as separate topmost windows"""
        if not self.window:
            print("❌ draw_click_points: No window")
            return
        
        print(f"\n🔍 Drawing click points as separate topmost windows")
        
                                   
        for indicator in self.point_indicators:
            try:
                indicator.destroy()
            except:
                pass
        self.point_indicators = []
        
        print(f"App point_coords: {self.app.point_coords}")
        print(f"App fruit_coords: {self.app.fruit_coords}")
        print(f"App fishing_location: {getattr(self.app, 'fishing_location', None)}")
        
                                                   
        points_config = [
                                    
            (getattr(self.app, 'fishing_location', None), '#FFD700', 'Cast Location'),          
            (self.app.point_coords.get(1, None), '#9370DB', 'Auto-Purchase Point 1'),          
            (self.app.point_coords.get(2, None), '#9370DB', 'Auto-Purchase Point 2'),          
            (self.app.point_coords.get(3, None), '#9370DB', 'Auto-Purchase Point 3'),          
            (self.app.fruit_coords.get('fruit_point', None), '#FF69B4', 'Fruit Storage Point'),        
            (self.app.fruit_coords.get('fruit_point_2', None), '#FF69B4', 'Fruit Storage Point 2'),        
            (self.app.fruit_coords.get('bait_point', None), '#00CED1', 'Bait Selection Point'),        
        ]
        
        for coords, color, label in points_config:
            if coords:
                                                 
                point_x = coords[0]
                point_y = coords[1]
                
                print(f"✅ Creating TOPMOST indicator window for {label} at screen ({point_x}, {point_y})")
                
                                                                     
                indicator_window = tk.Toplevel(self.app.root)
                indicator_window.overrideredirect(True)
                indicator_window.attributes('-topmost', True)
                indicator_window.attributes('-alpha', 0.95)
                indicator_window.attributes('-transparentcolor', 'black')
                
                                                      
                indicator_window.geometry(f"32x32+{point_x-16}+{point_y-16}")
                
                                              
                container = tk.Frame(indicator_window, bg='black')
                container.pack(fill='both', expand=True)
                
                                                   
                indicator = tk.Label(container, text="●", 
                                   fg=color, bg='black',
                                   font=('Arial', 22, 'bold'),
                                   relief='solid', bd=2,
                                   borderwidth=2,
                                   highlightbackground='white',
                                   highlightthickness=2)
                indicator.pack(expand=True, padx=2, pady=2)
                
                             
                ToolTip(indicator, label)
                
                self.point_indicators.append(indicator_window)
                print(f"✓ Drew {label} at ({point_x}, {point_y}) with color {color}")
    
    def destroy(self):
        if self.window is not None:
                                             
            current_layout = self.get_current_layout()
            area = {
                'x': self.window.winfo_x(),
                'y': self.window.winfo_y(),
                'width': self.window.winfo_width(),
                'height': self.window.winfo_height()
            }
            self.app.layout_manager.set_layout_area(current_layout, area)
            
                              
            for indicator in self.point_indicators:
                try:
                    indicator.destroy()
                except:
                    pass
            self.point_indicators = []
            
            self.window.destroy()
            self.window = None
            self.frame = None
            self.label = None
    
    def _get_resize_edge(self, x, y):
        width = self.window.winfo_width()
        height = self.window.winfo_height()
        edge_size = 10
        on_left = x < edge_size
        on_right = x > width - edge_size
        on_top = y < edge_size
        on_bottom = y > height - edge_size
        
        if on_top and on_left:
            return "nw"
        elif on_top and on_right:
            return "ne"
        elif on_bottom and on_left:
            return "sw"
        elif on_bottom and on_right:
            return "se"
        elif on_left:
            return "w"
        elif on_right:
            return "e"
        elif on_top:
            return "n"
        elif on_bottom:
            return "s"
        return None
    
    def _update_cursor(self, event):
        edge = self._get_resize_edge(event.x, event.y)
        cursor_map = {'nw': 'size_nw_se', 'ne': 'size_ne_sw', 'sw': 'size_ne_sw', 
                     'se': 'size_nw_se', 'n': 'size_ns', 's': 'size_ns', 
                     'e': 'size_we', 'w': 'size_we', None: 'arrow'}
        self.window.config(cursor=cursor_map.get(edge, 'arrow'))
    
    def _start_action(self, event):
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y
        self.drag_data['resize_edge'] = self._get_resize_edge(event.x, event.y)
        self.drag_data['start_width'] = self.window.winfo_width()
        self.drag_data['start_height'] = self.window.winfo_height()
        self.drag_data['start_x'] = self.window.winfo_x()
        self.drag_data['start_y'] = self.window.winfo_y()
    
    def _motion(self, event):
        edge = self.drag_data['resize_edge']
        
        if edge is None:
            x = self.window.winfo_x() + event.x - self.drag_data['x']
            y = self.window.winfo_y() + event.y - self.drag_data['y']
            self.window.geometry(f'+{x}+{y}')
                                       
            self.app.root.after(10, self.draw_click_points)
        else:
            dx = event.x - self.drag_data['x']
            dy = event.y - self.drag_data['y']
            
            new_width = self.drag_data['start_width']
            new_height = self.drag_data['start_height']
            new_x = self.drag_data['start_x']
            new_y = self.drag_data['start_y']
            
            if 'e' in edge:
                new_width = max(1, self.drag_data['start_width'] + dx)
            elif 'w' in edge:
                new_width = max(1, self.drag_data['start_width'] - dx)
                new_x = self.drag_data['start_x'] + dx
            
            if 's' in edge:
                new_height = max(1, self.drag_data['start_height'] + dy)
            elif 'n' in edge:
                new_height = max(1, self.drag_data['start_height'] - dy)
                new_y = self.drag_data['start_y'] + dy
            
            self.window.geometry(f"{new_width}x{new_height}+{new_x}+{new_y}")
                                         
            self.app.root.after(10, self.draw_click_points)
    
    def _on_configure(self, event=None):
        if self.window is not None:
                                                
            current_layout = self.get_current_layout()
            area = {
                'x': self.window.winfo_x(),
                'y': self.window.winfo_y(),
                'width': self.window.winfo_width(),
                'height': self.window.winfo_height()
            }
            self.app.layout_manager.set_layout_area(current_layout, area)

    
    def get_current_layout(self):
        """Get the layout this overlay should use"""
        return self.fixed_layout or self.app.layout_manager.current_layout
    
    def get_current_area(self):
        """Get area for current layout"""
        current_layout = self.get_current_layout()
        area = self.app.layout_manager.get_layout_area(current_layout)
        
                                                         
        if not area:
            if current_layout == 'bar':
                                                                
                area = {'x': 700, 'y': 400, 'width': 200, 'height': 100}
            elif current_layout == 'drop':
                                                                 
                area = {'x': 800, 'y': 200, 'width': 300, 'height': 400}
            else:
                                                 
                area = getattr(self.app, 'overlay_area', {'x': 100, 'y': 100, 'width': 200, 'height': 100}).copy()
        
        return area
    
    def update_layout(self):
        """Update overlay appearance for current layout"""
        if self.window is None:
            return
        
        current_layout = self.get_current_layout()
        layout_config = self.app.layout_manager.layouts[current_layout]
        
                       
        bg_color = self._rgb_to_hex(layout_config['color'])
        border_color = self._rgb_to_hex(layout_config['border_color'])
        
        if self.frame:
            self.frame.config(bg=bg_color, highlightbackground=border_color)
        
        if self.label:
            self.label.config(text=layout_config['name'], bg=bg_color)
                                                             
            self.label.place(relx=0.5, y=5, anchor='n')
        
                                                    
        if current_layout == 'drop' and not self.text_display:
                                                                                        
            self.text_display = tk.Text(self.frame, height=4, width=30, 
                                      bg=bg_color, fg='white', font=('Courier', 9),
                                      wrap=tk.WORD, state=tk.DISABLED, bd=0, 
                                      highlightthickness=0, relief='flat')
                                                           
            self.text_display.pack(pady=(30, 5), padx=5, fill=tk.BOTH, expand=True)
        elif current_layout == 'bar' and self.text_display:
            self.text_display.destroy()
            self.text_display = None
        
                                                 
        if self.text_display and current_layout == 'drop':
            self.text_display.config(bg=bg_color, fg='white')
        
                                                
        current_area = self.get_current_area()
        geometry = f"{current_area['width']}x{current_area['height']}+{current_area['x']}+{current_area['y']}"
        self.window.geometry(geometry)
        
                             
        self.draw_click_points()
        
        print(f"🎯 Overlay updated for {layout_config['name']}")
    
    def display_captured_text(self, text):
        """Display captured OCR text in the overlay"""
        if self.text_display and text:
            self.text_display.config(state=tk.NORMAL)
            self.text_display.delete(1.0, tk.END)
            
                           
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            self.text_display.insert(tk.END, f"[{timestamp}]\n", "timestamp")
            self.text_display.insert(tk.END, text + "\n\n")
            
                              
            self.text_display.see(tk.END)
            self.text_display.config(state=tk.DISABLED)
    
    def clear_text_display(self):
        """Clear the text display area"""
        if self.text_display:
            self.text_display.config(state=tk.NORMAL)
            self.text_display.delete(1.0, tk.END)
            self.text_display.config(state=tk.DISABLED)
    
    def _rgb_to_hex(self, rgb):
        """Convert RGB tuple to hex color"""
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
