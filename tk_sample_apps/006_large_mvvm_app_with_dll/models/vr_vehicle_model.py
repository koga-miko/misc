""" 車両機能の利用可能性を管理するためのモデルクラスです。"""
import ctypes
import os

# DLLをロード
current_file_path = os.path.abspath(__file__)  # 現在の .py ファイルのフルパス
dll_path = os.path.join(os.path.dirname(current_file_path), "VclModDll.dll")
dll = ctypes.CDLL(dll_path)

@ctypes.CFUNCTYPE(None, ctypes.c_int)
def callback_function_from_c(is_available):
    """ Cから呼び出されるコールバック関数 """
    model = VrVehicleModel()
    if model.notify_behicle_available is None:
        return
    model.notify_behicle_available(False if is_available == 0 else True)

class VrVehicleModel:
    """ 車両機能の利用可能性を管理するためのモデルクラス (シングルトン) """
    ### シングルトン化のためのコードの開始位置
    _instance = None  # シングルトンインスタンスを保持

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(VrVehicleModel, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):  # __init__ が複数回呼ばれないようにする

            # VrVehicleModelクラスの純粋な初期化処理（ここはシングルトン化のために一度だけ実行される）
            self.notify_behicle_available = None

            self.initialized = True  # 初期化済みフラグ
    ### シングルトン化のためのコードの終了位置

    @property
    def is_vehicle_available(self) -> bool:
        """ 車両が利用可能かどうか """
        return False if 0 == dll.VclMod_getAvailable() else True

    def register_notification_vehicle_available(self, callback: callable):
        """ 機能終了完了コールバック登録 """
        # コールバック登録
        self.notify_behicle_available = callback
        dll.VclMod_registerUpdatedAvailableCallback(callback_function_from_c)

