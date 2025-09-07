import json
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.utils.loader import import_from_string


def validate_json(path):
    with open(path, 'r') as f:
        return json.load(f)


def validate_dotted_paths(obj, label):
    failures = []
    if isinstance(obj, dict):
        for key, value in obj.items():
            failures.extend(validate_dotted_paths(value, f"{label}.{key}"))
    elif isinstance(obj, list):
        for i, value in enumerate(obj):
            failures.extend(validate_dotted_paths(value, f"{label}[{i}]"))
    elif isinstance(obj, str):
        try:
            import_from_string(obj)
        except Exception as e:
            failures.append((label, obj, str(e)))
    return failures


def main():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    paths = [
        os.path.join(root, 'agents', 'registry.json'),
        os.path.join(root, 'tools', 'registry.json'),
        os.path.join(root, 'memory', 'registry.json'),
    ]
    all_failures = []
    for p in paths:
        if not os.path.exists(p):
            print(f"Missing registry: {p}")
            all_failures.append((p, 'MISSING', 'File not found'))
            continue
        try:
            obj = validate_json(p)
        except Exception as e:
            print(f"Invalid JSON: {p} -> {e}")
            all_failures.append((p, 'JSON', str(e)))
            continue
        failures = validate_dotted_paths(obj, os.path.basename(p))
        if failures:
            print(f"Errors in {p}:")
            for where, dotted, err in failures:
                print(f"  - {where}: {dotted} -> {err}")
            all_failures.extend(failures)
        else:
            print(f"OK: {p}")

    if all_failures:
        sys.exit(1)


if __name__ == '__main__':
    main()


