import re

@cached_property
def sections(self) -> dict[str, str]:
    section_names = ["Filtering", "Transformation", "Enrichment", "Default"]
    # escape them just in case
    names = "|".join(map(re.escape, section_names))

    # (?m) → multiline so ^ and $ match at line boundaries
    # (?s) → dotall so . matches \n
    pattern = re.compile(
        rf"(?ms)^            # from the start of a line
           (?P<section>{names}) # section name
           :\s*\n             # colon, optional space(s), then the EOL
           (?P<content>       # start of content capture
             .*?              #    any chars (incl. newlines), non-greedy
           )                  # end of content capture
           (?=^({names}):|\Z) # up to the next “Name:” at BOL or end of string
        ",
        re.VERBOSE
    )

    sections: dict[str,str] = {
        m.group("section"): m.group("content")
        for m in pattern.finditer(self.docstring)
    }
    return sections
