from pypokerengine.engine.card import Card

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

# スートの数値表現（常に2桁で表現）
SUIT_VALUES = {
    "S": "16",  # スペード
    "H": "08",  # ハート
    "D": "04",  # ダイヤ
    "C": "02",  # クラブ
}

# スートの数値から文字表現へのマッピング
SUIT_FROM_VALUE = {
    "16": "S",  # スペード
    "08": "H",  # ハート
    "04": "D",  # ダイヤ
    "02": "C",  # クラブ
    # 互換性のために1桁も対応
    "8": "H", "4": "D", "2": "C",
}

# ランクの数値表現（常に2桁で表現）
RANK_VALUES = {
    "A": "14", "K": "13", "Q": "12", "J": "11", "T": "10", "10": "10",
    "9": "09", "8": "08", "7": "07", "6": "06", "5": "05", "4": "04", "3": "03", "2": "02"
}

# ランクの数値から文字表現へのマッピング
RANK_FROM_VALUE = {
    "14": "A", "13": "K", "12": "Q", "11": "J", "10": "T",
    "09": "9", "08": "8", "07": "7", "06": "6", "05": "5", "04": "4", "03": "3", "02": "2",
    # 互換性のために1桁も対応
    "9": "9", "8": "8", "7": "7", "6": "6", "5": "5", "4": "4", "3": "3", "2": "2",
}

def get_suit_symbol(suit):
    """スートを記号に変換する関数"""
    # 文字列の場合
    if isinstance(suit, str):
        # 2桁の数値表現の場合（"16", "08"など）
        if suit in SUIT_FROM_VALUE:
            suit_char = SUIT_FROM_VALUE[suit]
            return SUIT_DISPLAY.get(suit_char, "?")
        # 通常の文字表現の場合（"S", "H"など）
        return SUIT_DISPLAY.get(suit, "?")
    
    # 数値の場合
    suit_map = {
        16: "♠",  # スペード
        8: "♥",   # ハート
        4: "♦",   # ダイヤ
        2: "♣",   # クラブ
    }
    
    if suit in suit_map:
        return suit_map[suit]
    elif suit & Card.SPADE:  # 16とのビット演算
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
        # 2桁の数値表現の場合（"14", "02"など）
        if rank in RANK_FROM_VALUE:
            rank_char = RANK_FROM_VALUE[rank]
            if rank_char == "T":
                return "10"
            return rank_char
        # 通常の文字表現の場合（"A", "K"など）
        return RANK_DISPLAY.get(rank, rank)
    
    # 数値の場合
    rank_map = {
        14: "A", 13: "K", 12: "Q", 11: "J", 10: "10",
        2: "2", 3: "3", 4: "4", 5: "5", 
        6: "6", 7: "7", 8: "8", 9: "9", 1: "A"  # 1もAとして扱う
    }
    return rank_map.get(rank, str(rank))

def format_card_internal(suit, rank):
    """スートとランクを内部形式（スート,ランク）に変換する関数"""
    # スートを2桁の文字列に変換
    if isinstance(suit, int):
        suit_str = f"{suit:02d}"
    elif suit in SUIT_VALUES:
        suit_str = SUIT_VALUES[suit]
    else:
        suit_str = suit
    
    # ランクを2桁の文字列に変換
    if isinstance(rank, int):
        rank_str = f"{rank:02d}"
    elif rank in RANK_VALUES:
        rank_str = RANK_VALUES[rank]
    else:
        rank_str = rank
    
    return f"{suit_str},{rank_str}"

def parse_card_internal(card_str):
    """内部形式（スート,ランク）からスートとランクを取得する関数"""
    if "," in card_str:
        suit_str, rank_str = card_str.split(",")
        return suit_str, rank_str
    return None, None

def get_card_display(card):
    """カードを人間が読みやすい形式で表示する関数"""
    # カードオブジェクトの場合
    if hasattr(card, 'suit') and hasattr(card, 'rank'):
        suit_symbol = get_suit_symbol(card.suit)
        rank_display = get_rank_display(card.rank)
        return f"{rank_display}{suit_symbol}"
    
    # 内部形式（スート,ランク）の場合
    elif isinstance(card, str) and "," in card:
        suit_str, rank_str = card.split(",")
        suit_symbol = get_suit_symbol(suit_str)
        rank_display = get_rank_display(rank_str)
        return f"{rank_display}{suit_symbol}"
    
    # 文字列形式の場合（例：S10, H5）
    elif isinstance(card, str):
        if len(card) >= 2 and card[0] in "SHDC":
            suit = card[0]
            rank = card[1:]
            # 10の場合はTになっているので変換
            if rank == "T":
                rank = "10"
            # スートを記号に変換
            suit_symbol = get_suit_symbol(suit)
            return f"{rank}{suit_symbol}"
        else:
            # 旧形式の数値表現の文字列の場合（例："24", "811", "1614"）
            try:
                # カンマが含まれていない場合は旧形式と判断
                if "," not in card:
                    # まず内部形式に変換
                    internal_format = convert_legacy_to_internal(card)
                    if internal_format:
                        # 内部形式から表示形式に変換
                        suit_str, rank_str = internal_format.split(",")
                        suit_symbol = get_suit_symbol(suit_str)
                        rank_display = get_rank_display(rank_str)
                        return f"{rank_display}{suit_symbol}"
            except (ValueError, TypeError):
                return "--"
    
    # その他の場合
    return "--"

