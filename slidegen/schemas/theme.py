"""Theme color schemas for PowerPoint presentations."""

from pydantic import BaseModel, Field


class ThemeColorMapping(BaseModel):
    """
    PowerPoint theme color mapping.

    Maps theme color names to hex color values.
    Available theme colors:
    - dk1: Dark 1 (primary dark color, typically used for text)
    - lt1: Light 1 (primary light color, typically used for backgrounds)
    - dk2: Dark 2 (secondary dark color)
    - lt2: Light 2 (secondary light color)
    - accent1: Accent 1 (first accent color)
    - accent2: Accent 2 (second accent color)
    - accent3: Accent 3 (third accent color)
    - accent4: Accent 4 (fourth accent color)
    - accent5: Accent 5 (fifth accent color)
    - accent6: Accent 6 (sixth accent color)
    - hlink: Hyperlink color
    - folHlink: Followed hyperlink color
    """

    dk1: str | None = Field(None, description="Dark 1 color (hex, e.g., '000000')")
    lt1: str | None = Field(None, description="Light 1 color (hex, e.g., 'FFFFFF')")
    dk2: str | None = Field(None, description="Dark 2 color (hex, e.g., '44546A')")
    lt2: str | None = Field(None, description="Light 2 color (hex, e.g., 'E7E6E6')")
    accent1: str | None = Field(None, description="Accent 1 color (hex, e.g., '4472C4')")
    accent2: str | None = Field(None, description="Accent 2 color (hex, e.g., 'ED7D31')")
    accent3: str | None = Field(None, description="Accent 3 color (hex, e.g., 'A5A5A5')")
    accent4: str | None = Field(None, description="Accent 4 color (hex, e.g., 'FFC000')")
    accent5: str | None = Field(None, description="Accent 5 color (hex, e.g., '5B9BD5')")
    accent6: str | None = Field(None, description="Accent 6 color (hex, e.g., '70AD47')")
    hlink: str | None = Field(None, description="Hyperlink color (hex, e.g., '0563C1')")
    folHlink: str | None = Field(None, description="Followed hyperlink color (hex, e.g., '954F72')")

    def model_dump_colors(self) -> dict[str, str]:
        """Return only non-None color values as a dictionary."""
        return {k: v for k, v in self.model_dump().items() if v is not None}


class PresentationTheme(BaseModel):
    """PowerPoint presentation theme with color scheme."""

    name: str = Field(default="Custom Theme", description="Theme name")
    colors: ThemeColorMapping = Field(description="Theme color mapping")


