import re
from enum import Enum

from pptx.enum.shapes import PP_PLACEHOLDER

FONT_SIZE_CASE = {
    PP_PLACEHOLDER.TITLE: 54,
    PP_PLACEHOLDER.SUBTITLE: 40,
    PP_PLACEHOLDER.BODY: 14,
    PP_PLACEHOLDER.FOOTER: 24,
    PP_PLACEHOLDER.HEADER: 32,
    PP_PLACEHOLDER.CHART: 12,
    PP_PLACEHOLDER.MIXED: 18
}

# scale factor for emu to pt
SCALE_FACTOR = 12700
SCALE_FACTOR_CH = 16000

class CatalogLayout(Enum):
    """
    Catalog layout enum
    """
    VERTICAL = "vertical"
    HORIZONTAL = "horizontal"
    UNDEFINED = "undefined"


class CatalogItem:
    """
    Catalog item including number shape, text shape and background shape.
    """
    def __init__(self, number_shape: dict, text_shape: dict, background_shape: dict | None = None):
        self.number_shape = number_shape
        self.text_shape = text_shape
        self.background_shape = background_shape

    def asdict(self):
        return {
            "number_shape": self.number_shape,
            "text_shape": self.text_shape,
            "background_shape": self.background_shape
        }

class CatalogList(list):
    """
    Catalog list including a list of `CatalogItem`.
    """
    def asdict(self):
        return [item.asdict() for item in self]

def is_english(texts):
    eng = 0
    if not texts:
        return False
    for t in texts:
        if re.match(r"[ `a-zA-Z.,':;/\"?<>!\(\)-]", t.strip()):
            eng += 1
    if eng / len(texts) > 0.8:
        return True
    return False

def is_chinese(text):
    if not text:
        return False
    chinese = 0
    for ch in text:
        if '\u4e00' <= ch <= '\u9fff':
            chinese += 1
    if chinese / len(text) > 0.2:
        return True
    return False