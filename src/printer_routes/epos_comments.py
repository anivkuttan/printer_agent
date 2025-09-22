
class ESCPOSCommands:
    """ESC/POS command constants for thermal receipt printers"""

    # Basic commands
    ESC = b'\x1b'
    GS = b'\x1d'

    # Initialize printer
    INIT = ESC + b'@'

    # Text formatting
    BOLD_ON = ESC + b'E\x01'
    BOLD_OFF = ESC + b'E\x00'
    UNDERLINE_ON = ESC + b'-\x01'
    UNDERLINE_OFF = ESC + b'-\x00'
    DOUBLE_HEIGHT = ESC + b'!\x10'
    DOUBLE_WIDTH = ESC + b'!\x20'
    DOUBLE_SIZE = ESC + b'!\x30'
    NORMAL_SIZE = ESC + b'!\x00'

    # Text alignment
    ALIGN_LEFT = ESC + b'a\x00'
    ALIGN_CENTER = ESC + b'a\x01'
    ALIGN_RIGHT = ESC + b'a\x02'

    # Font selection
    FONT_A = ESC + b'M\x00'
    FONT_B = ESC + b'M\x01'

    # Paper control
    FEED_LINE = b'\n'
    FEED_LINES_3 = b'\n\n\n'
    CUT_PAPER = GS + b'V\x00'
    CUT_PAPER_PARTIAL = GS + b'V\x01'

    # Character encoding
    CODEPAGE_UTF8 = ESC + b't\x03'

    # Special characters
    HORIZONTAL_LINE = '-' * 48 + '\n'
    DOUBLE_LINE = '=' * 48 + '\n'

    ARABIC_CHARSET = b'\x1b\x74\x11'
