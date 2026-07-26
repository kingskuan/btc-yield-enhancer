#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一次性 1 小时监测脚本：每 5 分钟探一次 BTC(5050)/ETH(5051)。
异常即立即退出并打印报警；否则跑满 1 小时打印健康总结。
异常判定：请求失败 / HTTP!=200 / status!=running / trading!=True / errors 非空。
挂单为空不算硬异常（可能处于成交后 3 分钟冷却），但会记录连续空单次数，
连续 3 次(约15分钟)双边单都空 → 视为异常退出。
"""
import json, time, sys, urllib.request

INSTANCES = [("BTC", 5050), ("ETH", 5051)]
INTERVAL = 300          # 5 分钟
DURATION = 3600         # 1 小时
EMPTY_LIMIT = 3         # 连续空单容忍次数

def probe(port):
    url = f"http://127.0.0.1:{port}/api/status"
    try:
        with urllib.request.urlopen(url, timeout=8) as r:
            if r.status != 200:
                return None, f"HTTP {r.status}"
            return json.loads(r.read().decode()), None
    except Exception as e:
        return None, f"请求失败: {e}"

def check(name, port, empty_streak):
    d, err = probe(port)
    if err:
        return False, f"[{name}] {err}", empty_streak
    status = d.get("status")
    trading = d.get("trading_enabled")
    errors = d.get("errors") or []
    orders = d.get("open_orders") or []
    if status != "running":
        return False, f"[{name}] status={status}（非 running）", empty_streak
    if trading is not True:
        return False, f"[{name}] trading={trading}（交易关闭）", empty_streak
    if errors:
        return False, f"[{name}] errors={errors}", empty_streak
    n = len(orders)
    if n == 0:
        empty_streak += 1
        if empty_streak >= EMPTY_LIMIT:
            return False, f"[{name}] 连续{empty_streak}次无挂单（约{empty_streak*INTERVAL//60}分钟）", empty_streak
    else:
        empty_streak = 0
    bal = d.get("btc_balance"); idx = d.get("btc_index_price")
    return True, f"[{name}] ok status={status} trading={trading} orders={n} bal={bal} idx={idx}", empty_streak

def main():
    start = time.time()
    empty = {name: 0 for name, _ in INSTANCES}
    round_no = 0
    print(f"=== 监测开始 {time.strftime('%H:%M:%S')} 时长{DURATION//60}分钟 间隔{INTERVAL//60}分钟 ===", flush=True)
    # 首轮立即探一次
    while True:
        round_no += 1
        ts = time.strftime("%H:%M:%S")
        for name, port in INSTANCES:
            ok, msg, empty[name] = check(name, port, empty[name])
            print(f"{ts} 第{round_no}轮 {msg}", flush=True)
            if not ok:
                print(f"\n!!! 异常报警 {ts} !!! {msg}", flush=True)
                print(">>> 监测提前退出，需人工介入", flush=True)
                sys.exit(1)
        if time.time() - start >= DURATION:
            print(f"\n=== 监测完成 {ts} 满{DURATION//60}分钟，全程健康，无异常 ===", flush=True)
            sys.exit(0)
        time.sleep(INTERVAL)

if __name__ == "__main__":
    main()
