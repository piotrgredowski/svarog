from enum import Enum
from enum import auto


class MarkdownRenderType(str, Enum):
    """Enum for different markdown render types."""

    code_block = auto()
    table = auto()
    table_with_headers_capitalized = auto()
    table_with_headers_title_cased = auto()
