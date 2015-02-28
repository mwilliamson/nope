__all__ = ["escape"]


#:: str, ?quote: bool -> str
def escape(value, quote=None):
    value = value.replace("&", "&amp;")
    value = value.replace("<", "&lt;")
    value = value.replace(">", "&gt;")
    if quote:
        value = value.replace('"', "&quot;")
    return value

