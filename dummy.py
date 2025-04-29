        bullets = re.findall(r'^\s*-\s', block, re.MULTILINE)
        if len(bullets) == 0:
            raise AssertionError(f"Section “{name}” has NO bullets")
