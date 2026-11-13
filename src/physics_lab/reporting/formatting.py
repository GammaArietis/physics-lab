"""Terminal formatting helpers."""

from __future__ import annotations

from typing import Iterable, Sequence


def banner(title: str, width: int = 32) -> str:
    line = "=" * width
    return f"{line}\n{title}\n{line}"


def pad(text: str, width: int) -> str:
    text = str(text)
    if len(text) >= width:
        return text
    return text + " " * (width - len(text))


def table(headers: Sequence[str], rows: Iterable[Sequence[object]], widths: Sequence[int] | None = None) -> str:
    header_list = [str(h) for h in headers]
    row_lists = [[_cell(c) for c in row] for row in rows]
    if widths is None:
        widths = []
        for i, header in enumerate(header_list):
            longest = len(header)
            for row in row_lists:
                if i < len(row):
                    longest = max(longest, len(row[i]))
            widths.append(min(max(longest + 1, 8), 28))
    lines = [" ".join(pad(h, w) for h, w in zip(header_list, widths))]
    lines.append("-" * max(len(lines[0]), 8))
    for row in row_lists:
        padded = row + [""] * (len(header_list) - len(row))
        lines.append(" ".join(pad(c, w) for c, w in zip(padded, widths)))
    return "\n".join(lines)


def _cell(value: object) -> str:
    if value is None:
        return "---"
    if isinstance(value, float):
        if abs(value) < 1e-12:
            return "0"
        if abs(value) >= 1e4 or (0 < abs(value) < 1e-3):
            return f"{value:.6e}"
        return f"{value:.8g}"
    return str(value)


def tree_block(title: str, body: str) -> str:
    return f"{title}\n{body}"
