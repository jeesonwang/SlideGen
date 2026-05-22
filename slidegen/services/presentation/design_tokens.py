from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DesignTokens:
    primary: str
    accent: str
    light_bg: str
    light_bg_alt: str
    text_primary: str
    text_secondary: str
    text_on_dark: str
    semantic_positive: str = "#2E7D32"
    semantic_negative: str = "#C62828"
    semantic_neutral: str = "#757575"
    title_font: str = "Calibri"
    title_size: int = 28
    subtitle_font: str = "Calibri"
    subtitle_size: int = 20
    body_font: str = "Calibri"
    body_size: int = 14
    caption_font: str = "Calibri"
    caption_size: int = 10
    slide_width: float = 13.333
    slide_height: float = 7.5
    page_margin_x: float = 0.8
    page_margin_y: float = 0.6
    card_gap: float = 0.3
    section_gap: float = 0.5
    line_spacing_multiple: float = 1.2


# 内置预设主题

DEFAULT_TOKENS = DesignTokens(
    primary="#1A3A5C",
    accent="#E8703B",
    light_bg="#F5F6F8",
    light_bg_alt="#E8ECF1",
    text_primary="#1A1A1A",
    text_secondary="#5C5C5C",
    text_on_dark="#FFFFFF",
)

PRESET_TOKENS: dict[str, DesignTokens] = {
    "general": DEFAULT_TOKENS,
    "minimal": DesignTokens(
        primary="#2C2C2C",
        accent="#4A90D9",
        light_bg="#FFFFFF",
        light_bg_alt="#F0F0F0",
        text_primary="#1A1A1A",
        text_secondary="#888888",
        text_on_dark="#FFFFFF",
    ),
    "academic": DesignTokens(
        primary="#003366",
        accent="#8B0000",
        light_bg="#FAFAF5",
        light_bg_alt="#F0EDE5",
        text_primary="#1A1A1A",
        text_secondary="#555555",
        text_on_dark="#FFFFFF",
        title_font="Times New Roman",
        body_font="Times New Roman",
    ),
}


