from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QLabel,
    QFrame,
    QPushButton,
    QGridLayout,
    QDialog,
    QSpinBox,
    QInputDialog,
    QComboBox,
    QMessageBox,
    QMenuBar,
    QMenu,
    QMainWindow,
    QFileDialog,
    QGraphicsOpacityEffect,
)
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation, QAbstractAnimation, Property
import json
import sys
import os

# pypokerengineのインポート
from pypokerengine.engine.card import Card
from pypokerengine.engine.deck import Deck
from pypokerengine.engine.hand_evaluator import HandEvaluator
from pypokerengine.engine.game_evaluator import GameEvaluator
from pypokerengine.engine.poker_constants import PokerConstants as Const

POSITIONS = ["UTG", "+1", "LJ", "HJ", "CO", "BU", "SB", "BB"]

# プレイヤー数に応じたポジション順序（BUを基準に時計回りの順序）
POSITIONS_BY_PLAYER_COUNT = {
    3: ["BU", "SB", "BB"],
    4: ["BU", "SB", "BB", "CO"],
    5: ["BU", "SB", "BB", "UTG", "CO"],
    6: ["BU", "SB", "BB", "UTG", "HJ", "CO"],
    7: ["BU", "SB", "BB", "UTG", "LJ", "HJ", "CO"],
    8: ["BU", "SB", "BB", "UTG", "+1", "LJ", "HJ", "CO"]
}
SUITS = ["S", "H", "D", "C"]  # スペード、ハート、ダイヤ、クラブ
RANKS = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K"]

# 基本的なスート表示用のマッピング
SUIT_DISPLAY = {
    "S": "♠", 
    "H": "♥", 
    "D": "♦", 
    "C": "♣"
}

# 基本的なランク表示用のマッピング
RANK_DISPLAY = {
    "A": "A", "14": "A",
    "K": "K", "13": "K",
    "Q": "Q", "12": "Q",
    "J": "J", "11": "J",
    "T": "10", "10": "10",
    "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", "8": "8", "9": "9"
}

def get_suit_symbol(suit):
    """スートを記号に変換する関数（ビットマスクを使用）"""
    # 文字列の場合
    if isinstance(suit, str):
        return SUIT_DISPLAY.get(suit, "?")
    
    # 数値の場合はビットマスクで判定
    # pypokerengineの定義に基づく
    if suit & Card.SPADE:  # 16とのビット演算
        return "♠"
    elif suit & Card.HEART:  # 8とのビット演算
        return "♥"
    elif suit & Card.DIAMOND:  # 4とのビット演算
        return "♦"
    elif suit & Card.CLUB:  # 2とのビット演算
        return "♣"
    else:
        # 未知のスート値の場合はデバッグ出力
        print(f"Unknown suit value: {suit}")
        return "?"

def get_rank_display(rank):
    """ランクを表示用の文字に変換する関数"""
    # 文字列の場合
    if isinstance(rank, str):
        return RANK_DISPLAY.get(rank, rank)
    
    # 数値の場合
    rank_map = {
        14: "A", 13: "K", 12: "Q", 11: "J", 10: "10",
        2: "2", 3: "3", 4: "4", 5: "5", 
        6: "6", 7: "7", 8: "8", 9: "9", 1: "A"  # 1もAとして扱う
    }
    return rank_map.get(rank, str(rank))

def get_card_display(card):
    """カードを人間が読みやすい形式で表示する関数"""
    suit_symbol = get_suit_symbol(card.suit)
    rank_display = get_rank_display(card.rank)
    
    # 表示形式: 「A♠」
    return f"{rank_display}{suit_symbol}"


class CardInputDialog(QDialog):
    def __init__(self, title="カード入力"):
        super().__init__()
        self.setWindowTitle(title)
        layout = QGridLayout()
        
        # スート選択（スペード、ハート、ダイヤ、クラブ）
        self.suit_combo = QComboBox()
        self.suit_combo.addItems([SUIT_DISPLAY[s] for s in SUITS])
        layout.addWidget(QLabel("スート:"), 0, 0)
        layout.addWidget(self.suit_combo, 0, 1)
        
        # 数字選択（A, 2-10, J, Q, K）
        self.rank_combo = QComboBox()
        rank_display = ["A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K"]
        self.rank_combo.addItems(rank_display)
        layout.addWidget(QLabel("数字:"), 1, 0)
        layout.addWidget(self.rank_combo, 1, 1)
        
        # 確定ボタン
        confirm_button = QPushButton("OK")
        confirm_button.clicked.connect(self.accept)
        layout.addWidget(confirm_button, 2, 0, 1, 2)
        
        self.setLayout(layout)
    
    def get_card(self):
        # pypokerengineのCard形式に変換
        suit_map = {"♠": "S", "♥": "H", "♦": "D", "♣": "C"}
        rank_map = {"A": "A", "2": "2", "3": "3", "4": "4", "5": "5", "6": "6", "7": "7", 
                   "8": "8", "9": "9", "10": "T", "J": "J", "Q": "Q", "K": "K"}
        
        suit = suit_map[self.suit_combo.currentText()]
        rank = rank_map[self.rank_combo.currentText()]
        
        # デバッグ出力
        print(f"Selected suit: {self.suit_combo.currentText()} -> {suit}")
        print(f"Selected rank: {self.rank_combo.currentText()} -> {rank}")
        
        # pypokerengineのCard形式で返す
        card = Card.from_str(suit + rank)
        
        # デバッグ出力
        print(f"Created card: {card.suit}{card.rank}")
        
        return card


class BetAmountDialog(QDialog):
    def __init__(self, action_type=""):
        super().__init__()
        self.setWindowTitle(f"Enter Amount for {action_type}")
        layout = QGridLayout()
        self.spinbox = QSpinBox()
        self.spinbox.setRange(0, 1000000)
        layout.addWidget(self.spinbox, 0, 0, 1, 2)
        confirm_button = QPushButton("OK")
        confirm_button.clicked.connect(self.accept)
        layout.addWidget(confirm_button, 1, 0, 1, 2)
        self.setLayout(layout)

    def get_amount(self):
        return self.spinbox.value()


class BlindsDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Set Blinds")
        layout = QGridLayout()
        self.sb_spinbox = QSpinBox()
        self.sb_spinbox.setRange(0, 1000000)
        self.bb_spinbox = QSpinBox()
        self.bb_spinbox.setRange(0, 1000000)
        layout.addWidget(QLabel("SB:"), 0, 0)
        layout.addWidget(self.sb_spinbox, 0, 1)
        layout.addWidget(QLabel("BB:"), 1, 0)
        layout.addWidget(self.bb_spinbox, 1, 1)
        confirm_button = QPushButton("OK")
        confirm_button.clicked.connect(self.accept)
        layout.addWidget(confirm_button, 2, 0, 1, 2)
        self.setLayout(layout)

    def get_blinds(self):
        return self.sb_spinbox.value(), self.bb_spinbox.value()


class WinnerDialog(QDialog):
    def __init__(self, player_names, pot_type, pot_amount):
        super().__init__()
        self.setWindowTitle(f"Winner for {pot_type} (${pot_amount})")
        self.resize(800, 400)  # ウィンドウサイズを4倍に拡大

        layout = QGridLayout()
        self.combo_box = QComboBox()
        self.combo_box.addItems(player_names)
        layout.addWidget(self.combo_box, 0, 0, 1, 2)

        confirm_button = QPushButton("OK")
        confirm_button.clicked.connect(self.accept)
        layout.addWidget(confirm_button, 1, 0, 1, 2)

        self.setLayout(layout)

    def get_winner(self):
        return self.combo_box.currentText()


class RaiseAmountDialog(QDialog):
    def __init__(self, bb_value):
        super().__init__()
        self.setWindowTitle("Raise Amount")
        layout = QGridLayout()

        # BBの何倍かを選択するボタン
        self.bb_value = bb_value
        self.raise_amount = 0

        self.x2_button = QPushButton("x2")
        self.x2_button.clicked.connect(lambda: self.set_raise_amount(2))
        layout.addWidget(self.x2_button, 0, 0)

        self.x2_5_button = QPushButton("x2.5")
        self.x2_5_button.clicked.connect(lambda: self.set_raise_amount(2.5))
        layout.addWidget(self.x2_5_button, 0, 1)

        self.x3_button = QPushButton("x3")
        self.x3_button.clicked.connect(lambda: self.set_raise_amount(3))
        layout.addWidget(self.x3_button, 0, 2)

        # 数値入力フィールド
        self.spinbox = QSpinBox()
        self.spinbox.setRange(0, 1000000)
        layout.addWidget(self.spinbox, 1, 0, 1, 3)

        # OKボタン
        confirm_button = QPushButton("OK")
        confirm_button.clicked.connect(self.accept)
        layout.addWidget(confirm_button, 2, 0, 1, 3)

        self.setLayout(layout)

    def set_raise_amount(self, multiplier):
        """BBの何倍かを計算して設定"""
        self.spinbox.setValue(int(self.bb_value * multiplier))

    def get_amount(self):
        """選択されたレイズ額を取得"""
        return self.spinbox.value()


# pypokerengineのPayInfoクラスと互換性を持たせるためのアダプタクラス
class PlayerPayInfo:
    FOLDED = 0
    ALLIN = 1
    PAY_TILL_END = 2
    
    def __init__(self, player):
        self.player = player
        self.amount = 0
        self.status = self.PAY_TILL_END
        
    def update_by_pay(self, amount):
        self.amount += amount
        
    def update_to_fold(self):
        self.status = self.FOLDED
        
    def update_to_allin(self):
        self.status = self.ALLIN
        
    def serialize(self):
        return [self.amount, self.status]
        
    @classmethod
    def deserialize(cls, serial, player):
        pay_info = cls(player)
        pay_info.amount = serial[0]
        pay_info.status = serial[1]
        return pay_info


