import json
import os
from bot import compose


def load_test_cases():
    expanded_dir = os.path.join("dataset", "expanded")
    test_pairs_path = os.path.join(expanded_dir, "test_pairs.json")

    if os.path.exists(test_pairs_path):
        with open(test_pairs_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                print(f"Successfully loaded {len(data)} test pairs from {test_pairs_path}")
                cases = []
                for i, item in enumerate(data[:30]):
                    cases.append({
                        "test_id": item.get("test_id", f"T{i+1:02d}"),
                        "category": item.get("category", {}),
                        "merchant": item.get("merchant", {}),
                        "trigger": item.get("trigger", {}),
                        "customer": item.get("customer", None)
                    })
                return cases

    all_json_data = {}
    for root, dirs, files in os.walk(expanded_dir):
        for f in files:
            if f.endswith(".json"):
                full_path = os.path.join(root, f)
                try:
                    with open(full_path, "r", encoding="utf-8") as fp:
                        content = json.load(fp)
                    key = os.path.basename(root).lower() or f.lower()
                    if key not in all_json_data:
                        all_json_data[key] = []
                    if isinstance(content, list):
                        all_json_data[key].extend(content)
                    elif isinstance(content, dict):
                        all_json_data[key].append(content)
                except Exception:
                    pass

    merchants, triggers, customers = [], [], []
    for k, v in all_json_data.items():
        if "merchant" in k:
            merchants.extend(v)
        elif "trigger" in k:
            triggers.extend(v)
        elif "customer" in k:
            customers.extend(v)

    if not merchants or not triggers:
        raise ValueError(f"Could not parse entities. Directories found: {list(all_json_data.keys())}")

    cases = []
    num_cases = 30
    for i in range(num_cases):
        m = merchants[i % len(merchants)]
        t = triggers[i % len(triggers)]
        c = customers[i % len(customers)] if customers else None

        category = m.get("category", {})
        if isinstance(category, str):
            category = {"name": category}

        cases.append({
            "test_id": f"T{i+1:02d}",
            "category": category,
            "merchant": m,
            "trigger": t,
            "customer": c
        })

    return cases


def main():
    cases = load_test_cases()
    print(f"Processing {len(cases)} test cases through bot.py...")

    submission_rows = []
    for idx, case in enumerate(cases, start=1):
        test_id = case.get("test_id", f"T{idx:02d}")
        category = case.get("category", {})
        merchant = case.get("merchant", {})
        trigger = case.get("trigger", {})
        customer = case.get("customer", None)

        print(f"[{idx}/{len(cases)}] Generating response for {test_id}...")

        result = compose(category, merchant, trigger, customer)
        row = {"test_id": test_id, **result}
        submission_rows.append(row)

    with open("submission.jsonl", "w", encoding="utf-8") as f:
        for row in submission_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print(f"Done! Generated 'submission.jsonl' with {len(submission_rows)} rows.")


if __name__ == "__main__":
    main()
