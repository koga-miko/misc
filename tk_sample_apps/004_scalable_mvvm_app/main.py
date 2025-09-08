from model import VrModel
from view import View
from view_model import ViewModel

def main():
    """アプリケーションのエントリーポイント"""
    model = VrModel()
    view_model = ViewModel(model)
    view = View(view_model)

    # GUIメインループを開始
    view.mainloop()

if __name__ == "__main__":
    main()