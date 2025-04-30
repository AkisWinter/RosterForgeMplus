def sanitize_charname(name: str) -> str:
    return name.replace(" ", "").replace("'", "")

def split_charname(raw: str) -> tuple[str, str] | None:
    if "-" not in raw:
        return None
    return raw.split("-", 1)

def build_char_id(name: str, realm: str) -> str:
    return sanitize_charname(f"{name}-{realm}")