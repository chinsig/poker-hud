from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QScrollArea, QSpacerItem, QSizePolicy, QFrame, QLabel, QHBoxLayout, QGraphicsOpacityEffect
from PySide6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, QParallelAnimationGroup, QSequentialAnimationGroup, QPoint, QRect, Property
from PySide6.QtGui import QColor, QPalette
import json
import sys

# カード表示用のユーティリティをインポート
from card_utils import format_cards_for_display

class PlayerFrame(QFrame):
    def __init__(self, name, stack, position, action, cards, equity=None):
        super().__init__()
        self.setFixedSize(400, 96)  # プレイヤーフレームの高さを0.8倍に縮小
        self.setStyleSheet(
            """
            border: 1px solid white;
            padding: 0px;
            background-color: #333;
            color: white;
            """
        )
        
        # アニメーション用の透明度プロパティ
        self._opacity = 1.0
        self.position = position
        self.action = action
        self.name = name
        
        # QGraphicsOpacityEffectを設定
        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.opacity_effect.setOpacity(1.0)
        self.setGraphicsEffect(self.opacity_effect)

        # レイアウトを作成
        layout = QVBoxLayout()
        layout.setContentsMargins(4, 4, 4, 4)  # 外側の余白を少し縮小
        layout.setSpacing(4)  # 項目間の余白を少し縮小

        # 上段: 名前、カード、ポジション、エクイティ
        top_layout = QHBoxLayout()
        top_layout.setContentsMargins(0, 0, 0, 0)  # 上段の余白をゼロに設定
        top_layout.setSpacing(4)  # 項目間の余白を少し縮小

        name_label = QLabel(name)
        name_label.setStyleSheet("font-weight: bold; font-size: 16px;")  # フォントサイズを縮小
        name_label.setAlignment(Qt.AlignCenter)
        name_label.setFixedWidth(100)  # 横幅を少し縮小
        top_layout.addWidget(name_label)

        # カードラベルを保持するコンテナ
        cards_container = QWidget()
        cards_layout = QHBoxLayout(cards_container)
        cards_layout.setContentsMargins(0, 0, 0, 0)
        cards_layout.setSpacing(2)  # カード間の間隔を狭く

        # 2枚分のカードラベルを作成
        self.card_labels = []
        for i in range(2):
            card_label = QLabel("--")
            card_label.setStyleSheet(
                """
                font-size: 20px; font-weight: bold; 
                background-color: white; color: black;
                border: 1px solid black;
                """
            )
            card_label.setAlignment(Qt.AlignCenter)
            card_label.setFixedWidth(48)  # カードラベルの幅を設定
            card_label.setTextFormat(Qt.PlainText)  # HTMLタグを解釈しない
            
            # カードラベルにもQGraphicsOpacityEffectを設定
            card_opacity_effect = QGraphicsOpacityEffect(card_label)
            card_opacity_effect.setOpacity(1.0)
            card_label.setGraphicsEffect(card_opacity_effect)
            
            cards_layout.addWidget(card_label)
            self.card_labels.append(card_label)

        cards_container.setFixedWidth(100)  # コンテナの幅を設定
        top_layout.addWidget(cards_container)

        # ポジションとエクイティを横に並べるレイアウト
        pos_equity_layout = QHBoxLayout()
        pos_equity_layout.setContentsMargins(0, 0, 0, 0)
        pos_equity_layout.setSpacing(2)  # 間隔を狭く

        position_label = QLabel(position)
        position_label.setStyleSheet("font-size: 22px; font-weight: bold; color: white")
        position_label.setAlignment(Qt.AlignCenter)
        position_label.setFixedWidth(60)  # 横幅を縮小
        pos_equity_layout.addWidget(position_label)

        # エクイティラベル（ポジションの右に配置）
        self.equity_label = QLabel(self.format_equity_short(equity))
        self.equity_label.setStyleSheet("font-size: 16px; font-weight: bold; color: yellow;")
        self.equity_label.setAlignment(Qt.AlignCenter)
        self.equity_label.setFixedWidth(60)  # 横幅を設定
        pos_equity_layout.addWidget(self.equity_label)

        # ポジションとエクイティのレイアウトをコンテナに入れる
        pos_equity_container = QWidget()
        pos_equity_container.setLayout(pos_equity_layout)
        pos_equity_container.setFixedWidth(120)
        top_layout.addWidget(pos_equity_container)

        # 下段: スタック、アクション
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)  # 下段の余白をゼロに設定
        bottom_layout.setSpacing(4)  # 項目間の余白を少し縮小

        # スタックラベル（左側を1px右に詰める）
        stack_label = QLabel(f"{int(stack):,}")  # カンマ区切りでフォーマット
        stack_label.setStyleSheet("font-size: 22px; font-weight: bold; margin-left: 1px;")  # 左側を1px右に詰める
        stack_label.setAlignment(Qt.AlignCenter)
        stack_label.setFixedWidth(120)  # 横幅はそのまま
        bottom_layout.addWidget(stack_label)

        # アクションラベル（左右に2pxずつ広げる）
        action_label = QLabel(action)
        action_label.setStyleSheet("font-size: 22px; font-weight: bold; color: white; padding-left: 2px; padding-right: 2px;")  # 左右に2px広げる
        action_label.setAlignment(Qt.AlignCenter)
        action_label.setFixedWidth(244)  # 横幅を240pxから244pxに変更
        bottom_layout.addWidget(action_label)

        # レイアウトをまとめる
        layout.addLayout(top_layout)
        layout.addLayout(bottom_layout)
        self.setLayout(layout)
    
    def format_equity_short(self, equity):
        """エクイティ情報を短い形式でフォーマット（〇〇%の形式）"""
        if equity is None:
            return "---%"
        elif equity == "Fold":
            return "Fold"
        else:
            try:
                return f"{float(equity):.1f}%"
            except:
                return "---%"
    
    def format_equity(self, equity):
        """エクイティ情報を表示用にフォーマット（長い形式）"""
        if equity is None:
            return "Equity: ---%"
        elif equity == "Fold":
            return "Equity: Fold"
        else:
            try:
                return f"Equity: {float(equity):.1f}%"
            except:
                return "Equity: ---%"
    
    def update_cards(self, cards_list):
        """カード表示を更新（カードを1枚ずつ処理）"""
        # カードがない場合は何もしない
        if not cards_list or not isinstance(cards_list, list):
            return
            
        # カードラベルを更新
        for i, label in enumerate(self.card_labels):
            if i < len(cards_list):
                card_text = cards_list[i]
                label.setText(card_text)
                
                # カードのスートに応じて色を設定
                if "♠" in card_text:
                    label.setStyleSheet(
                        """
                        font-size: 20px; font-weight: bold; 
                        background-color: white; color: black; 
                        border: 1px solid black;
                        """
                    )
                elif "♦" in card_text:
                    label.setStyleSheet(
                        """
                        font-size: 20px; font-weight: bold; 
                        background-color: white; color: #0000CC; 
                        border: 1px solid black;
                        """
                    )
                elif "♥" in card_text:
                    label.setStyleSheet(
                        """
                        font-size: 20px; font-weight: bold; 
                        background-color: white; color: #CC0000; 
                        border: 1px solid black;
                        """
                    )
                elif "♣" in card_text:
                    label.setStyleSheet(
                        """
                        font-size: 20px; font-weight: bold; 
                        background-color: white; color: #006600; 
                        border: 1px solid black;
                        """
                    )
            else:
                label.setText("--")
                # デフォルトスタイル
                label.setStyleSheet(
                    """
                    font-size: 20px; font-weight: bold; 
                    background-color: white; color: black; 
                    border: 1px solid black;
                    """
                )
    
    def update_equity(self, equity):
        """エクイティ表示を更新"""
        self.equity_label.setText(self.format_equity_short(equity))
        
        # Foldの場合は赤色で表示
        if equity == "Fold":
            self.equity_label.setStyleSheet("font-size: 16px; font-weight: bold; color: red;")
        else:
            self.equity_label.setStyleSheet("font-size: 16px; font-weight: bold; color: yellow;")
    
    # 透明度プロパティの定義
    def get_opacity(self):
        return self._opacity
        
    def set_opacity(self, opacity):
        self._opacity = opacity
        # QGraphicsOpacityEffectの透明度を更新
        if hasattr(self, 'opacity_effect'):
            self.opacity_effect.setOpacity(opacity)
        
        # カードラベルの透明度も更新
        for label in self.card_labels:
            if label.graphicsEffect():
                label.graphicsEffect().setOpacity(opacity)
    
    # Propertyオブジェクトの作成
    opacity = Property(float, get_opacity, set_opacity)
    
    def fade_out(self, duration=1000, callback=None):
        """フェードアウトアニメーション"""
        self.animation = QPropertyAnimation(self, b"opacity")
        self.animation.setDuration(duration)  # 1秒かけてフェードアウト
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.0)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        if callback:
            self.animation.finished.connect(callback)
        self.animation.start()
        return self.animation


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Poker HUD - Player Info")
        self.setGeometry(100, 100, 500, 900)  # ウィンドウの位置とサイズを設定
        self.setFixedSize(500, 900)  # ウィンドウのサイズを固定
        self.setStyleSheet("background-color: green;")

        # プレイヤー情報を表示するエリア
        self.layout = QVBoxLayout()
        self.player_info_area = QScrollArea()
        self.player_info_content = QWidget()  # プレイヤーフレームを保持
        self.player_info_layout = QVBoxLayout(self.player_info_content)  # QVBoxLayoutを使用
        
        # 下から詰めるように配置を変更
        self.player_info_layout.setAlignment(Qt.AlignBottom)  # 下揃えに設定

        # プレイヤー間の空間を少し追加
        self.player_info_layout.setSpacing(10)  # プレイヤー枠同士の間隔を10pxに設定
        self.player_info_layout.setContentsMargins(5, 5, 5, 5)  # レイアウトの外側の余白を少し追加

        # スペーサーを上部に追加して下詰めにする
        self.spacer = QSpacerItem(20, 20, QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.player_info_layout.insertItem(0, self.spacer)  # 先頭（上部）にスペーサーを追加

        self.player_info_area.setWidget(self.player_info_content)
        self.player_info_area.setWidgetResizable(True)

        # プレイヤー情報エリアをメインレイアウトに追加
        self.layout.addWidget(self.player_info_area)

        self.setLayout(self.layout)

        self.players_data = []  # 現在のプレイヤーデータ
        self.previous_players_data = []  # 前回のプレイヤーデータ
        self.player_frames = {}  # プレイヤーフレームを保持する辞書（キー: position）
        self.current_action_index = 0  # 次にアクションするプレイヤーのインデックス
        self.animation_in_progress = False  # アニメーション実行中フラグ

        # 定期的にJSONを読み取るタイマー
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_players)
        self.timer.start(500)  # 0.5秒ごとに更新

    def animate_player_movement(self, frames, target_positions, duration=500):
        """プレイヤーフレームの移動アニメーション"""
        # アニメーショングループを作成
        self.move_animation_group = QParallelAnimationGroup()
        
        # 各フレームの移動アニメーションを作成
        for i, frame in enumerate(frames):
            if i < len(target_positions):
                # 現在の位置を取得
                current_pos = frame.pos()
                # 目標位置を設定
                target_pos = target_positions[i]
                
                # デバッグ出力
                print(f"Animating frame {i} from {current_pos} to {target_pos}")
                
                # 位置アニメーションを作成
                anim = QPropertyAnimation(frame, b"pos")
                anim.setDuration(duration)
                anim.setStartValue(current_pos)
                anim.setEndValue(target_pos)
                anim.setEasingCurve(QEasingCurve.InOutQuad)  # より自然な動きのためにInOutQuadに変更
                
                # アニメーショングループに追加
                self.move_animation_group.addAnimation(anim)
        
        # アニメーション完了時の処理
        self.move_animation_group.finished.connect(self.on_animation_finished)
        
        # アニメーションを開始
        self.move_animation_group.start()
    
    def on_animation_finished(self):
        """アニメーション完了時の処理"""
        self.animation_in_progress = False
        # 次のアップデートを許可
        self.timer.start()
    
    def detect_fold_players(self, current_data, previous_data):
        """Foldになったプレイヤーを検出"""
        fold_players = []
        
        # 前回のデータがない場合は空リストを返す
        if not previous_data:
            return fold_players
        
        # 前回アクティブだったプレイヤーのポジションを取得
        previous_positions = {p["position"]: p for p in previous_data if p["action"] != "Fold"}
        
        # 現在のデータでFoldになったプレイヤーを検出
        for player in current_data:
            position = player["position"]
            if position in previous_positions and player["action"] == "Fold":
                fold_players.append(position)
        
        return fold_players
    
    def update_players(self):
        # アニメーション実行中は更新をスキップ
        if self.animation_in_progress:
            return
            
        try:
            with open("status.json", "r", encoding="utf-8") as f:
                data = json.load(f)

            # プレイヤーの並び順を指定（逆順）
            position_order = ["BB", "SB", "BU", "CO", "HJ", "LJ", "+1", "UTG"]

            # プレイヤーを並べ替え
            sorted_players = sorted(data["players"], key=lambda p: position_order.index(p["position"]))
            
            # Foldになったプレイヤーを検出
            fold_positions = self.detect_fold_players(sorted_players, self.previous_players_data)
            
            # Foldになったプレイヤーがいる場合、フェードアウトアニメーションを実行
            if fold_positions and self.player_frames:
                self.animation_in_progress = True
                self.timer.stop()  # アニメーション中は更新を停止
                
                # フェードアウトアニメーションを実行
                self.fold_positions = fold_positions.copy()  # フォールドポジションを保存
                self.fade_animations = []
                self.fade_animation_completed = 0  # 完了したアニメーションのカウンター
                
                for position in fold_positions:
                    if position in self.player_frames:
                        frame = self.player_frames[position]
                        # フェードアウトアニメーションを作成
                        anim = frame.fade_out(1000)
                        # 各アニメーションの完了時に呼び出されるコールバックを設定
                        # ラムダ関数を使用せずに、functools.partialを使用して変数をバインド
                        from functools import partial
                        callback = partial(self.on_fade_animation_finished, position)
                        anim.finished.connect(callback)
                        self.fade_animations.append(anim)
                
                return
            
            # Foldになったプレイヤーがいない場合、通常の更新を実行
            self.update_player_frames(sorted_players)
            
            # 現在のデータを保存
            self.previous_players_data = sorted_players
            
        except FileNotFoundError:
            print("Error: 'status.json' file not found.")
        except json.JSONDecodeError:
            print("Error: Failed to decode 'status.json'. Please check the file format.")
        except Exception as e:
            print(f"Unexpected error during update_players: {e}")
    
    def remove_player_frame(self, position):
        """プレイヤーフレームを削除"""
        if position in self.player_frames:
            frame = self.player_frames[position]
            frame.setParent(None)
            del self.player_frames[position]
    
    def on_fade_animation_finished(self, position):
        """フェードアウトアニメーション完了時の処理"""
        print(f"Fade animation finished for position: {position}")
        
        # プレイヤーフレームを削除
        self.remove_player_frame(position)
        
        # 完了したアニメーションのカウンターをインクリメント
        self.fade_animation_completed += 1
        
        # 全てのフェードアウトアニメーションが完了したら、下詰めアニメーションを実行
        if self.fade_animation_completed >= len(self.fold_positions):
            self.update_layout_after_fold()
    
    def update_layout_after_fold(self):
        """Foldアニメーション後のレイアウト更新"""
        print("Updating layout after fold")
        
        try:
            # 最新のデータを取得
            with open("status.json", "r", encoding="utf-8") as f:
                data = json.load(f)
                
            # プレイヤーの並び順を指定（逆順）
            position_order = ["BB", "SB", "BU", "CO", "HJ", "LJ", "+1", "UTG"]
            
            # プレイヤーを並べ替え
            sorted_players = sorted(data["players"], key=lambda p: position_order.index(p["position"]))
            
            # FOLDしたプレイヤーを除外
            active_players = [p for p in sorted_players if p["action"] != "Fold"]
            
            # 現在のプレイヤーフレームを保持（アニメーション用）
            current_frames = []
            for position, frame in self.player_frames.items():
                current_frames.append(frame)
            
            # 新しいプレイヤーフレームを作成（まだレイアウトには追加しない）
            new_frames = []
            new_player_frames = {}
            
            for index, player in enumerate(active_players):
                # カード情報を取得（1枚ずつ処理）
                cards = player.get("cards", [])
                formatted_cards = self.format_cards_individually(cards)
                
                # エクイティ情報を取得
                equity = player.get("equity")
                
                # プレイヤーフレームを作成
                frame = PlayerFrame(
                    name=player["name"],
                    stack=player["stack"],
                    position=player["position"],
                    action=player["action"],
                    cards="-- --",  # 初期値は空白
                    equity=equity
                )
                
                # カード表示を更新（1枚ずつ処理）
                frame.update_cards(formatted_cards)
                
                # 新しいフレームを保持
                new_frames.append(frame)
                new_player_frames[player["position"]] = frame
            
            # Foldしたプレイヤー以外のアニメーションは廃止
            # 直接新しいフレームを配置する
            if current_frames:
                # 現在のフレームを削除
                for frame in current_frames:
                    frame.setParent(None)
                
                # 新しいフレームをレイアウトに追加
                for frame in new_frames:
                    self.player_info_layout.addWidget(frame)
                
                # プレイヤーフレームを更新
                self.player_frames = new_player_frames
                
                # 現在のデータを保存
                self.previous_players_data = sorted_players
                
                # アニメーション完了
                self.animation_in_progress = False
                self.timer.start()  # 更新を再開
            else:
                # 現在のフレームがない場合は、新しいフレームを直接追加
                for frame in new_frames:
                    self.player_info_layout.addWidget(frame)
                
                # プレイヤーフレームを更新
                self.player_frames = new_player_frames
                
                # 現在のデータを保存
                self.previous_players_data = sorted_players
                
                # アニメーション完了
                self.animation_in_progress = False
                self.timer.start()  # 更新を再開
        except Exception as e:
            print(f"Error updating layout after fold: {e}")
            # エラーが発生した場合は、アニメーションを終了
            self.animation_in_progress = False
            self.timer.start()
    
    def finish_layout_update(self, new_frames, new_player_frames, sorted_players):
        """アニメーション完了後のレイアウト更新"""
        print("Finishing layout update")
        
        # 現在のフレームを削除
        for i in reversed(range(1, self.player_info_layout.count())):
            widget = self.player_info_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # 新しいフレームをレイアウトに追加
        for frame in new_frames:
            self.player_info_layout.addWidget(frame)
        
        # プレイヤーフレームを更新
        self.player_frames = new_player_frames
        
        # 現在のデータを保存
        self.previous_players_data = sorted_players
        
        # アニメーション完了
        self.animation_in_progress = False
        self.timer.start()  # 更新を再開
    
    def update_player_frames(self, players_data):
        """プレイヤーフレームを更新"""
        # 一度全て削除（スペーサーは0番目なので1番目以降を削除）
        for i in reversed(range(1, self.player_info_layout.count())):
            widget = self.player_info_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # プレイヤーフレームを初期化
        self.player_frames = {}
        
        # FOLDしたプレイヤーを除外
        active_players = [p for p in players_data if p["action"] != "Fold"]
        
        # プレイヤー枠を表示
        for index, player in enumerate(active_players):
            # カード情報を取得（1枚ずつ処理）
            cards = player.get("cards", [])
            formatted_cards = self.format_cards_individually(cards)
            
            # エクイティ情報を取得
            equity = player.get("equity")
            
            # プレイヤーフレームを作成
            frame = PlayerFrame(
                name=player["name"],
                stack=player["stack"],
                position=player["position"],
                action=player["action"],
                cards="-- --",  # 初期値は空白
                equity=equity
            )
            
            # カード表示を更新（1枚ずつ処理）
            frame.update_cards(formatted_cards)
            
            # プレイヤーフレームをレイアウトに追加（スペーサーは0番目なので、単純に追加すれば下から詰める）
            self.player_info_layout.addWidget(frame)
            
            # プレイヤーフレームを保持
            self.player_frames[player["position"]] = frame
            
    def format_cards_individually(self, cards):
        """カード情報を1枚ずつ処理して表示用にフォーマット"""
        if not cards:
            return []
        
        # デバッグ出力
        print(f"Cards from status.json: {cards}")
        
        # カードを1枚ずつ内部形式に変換してから表示用にフォーマット
        from card_utils import convert_legacy_to_internal, get_colored_card_display
        
        formatted_cards = []
        for card in cards:
            internal_format = convert_legacy_to_internal(card)
            if internal_format:
                card_display = get_colored_card_display(internal_format)
                if card_display != "--":
                    formatted_cards.append(card_display)
        
        # デバッグ出力
        print(f"Formatted cards individually: {formatted_cards}")
        
        return formatted_cards


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