def convert_legacy_to_internal(card):
    """旧形式のカード表現を内部形式（スート,ランク）に変換する関数"""
    if isinstance(card, str):
        # 既に内部形式の場合はそのまま返す
        if "," in card:
            return card
            
        # 文字列形式（例：S10, H5）の場合
        if len(card) >= 2 and card[0] in "SHDC":
            suit = card[0]
            rank = card[1:]
            # スートとランクを内部形式に変換
            return format_card_internal(suit, rank)
            
        # 旧形式の数値表現の場合
        try:
            card_int = int(card)
            
            # 旧形式から新形式への変換マッピング
            legacy_mapping = {
                "1614": "16,14",  # A♠
                "811": "08,11",   # J♥
                "210": "02,10",   # 10♣
                "162": "16,02",   # 2♠
                "85": "08,05",    # 5♥
                # 追加のマッピング
                "412": "04,12",   # Q♦
                "168": "16,08",   # 8♠
                "86": "08,06"     # 6♥
            }
            
            if card in legacy_mapping:
                return legacy_mapping[card]
            
            # 旧形式の解析ロジック
            if card_int < 100:  # 2桁の場合
                suit = card_int // 10
                rank = card_int % 10
            elif card_int < 1000:  # 3桁の場合
                suit = card_int // 100
                rank = card_int % 100
            else:  # 4桁以上の場合
                suit = card_int // 100
                rank = card_int % 100
            
            # スートとランクを内部形式に変換
            return format_card_internal(suit, rank)
        except (ValueError, TypeError):
            return None
    
    # カードオブジェクトの場合
    elif hasattr(card, 'suit') and hasattr(card, 'rank'):
        return format_card_internal(card.suit, card.rank)
    
    return None

# 内部形式からpypokerengineのCardオブジェクトへの変換関数
def convert_internal_to_pypoker_card(internal_format):
    """内部形式（スート,ランク）からpypokerengineのCardオブジェクトに変換する関数"""
    if not internal_format or "," not in internal_format:
        return None
        
    try:
        suit_str, rank_str = internal_format.split(",")
        suit = int(suit_str)
        rank = int(rank_str)
        
        # pypokerengineのCardオブジェクトを作成
        from pypokerengine.engine.card import Card
        return Card(suit, rank)
    except (ValueError, TypeError):
        return None

# 内部形式からpypokerengineのCardオブジェクトへの変換関数（別名）
def convert_internal_to_pypoker(internal_format):
    """内部形式（スート,ランク）からpypokerengineのCardオブジェクトに変換する関数"""
    return convert_internal_to_pypoker_card(internal_format)

# pypokerengineのCardオブジェクトから内部形式への変換関数
def convert_pypoker_to_internal(card):
    """pypokerengineのCardオブジェクトから内部形式（スート,ランク）に変換する関数"""
    if hasattr(card, 'suit') and hasattr(card, 'rank'):
        return format_card_internal(card.suit, card.rank)
    return None

# スートごとの色情報（カード表示用）
SUIT_COLORS = {
    "♠": "black",    # スペード：黒
    "♦": "#0000CC",  # ダイヤ：濃い青
    "♥": "#CC0000",  # ハート：濃い赤
    "♣": "#006600",  # クラブ：濃い緑
}

def get_suit_color(suit_symbol):
    """スート記号から色を取得する関数"""
    return SUIT_COLORS.get(suit_symbol, "black")

def get_colored_card_display(card):
    """カードを表示する関数（色情報付き）"""
    # カードオブジェクトの場合
    if hasattr(card, 'suit') and hasattr(card, 'rank'):
        suit_symbol = get_suit_symbol(card.suit)
        rank_display = get_rank_display(card.rank)
    # 内部形式（スート,ランク）の場合
    elif isinstance(card, str) and "," in card:
        suit_str, rank_str = card.split(",")
        suit_symbol = get_suit_symbol(suit_str)
        rank_display = get_rank_display(rank_str)
    # その他の場合は通常の表示を返す
    else:
        return get_card_display(card)
    
    # 通常のテキスト形式で返す
    return f"{rank_display}{suit_symbol}"

def format_cards_for_display(cards):
    """カード情報を表示用にフォーマット"""
    if not cards:
        return "-- --"
    
    # デバッグ出力
    print(f"Cards from status.json: {cards}")
    
    # カードを内部形式に変換してから表示用にフォーマット
    internal_cards = [convert_legacy_to_internal(card) for card in cards]
    formatted_cards = [get_colored_card_display(card) for card in internal_cards if card]
    
    # デバッグ出力
    print(f"Internal cards: {internal_cards}")
    print(f"Formatted cards: {formatted_cards}")
    
    # カードを表示
    if len(formatted_cards) >= 2:
        return f"{formatted_cards[0]} {formatted_cards[1]}"
    elif len(formatted_cards) == 1:
        return f"{formatted_cards[0]} --"
    else:
        return "-- --"
