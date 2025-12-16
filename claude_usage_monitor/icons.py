"""Dynamic icon generation for Claude Usage Monitor."""

import math
import tempfile
from pathlib import Path
from typing import Tuple


def get_color_for_usage(usage: float, is_long_term: bool = False) -> str:
    """Get color based on usage percentage.

    5-hour colors: Green -> Orange -> Red
    7-day colors: Cyan -> Blue-Purple -> Deep Purple
    """
    if is_long_term:
        if usage >= 0.90:
            return "#7C3AED"  # Deep purple
        elif usage >= 0.70:
            return "#8B5CF6"  # Blue-purple
        else:
            return "#06B6D4"  # Cyan
    else:
        if usage >= 0.90:
            return "#EF4444"  # Red
        elif usage >= 0.70:
            return "#F97316"  # Orange
        else:
            return "#22C55E"  # Green


def create_ring_path(cx: float, cy: float, radius: float,
                     start_angle: float, end_angle: float) -> str:
    """Create SVG arc path for a ring segment."""
    start_rad = math.radians(start_angle - 90)  # Start from top
    end_rad = math.radians(end_angle - 90)

    x1 = cx + radius * math.cos(start_rad)
    y1 = cy + radius * math.sin(start_rad)
    x2 = cx + radius * math.cos(end_rad)
    y2 = cy + radius * math.sin(end_rad)

    large_arc = 1 if (end_angle - start_angle) > 180 else 0

    return f"M {x1} {y1} A {radius} {radius} 0 {large_arc} 1 {x2} {y2}"


def generate_dual_ring_svg(short_term_usage: float, long_term_usage: float,
                           size: int = 22) -> str:
    """Generate SVG with dual concentric progress rings.

    Outer ring: 5-hour usage
    Inner ring: 7-day usage
    """
    cx, cy = size / 2, size / 2
    outer_radius = size / 2 - 2
    inner_radius = size / 2 - 5
    stroke_width = 2.5

    # Background circles (gray tracks)
    bg_color = "#374151"  # Dark gray

    # Get colors based on usage
    outer_color = get_color_for_usage(short_term_usage, is_long_term=False)
    inner_color = get_color_for_usage(long_term_usage, is_long_term=True)

    # Calculate arc angles (0-360)
    outer_angle = min(short_term_usage, 1.0) * 360
    inner_angle = min(long_term_usage, 1.0) * 360

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <!-- Background tracks -->
  <circle cx="{cx}" cy="{cy}" r="{outer_radius}" fill="none" stroke="{bg_color}" stroke-width="{stroke_width}" opacity="0.3"/>
  <circle cx="{cx}" cy="{cy}" r="{inner_radius}" fill="none" stroke="{bg_color}" stroke-width="{stroke_width}" opacity="0.3"/>
'''

    # Add outer progress arc (5-hour)
    if outer_angle > 0:
        if outer_angle >= 360:
            svg += f'  <circle cx="{cx}" cy="{cy}" r="{outer_radius}" fill="none" stroke="{outer_color}" stroke-width="{stroke_width}"/>\n'
        else:
            path = create_ring_path(cx, cy, outer_radius, 0, outer_angle)
            svg += f'  <path d="{path}" fill="none" stroke="{outer_color}" stroke-width="{stroke_width}" stroke-linecap="round"/>\n'

    # Add inner progress arc (7-day)
    if inner_angle > 0:
        if inner_angle >= 360:
            svg += f'  <circle cx="{cx}" cy="{cy}" r="{inner_radius}" fill="none" stroke="{inner_color}" stroke-width="{stroke_width}"/>\n'
        else:
            path = create_ring_path(cx, cy, inner_radius, 0, inner_angle)
            svg += f'  <path d="{path}" fill="none" stroke="{inner_color}" stroke-width="{stroke_width}" stroke-linecap="round"/>\n'

    svg += '</svg>'
    return svg


def generate_single_ring_svg(usage: float, is_long_term: bool = False,
                             size: int = 22) -> str:
    """Generate SVG with single progress ring."""
    cx, cy = size / 2, size / 2
    radius = size / 2 - 2
    stroke_width = 3

    bg_color = "#374151"
    color = get_color_for_usage(usage, is_long_term)
    angle = min(usage, 1.0) * 360

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" viewBox="0 0 {size} {size}">
  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{bg_color}" stroke-width="{stroke_width}" opacity="0.3"/>
'''

    if angle > 0:
        if angle >= 360:
            svg += f'  <circle cx="{cx}" cy="{cy}" r="{radius}" fill="none" stroke="{color}" stroke-width="{stroke_width}"/>\n'
        else:
            path = create_ring_path(cx, cy, radius, 0, angle)
            svg += f'  <path d="{path}" fill="none" stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round"/>\n'

    svg += '</svg>'
    return svg


class DynamicIconManager:
    """Manages dynamic icon generation and caching."""

    def __init__(self):
        self.icon_dir = Path(tempfile.mkdtemp(prefix="claude-usage-icons-"))
        self._cache = {}

    def get_icon_path(self, short_term: float, long_term: float) -> str:
        """Get path to icon for given usage levels."""
        # Round to nearest 5% for caching
        short_key = round(short_term * 20) * 5
        long_key = round(long_term * 20) * 5
        cache_key = f"{short_key}_{long_key}"

        if cache_key in self._cache:
            return self._cache[cache_key]

        # Generate new icon
        svg = generate_dual_ring_svg(short_term, long_term)
        icon_path = self.icon_dir / f"usage_{cache_key}.svg"
        icon_path.write_text(svg)

        self._cache[cache_key] = str(icon_path)
        return str(icon_path)

    def get_disconnected_icon_path(self) -> str:
        """Get gray disconnected icon."""
        if "disconnected" in self._cache:
            return self._cache["disconnected"]

        svg = generate_dual_ring_svg(0, 0)
        icon_path = self.icon_dir / "disconnected.svg"
        icon_path.write_text(svg)

        self._cache["disconnected"] = str(icon_path)
        return str(icon_path)

    def cleanup(self):
        """Remove temporary icon files."""
        import shutil
        if self.icon_dir.exists():
            shutil.rmtree(self.icon_dir)