class PotManager:
    def __init__(self, players):
        self.players = players
        self.pot = 0
        self.bb = 0  # ビッグブラインドの初期値を追加
        self.side_pots = []  # サイドポットのリスト
        self.main_pot = 0  # メインポット

    def get_highest_raise(self):
        return max(player.current_bet for player in self.players)

    def collect_bets(self):
        """すべてのプレイヤーの current_bet を一度回収し、正しいサイドポット構造を作成"""
        # 現在のポット額を保存
        current_pot = self.pot
        current_main_pot = self.main_pot
        current_side_pots = self.side_pots.copy() if self.side_pots else []
        
        # デバッグ出力（ベット回収前）
        print(f"collect_bets - Before collecting bets - Current pot: {current_pot}")
        print(f"collect_bets - Before collecting bets - Current main pot: {current_main_pot}")
        print(f"collect_bets - Before collecting bets - Current side pots: {[p['amount'] for p in current_side_pots] if current_side_pots else []}")
        
        # プレイヤーのベットを回収し、pay_infoを更新
        total_collected_bets = 0
        for player in self.players:
            collected_bet = player.clear_action_and_return_bet()
            total_collected_bets += collected_bet
            if collected_bet > 0:
                player.pay_info.update_by_pay(collected_bet)
            
            # Foldしているプレイヤーのステータスを更新
            if player.action_display.text() == "Fold":
                player.pay_info.update_to_fold()
            
            # All-inしているプレイヤーのステータスを更新
            if "All-in" in player.action_display.text():
                player.pay_info.update_to_allin()
        
        # デバッグ出力（ベット回収後）
        print(f"collect_bets - Total collected bets: {total_collected_bets}")
        
        # 回収したベットがない場合は、現在のポット情報を維持
        if total_collected_bets <= 0:
            # デバッグ出力（ポット維持）
            print(f"collect_bets - No bets to collect, maintaining current pot")
            
            # pay_infoをリセット（オールインプレイヤーは除く）
            for player in self.players:
                player.pay_info.amount = 0
                if player.pay_info.status != PlayerPayInfo.FOLDED and player.pay_info.status != PlayerPayInfo.ALLIN:
                    player.pay_info.status = PlayerPayInfo.PAY_TILL_END
            
            # デバッグ出力
            print(f"collect_bets - Pot: {self.pot}")
            print(f"collect_bets - Main pot: {self.main_pot}")
            print(f"collect_bets - Side pots: {[p['amount'] for p in self.side_pots]}")
            
            return self.pot
        
        # pypokerengineのGameEvaluatorを使用してポットを計算
        pots = GameEvaluator.create_pot(self.players)
        
        # 新しいポット情報
        new_pot = sum(pot["amount"] for pot in pots)
        
        # 既存のポットに新しいポットを加算
        self.pot = current_pot + new_pot
        
        # サイドポット情報を更新
        self.side_pots = []
        for i, pot in enumerate(pots):
            if i == 0:  # 最初のポットをメインポットとして扱う
                self.main_pot = current_main_pot + pot["amount"]
            
            self.side_pots.append({
                "amount": pot["amount"] + (current_side_pots[i]["amount"] if i < len(current_side_pots) else 0),
                "players_in_pot": pot["eligibles"],
                "active_players": [p for p in pot["eligibles"] if p.pay_info.status != PlayerPayInfo.FOLDED]
            })
        
        # pay_infoをリセット（オールインプレイヤーは除く）
        for player in self.players:
            player.pay_info.amount = 0
            if player.pay_info.status != PlayerPayInfo.FOLDED and player.pay_info.status != PlayerPayInfo.ALLIN:
                player.pay_info.status = PlayerPayInfo.PAY_TILL_END
        
        # デバッグ出力
        print(f"collect_bets - Pot: {self.pot}")
        print(f"collect_bets - Main pot: {self.main_pot}")
        print(f"collect_bets - Side pots: {[p['amount'] for p in self.side_pots]}")
        
        return self.pot

    def reset_pot(self):
        self.pot = 0
        self.side_pots = []
        self.main_pot = 0


