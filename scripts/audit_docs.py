"""
Audit script checking:
1. Markdown file links across docs/ and README.md (ensures referenced files exist).
2. Verifies consistency of math variables and formulas.
3. Verifies test counts and active components.
"""

import os
import re
import sys

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DOC_FILES = [
    os.path.join(REPO_ROOT, "README.md"),
    os.path.join(REPO_ROOT, "docs", "architecture_and_workflow.md"),
    os.path.join(REPO_ROOT, "docs", "sentiment_math.md"),
    os.path.join(REPO_ROOT, "docs", "wiki_home.md"),
    os.path.join(REPO_ROOT, "docs", "build_progress.md"),
    os.path.join(REPO_ROOT, "reports", "benchmark_report.md"),
]

def check_file_links():
    print("=== 1. Checking Markdown File Links ===")
    link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    file_uri_pattern = re.compile(r'file:///([^\s\)]+)')
    
    broken_links = []
    total_links = 0

    for doc_path in DOC_FILES:
        rel_doc = os.path.relpath(doc_path, REPO_ROOT)
        if not os.path.exists(doc_path):
            print(f"ERROR: Doc not found: {rel_doc}")
            continue

        with open(doc_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check standard markdown links [text](path)
        for match in link_pattern.finditer(content):
            total_links += 1
            label = match.group(1)
            target = match.group(2)

            # Skip web URLs, anchors, mailto
            if target.startswith("http://") or target.startswith("https://") or target.startswith("#") or target.startswith("mailto:"):
                continue

            # Strip query params or line anchors like #L10-L20
            clean_target = target.split("#")[0].split("?")[0]
            if not clean_target:
                continue

            # Handle file:/// URIs
            if clean_target.startswith("file:///"):
                file_path = clean_target[len("file:///"):]
                # On Windows, could be d:/Dev/... or D:/Dev/...
                if not os.path.exists(file_path):
                    broken_links.append((rel_doc, target, f"File does not exist: {file_path}"))
                continue

            # Handle relative paths from doc location
            doc_dir = os.path.dirname(doc_path)
            resolved_path = os.path.abspath(os.path.join(doc_dir, clean_target))
            if not os.path.exists(resolved_path):
                # Also try relative from repo root
                root_resolved = os.path.abspath(os.path.join(REPO_ROOT, clean_target))
                if not os.path.exists(root_resolved):
                    broken_links.append((rel_doc, target, f"Target not found at {resolved_path} or {root_resolved}"))

    print(f"Total markdown links checked: {total_links}")
    if broken_links:
        print(f"Found {len(broken_links)} broken/unresolved links:")
        for doc, link, reason in broken_links:
            print(f"  [{doc}] -> '{link}': {reason}")
    else:
        print("All local file links successfully resolved!")
    return len(broken_links) == 0

def check_math_and_code_consistency():
    print("\n=== 2. Checking Math and Code Symbol Consistency ===")
    # Check that main.py implements S_rel, magnitude, etc.
    main_py = os.path.join(REPO_ROOT, "src", "main.py")
    with open(main_py, "r", encoding="utf-8") as f:
        main_code = f.read()

    symbols = [
        ("p_bull", "P(Bullish) probability"),
        ("p_bear", "P(Bearish) probability"),
        ("p_neut", "P(Neutral) probability"),
        ("s_rel", "Relative directional spread"),
        ("magnitude", "Neutral attenuation magnitude"),
        ("directional_score", "Directional score"),
    ]

    all_found = True
    for sym, desc in symbols:
        if sym in main_code:
            print(f"  [OK] Found symbol '{sym}' ({desc}) in src/main.py")
        else:
            print(f"  [MISSING] Symbol '{sym}' ({desc}) not found in src/main.py")
            all_found = False

    return all_found

def check_ui_components():
    print("\n=== 3. Checking Modular UI Components ===")
    components_dir = os.path.join(REPO_ROOT, "src", "ui", "components")
    expected_files = [
        "__init__.py", "common.py", "header.py", "toolbar.py",
        "analytics.py", "feed.py", "ledger.py"
    ]
    all_ok = True
    for f in expected_files:
        p = os.path.join(components_dir, f)
        if os.path.exists(p):
            print(f"  [OK] Component file exists: src/ui/components/{f}")
        else:
            print(f"  [MISSING] Component file missing: src/ui/components/{f}")
            all_ok = False

    styles_py = os.path.join(REPO_ROOT, "src", "ui", "styles.py")
    if os.path.exists(styles_py):
        print("  [OK] Styles file exists: src/ui/styles.py")
    else:
        print("  [MISSING] Styles file missing: src/ui/styles.py")
        all_ok = False

    return all_ok

def check_test_count():
    print("\n=== 4. Checking Unit Test Count ===")
    import unittest
    loader = unittest.TestLoader()
    suite = loader.discover(os.path.join(REPO_ROOT, "tests", "unit"), top_level_dir=REPO_ROOT)
    count = suite.countTestCases()
    print(f"Discovered test cases: {count}")
    return count

if __name__ == "__main__":
    links_ok = check_file_links()
    math_ok = check_math_and_code_consistency()
    ui_ok = check_ui_components()
    test_count = check_test_count()
    print(f"\nAudit complete: Links OK={links_ok}, Math OK={math_ok}, UI OK={ui_ok}, Test Count={test_count}")
