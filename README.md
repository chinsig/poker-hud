# Poker HUD

ポーカーのハンズヒストリーを記録・分析するためのGUIアプリケーションです。PyPokerEngineをベースに、直感的な操作でポーカーのプレイ状況を記録できます。

## 特徴

- 直感的なGUIインターフェース
- プレイヤー数の動的な変更（2-8人）
- リアルタイムのエクイティ計算
- メインポット/サイドポットの自動計算
- ハンドヒストリーのJSONエクスポート/インポート
- UNDO機能によるアクション修正
- 画面サイズの切り替え（標準/コンパクトモード）

## 必要要件

- Python 3.x
- PySide6
- PyPokerEngine

## インストール

1. リポジトリをクローン:
```bash
git clone https://github.com/chinsig/poker-hud.git
cd poker-hud
```

2. PyPokerEngineをインストール:
```bash
cd pypokerengine
pip install -e .
cd ..
```

3. 必要なパッケージをインストール:
```bash
pip install PySide6
```

## 使用方法

1. アプリケーションを起動:
```bash
## メイン画面起動
python poker_gui_engine.py

## プライヤー画面起動
python player.py
```

2. 基本設定:
   - メニューバーの「Action」から「Set Blinds」でブラインド額を設定
   - 「Set Stacks」で全プレイヤーのスタックを設定
   - 「Set BU」でディーラーポジションを設定
   - 「Change number of players」でプレイヤー数を変更

3. プレイの記録:
   - 各プレイヤーのカードを「Set Hand」ボタンで設定
   - アクションボタン（Fold/Call/Bet/Check/Raise/Allin）でアクションを記録
   - 「Next Street」でストリートを進める
   - 「Next Hand」で次のハンドに移動

4. その他の機能:
   - 「File」メニューからセッション状態の保存/読み込み
   - 「表示」メニューから画面サイズの変更
   - 「UNDO」ボタンで直前のアクションを取り消し

## ライセンス

MIT License

## 謝辞

このプロジェクトは[PyPokerEngine](https://github.com/ishikota/PyPokerEngine)をベースに開発されています。