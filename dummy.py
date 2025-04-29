import re

@cached_property
def sections(self) -> dict[str, str]:
    section_names = ["Filtering", "Transformation", "Enrichment", "Default"]
    joined = "|".join(section_names)
    pattern = rf"""
            (?m)                             # multiline mode
            ^\s*                             # start of a line + any indent
            (?P<section>{joined})           # capture one of the section names
            :\s*\n                           # colon + optional spaces + newline
            (?P<content>                     # now capture everything
                (?:.*\n)*?                  # non-greedy: any lines, including blanks
            )
            (?=                              # stop when we see:
                ^\s*(?:{joined}):            #   another header at line-start
              | \Z                           # or end-of-string
            )
        """

    sections: dict[str,str] = {
        m.group("section"): m.group("content")
        for m in pattern.finditer(self.docstring)
    }
    return sections
