# main.py
import tkinter as tk
from controller import ConvexHullController

if __name__ == "__main__":
    root = tk.Tk()
    app = ConvexHullController(root)
    root.mainloop()