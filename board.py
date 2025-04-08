from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout
from PySide6.QtCore import QTimer, Qt
import json
import sys

# カード表示用のユーティリティをインポート
from card_utils import get_card_display

class BoardFrame(QFrame):
    def __init__(self, pot_info, blinds, cards=None, street=None):
        super().__init__()
        self.setFixedSize(600, 140)  # 横長の長方形
        self.setStyleSheet(
            """
            border: 2px solid white;
            padding: 5px;
            background-color: #333;
            color: white;
            """
        )

        # レイアウトを作成
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)  # 外側の余白を少し縮小
        layout.setSpacing(4)  # 項目間の余白を少し縮小

        # 上段: カード5枚
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)  # 上段の余白をゼロに設定
        top_layout.setSpacing(8)  # カード間の余白を少し追加

        # カードラベルを保持するリスト
        self.card_labels = []
        
        # 5枚分のカードラベルを作成
        for i in range(5):
            card_label = QLabel("--")
            card_label.setStyleSheet(
                """
                font-size: 36px; font-weight: bold;  /* 文字を太字に設定 */
                background-color: white; 
                border: 1px solid black;
                padding-top: -20px;  /* 文字を中央に配置 */
                """
            )  # 白抜き背景に色付き文字
            card_label.setAlignment(Qt.AlignCenter)
            card_label.setFixedSize(80, 100)  # カードのサイズを広げる
            card_label.setTextFormat(Qt.PlainText)  # HTMLタグを解釈しない
            top_layout.addWidget(card_label)
            self.card_labels.append(card_label)
        
        # カード情報があれば表示
        if cards:
            self.update_cards(cards)
            
        # ストリート情報は表示しない（ユーザー要望により削除）

        # 下段: PotとBlinds
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)  # 下段の余白をゼロに設定
        bottom_layout.setSpacing(10)  # 項目間の余白を少し追加

        # ポット情報の表示
        pot_text = self.format_pot_display(pot_info)
        pot_label = QLabel(pot_text)
        pot_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        pot_label.setAlignment(Qt.AlignCenter)  # 中央揃え
        bottom_layout.addWidget(pot_label)

        blinds_label = QLabel(f"Blinds: {blinds}")
        blinds_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white;")
        blinds_label.setAlignment(Qt.AlignCenter)  # 中央揃え
        bottom_layout.addWidget(blinds_label)

        # レイアウトをまとめる
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
    
    def update_cards(self, cards):
        """カード情報を更新"""
        # カードがない場合は何もしない
        if not cards:
            return
            
        # デバッグ出力
        print(f"Board cards in update_cards: {cards}")
            
        # カード情報をフォーマット
        formatted_cards = []
        for card in cards:
            # 旧形式から内部形式に変換
            from card_utils import convert_legacy_to_internal, get_colored_card_display
            internal_format = convert_legacy_to_internal(card)
            if internal_format:
                # 内部形式から色付き表示形式に変換
                card_display = get_colored_card_display(internal_format)
                if card_display != "--":
                    formatted_cards.append(card_display)
        
        # デバッグ出力
        print(f"Formatted board cards: {formatted_cards}")
        
        # カードラベルを更新
        for i, label in enumerate(self.card_labels):
            if i < len(formatted_cards):
                card_text = formatted_cards[i]
                label.setText(card_text)
                
                # カードのスートに応じて色を設定
                if "♠" in card_text:
                    label.setStyleSheet(
                        """
                        font-size: 36px; font-weight: bold;
                        background-color: white; color: black;
                        border: 1px solid black;
                        padding-top: -20px;
                        """
                    )
                elif "♦" in card_text:
                    label.setStyleSheet(
                        """
                        font-size: 36px; font-weight: bold;
                        background-color: white; color: #0000CC;
                        border: 1px solid black;
                        padding-top: -20px;
                        """
                    )
                elif "♥" in card_text:
                    label.setStyleSheet(
                        """
                        font-size: 36px; font-weight: bold;
                        background-color: white; color: #CC0000;
                        border: 1px solid black;
                        padding-top: -20px;
                        """
                    )
                elif "♣" in card_text:
                    label.setStyleSheet(
                        """
                        font-size: 36px; font-weight: bold;
                        background-color: white; color: #006600;
                        border: 1px solid black;
                        padding-top: -20px;
                        """
                    )
            else:
                label.setText("--")
                # デフォルトスタイル
                label.setStyleSheet(
                    """
                    font-size: 36px; font-weight: bold;
                    background-color: white; color: black;
                    border: 1px solid black;
                    padding-top: -20px;
                    """
                )
    
    def format_pot_display(self, pot_info):
        """ポット情報を整形して表示用のテキストを生成"""
        # pot_infoはdictで、total, main_pot, side_potsを含む
        if not pot_info.get("side_pots"):
            return f"POT: {pot_info['total']}"
        
        main_pot = pot_info.get("main_pot", 0)
        side_pots = pot_info.get("side_pots", [])
        
        if side_pots:
            # サイドポットの合計を計算
            side_pots_total = sum(pot.get('amount', 0) for pot in side_pots)
            # 要求された形式: "POT: XX (Side XX)"
            return f"POT: {main_pot} (Side {side_pots_total})"
        else:
            return f"POT: {main_pot}"

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker HUD - Board Info")
        self.setGeometry(100, 100, 600, 200)
        self.setStyleSheet("background-color: black;")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_board)
        self.timer.start(1000)

    def update_board(self):
        # 一度消す
        for i in reversed(range(self.layout.count())):
            widget = self.layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)

        try:
            with open("status.json", "r", encoding="utf-8") as f:
                data = json.load(f)
            
            # ポット情報を構造化
            pot_info = {
                "total": data["board"]["pot"],
                "main_pot": data["board"].get("main_pot", data["board"]["pot"]),
                "side_pots": data["board"].get("side_pots", [])
            }
            
            # ブラインド情報を取得
            blinds = data["board"]["blinds"]
            
            # カード情報を取得
            cards = data["board"].get("cards", [])
            
            # カード情報をデバッグ出力
            print(f"Board cards from status.json: {cards}")
            
            # ストリート情報を取得
            street = data["board"].get("street", "Preflop")
            
            # ボードフレームを作成して表示
            frame = BoardFrame(pot_info, blinds, cards, street)
            self.layout.addWidget(frame)
            
            # デバッグ出力
            if cards:
                print(f"Board cards displayed: {cards}")
        except Exception as e:
            print(f"JSON load error: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
