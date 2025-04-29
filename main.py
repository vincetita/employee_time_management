import tkinter as tk
from login_gui import BenutzerLoginGUI

# Hauptprogramm
if __name__ == "__main__":
    root = tk.Tk()
    app = BenutzerLoginGUI(root)
    root.mainloop()