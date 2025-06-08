""" 車両機能の利用可能性を管理するためのモデルクラスです。"""
import threading

class VrVehicleModel:
    """ 車両機能の利用可能性を管理するためのモデルクラス """
    def __init__(self):
        self.notify_behicle_available = None
        self._is_vehicle_available = False

    @property
    def is_vehicle_available(self) -> bool:
        """ 車両が利用可能かどうか """
        return self._is_vehicle_available

    def register_notification_vehicle_available(self, callback: callable):
        """ 機能終了完了コールバック登録 """
        self.notify_behicle_available = callback
        # 車両が利用可能になるまでの遅延をシミュレート
        # ここでは5秒後に車両が利用可能になると仮定
        timer = threading.Timer(5, self.delayed_task)
        timer.start()

    def delayed_task(self):
        """ 車両が利用可能になったことを通知する """
        self._is_vehicle_available = True
        if self.notify_behicle_available:
            self.notify_behicle_available(self._is_vehicle_available)
