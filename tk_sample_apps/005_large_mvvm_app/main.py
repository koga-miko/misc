""" VR Top View Application Entry Point"""
import tkinter as tk
from views.vr_app_view import VrAppView

def main():
    """アプリケーションのエントリーポイント"""
    root = tk.Tk()
    VrAppView(root)
    root.mainloop()

if __name__ == "__main__":
    # アプリケーションのエントリーポイントを実行
    main()
