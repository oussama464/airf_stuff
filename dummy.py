def validate_sections(sections):
    """
    sections is a d
    This function will:
      * error if any of the 4 keys is missing
      * skip any section whose stripped content is "None" or "None."
      * for all other sections, error if any non-blank line
        • doesn’t begin with exactly four spaces, or
        • after those four spaces, doesn’t begin with "- "
    """
    required = ["Default", "Enrichment", "filtering", "Transformation"]
    for sec in required:
        if sec not in sections:
            raise KeyError(f"Missing section: {sec!r}")

        content = sections[sec]
        # if the whole section is literally "None" or "None.", skip validation
        if content.strip() in ("None", "None."):
            continue

        for i, line in enumerate(content.splitlines(), start=1):
            if not line.strip():
                # skip blank lines
                continue

            # 1) exactly four spaces?
            if not line.startswith("    "):
                raise ValueError(
                    f"{sec!r}, line {i}: bad indentation (need 4 spaces): {line!r}"
                )

            # 2) after those four spaces, must start with "- "
            if not line[4:].startswith("- "):
                raise ValueError(
                    f"{sec!r}, line {i}: missing '-' after indentation: {line!r}"
                )

    return True


# example usage
sections = {
}

validate_sections(sections)
print("✅ all non-None sections are valid!")



# run
docstring_lint_check(sections)

