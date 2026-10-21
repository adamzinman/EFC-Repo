"""Shared helpers: config.json loading and LaTeX text cleanup."""
import json, os, re

def cfg():
    if os.path.exists("config.json"):
        with open("config.json", encoding="utf-8") as h:
            return json.load(h)
    return {}

def clean(s):
    """Rough LaTeX -> plain text."""
    s = re.sub(r"(?<!\\)%.*", "", s)
    s = re.sub(r"\\(label|index)\{[^}]*\}", "", s)
    for _ in range(3):
        s = re.sub(r"\\[a-zA-Z]+\*?\{([^{}]*)\}", r"\1", s)
    s = re.sub(r"\\([_&%#$])", r"\1", s)
    s = re.sub(r"\\[a-zA-Z]+\*?", "", s)
    s = s.replace("~", " ").replace("{", "").replace("}", "")
    return re.sub(r"\s+", " ", s).strip()
