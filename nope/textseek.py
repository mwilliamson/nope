def seek_line(text, lineno):
    for current_lineno, line in enumerate(text, start=1):
        if current_lineno == lineno:
            return line.rstrip("\n")