class PlayerControlFrame(QFrame):
    def __init__(self, player_name, position, pot_manager, central_manager):
        super().__init__()
        self.pot_manager = pot_manager
        self.central_manager = central_manager
        
        # 固定サイズを大きく設定（横幅を5px大きく）
        self.setFixedSize(295, 295)
        
        self.setStyleSheet(
            "border: 1px solid white; padding: 5px; background-color: #333; color: white;"
        )
        
        # アニメーション用の設定
        self._opacity = 1.0
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity_effect)
        
        # pay_info属性を初期化
        self.pay_info = PlayerPayInfo(self)
        
        # ホールカード
        self.cards = []
        
        # 表示状態
        self.visible = True

        layout = QGridLayout()

        # 1行目: 左側にPlayer名、ポジション、スタック、右上にカード表示
        # 左側のレイアウト
        top_left_layout = QGridLayout()
        
        # Player名を短縮（P1, P2, ...）
        short_name = player_name.replace("Player ", "P")
        self.default_name_label = QLabel(short_name)  # P〇（目印として使用）
        self.default_name_label.setFixedHeight(30)  # 高さを小さく
        top_left_layout.addWidget(self.default_name_label, 0, 0)

        self.position_label = QLabel(position)
        self.position_label.setStyleSheet(
            "background-color: white; color: black; padding: 3px; font-weight: bold;"
        )
        self.position_label.setFixedHeight(30)  # 高さを小さく
        top_left_layout.addWidget(self.position_label, 0, 1)

        self.stack_label = QLabel("Stack: 0")
        self.stack_label.setStyleSheet("font-weight: bold; font-size: 16px;")  # フォントサイズを大きく
        self.stack_label.setAlignment(Qt.AlignCenter)
        self.stack_label.setFixedHeight(30)  # 高さを大きく
        top_left_layout.addWidget(self.stack_label, 0, 2)
        self.stack_value = 0

        self.stack_label.mousePressEvent = (
            self.set_stack
        )  # スタックをクリックで変更可能
        
        # 右上にカード表示（横幅を2/3に縮小）
        self.card_button = QPushButton("Set Hand")
        self.card_button.clicked.connect(self.input_cards)
        self.card_button.setStyleSheet("font-size: 16px; font-weight: bold;")
        self.card_button.setFixedWidth(100)  # 横幅を固定
        self.card_button.setFixedHeight(40)  # 高さを固定
        
        # 1行目のレイアウトを追加
        top_layout = QGridLayout()
        top_layout.addLayout(top_left_layout, 0, 0, 1, 4)  # 左側のレイアウトを広げる
        top_layout.addWidget(self.card_button, 0, 4, 1, 2)  # カードボタンの位置を調整
        layout.addLayout(top_layout, 0, 0, 1, 6)

        # 2行目: Set Nameボタン（高さを小さく）
        self.name_button = QPushButton("Set Name")  # Set Nameボタン
        self.name_button.clicked.connect(self.change_name)
        self.name_button.setFixedHeight(30)  # 高さを小さく
        layout.addWidget(self.name_button, 1, 0, 1, 6)

        # アクションボタンの設定（表示名と機能のマッピング）
        self.actions = {
            "Fold": self.handle_fold,
            "Call": self.handle_call,
            "Bet": lambda: self.get_amount_and_set_action("Bet"),
            "Check": self.handle_check,
            "Raise": lambda: self.get_amount_and_set_action("Raise"),
            "Allin": self.handle_all_in,  # All-in から Allin に変更
        }

        # 3-4行目: アクションボタン（固定サイズに設定、2行に分ける）
        # 1行目（3行目）: Fold, Call, Bet
        first_row_actions = ["Fold", "Call", "Bet"]
        for i, action in enumerate(first_row_actions):
            button = QPushButton(action)
            button.setStyleSheet("font-size: 20px; padding: 15px; font-weight: bold;")  # ボタンをより大きく、太字に
            button.setFixedWidth(90)  # 横幅を固定
            button.setFixedHeight(70)  # 高さを固定
            button.clicked.connect(self.actions[action])
            layout.addWidget(button, 2, i*2, 1, 2)  # 横に2つ分のスペースを使用
        
        # 2行目（4行目）: Check, Raise, Allin
        second_row_actions = ["Check", "Raise", "Allin"]
        for i, action in enumerate(second_row_actions):
            button = QPushButton(action)
            button.setStyleSheet("font-size: 20px; padding: 15px; font-weight: bold;")  # ボタンをより大きく、太字に
            button.setFixedWidth(90)  # 横幅を固定
            button.setFixedHeight(70)  # 高さを固定
            button.clicked.connect(self.actions[action])
            layout.addWidget(button, 3, i*2, 1, 2)  # 横に2つ分のスペースを使用

        # 最下段: アクション表示
        self.action_display = QLabel("")
        self.action_display.setStyleSheet(
            "background-color: white; color: black; padding: 4px; border: 1px solid black; font-size: 16px; font-weight: bold;"
        )
        self.action_display.setAlignment(Qt.AlignCenter)
        self.action_display.setMinimumHeight(30)
        layout.addWidget(self.action_display, 4, 0, 1, 6)
        
        # エクイティ表示は削除（非表示）
        self.equity_label = QLabel("Equity: ---%")
        self.equity_label.setVisible(False)

        self.current_bet = 0
        self.forced_blind_bet = 0
        self.cards = []  # プレイヤーのカード

        self.setLayout(layout)
        
    # 不透明度のプロパティを定義（アニメーション用）
    def get_opacity(self):
        return self._opacity

    def set_opacity(self, opacity):
        self._opacity = opacity
        self.opacity_effect.setOpacity(opacity)

    opacity = Property(float, get_opacity, set_opacity)

    # ハイライトメソッド（点灯のみ、点滅なし）
    def highlight_action(self, highlight=True):
        if highlight:
            # 枠だけを濃い黄色に設定（点滅なし）
            self.setStyleSheet(
                """
                border: 3px solid #FFCC00;
                background-color: #333;
                color: white;
                """
            )
        else:
            self.setStyleSheet(
                """
                border: 1px solid white;
                background-color: #333;
                color: white;
                """
            )
            # 不透明度を元に戻す（念のため）
            self.set_opacity(1.0)

    def clear_action_and_return_bet(self):
        """現在のベット額を返し、アクションをリセット。ただしFoldとAll-inは残す"""
        returned_bet = self.current_bet  # 現在のベット額を保持
        self.current_bet = 0  # ベット額をリセット
        self.forced_blind_bet = 0  # 強制ブラインドもリセット

        # FoldとAll-in以外のアクションをリセット
        action_text = self.action_display.text()
        if action_text != "Fold" and "All-in" not in action_text:
            self.action_display.setText("")  # アクションをリセット

        return returned_bet

    def update_position(self, position, sb=0, bb=0):
        """プレイヤーのポジションを更新"""
        self.position_label.setText(position)
        
        # アクション表示を明示的にリセット（All-inを含む全てのアクション）
        self.action_display.setText("")
        
        # ベット関連の値をリセット
        self.current_bet = 0
        self.forced_blind_bet = 0

        # SBとBBの場合、スタックを減らして表示を更新
        if position == "SB":
            self.set_action_label(f"SB {sb}")
            self.current_bet = sb
            self.forced_blind_bet = sb
            self.stack_value -= sb
        elif position == "BB":
            self.set_action_label(f"BB {bb}")
            self.current_bet = bb
            self.forced_blind_bet = bb
            self.stack_value -= bb

        # スタック表示を更新
        self.update_stack_display()

    def handle_call(self):
        """Callアクションを処理"""
        # デバッグ出力（Call前）
        print(f"handle_call - Before Call - Stack: {self.stack_value}, Current bet: {self.current_bet}")
        
        # 最高ベット額を取得
        highest_bet = self.pot_manager.get_highest_raise()
        
        # 差額を計算（最高ベット額との差）
        diff = highest_bet - self.current_bet
        diff = max(diff, 0)  # 負の値にならないようにする
        diff = min(diff, self.stack_value)  # スタック以上にならないようにする
        
        # スタックを減らし、ベット額を増やす
        self.stack_value -= diff
        self.current_bet += diff
        
        # アクション表示を更新
        self.action_display.setText(f"Call {self.current_bet}")
        
        # スタック表示を更新
        self.update_stack_display()
        
        # デバッグ出力（Call後）
        print(f"handle_call - After Call - Stack: {self.stack_value}, Current bet: {self.current_bet}")
        
        # スタックが0になった場合はAll-inステータスに更新
        if self.stack_value == 0:
            self.pay_info.update_to_allin()
            print(f"handle_call - Player is now All-in")
        
        # 状態を履歴に保存
        self.central_manager.save_state_to_history()
        
        # 次のプレイヤーに移動
        self.central_manager.move_to_next_player()
        
        print(f"handle_call - Call action completed for {self.name_button.text() or self.default_name_label.text()}")

    def handle_all_in(self):
        """All-inアクションを処理"""
        # デバッグ出力（All-in前）
        print(f"handle_all_in - Before All-in - Stack: {self.stack_value}, Current bet: {self.current_bet}")
        
        # All-in額を計算（現在のスタック + 現在のベット額）
        amount = self.stack_value + self.current_bet
        
        # アクション表示を更新
        self.action_display.setText(f"All-in {amount}")
        
        # スタックを0に、ベット額をAll-in額に設定
        self.stack_value = 0
        self.current_bet = amount
        
        # スタック表示を更新
        self.update_stack_display()
        
        # デバッグ出力（All-in後）
        print(f"handle_all_in - After All-in - Stack: {self.stack_value}, Current bet: {self.current_bet}")
        
        # 状態を履歴に保存
        self.central_manager.save_state_to_history()
        
        # pay_infoのステータスをAll-inに更新
        self.pay_info.update_to_allin()
        
        # 次のプレイヤーに移動
        self.central_manager.move_to_next_player()
        
        print(f"handle_all_in - All-in action completed for {self.name_button.text() or self.default_name_label.text()}")

    def handle_check(self):
        """Checkアクションを処理"""
        # デバッグ出力（Check前）
        print(f"handle_check - Before Check - Stack: {self.stack_value}, Current bet: {self.current_bet}")
        
        # アクション表示を更新
        self.action_display.setText("Check")
        
        # デバッグ出力（Check後）
        print(f"handle_check - After Check - Stack: {self.stack_value}, Current bet: {self.current_bet}")
        
        # 状態を履歴に保存
        self.central_manager.save_state_to_history()
        
        # 次のプレイヤーに移動
        self.central_manager.move_to_next_player()
        
        print(f"handle_check - Check action completed for {self.name_button.text() or self.default_name_label.text()}")

    def handle_fold(self):
        """Foldアクションを処理"""
        # デバッグ出力（Fold前）
        print(f"handle_fold - Before Fold - Stack: {self.stack_value}, Current bet: {self.current_bet}")
        
        # Foldしても、current_betはそのまま保持する（ポット計算時に回収される）
        # ただし、アクション表示はFoldに設定
        self.action_display.setText("Fold")  # アクション表示をFoldに設定
        
        # エクイティ表示をFoldに更新
        self.equity_label.setText("Equity: Fold")
        self.equity_label.setStyleSheet("color: red; font-weight: bold;")
        
        # スタック表示を更新
        self.update_stack_display()
        
        # デバッグ出力（Fold後）
        print(f"handle_fold - After Fold - Stack: {self.stack_value}, Current bet: {self.current_bet}")
        
        # pay_infoのステータスをFoldに更新
        self.pay_info.update_to_fold()
        
        # 状態を履歴に保存
        self.central_manager.save_state_to_history()
        
        # 次のプレイヤーに移動
        self.central_manager.move_to_next_player()
        
        print(f"handle_fold - Fold action completed for {self.name_button.text() or self.default_name_label.text()}")

    def get_amount_and_set_action(self, action_type):
        """ベットやレイズの金額を取得してアクションを設定"""
        # デバッグ出力（アクション前）
        print(f"get_amount_and_set_action - Before {action_type} - Stack: {self.stack_value}, Current bet: {self.current_bet}")
        
        # ダイアログを表示
        if action_type == "Raise":
            dialog = RaiseAmountDialog(self.pot_manager.bb)  # BBの値を渡す
        else:
            dialog = BetAmountDialog(action_type)

        if dialog.exec() == QDialog.Accepted:
            # 金額を取得
            amount = dialog.get_amount()
            
            # 差額を計算（現在のベット額との差）
            diff = amount - self.current_bet
            diff = max(diff, 0)  # 負の値にならないようにする
            diff = min(diff, self.stack_value)  # スタック以上にならないようにする
            
            # スタックを減らし、ベット額を増やす
            self.stack_value -= diff
            self.current_bet += diff
            
            # アクション表示を更新
            self.action_display.setText(f"{action_type} {self.current_bet}")
            
            # スタック表示を更新
            self.update_stack_display()
            
            # デバッグ出力（アクション後）
            print(f"get_amount_and_set_action - After {action_type} - Stack: {self.stack_value}, Current bet: {self.current_bet}")
            
            # スタックが0になった場合はAll-inステータスに更新
            if self.stack_value == 0:
                self.pay_info.update_to_allin()
                print(f"get_amount_and_set_action - Player is now All-in")
            
            # 状態を履歴に保存
            self.central_manager.save_state_to_history()
            
            # 次のプレイヤーに移動
            self.central_manager.move_to_next_player()
            
            print(f"get_amount_and_set_action - {action_type} action completed for {self.name_button.text() or self.default_name_label.text()}")

    def set_action_label(self, action):
        self.action_display.setText(action)
        self.current_bet = 0

    def change_name(self):
        """Set Nameボタンのテキストを変更"""
        new_name, ok = QInputDialog.getText(
            self, "Set Player Name", "Enter player name:"
        )
        if ok and new_name:
            self.name_button.setText(new_name)  # Set Nameボタンのテキストを変更
            self.central_manager.save_state_to_history()  # 状態を履歴に保存

    def set_stack(self, event=None):
        amount, ok = QInputDialog.getInt(
            self, "Set Stack", "Enter stack amount:", self.stack_value, 0, 1000000
        )
        if ok:
            self.stack_value = amount
            self.update_stack_display()
            self.central_manager.save_state_to_history()  # 状態を履歴に保存

    def update_stack_display(self):
        self.stack_label.setText(f"{self.stack_value}")
        
    def input_cards(self):
        """プレイヤーのカードを入力"""
        # 2枚のカードを入力
        cards = []
        for i in range(2):
            dialog = CardInputDialog(f"プレイヤーカード {i+1}/2")
            if dialog.exec() == QDialog.Accepted:
                card = dialog.get_card()
                cards.append(card)
                # デバッグ出力（人間が読みやすい形式で）
                card_display = get_card_display(card)
                print(f"Card {i+1}: {card_display} (内部表現: suit={card.suit}, rank={card.rank})")
            else:
                return  # キャンセルされた場合は中断
        
        self.cards = cards
        
        # カード表示を更新（1枚ずつ処理）
        from card_utils import get_colored_card_display
        card_displays = []
        for card in self.cards:
            card_display = get_colored_card_display(card)
            card_displays.append(card_display)
        
        # カードボタンのテキストを更新（シンプルに表示）
        self.card_button.setText(f"{' '.join(card_displays)}")
        
        # カードボタンのスタイルを更新（大きく表示）
        self.card_button.setStyleSheet("font-size: 18px; padding: 10px; font-weight: bold;")
        
        # デバッグ出力（人間が読みやすい形式で）
        debug_cards = [get_card_display(card) for card in self.cards]
        print(f"Player cards: {debug_cards}")
        
        # エクイティを計算して表示
        self.update_equity()
        
        # 全プレイヤーのエクイティを更新（他のプレイヤーのエクイティも変わるため）
        self.central_manager.calculate_all_equities(show_dialog=False)
        
        # 状態を履歴に保存
        self.central_manager.save_state_to_history()
        
    def update_equity(self):
        """エクイティを計算して表示"""
        # フォールドしている場合は計算しない
        if self.action_display.text() == "Fold":
            self.equity_label.setText("Equity: Fold")
            self.equity_label.setStyleSheet("color: red; font-weight: bold;")
            return
            
        if not self.cards or len(self.cards) != 2:
            self.equity_label.setText("Equity: ---%")
            return
            
        # 中央管理クラスからボードカードを取得
        board_cards = self.central_manager.board_cards
        
        # フロップが開くまではエクイティを表示しない
        if not board_cards or len(board_cards) < 3:
            self.equity_label.setText("Equity: ---%")
            return
            
        # アクティブなプレイヤー数を取得（自分を除く）
        active_players = len([p for p in self.central_manager.players if p.action_display.text() != "Fold" and p != self])
        
        # エクイティを計算
        equity = self.central_manager.calculate_equity(self.cards, board_cards, active_players)
        
        # エクイティを表示
        self.equity_label.setText(f"Equity: {equity:.1f}%")
        self.equity_label.setStyleSheet("color: yellow; font-weight: bold;")
    def set_frame_size(self, width, height):
        self.setFixedSize(width, height)