# Predefined theme presets
class ThemePresets:
    """Predefined theme color presets."""

    OCEAN_DEPTHS = PresentationTheme(
        name="Ocean Depths",
        colors=ThemeColorMapping(
            dk1="1A2332",  # Deep Navy for text
            lt1="F1FAEE",  # Cream for backgrounds
            dk2="1A2332",  # Deep Navy
            lt2="A8DADC",  # Seafoam
            accent1="2D8B8B",  # Teal
            accent2="A8DADC",  # Seafoam
            accent3="F1FAEE",  # Cream
            accent4="1A2332",  # Deep Navy
            accent5="2D8B8B",  # Teal
            accent6="A8DADC",  # Seafoam
            hlink="2D8B8B",  # Teal for hyperlinks
            folHlink="1A2332",  # Deep Navy for followed links
        ),
    )

    SUNSET_BOULEVARD = PresentationTheme(
        name="Sunset Boulevard",
        colors=ThemeColorMapping(
            dk1="264653",  # Deep purple for text
            lt1="FFFFFF",  # White for backgrounds
            dk2="264653",  # Deep purple
            lt2="F8EDEB",  # Light warm sand
            accent1="E76F51",  # Burnt orange
            accent2="F4A261",  # Coral
            accent3="E9C46A",  # Warm sand
            accent4="2A9D8F",  # Teal
            accent5="264653",  # Deep purple
            accent6="E76F51",  # Burnt orange
            hlink="E76F51",  # Burnt orange for hyperlinks
            folHlink="264653",  # Deep purple for followed links
        ),
    )

    FOREST_CANOPY = PresentationTheme(
        name="Forest Canopy",
        colors=ThemeColorMapping(
            dk1="2D4A2B",  # Forest Green for text
            lt1="FAF9F6",  # Ivory for backgrounds
            dk2="2D4A2B",  # Forest Green
            lt2="A4AC86",  # Olive
            accent1="2D4A2B",  # Forest Green
            accent2="7D8471",  # Sage
            accent3="A4AC86",  # Olive
            accent4="FAF9F6",  # Ivory
            accent5="2D4A2B",  # Forest Green
            accent6="7D8471",  # Sage
            hlink="2D4A2B",  # Forest Green for hyperlinks
            folHlink="7D8471",  # Sage for followed links
        ),
    )

    MODERN_MINIMALIST = PresentationTheme(
        name="Modern Minimalist",
        colors=ThemeColorMapping(
            dk1="36454F",  # Charcoal for text
            lt1="FFFFFF",  # White for backgrounds
            dk2="36454F",  # Charcoal
            lt2="D3D3D3",  # Light Gray
            accent1="708090",  # Slate Gray
            accent2="36454F",  # Charcoal
            accent3="D3D3D3",  # Light Gray
            accent4="708090",  # Slate Gray
            accent5="36454F",  # Charcoal
            accent6="D3D3D3",  # Light Gray
            hlink="708090",  # Slate Gray for hyperlinks
            folHlink="36454F",  # Charcoal for followed links
        ),
    )

    GOLDEN_HOUR = PresentationTheme(
        name="Golden Hour",
        colors=ThemeColorMapping(
            dk1="4A403A",  # Chocolate Brown for text
            lt1="D4B896",  # Warm Beige for backgrounds
            dk2="4A403A",  # Chocolate Brown
            lt2="D4B896",  # Warm Beige
            accent1="F4A900",  # Mustard Yellow
            accent2="C1666B",  # Terracotta
            accent3="D4B896",  # Warm Beige
            accent4="4A403A",  # Chocolate Brown
            accent5="F4A900",  # Mustard Yellow
            accent6="C1666B",  # Terracotta
            hlink="F4A900",  # Mustard Yellow for hyperlinks
            folHlink="C1666B",  # Terracotta for followed links
        ),
    )

    ARCTIC_FROST = PresentationTheme(
        name="Arctic Frost",
        colors=ThemeColorMapping(
            dk1="4A6FA5",  # Steel Blue for text
            lt1="FAFAFA",  # Crisp White for backgrounds
            dk2="4A6FA5",  # Steel Blue
            lt2="D4E4F7",  # Ice Blue
            accent1="4A6FA5",  # Steel Blue
            accent2="D4E4F7",  # Ice Blue
            accent3="C0C0C0",  # Silver
            accent4="FAFAFA",  # Crisp White
            accent5="4A6FA5",  # Steel Blue
            accent6="D4E4F7",  # Ice Blue
            hlink="4A6FA5",  # Steel Blue for hyperlinks
            folHlink="C0C0C0",  # Silver for followed links
        ),
    )

    DESERT_ROSE = PresentationTheme(
        name="Desert Rose",
        colors=ThemeColorMapping(
            dk1="5D2E46",  # Deep Burgundy for text
            lt1="E8D5C4",  # Sand for backgrounds
            dk2="5D2E46",  # Deep Burgundy
            lt2="E8D5C4",  # Sand
            accent1="D4A5A5",  # Dusty Rose
            accent2="B87D6D",  # Clay
            accent3="E8D5C4",  # Sand
            accent4="5D2E46",  # Deep Burgundy
            accent5="D4A5A5",  # Dusty Rose
            accent6="B87D6D",  # Clay
            hlink="D4A5A5",  # Dusty Rose for hyperlinks
            folHlink="5D2E46",  # Deep Burgundy for followed links
        ),
    )

    TECH_INNOVATION = PresentationTheme(
        name="Tech Innovation",
        colors=ThemeColorMapping(
            dk1="1E1E1E",  # Dark Gray for text
            lt1="FFFFFF",  # White for backgrounds
            dk2="1E1E1E",  # Dark Gray
            lt2="FFFFFF",  # White
            accent1="0066FF",  # Electric Blue
            accent2="00FFFF",  # Neon Cyan
            accent3="1E1E1E",  # Dark Gray
            accent4="0066FF",  # Electric Blue
            accent5="00FFFF",  # Neon Cyan
            accent6="FFFFFF",  # White
            hlink="0066FF",  # Electric Blue for hyperlinks
            folHlink="00FFFF",  # Neon Cyan for followed links
        ),
    )

    BOTANICAL_GARDEN = PresentationTheme(
        name="Botanical Garden",
        colors=ThemeColorMapping(
            dk1="4A7C59",  # Fern Green for text
            lt1="F5F3ED",  # Cream for backgrounds
            dk2="4A7C59",  # Fern Green
            lt2="F5F3ED",  # Cream
            accent1="4A7C59",  # Fern Green
            accent2="F9A620",  # Marigold
            accent3="B7472A",  # Terracotta
            accent4="F5F3ED",  # Cream
            accent5="4A7C59",  # Fern Green
            accent6="F9A620",  # Marigold
            hlink="4A7C59",  # Fern Green for hyperlinks
            folHlink="B7472A",  # Terracotta for followed links
        ),
    )

    MIDNIGHT_GALAXY = PresentationTheme(
        name="Midnight Galaxy",
        colors=ThemeColorMapping(
            dk1="2B1E3E",  # Deep Purple for text
            lt1="E6E6FA",  # Silver for backgrounds
            dk2="2B1E3E",  # Deep Purple
            lt2="A490C2",  # Lavender
            accent1="4A4E8F",  # Cosmic Blue
            accent2="A490C2",  # Lavender
            accent3="E6E6FA",  # Silver
            accent4="2B1E3E",  # Deep Purple
            accent5="4A4E8F",  # Cosmic Blue
            accent6="A490C2",  # Lavender
            hlink="4A4E8F",  # Cosmic Blue for hyperlinks
            folHlink="2B1E3E",  # Deep Purple for followed links
        ),
    )

    WARM_AUTUMN = PresentationTheme(
        name="Warm Autumn",
        colors=ThemeColorMapping(
            dk1="000000",  # Black for text (keep default)
            lt1="FFFFFF",  # White for backgrounds (keep default)
            dk2="5D1D2E",  # Deep Burgundy
            lt2="FFF5E6",  # Warm Beige
            accent1="E74C3C",  # Vibrant Red
            accent2="F39C12",  # Bright Orange
            accent3="E67E22",  # Deep Orange
            accent4="D35400",  # Pumpkin Orange
            accent5="C0392B",  # Deep Red
            accent6="F1C40F",  # Golden Yellow
            hlink="E67E22",  # Deep Orange for hyperlinks
            folHlink="C0392B",  # Deep Red for followed links
        ),
    )

    @classmethod
    def get_preset(cls, preset_name: str) -> PresentationTheme | None:
        """Get a theme preset by name."""
        presets = {
            "ocean_depths": cls.OCEAN_DEPTHS,
            "sunset_boulevard": cls.SUNSET_BOULEVARD,
            "forest_canopy": cls.FOREST_CANOPY,
            "modern_minimalist": cls.MODERN_MINIMALIST,
            "golden_hour": cls.GOLDEN_HOUR,
            "arctic_frost": cls.ARCTIC_FROST,
            "desert_rose": cls.DESERT_ROSE,
            "tech_innovation": cls.TECH_INNOVATION,
            "botanical_garden": cls.BOTANICAL_GARDEN,
            "midnight_galaxy": cls.MIDNIGHT_GALAXY,
            "warm_autumn": cls.WARM_AUTUMN,
        }
        return presets.get(preset_name.lower())

    @classmethod
    def list_presets(cls) -> list[str]:
        """List all available preset names."""
        return [
            "ocean_depths",
            "sunset_boulevard",
            "forest_canopy",
            "modern_minimalist",
            "golden_hour",
            "arctic_frost",
            "desert_rose",
            "tech_innovation",
            "botanical_garden",
            "midnight_galaxy",
            "warm_autumn",
        ]
