"""Generate high-resolution PNG and multi-size Windows ICO for Audingo Songs Forge."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter

ASSETS_DIR = Path(__file__).parent


def create_audingo_icon():
    size = 1024
    master = Image.new("RGBA", (size, size), (0, 0, 0, 0))

    # 1. Soft Ambient Drop Shadow
    shadow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(shadow)
    s_box = (82, 92, 942, 952)
    s_draw.rounded_rectangle(s_box, radius=210, fill=(0, 0, 0, 115))
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=28))
    master.alpha_composite(shadow)

    # 2. Apple-style Dark Squircle Canvas with Vertical Gradient
    sq_mask = Image.new("L", (size, size), 0)
    m_draw = ImageDraw.Draw(sq_mask)
    sq_box = (76, 76, 948, 948)
    m_draw.rounded_rectangle(sq_box, radius=205, fill=255)

    sq_surface = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for y in range(76, 949):
        factor = (y - 76) / (948 - 76)
        # Deep dark studio graphite gradient (#262830 -> #121316)
        r = int(38 * (1 - factor) + 18 * factor)
        g = int(40 * (1 - factor) + 19 * factor)
        b = int(48 * (1 - factor) + 23 * factor)
        line = Image.new("RGBA", (size, 1), (r, g, b, 255))
        sq_surface.paste(line, (0, y))

    # Subtle radial highlight at top
    sheen = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    sheen_draw = ImageDraw.Draw(sheen)
    cx, cy = 512, 140
    for r_val in range(400, 0, -4):
        alpha = int(22 * (1 - r_val / 400))
        sheen_draw.ellipse(
            (cx - r_val, cy - r_val // 2, cx + r_val, cy + r_val // 2),
            fill=(255, 255, 255, alpha),
        )
    sq_surface = Image.alpha_composite(sq_surface, sheen)

    # Inset Rim Highlight Border
    border_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    b_draw = ImageDraw.Draw(border_img)
    b_draw.rounded_rectangle(
        sq_box, radius=205, outline=(255, 255, 255, 34), width=3
    )
    sq_surface = Image.alpha_composite(sq_surface, border_img)

    master.paste(sq_surface, (0, 0), sq_mask)

    # 3. Waveform Audio Glow
    glow = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    g_draw = ImageDraw.Draw(glow)
    g_draw.ellipse((260, 260, 764, 764), fill=(0, 110, 255, 48))
    glow = glow.filter(ImageFilter.GaussianBlur(radius=55))
    master.alpha_composite(glow)

    # 4. Signature Waveform Bars (Matches Audingo studio identity)
    wave_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    bars = [
        (312, 130),  # outer left
        (412, 300),  # mid left
        (512, 460),  # center
        (612, 300),  # mid right
        (712, 130),  # outer right
    ]
    bar_width = 54
    radius = bar_width // 2

    for cx, h in bars:
        x0 = cx - radius
        y0 = 512 - h // 2

        # Vibrant Blue Studio Gradient (#40BCFF -> #0062E3)
        bar_tile = Image.new("RGBA", (bar_width, h), (0, 0, 0, 0))
        for by in range(h):
            bf = by / max(1, h - 1)
            br = int(64 * (1 - bf) + 0 * bf)
            bg = int(188 * (1 - bf) + 98 * bf)
            bb = int(255 * (1 - bf) + 227 * bf)
            line = Image.new("RGBA", (bar_width, 1), (br, bg, bb, 255))
            bar_tile.paste(line, (0, by))

        bar_mask = Image.new("L", (bar_width, h), 0)
        bm_draw = ImageDraw.Draw(bar_mask)
        bm_draw.rounded_rectangle(
            (0, 0, bar_width, h), radius=radius, fill=255
        )

        wave_img.paste(bar_tile, (x0, y0), bar_mask)

    master.alpha_composite(wave_img)

    # Save 512x512 PNG
    png_path = ASSETS_DIR / "audingo_logo.png"
    png_512 = master.resize((512, 512), Image.Resampling.LANCZOS)
    png_512.save(png_path)

    # Save Multi-resolution Windows ICO (256, 128, 64, 48, 32, 16)
    ico_path = ASSETS_DIR / "audingo_logo.ico"
    ico_sizes = [(256, 256), (128, 128), (64, 64), (48, 48), (32, 32), (16, 16)]
    ico_imgs = [master.resize(s, Image.Resampling.LANCZOS) for s in ico_sizes]
    ico_imgs[0].save(ico_path, format="ICO", sizes=ico_sizes)

    print(f"Generated {png_path} and {ico_path}")


if __name__ == "__main__":
    create_audingo_icon()

