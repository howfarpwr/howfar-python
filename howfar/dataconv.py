def opt3004_code_to_lx(code):
    """
    Convert OPT3004 internal floating-point representation to a direct measurement of Lx.
    See https://www.ti.com/lit/ds/symlink/opt3004.pdf page 21.
    """
    mantissa = code & 0xFFF
    exponent = code >> 12
    return (mantissa << exponent) * 0.01
