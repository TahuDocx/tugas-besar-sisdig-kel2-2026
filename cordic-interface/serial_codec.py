"""Pure byte codec between the GUI and the FPGA UART (no Qt, no I/O).

Protocol for now: t is sent as its ASCII text plus an optional line end; the FPGA replies
with ASCII. Swap encodeT/decodeRx when the real frame format is fixed.
"""

# === LINE ENDS ===

LINE_ENDS = {"None": b"", "LF": b"\n", "CR+LF": b"\r\n"}


# === ENCODER ===

def encodeT(text: str, line_end: str) -> bytes:
    """Returns the TX bytes for input t: stripped ASCII text + the named line end.

    Raises ValueError if text is empty after stripping, is not pure ASCII, or line_end is
    not a key of LINE_ENDS. No side effects.
    """
    if line_end not in LINE_ENDS:
        raise ValueError(f"unknown line end: {line_end!r}")
    value = text.strip()
    if not value:
        raise ValueError("t is empty")
    if not value.isascii():
        raise ValueError("t must be ASCII")
    return value.encode("ascii") + LINE_ENDS[line_end]


# === DECODER ===

def decodeRx(data: bytes) -> str:
    """Returns console text for received bytes: printable ASCII, LF and TAB as-is, CR dropped,
    every other byte as <HH> uppercase hex. Stateless, so chunk splits do not matter.
    """
    out = []
    for byte in data:
        if 0x20 <= byte <= 0x7E or byte in (0x09, 0x0A):
            out.append(chr(byte))
        elif byte != 0x0D:
            out.append(f"<{byte:02X}>")
    return "".join(out)
