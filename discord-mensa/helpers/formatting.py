ITALIC = lambda text: f"_{text}_" if text is not "" else ""
BOLD = lambda text: f"*{text}*" if text is not "" else ""
INLINE_CODE = lambda text: f"`{text}`" if text is not "" else ""
BLOCK_CODE = lambda text, lang="": f"```{lang}\n{text}\n```" if text is not "" else ""
