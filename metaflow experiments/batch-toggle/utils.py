"""Re-usable utility functions."""

def conditionally(dec, cond):
    """
    Conditionally adds a decorator based on cond value.

    Usage:
    @conditionally(batch(cpu=2), x==12)
    """

    def resdec(f):
        if not cond:
            return f
        return dec(f)
    return resdec
