import ast
import re
import sys

import polars as pl

from typing import Any

class DocRegexps:
    DOC_PRODUCER = re.compile(
        r"^\s*Producer of\s+`([^`]+?)`\s*\.?$", re.IGNORECASE | re.MULTILINE
    )
    DOC_PRIMARY_SOURCE = re.compile(
        r"^\s*Primary Source\s*:\s*`([^`]+?)`\s*\.?$", re.IGNORECASE | re.MULTILINE
    )
    BACKTICK_COL = re.compile(r"`([^`]+?)`")

    # Section headers may be prefixed with parentheses or indentation
    SECTION_HEADER = re.compile(
        r"^\s*\(?\s*(Filtering|Transformation|Enrichment|Default)\s*\)?:\s*$",
        re.IGNORECASE | re.MULTILINE,
    )

    # Item lines can start with optional hyphen or asterisk, then col_name:
    ITEM_LINE = re.compile(r"^\s*(?:[-*]\s*)?([A-Za-z_]\w*)\s*:", re.IGNORECASE)


def extract_from_docstring(docstring: str) -> dict[str,Any]:
    """
    Given a class-level docstring, extract:
      - producer
      - primary_source
      - source_cols (backtick columns in Filtering section)
      - transform_cols (cols named in Transformation section)
      - enrichment_cols (cols named in Enrichment section)
      - default_cols (cols named in Default section)
    """
    # Extract producer and primary source
    producer_match = DocRegexps.DOC_PRODUCER.search(docstring)
    primary_source_match = DocRegexps.DOC_PRIMARY_SOURCE.search(docstring)

    source_cols = []
    transform_cols = []
    enrichment_cols = []
    default_cols = []
    current_section = None

    for line in docstring.splitlines():
        # Section headers
        sec = DocRegexps.SECTION_HEADER.match(line)
        if sec:
            current_section = sec.group(1).lower()
            continue

        # Filtering: grab backtick-quoted names
        if current_section == "filtering":
            source_cols.extend(DocRegexps.BACKTICK_COL.findall(line))

        # Transformation: lines like 'col_name:'
        elif current_section == "transformation":
            m = DocRegexps.ITEM_LINE.match(line)
            if m:
                transform_cols.append(m.group(1))

        # Enrichment: same pattern
        elif current_section == "enrichment":
            m = DocRegexps.ITEM_LINE.match(line)
            if m:
                enrichment_cols.append(m.group(1))

        # Default: same pattern
        elif current_section == "default":
            m = DocRegexps.ITEM_LINE.match(line)
            if m:
                default_cols.append(m.group(1))

    # Deduplicate while preserving order
    def dedupe(seq):
        return list(dict.fromkeys(seq))

    return {
        "producer": producer_match.group(1) if producer_match else None,
        "primary_source": primary_source_match.group(1)
        if primary_source_match
        else None,
        "source_cols": dedupe(source_cols),
        "transform_cols": dedupe(transform_cols),
        "enrichment_cols": dedupe(enrichment_cols),
        "default_cols": dedupe(default_cols),
    }


def main():

    result = extract_from_docstring(docstring)
    pprint(result)


def analyze_file(path: str):
    """
    Parse a Python file, find all classes named 'Transform',
    extract their class docstrings, and pull structured information out.
    """
    with open(path, 'r', encoding='utf8') as f:
        tree = ast.parse(f.read(), filename=path)

    records = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'Transform':
            doc = ast.get_docstring(node)
            if doc:
                info = extract_from_docstring(doc)
                records.append(info)
    return records

def main():
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <python_source_file.py>")
        sys.exit(1)

    path = sys.argv[1]
    records = analyze_file(path)
    if not records:
        print("No `transform` methods with docstrings found.")
        return

    # Build a Polars DataFrame
    df = pl.DataFrame(
        {
            "producer":        [r["producer"]        for r in records],
            "primary_source":  [r["primary_source"]  for r in records],
            "source_cols":     [r["source_cols"]     for r in records],
            "transform_cols":  [r["transform_cols"]  for r in records],
            "enrichment_cols": [r["enrichment_cols"] for r in records],
            "default_cols":    [r["default_cols"]    for r in records],
        }
    )
    breakpoint()
    print(df)

################legacy parser############################"

def extract_matching_class_docstrings(path: str, var_name: str, target_value: str):
    """
    Scan the given Python file for classes where a class variable
    `var_name` equals `target_value`, and return their docstrings
    (or an explicit flag if missing).

    Returns a list of dicts:
      {
        "class_name":    <str>,
        "docstring":     <str or None>,
        "has_docstring": <bool>
      }
    """
    with open(path, 'r', encoding='utf8') as f:
        tree = ast.parse(f.read(), filename=path)

    results = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue

        # Look for class variable assignment like `name = "OUSS"`
        for stmt in node.body:
            if not isinstance(stmt, ast.Assign):
                continue

            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == var_name:
                    # Try to evaluate the assigned value

                        # Handles ast.Constant, ast.Str, ast.Num, lists, dicts, etc.
                    assigned = ast.literal_eval(stmt.value)


                    if assigned == target_value:
                        doc = ast.get_docstring(node)
                        results.append({
                            "class_name":    node.name,
                            "docstring":     doc,
                            "has_docstring": bool(doc),
                        })
    return results

# Example usage
if __name__ == "__main__":
    matches = extract_matching_class_docstrings("a1.py", "name", "miss")
    for info in matches:
        if info["has_docstring"]:
            print(f"Class {info['class_name']} docstring:\n{info['docstring']}\n")
        else:
            print(f"Class {info['class_name']} has no docstring.\n")
