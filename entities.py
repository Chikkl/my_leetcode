previousText = ""

CODE_COLORS = {
    "normal": "#eaeaea",
    "keywords": "#ea5f5f",
    "comments": "#5feaA5",
    "string": "#eaa25f",
    "background": "#2a2a2a",
    "font": "Consolas 13",
}

BG_COLOR = "white"
FG_COLOR = "black"

HIGHLIGHT_PATTERNS = [
    [
        r"(^| )(False|None|True|and|as|assert|async|await|break|class|continue|def|del|elif|else|except|finally|for|from|global|if|import|in|is|lambda|nonlocal|not|or|pass|raise|return|try|while|with|yield)($| )",
        CODE_COLORS["keywords"],
    ],
    [r'".*?"', CODE_COLORS["string"]],
    [r"\'.*?\'", CODE_COLORS["string"]],
    [r"#.*?$", CODE_COLORS["comments"]],
]
