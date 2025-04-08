# ファイル名: winner_dialog.py
from PySide6.QtWidgets import QDialog

class WinnerDialog(QDialog):
    def __init__(self, players, pot):
        super().__init__()
        self.setWindowTitle("勝者を選択")
    
    def get_winner(self):
        return 0, 0  # 仮の勝者と金額を返す
