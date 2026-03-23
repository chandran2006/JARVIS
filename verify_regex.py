import re

error_strings = [
    "'failed_generation': '<function=google_search\":{\"search_term\": \"quantum physics definition\"}</function>'",
    "'failed_generation': '<function=google_search={\"search_term\": \"Elon Musk\"}></function>'",
    "'failed_generation': '<function=google_search {\"search_term\": \"quantum mechanics explanation\"} </function>'",
    # Standard correct format
    "'failed_generation': '<function=google_search{\"search_term\": \"test\"}</function>'"
]

# Proposed new regex
regex = r"<function=(\w+)(?:.*?)(?=\{)(\{.*?\})<\/function>"

print("Testing Regex:", regex)
for i, err in enumerate(error_strings):
    print(f"\n--- Test Case {i+1} ---")
    print("Input:", err)
    match = re.search(regex, err)
    if match:
        func_name = match.group(1)
        args = match.group(2)
        print(f"MATCH: Name='{func_name}', Args='{args}'")
    else:
        print("NO MATCH")