def _extract_theme_colors(prs) -> dict[str, str | None]:
    """从 theme.xml 提取 <a:clrScheme> 颜色映射。"""
    from lxml import etree

    result: dict[str, str | None] = {}
    try:
        slide_master = prs.slide_masters[0]
        theme = slide_master.slide_layouts[0].slide_master.element
        nsmap = {
            "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        }
        dk1 = theme.find(".//a:dk1/a:srgbClr", namespaces=nsmap)
        dk2 = theme.find(".//a:dk2/a:srgbClr", namespaces=nsmap)
        lt1 = theme.find(".//a:lt1/a:srgbClr", namespaces=nsmap)
        lt2 = theme.find(".//a:lt2/a:srgbClr", namespaces=nsmap)
        accent1 = theme.find(".//a:accent1/a:srgbClr", namespaces=nsmap)
        accent2 = theme.find(".//a:accent2/a:srgbClr", namespaces=nsmap)
        accent3 = theme.find(".//a:accent3/a:srgbClr", namespaces=nsmap)
        result["dk1"] = dk1.get("val") if dk1 is not None else None
        result["dk2"] = dk2.get("val") if dk2 is not None else None
        result["lt1"] = lt1.get("val") if lt1 is not None else None
        result["lt2"] = lt2.get("val") if lt2 is not None else None
        result["accent1"] = accent1.get("val") if accent1 is not None else None
        result["accent2"] = accent2.get("val") if accent2 is not None else None
        result["accent3"] = accent3.get("val") if accent3 is not None else None
    except Exception:
        pass
    return result


def _extract_theme_fonts(prs) -> dict[str, str | None]:
    """从 theme.xml 提取 <a:fontScheme> 字体映射。"""
    result: dict[str, str | None] = {"major": None, "minor": None}
    try:
        nsmap = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        slide_master = prs.slide_masters[0]
        major = slide_master.element.find(".//a:majorFont/a:latin", namespaces=nsmap)
        minor = slide_master.element.find(".//a:minorFont/a:latin", namespaces=nsmap)
        if major is not None:
            result["major"] = major.get("typeface")
        if minor is not None:
            result["minor"] = minor.get("typeface")
    except Exception:
        pass
    return result


def _sample_shape_colors(prs, max_slides: int = 10) -> dict[str, list[tuple[str, float]]]:
    """从 shape 中采样实际使用的填充色和字体色（按面积加权）。

    Returns dict with 'fills' and 'fonts' keys, each a list of (hex_color, weight).
    """
    fills: list[tuple[str, float]] = []
    fonts: list[tuple[str, float]] = []
    min_area = 914400  # 1 square inch in EMU (914400 EMU)

    for slide in list(prs.slides)[:max_slides]:
        for shape in slide.shapes:
            area = shape.width * shape.height
            if area < min_area:
                continue
            try:
                fill = shape.fill
                if fill and fill.type is not None:
                    try:
                        rgb = fill.fore_color.rgb
                        if rgb:
                            fills.append((str(rgb), float(area)))
                    except Exception:
                        pass
            except Exception:
                pass
            if shape.has_text_frame:
                for para in shape.text_frame.paragraphs:
                    for run in para.runs:
                        try:
                            font_color = run.font.color
                            if font_color and font_color.rgb:
                                fonts.append((str(font_color.rgb), float(area)))
                        except Exception:
                            pass
    return {"fills": fills, "fonts": fonts}


def _hex_to_hsl(hex_color: str) -> tuple[float, float, float]:
    """将 hex 颜色转为 (hue, saturation, lightness)。"""
    hex_color = hex_color.lstrip("#")
    r, g, b = int(hex_color[0:2], 16) / 255.0, int(hex_color[2:4], 16) / 255.0, int(hex_color[4:6], 16) / 255.0
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2.0
    if max_c == min_c:
        return (0.0, 0.0, l)
    d = max_c - min_c
    s = d / (2.0 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)
    if max_c == r:
        h = ((g - b) / d) % 6
    elif max_c == g:
        h = (b - r) / d + 2
    else:
        h = (r - g) / d + 4
    return (h * 60, s, l)


def extract_design_tokens_from_presentation(prs, theme_name: str = "general") -> DesignTokens:
    """从模板 PPTX 提取 DesignTokens。两层策略：theme.xml + shape 采样。"""
    base = PRESET_TOKENS.get(theme_name, DEFAULT_TOKENS)

    # Layer 1: theme.xml
    theme_colors = _extract_theme_colors(prs)
    theme_fonts = _extract_theme_fonts(prs)

    # Layer 2: shape 采样（仅在 slide 数 >= 3 时启用）
    slide_count = len(prs.slides)
    sampled = {"fills": [], "fonts": []}
    if slide_count >= 3:
        sampled = _sample_shape_colors(prs)

    primary = theme_colors.get("dk1") or base.primary
    accent = theme_colors.get("accent1") or base.accent
    light_bg = theme_colors.get("lt1") or base.light_bg
    light_bg_alt = theme_colors.get("lt2") or base.light_bg_alt
    text_primary = theme_colors.get("dk2") or base.text_primary

    title_font = theme_fonts.get("major") or base.title_font
    body_font = theme_fonts.get("minor") or base.body_font

    return DesignTokens(
        primary=primary,
        accent=accent,
        light_bg=light_bg,
        light_bg_alt=light_bg_alt,
        text_primary=text_primary,
        text_secondary=base.text_secondary,
        text_on_dark=base.text_on_dark,
        title_font=title_font,
        title_size=base.title_size,
        subtitle_font=body_font,
        subtitle_size=base.subtitle_size,
        body_font=body_font,
        body_size=base.body_size,
        caption_font=base.caption_font,
        caption_size=base.caption_size,
    )
