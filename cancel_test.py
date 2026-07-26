"""临时压测脚本: 取消指定 order_id, 验证策略自愈。testnet 零风险。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def load_env():
    d = {}
    p = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(p):
        with open(p, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    d[k.strip()] = v.strip()
    return d


e = load_env()
import deribit_api

testnet = e.get("DERIBIT_TESTNET", "1") == "1"
c = deribit_api.DeribitClient(e["DERIBIT_ID"], e["DERIBIT_SECRET"], testnet=testnet)
oid = sys.argv[1] if len(sys.argv) > 1 else "BTC_USDC-1205720404"
r = c.cancel_order(oid)
print("CANCEL_RESULT:", r)
