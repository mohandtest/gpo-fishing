import tkinter as tk
import ctypes
import sys
import os

                                                
if 'pythonw' in sys.executable.lower():
    import io
                                                         
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

                                               
if hasattr(sys, '_MEIPASS'):
                                   
    sys.path.insert(0, sys._MEIPASS)
else:
                       
    sys.path.insert(0, os.path.dirname(__file__))

from gui import HotkeyGUI

def main():
    print("Starting GPO Autofish...")
    root = tk.Tk()
    print(f"Tk root created: {root}")
    
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        pass
    
                     
    try:
        from PIL import Image, ImageTk
        import os
        
                                                                      
        if hasattr(sys, '_MEIPASS'):
                                           
            icon_path = os.path.join(sys._MEIPASS, "images", "icon.webp")
        else:
                               
            icon_path = os.path.join(os.path.dirname(__file__), "..", "images", "icon.webp")
            
        if os.path.exists(icon_path):
            icon_image = Image.open(icon_path)
                                               
            photo = ImageTk.PhotoImage(icon_image)
            root.iconphoto(True, photo)
        else:
            print(f"Icon not found at: {icon_path}")
    except Exception as e:
        print(f"Could not load icon: {e}")
    
    print("Creating GUI...")
    try:
        app = HotkeyGUI(root)
        print(f"GUI created: {app}")
        root.protocol('WM_DELETE_WINDOW', app.exit_app)
                                    
        root.deiconify()
        root.lift()
        root.focus_force()
        print("Starting mainloop...")
        root.mainloop()
    except Exception as e:
        import traceback
                                         
        try:
            with open('error.log', 'w', encoding='utf-8', errors='replace') as f:
                f.write(f"Error: {e}\n")
                f.write(traceback.format_exc())
        except:
            pass
        raise

if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        import traceback
                                         
        try:
            with open('error.log', 'w', encoding='utf-8', errors='replace') as f:
                f.write(f"Fatal Error: {e}\n")
                f.write(traceback.format_exc())
        except:
            pass
