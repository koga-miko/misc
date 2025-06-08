""" VRセッションのViewModelクラス """
import tkinter as tk
from viewmodels.safe_view_updater import SafeViewUpdater
from models.vr_vehicle_model import VrVehicleModel

class VrHelpViewModel(SafeViewUpdater):
    """ViewModelはModelとViewの間を仲介する役割を持つ"""
    def __init__(self, root: tk):
        super().__init__(root)
        self.on_exit_callback = None
        self.model = VrVehicleModel()

        # 車両機能用ヘルプが表示されるかどうかのフラグ
        self._vehicle_available_var = tk.BooleanVar()
        self._vehicle_available_var.set(False)

        # Modelのコールバックを登録
        self.model.register_notification_vehicle_available(self._notify_vehicle_available)

    @property
    def vehicle_available_var(self):
        """車両機能用ヘルプが表示されるかどうかのフラグを取得"""
        return self._vehicle_available_var

    def _notify_vehicle_available(self, is_available: bool):
        """車両が利用可能になったときに呼び出されるコールバック"""
        self.update_view_safety(
            lambda: self._vehicle_available_var.set(is_available),
        )
