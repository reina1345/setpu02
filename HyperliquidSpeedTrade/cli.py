"""
CLI エントリポイント（裁量補助向け・ヘッドレス運用）

コマンド一覧:
  - run: 接続確認とヘルス監視（価格WS購読、口座/ポジションの周期更新）
  - health: 単発のヘルスチェックを実行
  - close-all: 全ポジションを一括決済
  - positions: 現在のポジション一覧を表示
  - open-orders: 未約定注文一覧を表示
  - price: 指定シンボルの現在価格を表示
"""
import argparse
import sys
import time
from typing import List
from config import Config
from hyperliquid_api import HyperliquidAPI


def cmd_run(args: argparse.Namespace) -> int:
    api = HyperliquidAPI()
    if not api.initialize():
        print("[NG] API初期化に失敗しました (.env の PRIVATE_KEY 等を確認)\n")
        return 1

    # 銘柄一覧（出来高順）
    symbols: List[str] = api.get_symbols_by_volume()
    subscribe_symbols = symbols[:100] if len(symbols) > 100 else symbols

    # 価格更新の簡易ハンドラ（P95遅延監視などは今後拡張）
    latest_prices = {"_ts": 0.0}

    def on_prices(mids: dict):
        latest_prices.update(mids)
        latest_prices["_ts"] = time.time()

    api.start_price_stream(subscribe_symbols, on_prices)

    print(f"[OK] 価格WS購読開始: {len(subscribe_symbols)}銘柄")
    print("[INFO] Ctrl-Cで終了。--dry-run フラグは将来の自動執行抑止用に予約済み。")

    # 周期ヘルス監視ループ
    try:
        while True:
            time.sleep(5)
            # 口座/ポジション/未約定を軽量にポーリング
            positions = api.get_positions()
            account_info = api.get_account_info()

            lag_s = time.time() - latest_prices.get("_ts", 0) if latest_prices.get("_ts") else float("inf")
            lag_text = (
                "🟢 接続良好" if lag_s <= 5 else ("🟡 遅延あり" if lag_s <= 10 else "🔴 接続断")
            )

            equity = account_info.get("equity", 0) if account_info else 0
            print(
                f"[HEALTH] WS:{lag_text}  Equity:${equity:,.2f}  Positions:{len(positions)}  Time:{time.strftime('%H:%M:%S')}"
            )
    except KeyboardInterrupt:
        print("\n停止します...")
        return 0


def cmd_health(args: argparse.Namespace) -> int:
    api = HyperliquidAPI()
    if not api.initialize():
        print("[NG] API初期化に失敗しました")
        return 1
    price = api.get_price(Config.DEFAULT_SYMBOL)
    account = api.get_account_info()
    print(f"[OK] 接続: {'テストネット' if Config.USE_TESTNET else 'メインネット'}  アドレス初期化済み")
    print(f"[DATA] {Config.DEFAULT_SYMBOL} 価格: {price if price is not None else 'N/A'}")
    if account:
        print(f"[DATA] Equity:${account['equity']:,.2f} Spot:${account['spot']:,.2f} Perps:${account['perps']:,.2f}")
    return 0


def cmd_close_all(args: argparse.Namespace) -> int:
    api = HyperliquidAPI()
    if not api.initialize():
        return 1
    result = api.close_all_positions()
    print(result.get("message", ""))
    return 0 if result.get("success") else 2


def cmd_positions(args: argparse.Namespace) -> int:
    api = HyperliquidAPI()
    if not api.initialize():
        return 1
    positions = api.get_positions()
    if not positions:
        print("ポジションなし")
        return 0
    for p in positions:
        side = "LONG" if p["size"] > 0 else "SHORT"
        print(f"{p['coin']}: {side} {abs(p['size']):.6f}  EP:${p['entry_price']:.2f}  PnL:${p['unrealized_pnl']:.2f}")
    return 0


def cmd_open_orders(args: argparse.Namespace) -> int:
    api = HyperliquidAPI()
    if not api.initialize():
        return 1
    orders = api.get_open_orders()
    if not orders:
        print("未約定注文なし")
        return 0
    for o in orders:
        side = "BUY" if o["is_buy"] else "SELL"
        print(f"{o['coin']} {side} {o['size']:.6f} @ ${o['limit_price']:.4f}  ID:{o['order_id']}")
    return 0


def cmd_price(args: argparse.Namespace) -> int:
    api = HyperliquidAPI()
    if not api.initialize():
        return 1
    sym = args.symbol or Config.DEFAULT_SYMBOL
    px = api.get_price(sym)
    if px is None:
        print(f"{sym}: 価格取得失敗")
        return 2
    print(f"{sym}: ${px:,.4f}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="hl-cli", description="Hyperliquid 裁量補助 CLI")
    sub = parser.add_subparsers(dest="command")

    p_run = sub.add_parser("run", help="ヘルス監視を開始 (Ctrl-Cで終了)")
    p_run.add_argument("--dry-run", action="store_true", help="将来の自動執行抑止用 (現状は表示のみ)")
    p_run.set_defaults(func=cmd_run)

    p_health = sub.add_parser("health", help="単発ヘルスチェック")
    p_health.set_defaults(func=cmd_health)

    p_close = sub.add_parser("close-all", help="全ポジションを一括決済")
    p_close.set_defaults(func=cmd_close_all)

    p_pos = sub.add_parser("positions", help="現在のポジション一覧を表示")
    p_pos.set_defaults(func=cmd_positions)

    p_oo = sub.add_parser("open-orders", help="未約定注文一覧を表示")
    p_oo.set_defaults(func=cmd_open_orders)

    p_price = sub.add_parser("price", help="指定シンボルの現在価格を表示")
    p_price.add_argument("--symbol", type=str, help="通貨シンボル (例: BTC)")
    p_price.set_defaults(func=cmd_price)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())



