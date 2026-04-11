import sys, json
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

with open("finance_test.txt", "w", encoding="utf-8") as f:
    def log(m): f.write(m+"\n"); f.flush(); print(m, flush=True)

    from dotenv import load_dotenv; load_dotenv()
    from core.registry import SkillRegistry
    r = SkillRegistry()
    r.load_skills("skills")

    tests = [
        ("get_commodity_price", {"commodity": "gold"}),
        ("get_commodity_price", {"commodity": "silver"}),
        ("get_commodity_price", {"commodity": "crude oil"}),
        ("get_crypto_price",    {"coin": "bitcoin"}),
        ("get_crypto_price",    {"coin": "ethereum"}),
        ("get_stock_price",     {"symbol": "AAPL"}),
        ("get_stock_price",     {"symbol": "RELIANCE.NS"}),
        ("get_market_overview", {}),
        ("get_forex_rate",      {"from_currency": "USD", "to_currency": "INR"}),
    ]
    for fn_name, args in tests:
        fn = r.get_function(fn_name)
        if not fn:
            log(f"{fn_name}: NOT FOUND"); continue
        try:
            res = json.loads(fn(**args))
            log(f"{fn_name}({args}): {res.get('status')} -> {res.get('message','')[:120]}")
        except Exception as e:
            log(f"{fn_name}({args}): ERROR {e}")
