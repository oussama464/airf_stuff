
def docstring_lint_check(sections_dict):
    required = ["Default", "Enrichment", "Filtering", "Transformation"]

    for sec in required:
        text = sections_dict.get(sec)
        if text is None:
            raise ValueError(f"Missing section “{sec}”")

        # if the section is exactly "None.", skip all validation
        if text.strip() == "None.":
            continue

        # 1) at least one bullet anywhere?
        if not re.search(r"-\s+", text):
            raise ValueError(f"Section “{sec}” has no bullets (no “- ” found).")

        # 2) check every bullet-line for exactly 4 spaces before the dash
        for m in re.finditer(r"^(\s*)-\s+", text, flags=re.MULTILINE):
            indent = len(m.group(1))
            if indent != 4:
                lineno = text[: m.start()].count("\n") + 1
                raise ValueError(
                    f"Section “{sec}”, line {lineno}: "
                    f"bullet is indented {indent} spaces (should be 4)."
                )


# run
docstring_lint_check(sections)