class CentralManager(QWidget):
    def __init__(self, pot_manager, players):
        super().__init__()
        self.pot_manager = pot_manager
        self.players = players
        self.sb = 0
        self.bb = 0
        self.bu_position = 0  # 初期値は0
        self.current_action_index = 0
        self.board_cards = []  # ボードカード
        
        # 自動保存用のパス
        self.auto_save_path = "status.json"
        
        # UNDO機能のための状態履歴
        self.state_history = []  # 状態履歴を保持するリスト
        self.history_index = -1  # 現在の履歴インデックス
        self.max_history = 10    # 保持する履歴の最大数

        layout = QGridLayout()
        self.setLayout(layout)

        # スタイル設定
        button_style = "font-size: 16px; padding: 10px; font-weight: bold;"

        # 1行目: Blinds, POT, Street表示（細いラベル）
        label_style = "font-size: 14px; font-weight: bold; padding: 2px; min-height: 20px; max-height: 20px;"
        
        self.blinds_label = QLabel("Blinds: 0/0")
        self.blinds_label.setStyleSheet(label_style)
        self.blinds_label.setFixedWidth(120)
        
        self.pot_label = QLabel("POT: 0")
        self.pot_label.setStyleSheet(label_style)
        self.pot_label.setFixedWidth(120)
        
        self.street_label = QLabel("Street: Preflop")
        self.street_label.setStyleSheet(label_style + "color: Black;")
        self.street_label.setFixedWidth(120)
        
        # 1行目のラベルを水平に配置
        header_layout = QGridLayout()
        header_layout.addWidget(self.blinds_label, 0, 0)
        header_layout.addWidget(self.pot_label, 0, 1)
        header_layout.addWidget(self.street_label, 0, 2)
        header_layout.setColumnStretch(3, 1)  # 右側の余白を伸ばす
        
        # ヘッダーレイアウトをメインレイアウトに追加
        layout.addLayout(header_layout, 0, 0, 1, 6)
        
        # 2行目: ボードカード表示
        self.board_cards_label = QLabel("Board: ")
        self.board_cards_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 2px; min-height: 20px; max-height: 20px;")
        self.board_cards_label.setTextFormat(Qt.PlainText)  # HTMLタグを解釈しない
        layout.addWidget(self.board_cards_label, 1, 0, 1, 6)
        
        # 3行目: 正方形のボタン (Next Hand, Next Street, UNDO)
        square_button_style = """
            font-size: 16px; 
            font-weight: bold; 
            padding: 10px; 
            min-width: 120px; 
            max-width: 120px; 
            min-height: 120px; 
            max-height: 120px;
        """
        
        next_hand_btn = QPushButton("Next Hand")
        next_hand_btn.setStyleSheet(square_button_style)
        next_hand_btn.clicked.connect(self.next_hand)
        
        next_street_btn = QPushButton("Next Street")
        next_street_btn.setStyleSheet(square_button_style)
        next_street_btn.clicked.connect(self.next_street)
        
        undo_btn = QPushButton("UNDO")
        undo_btn.setStyleSheet(square_button_style + "background-color: #ff9900; color: black;")
        undo_btn.clicked.connect(self.undo)
        
        # ボタンを水平に配置
        button_layout = QGridLayout()
        button_layout.addWidget(next_hand_btn, 0, 0)
        button_layout.addWidget(next_street_btn, 0, 1)
        button_layout.addWidget(undo_btn, 0, 2)
        button_layout.setColumnStretch(3, 1)  # 右側の余白を伸ばす
        
        # ボタンレイアウトをメインレイアウトに追加
        layout.addLayout(button_layout, 2, 0, 1, 6)
        
        # 非表示ボタン（メニューからアクセス可能）
        self.blinds_btn = QPushButton("Set Blinds")
        self.blinds_btn.clicked.connect(self.set_blinds)
        self.blinds_btn.setVisible(False)
        
        self.stacks_btn = QPushButton("Set All Stacks")
        self.stacks_btn.clicked.connect(self.set_all_stacks)
        self.stacks_btn.setVisible(False)
        
        self.set_bu_btn = QPushButton("Set BU")
        self.set_bu_btn.clicked.connect(self.set_bu)
        self.set_bu_btn.setVisible(False)
        
        self.export_btn = QPushButton("Export JSON")
        self.export_btn.clicked.connect(self.export_json)
        self.export_btn.setVisible(False)
        
        self.board_cards_btn = QPushButton("ボードカード入力")
        self.board_cards_btn.clicked.connect(self.input_board_cards)
        self.board_cards_btn.setVisible(False)
        
        self.equity_btn = QPushButton("エクイティ計算")
        self.equity_btn.clicked.connect(self.calculate_all_equities)
        self.equity_btn.setVisible(False)
        
        self.players_count_btn = QPushButton("プレイヤー数設定")
        self.players_count_btn.clicked.connect(self.set_players_count)
        self.players_count_btn.setVisible(False)

        # 自動更新タイマー：1秒ごとにauto_save_pathに更新
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.auto_save)
        self.timer.start(1000)
        
        # 初期状態で次のプレイヤーをハイライト
        self.highlight_next_player()

    def set_blinds(self):
        dialog = BlindsDialog()
        if dialog.exec() == QDialog.Accepted:
            self.sb, self.bb = dialog.get_blinds()
            self.pot_manager.bb = self.bb  # PotManagerにBBを設定
            self.blinds_label.setText(f"Blinds: {self.sb}/{self.bb}")
            self.update_positions()
            self.save_state_to_history()  # 状態を履歴に保存

    def set_all_stacks(self):
        amount, ok = QInputDialog.getInt(
            self, "Set All Stacks", "Enter stack amount:", 1000, 0, 1000000
        )
        if ok:
            for p in self.players:
                # SBとBBのプレイヤーはブラインド額を引いた値に設定
                if p.position_label.text() == "SB":
                    p.stack_value = amount - self.sb
                elif p.position_label.text() == "BB":
                    p.stack_value = amount - self.bb
                else:
                    p.stack_value = amount
                p.update_stack_display()
            self.save_state_to_history()  # 状態を履歴に保存

    def set_bu(self):
        """SET BUボタンの処理"""
        player_names = [
            p.name_button.text() or p.default_name_label.text() for p in self.players
        ]
        # ダミーのpot_typeとpot_amountを渡す
        dialog = WinnerDialog(player_names, "Set BU", 0)
        if dialog.exec() == QDialog.Accepted:
            selected_player = dialog.get_winner()
            for i, p in enumerate(self.players):
                player_name = p.name_button.text() or p.default_name_label.text()
                if player_name == selected_player:
                    self.bu_position = i  # 選択されたプレイヤーをBUに設定
                    break
            self.update_positions()  # ポジションを再割り振り
            self.save_state_to_history()  # 状態を履歴に保存

    def next_hand(self):
        """次のハンドに進む（メインポット＋サイドポット配布対応）"""
        # 状態を履歴に保存（操作前）
        self.save_state_to_history()
        
        # ベットを回収してポットを計算
        pot = self.pot_manager.collect_bets()
        
        # デバッグ出力
        print(f"Next Hand - Pot after collect_bets: {pot}")
        print(f"Next Hand - self.pot_manager.pot: {self.pot_manager.pot}")
        print(f"Next Hand - Main pot: {self.pot_manager.main_pot}")
        print(f"Next Hand - Side pots: {[p['amount'] for p in self.pot_manager.side_pots]}")

        # サイドポットの表示を更新
        self.update_pot_display()

        # 全てのポットが0の場合は配布をスキップ
        total_pot = sum(pot["amount"] for pot in self.pot_manager.side_pots)
        if total_pot <= 0:
            print(f"Next Hand - Skipping pot distribution because total_pot is {total_pot}")
            # ポジションを更新して次のハンドへ
            self.bu_position = (self.bu_position + 1) % len(self.players)
            
            # プリフロップのアクションプレイヤーを設定（BBの次のプレイヤー）
            # プレイヤー数に応じて、BBの次のプレイヤーの位置を計算
            visible_players = [p for p in self.players if p.visible]
            num_visible_players = len(visible_players)
            
            # BBの次のプレイヤーからアクション開始
            # BUの位置から3つ先（SB, BB, BBの次）
            self.current_action_index = (self.bu_position + 3) % len(self.players)
            
            # UTGがFoldまたはAll-inの場合を考慮して、実際に可能なプレイヤーを探す
            while self.players[self.current_action_index].action_display.text() in ["Fold", "All-in"]:
                self.current_action_index = (self.current_action_index + 1) % len(self.players)
                
            self.update_positions()
            self.highlight_next_player()  # ⭐ ハイライトを更新
            self.export_json()
            return

        # 配布するポット（メイン＋サイド層）
        pots_to_distribute = []
        if self.pot_manager.main_pot > 0:
            # メインポットを追加（side_pots[0]がメインポット）
            if self.pot_manager.side_pots:
                pots_to_distribute.append(self.pot_manager.side_pots[0])
            else:
                # メインポットのみの場合
                pots_to_distribute.append({
                    "amount": self.pot_manager.main_pot,
                    "players_in_pot": self.players,
                    "active_players": [p for p in self.players if p.action_display.text() != "Fold"]
                })
                
        # サイドポットを追加（存在する場合）
        if len(self.pot_manager.side_pots) > 1:
            pots_to_distribute.extend(self.pot_manager.side_pots[1:])
            
        # ポットがない場合でもダミーのポットを作成して勝者を選択
        if not pots_to_distribute and self.pot_manager.pot > 0:
            pots_to_distribute = [
                {
                    "amount": self.pot_manager.pot,
                    "players_in_pot": self.players,
                    "active_players": [
                        p for p in self.players if p.action_display.text() != "Fold"
                    ],
                }
            ]

        for i, pot_info in enumerate(pots_to_distribute):
            pot_amount = pot_info["amount"]
            pot_type = "Main Pot" if i == 0 else f"Side Pot {i}"

            # ポット額が0の場合はスキップ
            if pot_amount <= 0:
                continue

            # その層に参加しているアクティブプレイヤーを対象（Foldしていないプレイヤー）
            eligible_players = pot_info.get("active_players", [])

            # アクティブプレイヤーがいない場合は、その層に参加している全プレイヤーを対象
            if not eligible_players:
                eligible_players = pot_info["players_in_pot"]

            # 名前が設定されていない場合はデフォルト名を使用
            player_names = []
            for p in eligible_players:
                if p.name_button.text():
                    player_names.append(p.name_button.text())
                else:
                    player_names.append(p.default_name_label.text())

            # プレイヤーがいない場合は全プレイヤーを対象にする
            if not player_names:
                player_names = [
                    p.name_button.text() or p.default_name_label.text()
                    for p in self.players
                ]
                eligible_players = self.players

            # 勝者選択ダイアログ
            dialog = WinnerDialog(player_names, pot_type, pot_amount)
            if dialog.exec() == QDialog.Accepted:
                winner = dialog.get_winner()
                # 勝者を見つけてポットを配布
                winner_found = False
                for p in eligible_players:
                    player_name = p.name_button.text() or p.default_name_label.text()
                    if player_name == winner:
                        p.stack_value += pot_amount
                        p.update_stack_display()
                        winner_found = True
                        break

                # 勝者が見つからない場合（通常は発生しないはず）
                if not winner_found and self.players:
                    # 最初のプレイヤーにポットを与える
                    self.players[0].stack_value += pot_amount
                    self.players[0].update_stack_display()

        # ポットをリセット
        self.pot_manager.reset_pot()
        self.pot_label.setText("POT: 0")
        
        # ボードカードをリセット
        self.board_cards = []
        self.update_board_display()
        
        # ストリート表示を更新
        self.street_label.setText("Street: Preflop")
        
        # 各プレイヤーのカード情報とアクション表示をリセット
        for p in self.players:
            if hasattr(p, 'cards'):
                p.cards = []
            if hasattr(p, 'card_button'):
                p.card_button.setText("Set Hand")
            if hasattr(p, 'equity_label'):
                p.equity_label.setText("Equity: ---%")
                p.equity_label.setStyleSheet("color: yellow; font-weight: bold;")
            # アクション表示を明示的にリセット（All-inを含む全てのアクション）
            p.action_display.setText("")

        # ボタンポジションを更新
        self.bu_position = (self.bu_position + 1) % len(self.players)
        
        # プリフロップのアクションプレイヤー（最初にアクションするのはUTG）
        self.current_action_index = (self.bu_position + 3) % len(self.players)
        
        # UTGがFoldまたはAll-inの場合を考慮して、実際に可能なプレイヤーを探す
        while self.players[self.current_action_index].action_display.text() in ["Fold", "All-in"]:
            self.current_action_index = (self.current_action_index + 1) % len(self.players)
            
        self.update_positions()
        self.highlight_next_player()  # 次のプレイヤーをハイライト
        self.auto_save()  # 自動保存パスに保存
        
    def next_street(self):
        """次のストリートに進む（ベットを回収してポットを更新）"""
        # 現在のストリートを判定
        current_street = "preflop"
        if len(self.board_cards) >= 3:
            current_street = "flop"
        if len(self.board_cards) >= 4:
            current_street = "turn"
        if len(self.board_cards) >= 5:
            current_street = "river"
            
        # 次のストリートを決定
        next_street_map = {
            "preflop": "flop",
            "flop": "turn",
            "turn": "river",
            "river": "showdown"  # ショーダウン（勝者判定）
        }
        next_street = next_street_map[current_street]
        
        # ベットを回収してポットを更新（既存の処理）
        pot = self.pot_manager.collect_bets()
        
        # ポット情報をデバッグ出力
        print(f"Next Street - Pot after collect_bets: {self.pot_manager.pot}")
        print(f"Next Street - Main pot: {self.pot_manager.main_pot}")
        print(f"Next Street - Side pots: {[p['amount'] for p in self.pot_manager.side_pots]}")
        
        # ポット表示を更新
        self.update_pot_display()
        
        # フロップ以降は、SBからアクション開始（BUの次）
        self.current_action_index = (self.bu_position + 1) % len(self.players)
        
        # FoldやAll-inプレイヤーをスキップ
        while self.players[self.current_action_index].action_display.text() in ["Fold", "All-in"]:
            self.current_action_index = (self.current_action_index + 1) % len(self.players)
            
        # 次のプレイヤーをハイライト
        self.highlight_next_player()
        
        # 次のストリートに応じた処理
        if next_street == "flop":
            # フロップカード入力（3枚）
            self.input_street_cards("flop", 3)
        elif next_street == "turn":
            # ターンカード入力（1枚）
            self.input_street_cards("turn", 1)
        elif next_street == "river":
            # リバーカード入力（1枚）
            self.input_street_cards("river", 1)
        
        # ポット表示を再度更新（エクイティ計算後）
        self.update_pot_display()
        
        # 自動保存
        self.auto_save()
    
    def input_street_cards(self, street_name, card_count):
        """ストリートのカードを入力"""
        # ポット情報をデバッグ出力（カード入力前）
        print(f"input_street_cards - Before card input - Pot: {self.pot_manager.pot}")
        print(f"input_street_cards - Before card input - Main pot: {self.pot_manager.main_pot}")
        print(f"input_street_cards - Before card input - Side pots: {[p['amount'] for p in self.pot_manager.side_pots]}")
        
        cards = []
        for i in range(card_count):
            dialog = CardInputDialog(f"{street_name.capitalize()} カード {i+1}/{card_count}")
            if dialog.exec() == QDialog.Accepted:
                card = dialog.get_card()
                cards.append(card)
                # デバッグ出力（人間が読みやすい形式で）
                card_display = get_card_display(card)
                print(f"{street_name.capitalize()} Card {i+1}: {card_display} (内部表現: suit={card.suit}, rank={card.rank})")
            else:
                # キャンセルされた場合は処理を中断
                return
        
        # ボードカードを更新
        self.board_cards.extend(cards)
        
        # デバッグ出力（人間が読みやすい形式で）
        debug_cards = [get_card_display(card) for card in self.board_cards]
        print(f"Board cards after {street_name}: {debug_cards}")
        
        # ストリート表示を更新
        self.street_label.setText(f"Street: {street_name.capitalize()}")
        
        # ボードカード表示を更新
        self.update_board_display()
        
        # カード表示を更新
        card_str = [get_card_display(card) for card in self.board_cards]
        
        # ポット情報をデバッグ出力（カード入力後）
        print(f"input_street_cards - After card input - Pot: {self.pot_manager.pot}")
        print(f"input_street_cards - After card input - Main pot: {self.pot_manager.main_pot}")
        print(f"input_street_cards - After card input - Side pots: {[p['amount'] for p in self.pot_manager.side_pots]}")
        
        # ポット表示を更新（カード入力後に再度更新）
        self.update_pot_display()
        
        QMessageBox.information(self, f"{street_name.capitalize()}", f"ボードカード: {' '.join(card_str)}")
        
        # 全プレイヤーのエクイティを自動計算
        self.calculate_all_equities(show_dialog=False)
    
    def input_board_cards(self):
        """ボードカードを手動入力"""
        # 現在のストリートに応じたカード枚数を決定
        street_card_count = {
            "preflop": 0,
            "flop": 3,
            "turn": 1,
            "river": 1
        }
        
        # 現在のストリートを選択
        street, ok = QInputDialog.getItem(
            self, "ストリート選択", "ストリートを選択してください:",
            ["flop", "turn", "river"], 0, False
        )
        
        if not ok:
            return
            
        # 選択されたストリートに応じたカード枚数を入力
        cards = []
        for i in range(street_card_count[street]):
            dialog = CardInputDialog(f"{street.capitalize()} カード {i+1}/{street_card_count[street]}")
            if dialog.exec() == QDialog.Accepted:
                card = dialog.get_card()
                cards.append(card)
                # デバッグ出力（人間が読みやすい形式で）
                card_display = get_card_display(card)
                print(f"{street.capitalize()} Card {i+1}: {card_display} (内部表現: suit={card.suit}, rank={card.rank})")
            else:
                return  # キャンセルされた場合は中断
        
        # ストリートに応じてボードカードを更新
        if street == "flop":
            self.board_cards = cards
        else:
            self.board_cards.extend(cards)
            
        # ストリート表示を更新
        self.street_label.setText(f"Street: {street.capitalize()}")
        
        # ボードカード表示を更新
        self.update_board_display()
        
        # カード表示を更新
        card_str = [get_card_display(card) for card in self.board_cards]
        
        QMessageBox.information(self, f"{street.capitalize()}", f"ボードカード: {' '.join(card_str)}")
        
        # 全プレイヤーのエクイティを更新
        self.calculate_all_equities()
    
    def calculate_equity(self, player_cards, board_cards, opponent_count=1, simulation_count=1000):
        """モンテカルロシミュレーションでハンドエクイティを計算"""
        # プレイヤーのカードがない場合は0%を返す
        if not player_cards or len(player_cards) != 2:
            return 0.0
            
        # 対戦相手がいない場合は100%を返す
        if opponent_count <= 0:
            return 100.0
        
        # 既知のカードを除外したデッキを作成
        deck = Deck()
        for card in player_cards + board_cards:
            if card in deck.deck:  # カードがデッキに存在する場合のみ削除
                deck.deck.remove(card)
        
        win_count = 0
        
        # シミュレーション実行
        for _ in range(simulation_count):
            deck.shuffle()
            
            # 残りのボードカードを生成（5枚になるまで）
            remaining_board = board_cards.copy()
            remaining_to_deal = 5 - len(board_cards)
            remaining_board_cards = []
            for _ in range(remaining_to_deal):
                card = deck.draw_card()
                remaining_board.append(card)
                remaining_board_cards.append(card)
            
            # 対戦相手のハンドを生成
            opponents_hands = []
            for _ in range(opponent_count):
                opponent_hand = [deck.draw_card(), deck.draw_card()]
                opponents_hands.append(opponent_hand)
            
            # 自分のハンド強度
            my_strength = HandEvaluator.eval_hand(player_cards, remaining_board)
            
            # 対戦相手のハンド強度
            opponents_strengths = [HandEvaluator.eval_hand(hand, remaining_board) for hand in opponents_hands]
            
            # 勝敗判定
            if my_strength > max(opponents_strengths):
                win_count += 1
            
            # カードをデッキに戻す
            for card in remaining_board_cards:
                deck.deck.append(card)
            for hand in opponents_hands:
                for card in hand:
                    deck.deck.append(card)
        
        # 勝率を計算
        equity = win_count / simulation_count * 100
        return equity
    
    def calculate_all_equities(self, show_dialog=False):
        """全プレイヤーのエクイティを計算して表示"""
        # ポット情報をデバッグ出力（エクイティ計算前）
        print(f"calculate_all_equities - Before equity calculation - Pot: {self.pot_manager.pot}")
        print(f"calculate_all_equities - Before equity calculation - Main pot: {self.pot_manager.main_pot}")
        print(f"calculate_all_equities - Before equity calculation - Side pots: {[p['amount'] for p in self.pot_manager.side_pots]}")
        
        # ボードカードがない場合は確認（ダイアログ表示オプション）
        if not self.board_cards and show_dialog and QMessageBox.question(
            self, "確認", "ボードカードが設定されていません。プリフロップのエクイティを計算しますか？",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.No:
            return
            
        # アクティブなプレイヤー（Foldしていない）を取得
        active_players = [p for p in self.players if p.action_display.text() != "Fold"]
        
        # カードが設定されているプレイヤーのみ処理
        players_with_cards = [p for p in active_players if hasattr(p, 'cards') and p.cards and len(p.cards) == 2]
        
        if not players_with_cards:
            if show_dialog:
                QMessageBox.warning(self, "エラー", "カードが設定されているプレイヤーがいません")
            return
            
        # 各プレイヤーのエクイティを更新
        for player in players_with_cards:
            player.update_equity()
            
        # フォールドしたプレイヤーのエクイティ表示を更新
        for player in self.players:
            if player.action_display.text() == "Fold" and hasattr(player, 'equity_label'):
                player.equity_label.setText("Equity: Fold")
                player.equity_label.setStyleSheet("color: red; font-weight: bold;")
            
        # 現在のストリート名を取得
        street_name = "プリフロップ"
        if len(self.board_cards) >= 3:
            street_name = "フロップ"
        if len(self.board_cards) >= 4:
            street_name = "ターン"
        if len(self.board_cards) >= 5:
            street_name = "リバー"
            
        # 完了ダイアログ（オプション）
        if show_dialog:
            QMessageBox.information(self, "エクイティ計算完了", f"{street_name}のエクイティ計算が完了しました")
        
        # ポット情報をデバッグ出力（エクイティ計算後）
        print(f"calculate_all_equities - After equity calculation - Pot: {self.pot_manager.pot}")
        print(f"calculate_all_equities - After equity calculation - Main pot: {self.pot_manager.main_pot}")
        print(f"calculate_all_equities - After equity calculation - Side pots: {[p['amount'] for p in self.pot_manager.side_pots]}")
        
        # 自動保存（エクイティ情報を更新するため）
        self.auto_save()
    
    def determine_winner(self):
        """pypokerengineを使用して勝者を判定（ポットは配布せず）"""
        # アクティブなプレイヤー（Foldしていない）を取得
        active_players = [p for p in self.players if p.action_display.text() != "Fold"]
        
        # ボードカードがない場合は処理しない
        if not self.board_cards:
            QMessageBox.warning(self, "エラー", "ボードカードが設定されていません")
            return
            
        # 各プレイヤーのハンドを評価
        player_hands = []
        for player in active_players:
            if not player.cards or len(player.cards) != 2:
                QMessageBox.warning(self, "エラー", f"{player.name_button.text() or player.default_name_label.text()}のカードが設定されていません")
                return
                
            # ハンドの強さを評価
            hand_strength = HandEvaluator.eval_hand(player.cards, self.board_cards)
            player_hands.append((player, hand_strength))
        
        if not player_hands:
            QMessageBox.warning(self, "エラー", "有効なプレイヤーがいません")
            return
            
        # 最強のハンドを持つプレイヤーを特定
        winner, strength = max(player_hands, key=lambda x: x[1])
        
        # 勝者ダイアログを表示（ポットは配布せず）
        winner_name = winner.name_button.text() or winner.default_name_label.text()
        QMessageBox.information(self, "勝者判定", f"勝者判定: {winner_name}\n\n※ポットはNextHandボタンで配布します")
        
        # 勝者情報をデバッグ出力
        print(f"Winner determined: {winner_name} (Pot will be distributed when Next Hand is clicked)")
        
        # 自動保存に勝者情報を追加
        self.auto_save()
    
    def update_pot_display(self):
        """ポット表示を更新"""
        # ポット情報をデバッグ出力（表示更新前）
        print(f"update_pot_display - Before updating display - Pot: {self.pot_manager.pot}")
        print(f"update_pot_display - Before updating display - Main pot: {self.pot_manager.main_pot}")
        print(f"update_pot_display - Before updating display - Side pots: {[p['amount'] for p in self.pot_manager.side_pots]}")
        
        if self.pot_manager.side_pots:
            # メインポットとサイドポットを分けて表示
            main_pot = self.pot_manager.main_pot  # 最初のポットがメインポット
            
            # サイドポットは最初の要素を除いた全て
            side_pots = self.pot_manager.side_pots[1:]  # 最初の要素を除く

            if side_pots:
                # 各サイドポットを個別に表示
                side_pots_str = " + ".join([f"Side{i+1}:{pot['amount']}" for i, pot in enumerate(side_pots) if pot["amount"] > 0])
                self.pot_label.setText(f"POT: {main_pot} ({side_pots_str})")
            else:
                self.pot_label.setText(f"POT: {main_pot}")
        else:
            self.pot_label.setText(f"POT: {self.pot_manager.pot}")
            
        # ポット情報をデバッグ出力（表示更新後）
        print(f"update_pot_display - After updating display - Pot: {self.pot_manager.pot}")
        print(f"update_pot_display - After updating display - Main pot: {self.pot_manager.main_pot}")
        print(f"update_pot_display - After updating display - Side pots: {[p['amount'] for p in self.pot_manager.side_pots]}")
    
    def move_to_next_player(self):
        """次のプレイヤーに移動する処理"""
        # 次のプレイヤーのインデックスを計算
        self.current_action_index = (self.current_action_index + 1) % len(self.players)
        
        # FoldやAll-inプレイヤーをスキップ
        while self.players[self.current_action_index].action_display.text() in ["Fold", "All-in"]:
            self.current_action_index = (self.current_action_index + 1) % len(self.players)
        
        # 次のプレイヤーをハイライト
        self.highlight_next_player()
    
    def highlight_next_player(self):
        """次のアクションプレイヤーをハイライト表示"""
        for idx, player_frame in enumerate(self.players):
            if idx == self.current_action_index:
                player_frame.highlight_action(True)
            else:
                player_frame.highlight_action(False)
    
    def update_positions(self):
        """ポジションを再割り振り"""
        # 表示されているプレイヤーだけ抽出
        visible_players = [p for p in self.players if p.visible]
        num_visible_players = len(visible_players)

        # 人数に応じたポジション順を取得
        positions = POSITIONS_BY_PLAYER_COUNT.get(num_visible_players, POSITIONS[:num_visible_players])

        # BUから時計回りにポジションを割り振る
        for i, player in enumerate(visible_players):
            # プレイヤー順をBU基準でローテーション
            pos_index = (i - self.bu_position + num_visible_players) % num_visible_players
            position = positions[pos_index]
            player.update_position(position, self.sb, self.bb)

        # 非表示のプレイヤーには空のポジションを設定
        for player in self.players:
            if not player.visible:
                player.update_position("", self.sb, self.bb)

    
    def set_players_count(self):
        """プレイヤー数を設定"""
        # 現在のプレイヤー数
        current_count = len([p for p in self.players if p.visible])
        
        # プレイヤー数選択ダイアログ
        count, ok = QInputDialog.getInt(
            self, "プレイヤー数設定", "プレイヤー数を選択してください:", 
            current_count, 2, 8, 1
        )
        
        if not ok:
            return
            
        # プレイヤーの表示/非表示を設定
        for i, player in enumerate(self.players):
            if i < count:
                player.setVisible(True)
                player.visible = True
            else:
                player.setVisible(False)
                player.visible = False
        
        # ポジションを再割り振り
        self.update_positions()
        
        # 自動保存
        self.auto_save()
        
        QMessageBox.information(self, "プレイヤー数設定", f"プレイヤー数を{count}人に設定しました")
    
    def update_board_display(self):
        """ボードカード表示を更新（カードを1枚ずつ処理）"""
        if not self.board_cards:
            self.board_cards_label.setText("Board: ")
            self.board_cards_label.setStyleSheet("font-size: 16px; font-weight: bold; color: yellow; background-color: #444; padding: 3px; border-radius: 3px;")
            return
            
        # カード表示を更新（1枚ずつ処理）
        from card_utils import get_colored_card_display
        card_displays = []
        for card in self.board_cards:
            card_display = get_colored_card_display(card)
            card_displays.append(card_display)
        
        # ボードカード表示を更新
        self.board_cards_label.setText(f"Board: {' '.join(card_displays)}")
        
        # ボードカードラベルのスタイルをデフォルトに戻す
        self.board_cards_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white; background-color: #444; padding: 3px; border-radius: 3px;")
    
    def save_as(self):
        """Save AS メニューから呼ばれて、任意のファイル名で保存する"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "名前を付けて保存", "status.json", "JSON Files (*.json)"
        )
        if filename:
            self.export_json(filepath=filename)
            
    def load(self):
        """Load メニューから呼ばれて、JSONファイルを読み込む"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "ファイルを開く", "", "JSON Files (*.json)"
        )
        if not filename:
            return
            
        try:
            with open(filename, "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # ボード情報を更新
            board_data = data.get("board", {})
            
            # ポット情報を更新
            self.pot_manager.pot = board_data.get("pot", 0)
            self.pot_manager.main_pot = board_data.get("main_pot", 0)
            
            # サイドポット情報を更新（簡易版）
            self.pot_manager.side_pots = []
            if board_data.get("side_pots"):
                for pot_info in board_data.get("side_pots", []):
                    # 簡易的なサイドポット情報を作成
                    self.pot_manager.side_pots.append({
                        "amount": pot_info.get("amount", 0),
                        "players_in_pot": self.players,  # 全プレイヤーを対象とする
                        "active_players": [p for p in self.players if p.action_display.text() != "Fold"]
                    })
            
            # ブラインド情報を更新
            blinds = board_data.get("blinds", "0/0").split("/")
            if len(blinds) == 2:
                try:
                    self.sb = int(blinds[0])
                    self.bb = int(blinds[1])
                    self.pot_manager.bb = self.bb
                    self.blinds_label.setText(f"Blinds: {self.sb}/{self.bb}")
                except ValueError:
                    pass
            
            # ボードカードを更新
            self.board_cards = []
            for card_info in board_data.get("cards", []):
                # 内部形式からpypokerengineのCard形式に変換
                from card_utils import convert_internal_to_pypoker
                card = convert_internal_to_pypoker(card_info)
                if card:
                    self.board_cards.append(card)
            
            # ストリート情報を更新
            street = board_data.get("street", "Preflop")
            self.street_label.setText(f"Street: {street}")
            
            # ボードカード表示を更新
            self.update_board_display()
            
            # ポット表示を更新
            self.update_pot_display()
            
            # プレイヤー情報を更新
            player_data = data.get("players", [])
            for i, player_info in enumerate(player_data):
                if i < len(self.players):
                    player = self.players[i]
                    
                    # 名前を更新
                    if player_info.get("name"):
                        player.name_button.setText(player_info.get("name"))
                    
                    # スタックを更新
                    player.stack_value = player_info.get("stack", 0)
                    player.update_stack_display()
                    
                    # ポジションを更新
                    position = player_info.get("position", "")
                    if position:
                        player.position_label.setText(position)
                    
                    # アクションを更新（空文字列の場合も明示的に設定）
                    action = player_info.get("action", "")
                    player.action_display.setText(action)
                    
                    # カード情報を更新
                    player.cards = []
                    for card_info in player_info.get("cards", []):
                        # 内部形式からpypokerengineのCard形式に変換
                        from card_utils import convert_internal_to_pypoker
                        card = convert_internal_to_pypoker(card_info)
                        if card:
                            player.cards.append(card)
                    
                    # カード表示を更新
                    if player.cards:
                        from card_utils import get_colored_card_display
                        card_displays = []
                        for card in player.cards:
                            card_display = get_colored_card_display(card)
                            card_displays.append(card_display)
                        player.card_button.setText(f"{' '.join(card_displays)}")
                        player.card_button.setStyleSheet("font-size: 18px; padding: 10px; font-weight: bold;")
                    
                    # エクイティ情報を更新
                    equity = player_info.get("equity")
                    if equity == "Fold":
                        player.equity_label.setText("Equity: Fold")
                        player.equity_label.setStyleSheet("color: red; font-weight: bold;")
                    elif equity is not None:
                        player.equity_label.setText(f"Equity: {equity:.1f}%")
                        player.equity_label.setStyleSheet("color: yellow; font-weight: bold;")
            
            # 全プレイヤーのエクイティを更新
            self.calculate_all_equities(show_dialog=False)
            
            QMessageBox.information(self, "ファイル読み込み", f"ファイルを読み込みました: {filename}")
            
        except Exception as e:
            QMessageBox.warning(self, "エラー", f"ファイルの読み込みに失敗しました: {str(e)}")
            
    def get_current_state_as_dict(self):
        """現在の状態をディクショナリとして取得"""
        # ボードカード情報を内部形式に変換
        board_card_info = []
        for card in self.board_cards:
            # カードを内部形式に変換
            from card_utils import convert_pypoker_to_internal
            internal_format = convert_pypoker_to_internal(card)
            if internal_format:
                board_card_info.append(internal_format)
            
        data = {
            "players": [],
            "board": {
                "pot": self.pot_manager.pot,
                "blinds": f"{self.sb}/{self.bb}",
                "main_pot": self.pot_manager.main_pot,
                "side_pots": [
                    {
                        "amount": pot["amount"],
                        "players": [
                            p.name_button.text() or p.default_name_label.text()
                            for p in pot["players_in_pot"] if hasattr(p, 'visible') and p.visible
                        ],
                    }
                    for pot in self.pot_manager.side_pots[1:]  # 最初の要素を除く
                    if self.pot_manager.side_pots
                ],
                "cards": board_card_info,  # 文字列形式のボードカード情報
                "street": self.street_label.text().replace("Street: ", "")  # ストリート情報
            },
            "current_action_index": self.current_action_index,
            "bu_position": self.bu_position,
        }
        
        # 表示されているプレイヤーのみを出力
        visible_players = [p for p in self.players if hasattr(p, 'visible') and p.visible]
        
        for p in visible_players:
            # エクイティ情報を取得
            equity = None
            if p.action_display.text() == "Fold":
                equity = "Fold"  # フォールドプレイヤーは明示的に「Fold」と設定
            elif hasattr(p, 'equity_label'):
                equity_text = p.equity_label.text()
                if "---" not in equity_text and "Fold" not in equity_text:
                    try:
                        equity = float(equity_text.replace("Equity: ", "").replace("%", ""))
                    except:
                        pass
            
            # カード情報を取得（内部形式に変換）
            card_info = []
            if hasattr(p, 'cards') and p.cards:
                for card in p.cards:
                    # カードを内部形式に変換
                    from card_utils import convert_pypoker_to_internal
                    internal_format = convert_pypoker_to_internal(card)
                    if internal_format:
                        card_info.append(internal_format)
            
            # プレイヤー情報を追加
            player_info = {
                "name": p.name_button.text() or p.default_name_label.text(),
                "stack": p.stack_value,
                "position": p.position_label.text(),
                "action": p.action_display.text(),
                "cards": card_info,
                "equity": equity,
                "current_bet": p.current_bet,
                "forced_blind_bet": p.forced_blind_bet,
                "visible": p.visible,
                "index": self.players.index(p)
            }
            data["players"].append(player_info)
            
        return data
        
    def restore_state_from_dict(self, state_dict):
        """ディクショナリから状態を復元"""
        # ボード情報を更新
        board_data = state_dict.get("board", {})
        
        # ポット情報を更新
        self.pot_manager.pot = board_data.get("pot", 0)
        self.pot_manager.main_pot = board_data.get("main_pot", 0)
        
        # サイドポット情報を更新（簡易版）
        self.pot_manager.side_pots = []
        if board_data.get("side_pots"):
            for pot_info in board_data.get("side_pots", []):
                # 簡易的なサイドポット情報を作成
                self.pot_manager.side_pots.append({
                    "amount": pot_info.get("amount", 0),
                    "players_in_pot": self.players,  # 全プレイヤーを対象とする
                    "active_players": [p for p in self.players if p.action_display.text() != "Fold"]
                })
        
        # ブラインド情報を更新
        blinds = board_data.get("blinds", "0/0").split("/")
        if len(blinds) == 2:
            try:
                self.sb = int(blinds[0])
                self.bb = int(blinds[1])
                self.pot_manager.bb = self.bb
                self.blinds_label.setText(f"Blinds: {self.sb}/{self.bb}")
            except ValueError:
                pass
        
        # ボードカードを更新
        self.board_cards = []
        for card_info in board_data.get("cards", []):
            # 内部形式からpypokerengineのCard形式に変換
            from card_utils import convert_internal_to_pypoker
            card = convert_internal_to_pypoker(card_info)
            if card:
                self.board_cards.append(card)
        
        # ストリート情報を更新
        street = board_data.get("street", "Preflop")
        self.street_label.setText(f"Street: {street}")
        
        # ボードカード表示を更新
        self.update_board_display()
        
        # ポット表示を更新
        self.update_pot_display()
        
        # BUポジションを更新
        self.bu_position = state_dict.get("bu_position", 0)
        self.current_action_index = state_dict.get("current_action_index", 0)
        
        # プレイヤー情報を更新
        player_data = state_dict.get("players", [])
        for player_info in player_data:
            # プレイヤーのインデックスを取得
            player_index = player_info.get("index", -1)
            if 0 <= player_index < len(self.players):
                player = self.players[player_index]
                
                # 名前を更新
                if player_info.get("name"):
                    player.name_button.setText(player_info.get("name"))
                
                # スタックを更新
                player.stack_value = player_info.get("stack", 0)
                player.update_stack_display()
                
                # ポジションを更新
                position = player_info.get("position", "")
                if position:
                    player.position_label.setText(position)
                
                # アクションを更新（空文字列の場合も明示的に設定）
                action = player_info.get("action", "")
                player.action_display.setText(action)
                
                # ベット情報を更新
                player.current_bet = player_info.get("current_bet", 0)
                player.forced_blind_bet = player_info.get("forced_blind_bet", 0)
                
                # 表示状態を更新
                player.visible = player_info.get("visible", True)
                player.setVisible(player.visible)
                
                # カード情報を更新
                player.cards = []
                for card_info in player_info.get("cards", []):
                    # 内部形式からpypokerengineのCard形式に変換
                    from card_utils import convert_internal_to_pypoker
                    card = convert_internal_to_pypoker(card_info)
                    if card:
                        player.cards.append(card)
                
                # カード表示を更新
                if player.cards:
                    from card_utils import get_colored_card_display
                    card_displays = []
                    for card in player.cards:
                        card_display = get_colored_card_display(card)
                        card_displays.append(card_display)
                    player.card_button.setText(f"{' '.join(card_displays)}")
                    player.card_button.setStyleSheet("font-size: 18px; padding: 10px; font-weight: bold;")
                else:
                    player.card_button.setText("Set Hand")
                
                # エクイティ情報を更新
                equity = player_info.get("equity")
                if equity == "Fold":
                    player.equity_label.setText("Equity: Fold")
                    player.equity_label.setStyleSheet("color: red; font-weight: bold;")
                elif equity is not None:
                    player.equity_label.setText(f"Equity: {equity:.1f}%")
                    player.equity_label.setStyleSheet("color: yellow; font-weight: bold;")
                else:
                    player.equity_label.setText("Equity: ---%")
                    player.equity_label.setStyleSheet("color: yellow; font-weight: bold;")
    
    def save_state_to_history(self):
        """現在の状態を履歴に保存"""
        # 現在の状態をJSONとして取得（データだけ取得して保存しない）
        current_state = self.get_current_state_as_dict()
        
        # 前回の状態と比較して変化があれば保存
        if self.history_index >= 0 and self.state_history and self.compare_states(self.state_history[self.history_index], current_state):
            return  # 変化がなければ何もしない
            
        # 履歴の途中でUNDOした後に新しい操作をした場合、それ以降の履歴を削除
        if self.history_index < len(self.state_history) - 1:
            self.state_history = self.state_history[:self.history_index + 1]
        
        # 履歴に追加
        self.state_history.append(current_state)
        self.history_index = len(self.state_history) - 1
        
        # 最大数を超えたら古いものを削除
        if len(self.state_history) > self.max_history:
            self.state_history.pop(0)
            self.history_index -= 1
            
        print(f"State saved to history. History size: {len(self.state_history)}, Index: {self.history_index}")
    
    def compare_states(self, state1, state2):
        """2つの状態を比較して同じかどうかを判定（重要な部分のみ比較）"""
        # デバッグ出力
        print("Comparing states...")
        
        # ボード情報の比較
        board1 = state1.get("board", {})
        board2 = state2.get("board", {})
        
        if board1.get("pot") != board2.get("pot"):
            print(f"Pot differs: {board1.get('pot')} vs {board2.get('pot')}")
            return False
        if board1.get("blinds") != board2.get("blinds"):
            print(f"Blinds differ: {board1.get('blinds')} vs {board2.get('blinds')}")
            return False
        if len(board1.get("cards", [])) != len(board2.get("cards", [])):
            print(f"Card count differs: {len(board1.get('cards', []))} vs {len(board2.get('cards', []))}")
            return False
        if board1.get("street") != board2.get("street"):
            print(f"Street differs: {board1.get('street')} vs {board2.get('street')}")
            return False
        
        # BUポジションの比較
        if state1.get("bu_position") != state2.get("bu_position"):
            print(f"BU position differs: {state1.get('bu_position')} vs {state2.get('bu_position')}")
            return False
            
        # プレイヤー情報の比較
        players1 = state1.get("players", [])
        players2 = state2.get("players", [])
        if len(players1) != len(players2):
            print(f"Player count differs: {len(players1)} vs {len(players2)}")
            return False
            
        for i in range(len(players1)):
            p1 = players1[i]
            p2 = players2[i]
            
            # プレイヤー名の比較
            if p1.get("name") != p2.get("name"):
                print(f"Player {i} name differs: {p1.get('name')} vs {p2.get('name')}")
                return False
                
            # スタックの比較
            if p1.get("stack") != p2.get("stack"):
                print(f"Player {i} stack differs: {p1.get('stack')} vs {p2.get('stack')}")
                return False
                
            # ポジションの比較
            if p1.get("position") != p2.get("position"):
                print(f"Player {i} position differs: {p1.get('position')} vs {p2.get('position')}")
                return False
                
            # アクションの比較
            if p1.get("action") != p2.get("action"):
                print(f"Player {i} action differs: {p1.get('action')} vs {p2.get('action')}")
                return False
                
            # カード枚数の比較
            if len(p1.get("cards", [])) != len(p2.get("cards", [])):
                print(f"Player {i} card count differs: {len(p1.get('cards', []))} vs {len(p2.get('cards', []))}")
                return False
                
            # ベット額の比較
            if p1.get("current_bet") != p2.get("current_bet"):
                print(f"Player {i} current bet differs: {p1.get('current_bet')} vs {p2.get('current_bet')}")
                return False
                
            # エクイティの比較
            if p1.get("equity") != p2.get("equity"):
                print(f"Player {i} equity differs: {p1.get('equity')} vs {p2.get('equity')}")
                return False
                
        print("States are identical")
        return True  # 重要な部分がすべて一致
    
    def undo(self):
        """一つ前の状態に戻す"""
        # デバッグ出力
        print(f"UNDO - Current history index: {self.history_index}, History size: {len(self.state_history)}")
        
        if self.history_index <= 0 or len(self.state_history) <= 1:
            print("UNDO - Cannot undo further, no more history")
            QMessageBox.information(self, "UNDO", "これ以上戻れません")
            return
            
        # インデックスを一つ戻す
        self.history_index -= 1
        print(f"UNDO - Moving to history index: {self.history_index}")
        
        # 履歴から状態を復元
        previous_state = self.state_history[self.history_index]
        
        # 状態の内容をデバッグ出力（エラー修正）
        print("UNDO - Restoring previous state:")
        if 'board' in previous_state:
            print(f"  - Board pot: {previous_state['board'].get('pot', 0)}")
            print(f"  - Board cards: {len(previous_state['board'].get('cards', []))}")
            print(f"  - Street: {previous_state['board'].get('street', '')}")
        
        # プレイヤー情報をデバッグ出力
        for i, player in enumerate(previous_state.get("players", [])):
            print(f"  - Player {i} action: {player.get('action')}")
            print(f"  - Player {i} stack: {player.get('stack')}")
            print(f"  - Player {i} current_bet: {player.get('current_bet')}")
        
        # 状態を復元
        self.restore_state_from_dict(previous_state)
        
        # 復元後の状態をデバッグ出力
        print("UNDO - State restored successfully")
        
        QMessageBox.information(self, "UNDO", "前の状態に戻りました")
        
    def auto_save(self):
        """タイマーから呼ばれる自動保存処理（常にauto_save_pathに保存）"""
        self.export_json(filepath=self.auto_save_path)
        
    def export_json(self, filepath=None):
        """現在の状態をJSONファイルにエクスポート"""
        # filepathが指定されていない場合はauto_save_pathを使用
        if filepath is None:
            filepath = self.auto_save_path
            
        # ポット情報をデバッグ出力（JSON出力前）
        print(f"export_json - Before JSON export - Pot: {self.pot_manager.pot}")
        print(f"export_json - Before JSON export - Main pot: {self.pot_manager.main_pot}")
        print(f"export_json - Before JSON export - Side pots: {[p['amount'] for p in self.pot_manager.side_pots]}")
        
        # 現在の状態をディクショナリとして取得
        data = self.get_current_state_as_dict()
        
        # 不要なフィールドを削除（JSONファイルには含めない）
        if "bu_position" in data:
            del data["bu_position"]
        for player in data.get("players", []):
            if "index" in player:
                del player["index"]
            if "current_bet" in player:
                del player["current_bet"]
            if "forced_blind_bet" in player:
                del player["forced_blind_bet"]
            if "visible" in player:
                del player["visible"]
        
        # デバッグ出力（カード情報を確認 - 人間が読みやすい形式で）
        debug_board_cards = [get_card_display(card) for card in self.board_cards]
        print(f"Board cards: {debug_board_cards}")
        
        # 表示されているプレイヤーのみを出力
        visible_players = [p for p in self.players if hasattr(p, 'visible') and p.visible]
        
        for p in visible_players:
            # デバッグ出力（人間が読みやすい形式で）
            if hasattr(p, 'cards') and p.cards:
                debug_player_cards = [get_card_display(card) for card in p.cards]
                print(f"Player {p.name_button.text() or p.default_name_label.text()} cards: {debug_player_cards}")

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            
        # 状態を履歴に保存（ファイル保存時は常に保存）
        self.save_state_to_history()


from PySide6.QtWidgets import QApplication
import ctypes

# Windowsの高DPIスケーリングを有効化
ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Windows 8.1以降


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = QMainWindow()
    
    # 初期ウィンドウサイズ（標準モード）
    window.resize(1200, 900)

    # 中央ウィジェットとレイアウトの準備
    content_widget = QWidget()
    layout = QGridLayout()
    layout.setSpacing(2)
    layout.setContentsMargins(2, 2, 2, 2)

    players = []
    pot_manager = PotManager(players)
    central_manager = CentralManager(pot_manager, players)

    # メニューバー作成
    menu_bar = window.menuBar()

    # File メニュー
    file_menu = menu_bar.addMenu("File")
    save_as_action = file_menu.addAction("Save AS")
    save_as_action.triggered.connect(central_manager.save_as)
    load_action = file_menu.addAction("Load")
    load_action.triggered.connect(central_manager.load)

    # Action メニュー
    action_menu = menu_bar.addMenu("Action")
    set_blinds_action = action_menu.addAction("Set Blinds")
    set_blinds_action.triggered.connect(central_manager.set_blinds)
    set_stacks_action = action_menu.addAction("Set Stacks")
    set_stacks_action.triggered.connect(central_manager.set_all_stacks)
    set_bu_action = action_menu.addAction("Set BU")
    set_bu_action.triggered.connect(central_manager.set_bu)
    change_players_action = action_menu.addAction("Change number of players")
    change_players_action.triggered.connect(central_manager.set_players_count)

    # ⬜ 表示メニューと画面サイズ設定の追加
    view_menu = menu_bar.addMenu("表示")
    screen_size_menu = QMenu("画面サイズ設定", window)

    def set_standard_mode():
        window.setFixedSize(1200, 900)
        for p in players:
            p.set_frame_size(295, 295)

    def set_compact_mode():
        window.setFixedSize(800, 600)
        for p in players:
            p.set_frame_size(220, 220)

    standard_mode_action = screen_size_menu.addAction("標準モード (1200x900)")
    standard_mode_action.triggered.connect(set_standard_mode)

    compact_mode_action = screen_size_menu.addAction("コンパクトモード (1000x700)")
    compact_mode_action.triggered.connect(set_compact_mode)

    view_menu.addMenu(screen_size_menu)

    # プレイヤーの配置
    positions_coords = [
        (3, 1), (3, 0), (0, 0), (0, 1),
        (0, 2), (0, 3), (3, 3), (3, 2)
    ]

    for i in range(8):
        p = PlayerControlFrame(f"Player {i+1}", POSITIONS[i], pot_manager, central_manager)
        players.append(p)
        x, y = positions_coords[i]
        layout.addWidget(p, x, y)

    for player in players:
        player.pay_info = PlayerPayInfo(player)

    pot_manager.players = players
    central_manager.players = players
    layout.addWidget(central_manager, 1, 1, 2, 2)

    content_widget.setLayout(layout)
    window.setCentralWidget(content_widget)
    window.show()
    sys.exit(app.exec())
