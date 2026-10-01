import re


def needs_camera(text):
    """Conservative explicit scene requests. No speculative camera capture."""
    return bool(re.search(r"\b(what (?:am i|are we) (?:looking at|seeing)|read this|describe this|what (?:is|are) (?:this|these|that)|explain what i(?:'m| am) seeing)\b",text,re.I))
