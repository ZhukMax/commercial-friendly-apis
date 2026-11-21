"""Deterministic verdict from terms fields (see README legend)."""

def compute(e):
    if e.get("verdict_override"):
        return e["verdict_override"]
    cu = e.get("commercial_use", "unknown")
    st = e.get("storage_caching", "unknown")
    rd = e.get("redistribution_display", "unknown")
    sa = e.get("share_alike", "unknown")
    if cu == "no" or rd == "no":
        return "red"
    if cu == "unknown":
        return "unknown"
    if cu in ("paid-only", "ambiguous"):
        return "yellow"
    # cu == "yes": allowed, but green needs confirmed storage AND display; silence keeps it at yellow
    if st != "yes" or rd != "yes" or sa == "yes":
        return "yellow"
    return "green"
