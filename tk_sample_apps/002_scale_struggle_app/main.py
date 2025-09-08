from model import VrModel
from view import View

def main():
    """アプリケーションのエントリーポイント"""
    model = VrModel()
    view = View(model)

    # GUIメインループを開始
    view.mainloop()

if __name__ == "__main__":
    main()

