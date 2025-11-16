"""
GUI モジュール
CustomTkinterを使用したユーザーインターフェース
"""
import customtkinter as ctk
from typing import Callable
from config import Config

class SpeedTradeGUI:
    """スピード注文GUIクラス"""
    
    def __init__(self):
        """初期化"""
        self.root = None
        self.price_label = None
        self.status_label = None
        self.size_entry = None
        self.position_frame = None
        
        # コールバック関数
        self.on_buy_callback = None
        self.on_sell_callback = None
        self.on_limit_buy_callback = None  # 指値買い
        self.on_limit_sell_callback = None  # 指値売り
        self.on_close_callback = None
        self.on_symbol_change_callback = None
        self.on_cancel_order_callback = None  # 注文キャンセル
        
        # 現在の価格
        self.current_prices = {}
        self.current_symbol = Config.DEFAULT_SYMBOL
        # 前回価格（変化を表示するため）
        self.previous_price = None
        self.price_change_label = None  # 価格変化表示用ラベル
        self.price_24h_change_label = None  # 24時間変動率表示用ラベル
        
        # WebSocket遅延管理
        self.last_price_update = None
        self.lag_indicator = None
        
        # アカウントレバレッジ表示
        self.account_leverage_label = None
        
        # アカウント情報表示
        self.account_equity_label = None
        self.account_spot_label = None
        self.account_perps_label = None
        
        # 約定ログ
        self.log_textbox = None
        
        # 現在のポジションリスト（決済ダイアログで使用）
        self.current_positions = []
        
        # 通貨ペアリスト（出来高順）
        self.available_symbols = Config.AVAILABLE_SYMBOLS
        
    def create_window(self, symbols=None):
        """メインウィンドウを作成
        
        Args:
            symbols: 通貨ペアのリスト（出来高順など）。Noneの場合はデフォルトリストを使用
        """
        # 通貨ペアリストを設定
        if symbols:
            self.available_symbols = symbols
        
        # 外観設定
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme(Config.THEME)
        
        # メインウィンドウ
        self.root = ctk.CTk()
        self.root.title("Hyperliquid Speed Trade")
        self.root.geometry(f"{Config.WINDOW_WIDTH}x{Config.WINDOW_HEIGHT}")
        
        # ウィンドウを最前面に表示するオプション
        self.root.attributes('-topmost', True)
        
        # グリッドの設定
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(3, weight=1)  # ポジションエリア
        self.root.grid_rowconfigure(4, weight=0)  # 未約定注文エリア（新規）
        self.root.grid_rowconfigure(5, weight=0)  # 約定ログエリア
        
        # ヘッダー
        self._create_header()
        
        # 価格表示エリア
        self._create_price_area()
        
        # 注文パネル
        self._create_order_panel()
        
        # ポジション表示エリア
        self._create_position_area()
        
        # 未約定注文エリア（新規）
        self._create_open_orders_area()
        
        # 約定ログエリア
        self._create_log_area()
        
        # ステータスバー
        self._create_status_bar()
        
        # ショートカットキーバインドを設定
        self._setup_shortcut_keys()
        
    def _setup_shortcut_keys(self):
        """ショートカットキーバインドを設定"""
        # F1: 買い注文（成行）
        self.root.bind('<F1>', lambda e: self._execute_buy_market())
        # F2: 売り注文（成行）
        self.root.bind('<F2>', lambda e: self._execute_sell_market())
        # F3: 指値買い
        self.root.bind('<F3>', lambda e: self._execute_buy_limit())
        # F4: 指値売り
        self.root.bind('<F4>', lambda e: self._execute_sell_limit())
        # F5: 全決済
        self.root.bind('<F5>', lambda e: self._on_close_all_clicked())
        # Esc: ダイアログ閉じる/キャンセル（デフォルト動作に任せる）
        self.root.bind('<Escape>', lambda e: self._handle_escape())
        # Enter: 注文送信確定（フォーカスがエントリー上にある場合のみ）
        self.root.bind('<Return>', lambda e: self._handle_enter())
        
        # フォーカスをウィンドウ全体に設定（どこでもショートカットが効くように）
        self.root.focus_set()
        
    def _execute_buy_market(self):
        """F1キー: 成行買い注文を即座に実行"""
        try:
            size = float(self.size_entry.get())
            if size <= 0:
                self.show_error("サイズは正の数である必要があります")
                return
            
            # 確認なしで即座に実行（MT4ライク）
            if not self.confirm_orders_var.get():
                if self.on_buy_callback:
                    self.on_buy_callback(self.current_symbol, size)
            else:
                # 確認が必要な場合は通常のフロー
                self._on_buy_clicked()
        except ValueError:
            self.show_error("無効なサイズです")
    
    def _execute_sell_market(self):
        """F2キー: 成行売り注文を即座に実行"""
        try:
            size = float(self.size_entry.get())
            if size <= 0:
                self.show_error("サイズは正の数である必要があります")
                return
            
            # 確認なしで即座に実行（MT4ライク）
            if not self.confirm_orders_var.get():
                if self.on_sell_callback:
                    self.on_sell_callback(self.current_symbol, size)
            else:
                # 確認が必要な場合は通常のフロー
                self._on_sell_clicked()
        except ValueError:
            self.show_error("無効なサイズです")
    
    def _execute_buy_limit(self):
        """F3キー: 指値買い注文"""
        # 指値モードに切り替え（必要に応じて）
        self.order_type.set("limit")
        self._on_order_type_changed()
        # 通常のフローで実行
        self._on_buy_clicked()
    
    def _execute_sell_limit(self):
        """F4キー: 指値売り注文"""
        # 指値モードに切り替え（必要に応じて）
        self.order_type.set("limit")
        self._on_order_type_changed()
        # 通常のフローで実行
        self._on_sell_clicked()
    
    def _handle_escape(self):
        """Escキー: ダイアログを閉じる"""
        # フォーカスをメインウィンドウに戻す
        self.root.focus_set()
        # 最前面のトップレベルウィンドウがある場合は閉じる（基本的にTkinterが自動処理）
    
    def _handle_enter(self):
        """Enterキー: フォーカスされているエントリーから注文を送信"""
        # フォーカスがサイズエントリーにある場合は買い注文
        if self.root.focus_get() == self.size_entry:
            self._on_buy_clicked()
        # フォーカスが価格エントリーにある場合は指値買い
        elif hasattr(self, 'price_entry') and self.root.focus_get() == self.price_entry:
            self._on_buy_clicked()
        
    def _create_header(self):
        """ヘッダーを作成"""
        header_frame = ctk.CTkFrame(self.root)
        header_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="⚡ Hyperliquid Speed Trade",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=10)
        
        network_text = "🟢 テストネット" if Config.USE_TESTNET else "🔴 メインネット"
        network_label = ctk.CTkLabel(
            header_frame,
            text=network_text,
            font=ctk.CTkFont(size=12)
        )
        network_label.pack()
        
        # アカウント情報フレーム
        account_info_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        account_info_frame.pack(pady=3)
        
        # アカウントレバレッジ
        self.account_leverage_label = ctk.CTkLabel(
            account_info_frame,
            text="📊 Leverage: --x",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#FFA500"
        )
        self.account_leverage_label.pack(side="left", padx=5)
        
        # Account Equity
        self.account_equity_label = ctk.CTkLabel(
            account_info_frame,
            text="💰 Equity: $--",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color="#44FF44"
        )
        self.account_equity_label.pack(side="left", padx=5)
        
        # Spot
        self.account_spot_label = ctk.CTkLabel(
            account_info_frame,
            text="Spot: $--",
            font=ctk.CTkFont(size=10),
            text_color="#AAAAAA"
        )
        self.account_spot_label.pack(side="left", padx=3)
        
        # Perps
        self.account_perps_label = ctk.CTkLabel(
            account_info_frame,
            text="Perps: $--",
            font=ctk.CTkFont(size=10),
            text_color="#AAAAAA"
        )
        self.account_perps_label.pack(side="left", padx=3)
        
        # 確認ダイアログのトグル
        self.confirm_orders_var = ctk.BooleanVar(value=Config.CONFIRM_ORDERS)
        confirm_toggle = ctk.CTkCheckBox(
            header_frame,
            text="注文確認ダイアログを表示",
            variable=self.confirm_orders_var,
            font=ctk.CTkFont(size=11)
        )
        confirm_toggle.pack(pady=5)
    
    def _create_price_area(self):
        """価格表示エリアを作成"""
        price_frame = ctk.CTkFrame(self.root)
        price_frame.grid(row=1, column=0, padx=10, pady=10, sticky="ew")
        
        # 通貨ペア選択
        symbol_select_frame = ctk.CTkFrame(price_frame)
        symbol_select_frame.pack(pady=5)
        
        symbol_label = ctk.CTkLabel(
            symbol_select_frame,
            text="通貨ペア:",
            font=ctk.CTkFont(size=14)
        )
        symbol_label.pack(side="left", padx=5)
        
        self.symbol_combo = ctk.CTkComboBox(
            symbol_select_frame,
            values=self.available_symbols,
            command=self._on_symbol_changed,
            width=150,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        # デフォルトは出来高順リストの最初の通貨
        default_symbol = self.available_symbols[0] if self.available_symbols else Config.DEFAULT_SYMBOL
        self.symbol_combo.set(default_symbol)
        self.current_symbol = default_symbol
        self.symbol_combo.pack(side="left", padx=5)
        
        self.symbol_label = ctk.CTkLabel(
            price_frame,
            text=f"{self.current_symbol}-USD",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.symbol_label.pack(pady=5)
        
        # 価格表示（MT4ライクな大きな表示）
        price_display_frame = ctk.CTkFrame(price_frame, fg_color="transparent")
        price_display_frame.pack(pady=10)
        
        self.price_label = ctk.CTkLabel(
            price_display_frame,
            text="価格: ---.--",
            font=ctk.CTkFont(size=48, weight="bold")
        )
        self.price_label.pack()
        
        # 価格変化表示（前回価格からの変化）
        self.price_change_label = ctk.CTkLabel(
            price_display_frame,
            text="",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        self.price_change_label.pack(pady=2)
        
        # 24時間変動率（将来実装予定、今はプレースホルダー）
        self.price_24h_change_label = ctk.CTkLabel(
            price_display_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        self.price_24h_change_label.pack(pady=2)
        
        update_label = ctk.CTkLabel(
            price_frame,
            text="更新待ち...",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        update_label.pack(pady=5)
        
        # ワンクリック注文パネル（価格の上下に配置）
        one_click_frame = ctk.CTkFrame(price_frame, fg_color="transparent")
        one_click_frame.pack(pady=10)
        
        # 買いボタン（価格の上）
        self.one_click_buy_button = ctk.CTkButton(
            one_click_frame,
            text="⬆️ 買い (BUY)",
            command=self._on_one_click_buy,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="green",
            hover_color="darkgreen",
            width=200,
            height=45
        )
        self.one_click_buy_button.pack(pady=5)
        
        # 売りボタン（価格の下）
        self.one_click_sell_button = ctk.CTkButton(
            one_click_frame,
            text="⬇️ 売り (SELL)",
            command=self._on_one_click_sell,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="red",
            hover_color="darkred",
            width=200,
            height=45
        )
        self.one_click_sell_button.pack(pady=5)
    
    def _create_order_panel(self):
        """注文パネルを作成"""
        order_frame = ctk.CTkFrame(self.root)
        order_frame.grid(row=2, column=0, padx=10, pady=10, sticky="ew")
        
        # 注文タイプ選択
        self.order_type_frame = ctk.CTkFrame(order_frame, fg_color="transparent")
        self.order_type_frame.pack(pady=5)
        
        order_type_label = ctk.CTkLabel(
            self.order_type_frame,
            text="注文タイプ:",
            font=ctk.CTkFont(size=12)
        )
        order_type_label.pack(side="left", padx=5)
        
        self.order_type = ctk.StringVar(value="market")  # デフォルトは成行
        
        market_radio = ctk.CTkRadioButton(
            self.order_type_frame,
            text="成行",
            variable=self.order_type,
            value="market",
            command=self._on_order_type_changed,
            font=ctk.CTkFont(size=12)
        )
        market_radio.pack(side="left", padx=5)
        
        limit_radio = ctk.CTkRadioButton(
            self.order_type_frame,
            text="指値",
            variable=self.order_type,
            value="limit",
            command=self._on_order_type_changed,
            font=ctk.CTkFont(size=12)
        )
        limit_radio.pack(side="left", padx=5)
        
        # 価格入力（指値用）
        self.price_frame = ctk.CTkFrame(order_frame, fg_color="transparent")
        self.price_frame.pack(pady=5)
        
        price_label = ctk.CTkLabel(
            self.price_frame,
            text="指値価格 ($):",
            font=ctk.CTkFont(size=14)
        )
        price_label.pack(pady=5)
        
        self.price_entry = ctk.CTkEntry(
            self.price_frame,
            width=200,
            font=ctk.CTkFont(size=16),
            justify="center",
            placeholder_text="価格を入力"
        )
        self.price_entry.pack(pady=5)
        
        # 価格フレームを最初は非表示
        self.price_frame.pack_forget()
        
        # サイズ入力
        size_label = ctk.CTkLabel(
            order_frame,
            text="注文サイズ:",
            font=ctk.CTkFont(size=14)
        )
        size_label.pack(pady=5)
        
        self.size_entry = ctk.CTkEntry(
            order_frame,
            width=200,
            font=ctk.CTkFont(size=16),
            justify="center"
        )
        self.size_entry.pack(pady=5)
        self.size_entry.insert(0, str(Config.DEFAULT_SIZE))
        
        # プリセットサイズボタン
        preset_frame = ctk.CTkFrame(order_frame, fg_color="transparent")
        preset_frame.pack(pady=5)
        
        preset_label = ctk.CTkLabel(
            preset_frame,
            text="プリセット:",
            font=ctk.CTkFont(size=10)
        )
        preset_label.pack(side="left", padx=5)
        
        for size in [0.01, 0.05, 0.1]:
            btn = ctk.CTkButton(
                preset_frame,
                text=str(size),
                command=lambda s=size: self._set_size(s),
                font=ctk.CTkFont(size=10),
                width=50,
                height=25
            )
            btn.pack(side="left", padx=2)
        
        # ボタンフレーム
        button_frame = ctk.CTkFrame(order_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        # 買いボタン
        buy_button = ctk.CTkButton(
            button_frame,
            text="買い (BUY)",
            command=self._on_buy_clicked,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="green",
            hover_color="darkgreen",
            width=180,
            height=50
        )
        buy_button.pack(side="left", padx=10)
        
        # 売りボタン
        sell_button = ctk.CTkButton(
            button_frame,
            text="売り (SELL)",
            command=self._on_sell_clicked,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color="red",
            hover_color="darkred",
            width=180,
            height=50
        )
        sell_button.pack(side="left", padx=10)
    
    def _create_position_area(self):
        """ポジション表示エリアを作成"""
        position_outer_frame = ctk.CTkFrame(self.root)
        position_outer_frame.grid(row=3, column=0, padx=10, pady=10, sticky="nsew")
        
        # タイトルと全決済ボタンのフレーム（固定）
        title_frame = ctk.CTkFrame(position_outer_frame)
        title_frame.pack(pady=5, fill="x", padx=10)
        
        title_label = ctk.CTkLabel(
            title_frame,
            text="現在のポジション",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.pack(side="left", padx=5)
        
        # 全決済ボタン（常に表示）
        self.close_all_button = ctk.CTkButton(
            title_frame,
            text="🔥 全決済",
            command=self._on_close_all_clicked,
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#FF6B00",
            hover_color="#CC5500",
            width=120,
            height=35,
            corner_radius=8
        )
        self.close_all_button.pack(side="right", padx=5)
        
        # スクロール可能なフレーム
        self.position_frame = ctk.CTkScrollableFrame(
            position_outer_frame,
            width=760,
            height=150
        )
        self.position_frame.pack(pady=5, padx=5, fill="both", expand=True)
        
        # 初期メッセージ
        no_position_label = ctk.CTkLabel(
            self.position_frame,
            text="ポジションがありません",
            text_color="gray"
        )
        no_position_label.pack(pady=20)
    
    def _create_open_orders_area(self):
        """未約定注文エリアを作成"""
        orders_outer_frame = ctk.CTkFrame(self.root)
        orders_outer_frame.grid(row=4, column=0, padx=10, pady=5, sticky="ew")
        
        # タイトル
        title_label = ctk.CTkLabel(
            orders_outer_frame,
            text="📌 未約定注文（オープンオーダー）",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        title_label.pack(pady=5)
        
        # スクロール可能なフレーム（高さは低めに設定）
        self.open_orders_frame = ctk.CTkScrollableFrame(
            orders_outer_frame,
            width=760,
            height=80
        )
        self.open_orders_frame.pack(pady=5, padx=5, fill="x")
        
        # 初期メッセージ
        no_orders_label = ctk.CTkLabel(
            self.open_orders_frame,
            text="未約定注文がありません",
            text_color="gray",
            font=ctk.CTkFont(size=10)
        )
        no_orders_label.pack(pady=10)
    
    def _create_log_area(self):
        """約定ログエリアを作成"""
        log_frame = ctk.CTkFrame(self.root)
        log_frame.grid(row=5, column=0, padx=10, pady=5, sticky="ew")
        
        log_title = ctk.CTkLabel(
            log_frame,
            text="📋 約定ログ",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        log_title.pack(pady=3)
        
        # スクロール可能なテキストボックス
        self.log_textbox = ctk.CTkTextbox(
            log_frame,
            width=760,
            height=100,
            font=ctk.CTkFont(size=10),
            wrap="none"
        )
        self.log_textbox.pack(pady=5, padx=5, fill="both")
        
        # 初期メッセージ
        self.log_textbox.insert("1.0", "約定ログがここに表示されます...\n")
        self.log_textbox.configure(state="disabled")  # 読み取り専用
    
    def _create_status_bar(self):
        """ステータスバーを作成"""
        status_frame = ctk.CTkFrame(self.root, height=30)
        status_frame.grid(row=6, column=0, padx=10, pady=5, sticky="ew")
        
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="準備完了",
            font=ctk.CTkFont(size=10),
            anchor="w"
        )
        self.status_label.pack(side="left", padx=10)
        
        # 接続状態インジケーター（右側）
        connection_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        connection_frame.pack(side="right", padx=10)
        
        # WebSocket遅延インジケーター
        self.lag_indicator = ctk.CTkLabel(
            connection_frame,
            text="🟢 接続良好",
            font=ctk.CTkFont(size=10),
            anchor="e"
        )
        self.lag_indicator.pack(side="left", padx=5)
        
        # API接続状態インジケーター
        self.api_status_indicator = ctk.CTkLabel(
            connection_frame,
            text="🟢 API接続",
            font=ctk.CTkFont(size=10),
            text_color="green"
        )
        self.api_status_indicator.pack(side="left", padx=5)
        
        # レートリミット状態インジケーター
        self.rate_limit_indicator = ctk.CTkLabel(
            connection_frame,
            text="📊 レート: --/--",
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        self.rate_limit_indicator.pack(side="left", padx=5)
    
    def _on_one_click_buy(self):
        """ワンクリック買い注文"""
        try:
            size = float(self.size_entry.get())
            if size <= 0:
                self.show_error("サイズは正の数である必要があります")
                return
            
            # 確認なしで即座に実行（MT4ライク）
            if not self.confirm_orders_var.get():
                if self.on_buy_callback:
                    self.on_buy_callback(self.current_symbol, size)
            else:
                # 確認が必要な場合は通常のフロー
                self._on_buy_clicked()
        except ValueError:
            self.show_error("無効なサイズです")
    
    def _on_one_click_sell(self):
        """ワンクリック売り注文"""
        try:
            size = float(self.size_entry.get())
            if size <= 0:
                self.show_error("サイズは正の数である必要があります")
                return
            
            # 確認なしで即座に実行（MT4ライク）
            if not self.confirm_orders_var.get():
                if self.on_sell_callback:
                    self.on_sell_callback(self.current_symbol, size)
            else:
                # 確認が必要な場合は通常のフロー
                self._on_sell_clicked()
        except ValueError:
            self.show_error("無効なサイズです")
    
    def _on_symbol_changed(self, new_symbol: str):
        """通貨ペアが変更された時"""
        self.current_symbol = new_symbol
        self.symbol_label.configure(text=f"{new_symbol}-USD")
        
        # 価格表示をリセット
        if new_symbol in self.current_prices:
            price = float(self.current_prices[new_symbol])
            self.price_label.configure(text=f"${price:,.2f}")
            self.previous_price = price  # リセット
        else:
            self.price_label.configure(text="価格: ---.--")
            self.previous_price = None
        
        # 価格変化表示をリセット
        if self.price_change_label:
            self.price_change_label.configure(text="")
        
        # コールバックを呼び出す
        if self.on_symbol_change_callback:
            self.on_symbol_change_callback(new_symbol)
    
    def _set_size(self, size: float):
        """プリセットサイズをセット"""
        self.size_entry.delete(0, "end")
        self.size_entry.insert(0, str(size))
    
    def _on_order_type_changed(self):
        """注文タイプが変更された時"""
        if self.order_type.get() == "limit":
            # 指値が選択された場合、価格入力を表示（注文タイプフレームの直後）
            self.price_frame.pack(after=self.order_type_frame, pady=5)
            
            # 現在価格を自動入力
            if self.current_symbol in self.current_prices:
                current_price = float(self.current_prices[self.current_symbol])
                self.price_entry.delete(0, "end")
                self.price_entry.insert(0, str(current_price))
        else:
            # 成行が選択された場合、価格入力を非表示
            self.price_frame.pack_forget()
    
    def _on_buy_clicked(self):
        """買いボタンがクリックされた時"""
        try:
            size = float(self.size_entry.get())
            if size <= 0:
                self.show_error("サイズは正の数である必要があります")
                return
            
            order_type = self.order_type.get()
            
            # 指値注文の場合は価格も取得
            if order_type == "limit":
                try:
                    price = float(self.price_entry.get())
                    if price <= 0:
                        self.show_error("価格は正の数である必要があります")
                        return
                except ValueError:
                    self.show_error("無効な価格です")
                    return
                
                # 確認ダイアログを表示（トグルで設定）
                if self.confirm_orders_var.get():
                    if self._confirm_order(self.current_symbol, "買い（指値）", size, price):
                        if self.on_limit_buy_callback:
                            self.on_limit_buy_callback(self.current_symbol, size, price)
                else:
                    if self.on_limit_buy_callback:
                        self.on_limit_buy_callback(self.current_symbol, size, price)
            else:
                # 成行注文
                # 確認ダイアログを表示（トグルで設定）
                if self.confirm_orders_var.get():
                    if self._confirm_order(self.current_symbol, "買い（成行）", size):
                        if self.on_buy_callback:
                            self.on_buy_callback(self.current_symbol, size)
                else:
                    if self.on_buy_callback:
                        self.on_buy_callback(self.current_symbol, size)
        except ValueError:
            self.show_error("無効なサイズです")
    
    def _on_sell_clicked(self):
        """売りボタンがクリックされた時"""
        try:
            size = float(self.size_entry.get())
            if size <= 0:
                self.show_error("サイズは正の数である必要があります")
                return
            
            order_type = self.order_type.get()
            
            # 指値注文の場合は価格も取得
            if order_type == "limit":
                try:
                    price = float(self.price_entry.get())
                    if price <= 0:
                        self.show_error("価格は正の数である必要があります")
                        return
                except ValueError:
                    self.show_error("無効な価格です")
                    return
                
                # 確認ダイアログを表示（トグルで設定）
                if self.confirm_orders_var.get():
                    if self._confirm_order(self.current_symbol, "売り（指値）", size, price):
                        if self.on_limit_sell_callback:
                            self.on_limit_sell_callback(self.current_symbol, size, price)
                else:
                    if self.on_limit_sell_callback:
                        self.on_limit_sell_callback(self.current_symbol, size, price)
            else:
                # 成行注文
                # 確認ダイアログを表示（トグルで設定）
                if self.confirm_orders_var.get():
                    if self._confirm_order(self.current_symbol, "売り（成行）", size):
                        if self.on_sell_callback:
                            self.on_sell_callback(self.current_symbol, size)
                else:
                    if self.on_sell_callback:
                        self.on_sell_callback(self.current_symbol, size)
        except ValueError:
            self.show_error("無効なサイズです")
    
    def _on_close_all_clicked(self):
        """全決済ボタンがクリックされた時"""
        # 全決済は確認なしで即実行（高速取引のため）
        if self.on_close_callback:
            self.on_close_callback(None)  # None = 全決済
            self.show_status("全決済を実行中...")
    
    def _confirm_order(self, symbol: str, side: str, size: float, limit_price: float = None) -> bool:
        """注文確認ダイアログを表示"""
        # 現在価格を取得
        current_price = "不明"
        if symbol in self.current_prices:
            current_price = f"${float(self.current_prices[symbol]):,.2f}"
        
        # 確認メッセージ
        if limit_price is not None:
            # 指値注文
            message = f"""
注文内容を確認してください:

通貨ペア: {symbol}-USD
方向: {side}
サイズ: {size}
指値価格: ${limit_price:,.2f}
現在価格: {current_price}

この注文を実行しますか？
確認するには 'yes' と入力してください
            """
        else:
            # 成行注文
            message = f"""
注文内容を確認してください:

通貨ペア: {symbol}-USD
方向: {side}
サイズ: {size}
現在価格: {current_price}

この注文を実行しますか？
確認するには 'yes' と入力してください
            """
        
        dialog = ctk.CTkInputDialog(
            text=message.strip(),
            title="注文確認"
        )
        
        user_input = dialog.get_input()
        
        if user_input and user_input.lower() == 'yes':
            return True
        else:
            self.show_status("注文がキャンセルされました")
            return False
    
    def update_price(self, prices: dict):
        """価格を更新（前回価格からの変化を表示）"""
        import time
        self.current_prices = prices
        self.last_price_update = time.time()
        
        # WebSocket遅延インジケーターを更新
        if self.lag_indicator:
            self.lag_indicator.configure(text="🟢 接続良好", text_color="green")
        
        if self.current_symbol in prices:
            price = float(prices[self.current_symbol])
            
            # 価格表示を更新
            self.price_label.configure(text=f"${price:,.2f}")
            
            # 前回価格からの変化を表示
            if self.previous_price is not None and self.price_change_label:
                change = price - self.previous_price
                change_pct = (change / self.previous_price * 100) if self.previous_price > 0 else 0
                
                if change > 0:
                    # 上昇（緑色）
                    self.price_change_label.configure(
                        text=f"+${change:,.2f} (+{change_pct:.2f}%)",
                        text_color="#44FF44"
                    )
                elif change < 0:
                    # 下降（赤色）
                    self.price_change_label.configure(
                        text=f"${change:,.2f} ({change_pct:.2f}%)",
                        text_color="#FF4444"
                    )
                else:
                    # 変化なし（グレー）
                    self.price_change_label.configure(
                        text="$0.00 (0.00%)",
                        text_color="gray"
                    )
            
            # 前回価格を更新
            self.previous_price = price
    
    def update_positions(self, positions: list):
        """ポジションを更新"""
        # 現在のポジションリストを保存（決済ダイアログで使用）
        self.current_positions = positions
        
        # 既存のウィジェットをクリア
        for widget in self.position_frame.winfo_children():
            widget.destroy()
        
        if not positions:
            no_position_label = ctk.CTkLabel(
                self.position_frame,
                text="ポジションがありません",
                text_color="gray"
            )
            no_position_label.pack(pady=20)
            return
        
        # ポジションを表示
        for pos in positions:
            pos_frame = ctk.CTkFrame(self.position_frame)
            pos_frame.pack(pady=5, padx=5, fill="x")
            
            # シンボル
            symbol_label = ctk.CTkLabel(
                pos_frame,
                text=pos['coin'],
                font=ctk.CTkFont(size=14, weight="bold"),
                width=80
            )
            symbol_label.pack(side="left", padx=5)
            
            # サイズ
            size = pos['size']
            side_text = "ロング" if size > 0 else "ショート"
            side_color = "green" if size > 0 else "red"
            size_label = ctk.CTkLabel(
                pos_frame,
                text=f"{side_text} {abs(size):.4f}",
                font=ctk.CTkFont(size=12),
                text_color=side_color,
                width=120
            )
            size_label.pack(side="left", padx=5)
            
            # エントリー価格
            entry_label = ctk.CTkLabel(
                pos_frame,
                text=f"EP: ${pos['entry_price']:.2f}",
                font=ctk.CTkFont(size=12),
                width=110
            )
            entry_label.pack(side="left", padx=3)
            
            # レバレッジ
            leverage = pos.get('leverage', {})
            if isinstance(leverage, dict):
                lev_value = leverage.get('value', 1)
            else:
                lev_value = leverage if leverage else 1
            lev_label = ctk.CTkLabel(
                pos_frame,
                text=f"⚡{lev_value}x",
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color="#FFA500",
                width=50
            )
            lev_label.pack(side="left", padx=3)
            
            # 損益
            pnl = pos['unrealized_pnl']
            pnl_color = "green" if pnl >= 0 else "red"
            pnl_label = ctk.CTkLabel(
                pos_frame,
                text=f"PnL: ${pnl:.2f}",
                font=ctk.CTkFont(size=12, weight="bold"),
                text_color=pnl_color,
                width=90
            )
            pnl_label.pack(side="left", padx=3)
            
            # 決済ボタン
            close_button = ctk.CTkButton(
                pos_frame,
                text="決済",
                command=lambda c=pos['coin']: self._on_close_position(c),
                width=80,
                height=30,
                fg_color="orange",
                hover_color="darkorange"
            )
            close_button.pack(side="right", padx=5)
    
    def update_open_orders(self, orders: list):
        """未約定注文を更新"""
        # 既存のウィジェットをクリア
        for widget in self.open_orders_frame.winfo_children():
            widget.destroy()
        
        if not orders:
            no_orders_label = ctk.CTkLabel(
                self.open_orders_frame,
                text="未約定注文がありません",
                text_color="gray",
                font=ctk.CTkFont(size=10)
            )
            no_orders_label.pack(pady=10)
            return
        
        # 注文を表示
        for order in orders:
            order_frame = ctk.CTkFrame(self.open_orders_frame)
            order_frame.pack(pady=3, padx=5, fill="x")
            
            # シンボル
            symbol_label = ctk.CTkLabel(
                order_frame,
                text=order['coin'],
                font=ctk.CTkFont(size=12, weight="bold"),
                width=70
            )
            symbol_label.pack(side="left", padx=5)
            
            # タイプ（買い/売り）
            side_text = "買い" if order['is_buy'] else "売り"
            side_color = "green" if order['is_buy'] else "red"
            side_label = ctk.CTkLabel(
                order_frame,
                text=side_text,
                font=ctk.CTkFont(size=11, weight="bold"),
                text_color=side_color,
                width=50
            )
            side_label.pack(side="left", padx=5)
            
            # サイズ
            size_label = ctk.CTkLabel(
                order_frame,
                text=f"{order['size']:.4f}",
                font=ctk.CTkFont(size=11),
                width=80
            )
            size_label.pack(side="left", padx=5)
            
            # 指値価格
            price_label = ctk.CTkLabel(
                order_frame,
                text=f"@ ${order['limit_price']:.4f}",
                font=ctk.CTkFont(size=11),
                width=110
            )
            price_label.pack(side="left", padx=5)
            
            # 注文ID
            oid_label = ctk.CTkLabel(
                order_frame,
                text=f"ID: {order['order_id']}",
                font=ctk.CTkFont(size=9),
                text_color="gray",
                width=90
            )
            oid_label.pack(side="left", padx=5)
            
            # キャンセルボタン
            cancel_button = ctk.CTkButton(
                order_frame,
                text="キャンセル",
                command=lambda symbol=order['coin'], oid=order['order_id']: self._on_cancel_order(symbol, oid),
                width=90,
                height=25,
                fg_color="#DC3545",
                hover_color="#A02A37",
                font=ctk.CTkFont(size=10)
            )
            cancel_button.pack(side="right", padx=5)
    
    def _on_cancel_order(self, symbol: str, order_id: int):
        """注文キャンセルボタンがクリックされた時"""
        if self.on_cancel_order_callback:
            self.on_cancel_order_callback(symbol, order_id)
    
    def _on_close_position(self, symbol: str):
        """ポジション決済ボタンがクリックされた時"""
        # 現在のポジションを探す
        position_size = None
        for pos in self.current_positions:
            if pos['coin'] == symbol:
                position_size = abs(pos['size'])
                break
        
        if position_size is None:
            self.show_error(f"{symbol}のポジションが見つかりません")
            return
        
        # 現在価格を取得
        current_price = self.current_prices.get(symbol, 0)
        if isinstance(current_price, str):
            current_price = float(current_price)
        
        # カスタムダイアログを作成
        self._show_close_dialog(symbol, position_size, current_price)
    
    def _show_close_dialog(self, symbol: str, position_size: float, current_price: float):
        """決済ダイアログを表示（パーセンテージ選択付き + リアルタイム検証）"""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title(f"{symbol} 決済")
        dialog.geometry("420x550")
        dialog.resizable(False, False)
        
        # ダイアログを中央に配置
        dialog.transient(self.root)
        dialog.grab_set()
        
        # タイトル
        title_label = ctk.CTkLabel(
            dialog,
            text=f"{symbol} ポジション決済",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=15)
        
        # ポジション情報フレーム
        info_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        info_frame.pack(pady=5)
        
        # ポジションサイズ表示
        size_label = ctk.CTkLabel(
            info_frame,
            text=f"現在のサイズ: {position_size}",
            font=ctk.CTkFont(size=14)
        )
        size_label.pack()
        
        # 現在価格表示
        price_label = ctk.CTkLabel(
            info_frame,
            text=f"現在価格: ${current_price:,.2f}",
            font=ctk.CTkFont(size=12),
            text_color="#AAAAAA"
        )
        price_label.pack()
        
        # 最低決済サイズ計算
        min_close_size = 10.0 / current_price if current_price > 0 else 0
        min_size_label = ctk.CTkLabel(
            info_frame,
            text=f"[!] 最低決済サイズ: {min_close_size:.6f} (~$10)",
            font=ctk.CTkFont(size=11),
            text_color="#FFA500"
        )
        min_size_label.pack(pady=3)
        
        # パーセンテージボタンフレーム
        percentage_frame = ctk.CTkFrame(dialog)
        percentage_frame.pack(pady=15, padx=20, fill="x")
        
        percentage_label = ctk.CTkLabel(
            percentage_frame,
            text="クイック決済:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        percentage_label.pack(pady=5)
        
        # パーセンテージボタン
        button_frame = ctk.CTkFrame(percentage_frame, fg_color="transparent")
        button_frame.pack(pady=5)
        
        result_var = {"size": None, "confirmed": False}
        
        def set_percentage(pct: float):
            size = position_size * (pct / 100.0)
            size_entry.delete(0, "end")
            size_entry.insert(0, str(size))
            # 検証を実行
            validate_size()
        
        percentages = [25, 50, 75, 100]
        for i, pct in enumerate(percentages):
            btn = ctk.CTkButton(
                button_frame,
                text=f"{pct}%",
                command=lambda p=pct: set_percentage(p),
                width=80,
                height=35,
                fg_color="#3B8ED0" if pct != 100 else "#FF6B6B",
                hover_color="#36719F" if pct != 100 else "#CC5555"
            )
            btn.grid(row=0, column=i, padx=5)
        
        # カスタムサイズ入力
        custom_frame = ctk.CTkFrame(dialog)
        custom_frame.pack(pady=15, padx=20, fill="x")
        
        custom_label = ctk.CTkLabel(
            custom_frame,
            text="カスタムサイズ:",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        custom_label.pack(pady=5)
        
        size_entry = ctk.CTkEntry(
            custom_frame,
            placeholder_text="決済サイズを入力",
            font=ctk.CTkFont(size=14),
            height=40
        )
        size_entry.pack(pady=5, padx=10, fill="x")
        
        # 検証警告ラベル
        warning_label = ctk.CTkLabel(
            custom_frame,
            text="",
            font=ctk.CTkFont(size=11),
            text_color="#FF6B6B"
        )
        warning_label.pack(pady=3)
        
        # ボタンフレーム
        action_frame = ctk.CTkFrame(dialog, fg_color="transparent")
        action_frame.pack(pady=15, padx=20, fill="x")
        
        # リアルタイム検証関数（ここで定義）
        def validate_size(*args):
            """入力サイズをリアルタイムで検証"""
            size_text = size_entry.get().strip()
            
            if not size_text:
                # 空欄 = 全決済 = OK
                warning_label.configure(text="")
                confirm_button.configure(state="normal")
                return
            
            try:
                # パーセンテージチェック
                if size_text.endswith('%'):
                    pct = float(size_text[:-1])
                    size = position_size * (pct / 100.0)
                else:
                    size = float(size_text)
                
                # 検証
                if size <= 0:
                    warning_label.configure(text="⚠️ サイズは正の数である必要があります")
                    confirm_button.configure(state="disabled")
                elif size > position_size:
                    warning_label.configure(text=f"⚠️ サイズがポジション({position_size})を超えています")
                    confirm_button.configure(state="disabled")
                else:
                    # 決済額を計算
                    order_value = size * current_price
                    
                    if order_value < 10.0:
                        # $10未満 = エラー
                        warning_label.configure(
                            text=f"❌ 決済額: ${order_value:.2f} (最低$10必要)"
                        )
                        confirm_button.configure(state="disabled")
                    else:
                        # OK
                        warning_label.configure(
                            text=f"✅ 決済額: ${order_value:.2f}",
                            text_color="#44FF44"
                        )
                        confirm_button.configure(state="normal")
            
            except ValueError:
                warning_label.configure(text="⚠️ 無効な入力です")
                confirm_button.configure(state="disabled")
        
        def on_confirm():
            size_text = size_entry.get().strip()
            
            if not size_text:
                # 全決済
                result_var["size"] = None
                result_var["confirmed"] = True
                dialog.destroy()
            else:
                try:
                    # パーセンテージ入力チェック（例: "50%"）
                    if size_text.endswith('%'):
                        pct = float(size_text[:-1])
                        if pct <= 0 or pct > 100:
                            self.show_error("パーセンテージは1〜100の範囲で入力してください")
                            return
                        size = position_size * (pct / 100.0)
                    else:
                        size = float(size_text)
                    
                    if size <= 0:
                        self.show_error("サイズは正の数である必要があります")
                        return
                    
                    if size > position_size:
                        self.show_error(f"サイズがポジション({position_size})を超えています")
                        return
                    
                    result_var["size"] = size
                    result_var["confirmed"] = True
                    dialog.destroy()
                    
                except ValueError:
                    self.show_error("無効なサイズです")
        
        def on_cancel():
            result_var["confirmed"] = False
            dialog.destroy()
        
        # 決済ボタン
        confirm_button = ctk.CTkButton(
            action_frame,
            text="✓ 決済実行",
            command=on_confirm,
            width=150,
            height=40,
            fg_color="#28A745",
            hover_color="#218838",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        confirm_button.pack(side="left", padx=5, expand=True)
        
        # キャンセルボタン
        cancel_btn = ctk.CTkButton(
            action_frame,
            text="✗ キャンセル",
            command=on_cancel,
            width=150,
            height=40,
            fg_color="#6C757D",
            hover_color="#5A6268",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        cancel_btn.pack(side="right", padx=5, expand=True)
        
        # イベントバインド
        size_entry.bind("<Return>", lambda e: on_confirm())  # Enterキーで決済
        size_entry.bind("<KeyRelease>", validate_size)       # リアルタイム検証
        
        # ダイアログが閉じられるのを待つ
        self.root.wait_window(dialog)
        
        # 結果を処理
        if result_var["confirmed"] and self.on_close_callback:
            self.on_close_callback(symbol, size=result_var["size"])
    
    def show_status(self, message: str):
        """ステータスメッセージを表示"""
        self.status_label.configure(text=message)
    
    def show_error(self, message: str):
        """エラーメッセージを表示"""
        self.status_label.configure(text=f"❌ {message}", text_color="red")
        # 3秒後に元に戻す
        self.root.after(3000, lambda: self.status_label.configure(text_color="white"))
    
    def show_success(self, message: str):
        """成功メッセージを表示"""
        self.status_label.configure(text=f"✅ {message}", text_color="green")
        # 3秒後に元に戻す
        self.root.after(3000, lambda: self.status_label.configure(text_color="white"))
    
    def update_account_leverage(self, leverage: float):
        """アカウント全体のレバレッジを更新"""
        if self.account_leverage_label:
            if leverage is not None:
                # レバレッジに応じて色を変更
                if leverage >= 5:
                    color = "#FF4444"  # 赤（高リスク）
                elif leverage >= 3:
                    color = "#FFA500"  # オレンジ（中リスク）
                else:
                    color = "#44FF44"  # 緑（低リスク）
                
                self.account_leverage_label.configure(
                    text=f"📊 Leverage: {leverage:.2f}x",
                    text_color=color
                )
            else:
                self.account_leverage_label.configure(
                    text="📊 Leverage: --x",
                    text_color="#888888"
                )
    
    def update_account_info(self, equity: float = None, spot: float = None, perps: float = None):
        """アカウント情報を更新"""
        if equity is not None and self.account_equity_label:
            self.account_equity_label.configure(
                text=f"💰 Equity: ${equity:,.2f}"
            )
        
        if spot is not None and self.account_spot_label:
            self.account_spot_label.configure(
                text=f"Spot: ${spot:,.2f}"
            )
        
        if perps is not None and self.account_perps_label:
            self.account_perps_label.configure(
                text=f"Perps: ${perps:,.2f}"
            )
    
    def add_log(self, message: str):
        """約定ログを追加"""
        if self.log_textbox:
            import datetime
            timestamp = datetime.datetime.now().strftime("%H:%M:%S")
            log_message = f"[{timestamp}] {message}\n"
            
            self.log_textbox.configure(state="normal")
            self.log_textbox.insert("end", log_message)
            self.log_textbox.see("end")  # 最新行にスクロール
            self.log_textbox.configure(state="disabled")
    
    def set_buy_callback(self, callback: Callable):
        """買い注文のコールバックを設定"""
        self.on_buy_callback = callback
    
    def set_sell_callback(self, callback: Callable):
        """売り注文のコールバックを設定"""
        self.on_sell_callback = callback
    
    def set_close_callback(self, callback: Callable):
        """決済のコールバックを設定"""
        self.on_close_callback = callback
    
    def check_connection_lag(self):
        """接続遅延をチェック"""
        import time
        if self.last_price_update and self.lag_indicator:
            lag = time.time() - self.last_price_update
            if lag > 10:
                self.lag_indicator.configure(text="🔴 接続断", text_color="red")
            elif lag > 5:
                self.lag_indicator.configure(text="🟡 遅延あり", text_color="yellow")
            else:
                self.lag_indicator.configure(text="🟢 接続良好", text_color="green")
        
        # 1秒ごとに再チェック
        if self.root:
            self.root.after(1000, self.check_connection_lag)
    
    def update_api_status(self, is_connected: bool):
        """API接続状態を更新"""
        if self.api_status_indicator:
            if is_connected:
                self.api_status_indicator.configure(
                    text="🟢 API接続",
                    text_color="green"
                )
            else:
                self.api_status_indicator.configure(
                    text="🔴 API切断",
                    text_color="red"
                )
    
    def update_rate_limit_status(self, current: int, max_calls: int):
        """レートリミット状態を更新"""
        if self.rate_limit_indicator:
            # 使用率を計算
            usage_pct = (current / max_calls * 100) if max_calls > 0 else 0
            
            # 色を設定（80%以上で警告、50%以上で注意）
            if usage_pct >= 80:
                color = "#FF4444"  # 赤（警告）
            elif usage_pct >= 50:
                color = "#FFA500"  # オレンジ（注意）
            else:
                color = "gray"  # グレー（正常）
            
            self.rate_limit_indicator.configure(
                text=f"📊 レート: {current}/{max_calls}",
                text_color=color
            )
    
    def run(self):
        """GUIを起動"""
        if self.root:
            # 接続遅延チェックを開始
            self.root.after(1000, self.check_connection_lag)
            self.root.mainloop()

