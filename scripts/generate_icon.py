"""
Generate Conduital app icon (.ico) with 16-256px variants.

Design: Stylized "C" conduit shape with momentum arrow motif.
- Deep blue gradient background (#1e3a5f to #0f2137)
- White/light conduit shape suggesting flow and momentum
- Clean, modern, recognizable at small sizes

Usage:
    python scripts/generate_icon.py

Output:
    assets/conduital.ico (multi-resolution: 16, 32, 48, 64, 128, 256)
"""

import math
import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    print("ERROR: Pillow is required. Install with: pip install Pillow")
    sys.exit(1)


def draw_icon(size: int) -> Image.Image:
    """Draw the Conduital icon at the given size."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # --- Background: rounded square with deep blue gradient ---
    margin = max(1, size // 32)
    corner_radius = max(2, size // 5)

    # Draw rounded rectangle background
    # Gradient from top-left (#2563eb, blue-600) to bottom-right (#1e40af, blue-800)
    for y in range(size):
        t = y / max(1, size - 1)
        r = int(30 + t * (15 - 30))    # 30 -> 15
        g = int(99 + t * (64 - 99))    # 99 -> 64
        b = int(235 + t * (175 - 235)) # 235 -> 175
        draw.line([(margin, y), (size - margin - 1, y)], fill=(r, g, b, 255))

    # Create rounded corner mask
    mask = Image.new("L", (size, size), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle(
        [margin, margin, size - margin - 1, size - margin - 1],
        radius=corner_radius,
        fill=255,
    )
    img.putalpha(mask)

    # Re-create draw on the masked image
    # We need to draw the gradient again properly within the mask
    bg = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bg_draw = ImageDraw.Draw(bg)
    for y in range(size):
        t = y / max(1, size - 1)
        r = int(37 + t * (30 - 37))
        g = int(99 + t * (64 - 99))
        b = int(235 + t * (175 - 235))
        bg_draw.line([(0, y), (size - 1, y)], fill=(r, g, b, 255))

    # Apply rounded rect mask to gradient
    result = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    result.paste(bg, mask=mask)
    draw = ImageDraw.Draw(result)

    # --- Foreground: Stylized momentum conduit ---
    # Design: An upward-right arrow/chevron shape suggesting flow
    # At larger sizes this is detailed; at small sizes it simplifies

    cx, cy = size / 2, size / 2
    unit = size / 16  # Design unit

    if size >= 48:
        # Detailed design: Bold "C" conduit with momentum arrow
        # Draw a bold stylized letter "C" with an integrated forward arrow

        # The "C" shape — thick arc
        pen_width = max(2, int(unit * 2.2))

        # Draw the C as a thick arc
        bbox_inset = unit * 3.5
        bbox = [bbox_inset, bbox_inset, size - bbox_inset, size - bbox_inset]

        # Main C arc (open on the right side)
        draw.arc(bbox, start=45, end=315, fill=(255, 255, 255, 240), width=pen_width)

        # Momentum arrow tip at the top opening of the C
        # Arrow points upper-right from the C opening
        arrow_len = unit * 2.5
        # Top end of C arc (at 45 degrees)
        arc_cx = cx
        arc_cy = cy
        arc_r = (size - 2 * bbox_inset) / 2
        top_x = arc_cx + arc_r * math.cos(math.radians(-45))
        top_y = arc_cy + arc_r * math.sin(math.radians(-45))

        # Arrow head pointing upper-right
        arrow_tip_x = top_x + arrow_len * 0.7
        arrow_tip_y = top_y - arrow_len * 0.7

        # Arrow barbs
        barb_len = arrow_len * 0.6
        barb1_x = arrow_tip_x - barb_len
        barb1_y = arrow_tip_y
        barb2_x = arrow_tip_x
        barb2_y = arrow_tip_y + barb_len

        arrow_width = max(2, int(unit * 1.5))
        # Arrow shaft
        draw.line(
            [(top_x, top_y), (arrow_tip_x, arrow_tip_y)],
            fill=(255, 255, 255, 240),
            width=arrow_width,
        )
        # Arrow head barbs
        draw.line(
            [(barb1_x, barb1_y), (arrow_tip_x, arrow_tip_y)],
            fill=(255, 255, 255, 240),
            width=arrow_width,
        )
        draw.line(
            [(barb2_x, barb2_y), (arrow_tip_x, arrow_tip_y)],
            fill=(255, 255, 255, 240),
            width=arrow_width,
        )

        # Bottom momentum streak (from bottom of C)
        bottom_x = arc_cx + arc_r * math.cos(math.radians(45))
        bottom_y = arc_cy + arc_r * math.sin(math.radians(45))
        streak_len = unit * 1.8
        draw.line(
            [(bottom_x, bottom_y), (bottom_x + streak_len * 0.7, bottom_y + streak_len * 0.3)],
            fill=(255, 255, 255, 160),
            width=max(1, int(unit * 0.8)),
        )

    elif size >= 32:
        # Medium design: Simpler C + arrow
        pen_width = max(2, int(unit * 2.5))
        bbox_inset = unit * 3.5
        bbox = [bbox_inset, bbox_inset, size - bbox_inset, size - bbox_inset]
        draw.arc(bbox, start=50, end=310, fill=(255, 255, 255, 240), width=pen_width)

        # Simple arrow at top-right
        arc_r = (size - 2 * bbox_inset) / 2
        top_x = cx + arc_r * math.cos(math.radians(-50))
        top_y = cy + arc_r * math.sin(math.radians(-50))
        arrow_len = unit * 2
        tip_x = top_x + arrow_len * 0.6
        tip_y = top_y - arrow_len * 0.6
        aw = max(2, int(unit * 1.2))
        draw.line([(top_x, top_y), (tip_x, tip_y)], fill=(255, 255, 255, 240), width=aw)
        draw.line([(tip_x - unit, tip_y), (tip_x, tip_y)], fill=(255, 255, 255, 240), width=aw)
        draw.line([(tip_x, tip_y + unit), (tip_x, tip_y)], fill=(255, 255, 255, 240), width=aw)

    else:
        # Small (16px): Just a bold C shape
        pen_width = max(2, int(unit * 3))
        bbox_inset = unit * 3
        bbox = [bbox_inset, bbox_inset, size - bbox_inset, size - bbox_inset]
        draw.arc(bbox, start=50, end=310, fill=(255, 255, 255, 255), width=pen_width)

    return result


def main():
    sizes = [16, 32, 48, 64, 128, 256]
    images = [draw_icon(s) for s in sizes]

    # Determine output path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    assets_dir = os.path.join(project_root, "assets")
    os.makedirs(assets_dir, exist_ok=True)

    ico_path = os.path.join(assets_dir, "conduital.ico")

    # Save as .ico with all sizes
    images[0].save(
        ico_path,
        format="ICO",
        sizes=[(s, s) for s in sizes],
        append_images=images[1:],
    )

    print(f"Icon saved to {ico_path}")
    print(f"Sizes: {', '.join(f'{s}x{s}' for s in sizes)}")

    # Also save individual PNGs for reference
    for img, s in zip(images, sizes):
        png_path = os.path.join(assets_dir, f"conduital-{s}.png")
        img.save(png_path)
    print(f"Individual PNGs saved to {assets_dir}")


if __name__ == "__main__":
    main()
