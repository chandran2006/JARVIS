import re, sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

def enforce_one_sir(text):
    occurrences = [m.start() for m in re.finditer(r'\bsir\b', text, re.I)]
    if len(occurrences) <= 1:
        return text
    result = list(text)
    for pos in occurrences[1:]:
        result[pos:pos+3] = ['', '', '']
    cleaned = re.sub(r',\s*,', ',', ''.join(result))
    cleaned = re.sub(r'\s{2,}', ' ', cleaned).strip()
    return cleaned

tests = [
    "Good morning, sir. It is a pleasure, sir, to assist you today, sir.",
    "Of course, sir. The time is 10 AM, sir.",
    "Hello sir, how can I help you sir today sir?",
    "Done, sir.",
    "No mention here at all.",
    "Sir, I will help you sir right away sir.",
]
all_pass = True
for t in tests:
    out = enforce_one_sir(t)
    count = len(re.findall(r'\bsir\b', out, re.I))
    status = "PASS" if count <= 1 else "FAIL"
    if status == "FAIL": all_pass = False
    print(f"[{status}] IN : {t}")
    print(f"       OUT: {out}  [sir x{count}]")
    print()

print("ALL PASS" if all_pass else "SOME FAILED")
