#!/usr/bin/env python3
"""Generate the Faustian Fabricator entity sprites and icon.

The machine is drawn as an occult altar: an obsidian plinth with a brass-ringed
summoning circle and four candle-topped obelisks. While powered, control.lua
draws the "awake" animation on top: a hovering soul orb, a rotating rune ring
and a pulsing heptagram.

Outputs (all high resolution, used at scale 0.5 => 64 px per tile):
  graphics/entity/faustian-fabricator.png         static body (dormant altar)
  graphics/entity/faustian-fabricator-shadow.png  static shadow
  graphics/entity/faustian-fabricator-awake.png   animated orb (FRAMES frames)
  graphics/entity/faustian-fabricator-glow.png    animated emissive layer (FRAMES frames)
  graphics/icons/faustian-fabricator.png          64 px icon with mipmaps
  thumbnail.png                                   144 px mod portal thumbnail

Every frame shares the same canvas, so all layers use the same shift. Keep the
constants below in sync with data.lua.
"""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

REPO_ROOT = Path(__file__).resolve().parent

FRAMES = 32
LINE_LENGTH = 8
FRAME_W = 320
FRAME_H = 320
TILE = 64  # pixels per tile at hr resolution
SS = 4  # supersampling factor

# Entity center (center of the 3x3 footprint) inside the frame. The canvas is
# taller above the footprint to fit the obelisks, so the sprite center sits
# above the entity center: shift = (FRAME_CENTER - ENTITY_CENTER) / TILE.
CX = FRAME_W / 2
CY = FRAME_H / 2 + 32
SHIFT = ((FRAME_W / 2 - CX) / TILE, (FRAME_H / 2 - CY) / TILE)

# Palette
OBSIDIAN = (38, 30, 38)
OBSIDIAN_LIGHT = (70, 56, 68)
OBSIDIAN_DARK = (20, 15, 20)
BRASS = (170, 128, 62)
BRASS_DARK = (96, 66, 30)
BRASS_LIGHT = (232, 196, 120)
EMBER_DIM = (110, 18, 12)
EMBER = (255, 70, 30)
SOUL = (255, 60, 40)
FLAME = (255, 190, 90)


def s(v: float) -> float:
    return v * SS


def pts(points):
    return [(s(x), s(y)) for x, y in points]


def new_layer() -> Image.Image:
    return Image.new("RGBA", (FRAME_W * SS, FRAME_H * SS), (0, 0, 0, 0))


def octagon(cx, top, bottom, half_w, chamfer):
    return [
        (cx - half_w + chamfer, top),
        (cx + half_w - chamfer, top),
        (cx + half_w, top + chamfer * 0.8),
        (cx + half_w, bottom - chamfer * 0.8),
        (cx + half_w - chamfer, bottom),
        (cx - half_w + chamfer, bottom),
        (cx - half_w, bottom - chamfer * 0.8),
        (cx - half_w, top + chamfer * 0.8),
    ]


# Plinth geometry (frame pixels)
PLINTH_HALF_W = 88
PLINTH_TOP = CY - 86
PLINTH_BOTTOM = CY + 62
PLINTH_DEPTH = 24
CHAMFER = 30
TOP_FACE = octagon(CX, PLINTH_TOP, PLINTH_BOTTOM, PLINTH_HALF_W, CHAMFER)

CIRCLE_CX = CX
CIRCLE_CY = CY - 12
CIRCLE_RX = 68
CIRCLE_RY = 56

OBELISKS = [  # (x, base y, height)
    (CX - 70, CY - 66, 78),
    (CX + 70, CY - 66, 78),
    (CX - 70, CY + 42, 62),
    (CX + 70, CY + 42, 62),
]

RNG = np.random.default_rng(666)


def noise_texture(size, base, spread, blur):
    w, h = size
    n = RNG.normal(0, 1, (h // 8 + 1, w // 8 + 1))
    img = Image.fromarray(((n - n.min()) / (np.ptp(n) or 1) * 255).astype(np.uint8))
    img = img.resize((w, h), Image.BICUBIC).filter(ImageFilter.GaussianBlur(blur))
    grain = Image.fromarray(RNG.integers(0, 255, (h, w), dtype=np.uint8)).filter(ImageFilter.GaussianBlur(SS))
    a = np.asarray(img, dtype=np.float32) / 255 * 0.7 + np.asarray(grain, dtype=np.float32) / 255 * 0.3
    rgb = np.array(base, dtype=np.float32)[None, None, :] + (a[..., None] - 0.5) * spread
    return Image.fromarray(np.clip(rgb, 0, 255).astype(np.uint8), "RGB").convert("RGBA")


STONE = noise_texture((FRAME_W * SS, FRAME_H * SS), OBSIDIAN, 40, SS * 3)


def fill_textured(layer, polygon, texture, shade=1.0):
    mask = Image.new("L", layer.size, 0)
    ImageDraw.Draw(mask).polygon(pts(polygon), fill=255)
    tex = texture if shade == 1.0 else Image.eval(texture, lambda v: int(v * shade))
    tex = tex.copy()
    tex.putalpha(mask)
    layer.alpha_composite(tex)


def ellipse_box(cx, cy, rx, ry):
    return [s(cx - rx), s(cy - ry), s(cx + rx), s(cy + ry)]


def on_circle(angle, rx, ry, cx=CIRCLE_CX, cy=CIRCLE_CY):
    return cx + math.cos(angle) * rx, cy + math.sin(angle) * ry


# Rune glyphs: short stroke patterns in a unit box, repeated around the ring.
GLYPHS = [
    [((0, -1), (0, 1)), ((-0.6, -0.4), (0.6, 0.4))],
    [((-0.6, 1), (0, -1)), ((0, -1), (0.6, 1)), ((-0.3, 0.2), (0.3, 0.2))],
    [((0, -1), (0, 1)), ((0, -1), (0.6, -0.5)), ((0, 0), (-0.6, 0.5))],
    [((-0.5, -1), (0.5, 1)), ((0.5, -1), (-0.5, 1))],
    [((-0.5, -1), (-0.5, 1)), ((-0.5, 0), (0.5, -0.8)), ((-0.5, 0), (0.5, 0.8))],
    [((0, -1), (0, 1)), ((-0.6, -1), (0.6, -1)), ((-0.6, 1), (0.6, 1))],
]
RUNE_SECTORS = 8  # pattern repeats per sector, so rotating one sector per loop is seamless
RUNES_PER_SECTOR = 3
RUNE_PATTERN = (0, 3, 4)  # indices into GLYPHS, one per rune in a sector


def draw_runes(draw, phase, color, width):
    count = RUNE_SECTORS * RUNES_PER_SECTOR
    rx, ry = CIRCLE_RX - 12, CIRCLE_RY - 10
    for i in range(count):
        angle = (i / count) * 2 * math.pi + phase
        gx, gy = on_circle(angle, rx, ry)
        glyph = GLYPHS[RUNE_PATTERN[i % RUNES_PER_SECTOR]]
        # Glyphs stand "upright" pointing outward from the center
        rot = angle + math.pi / 2
        size = 4.2
        for (x0, y0), (x1, y1) in glyph:
            a = (gx + (x0 * math.cos(rot) - y0 * math.sin(rot)) * size,
                 gy + (x0 * math.sin(rot) + y0 * math.cos(rot)) * size * (CIRCLE_RY / CIRCLE_RX))
            b = (gx + (x1 * math.cos(rot) - y1 * math.sin(rot)) * size,
                 gy + (x1 * math.sin(rot) + y1 * math.cos(rot)) * size * (CIRCLE_RY / CIRCLE_RX))
            draw.line(pts([a, b]), fill=color, width=int(s(width)))


def draw_heptagram(draw, phase, color, width):
    rx, ry = CIRCLE_RX - 26, CIRCLE_RY - 22
    star = [on_circle(phase + i * 3 * 2 * math.pi / 7 - math.pi / 2, rx, ry) for i in range(8)]
    draw.line(pts(star), fill=color, width=int(s(width)), joint="curve")
    draw.ellipse(ellipse_box(CIRCLE_CX, CIRCLE_CY, rx, ry), outline=color, width=int(s(width * 0.8)))


def draw_obelisk(layer, x, base_y, height, flicker):
    d = ImageDraw.Draw(layer)
    w_base, w_top = 11, 6
    top_y = base_y - height
    left = [(x - w_base, base_y), (x, base_y + 4), (x, top_y + 6), (x - w_top, top_y + 4)]
    right = [(x, base_y + 4), (x + w_base, base_y), (x + w_top, top_y + 4), (x, top_y + 6)]
    cap = [(x - w_top, top_y + 4), (x, top_y - 2), (x + w_top, top_y + 4), (x, top_y + 6)]
    fill_textured(layer, left, STONE, 1.25)
    fill_textured(layer, right, STONE, 0.7)
    fill_textured(layer, cap, STONE, 1.6)
    # Brass bands
    for t in (0.18, 0.62):
        y = base_y - height * t
        hw = w_base - (w_base - w_top) * t
        d.polygon(pts([(x - hw - 1, y), (x, y + 4), (x + hw + 1, y), (x + hw + 1, y - 3), (x, y + 1), (x - hw - 1, y - 3)]),
                  fill=BRASS)
        d.line(pts([(x - hw - 1, y - 3), (x, y + 1)]), fill=BRASS_LIGHT, width=int(s(0.8)))
    # Candle
    cy = top_y - 2
    d.rectangle([s(x - 2.2), s(cy - 7), s(x + 2.2), s(cy)], fill=(214, 200, 176))
    d.ellipse(ellipse_box(x, cy, 2.2, 1.2), fill=(184, 168, 140))
    flame_h = 7 + flicker * 2.5
    lean = (flicker - 0.5) * 1.6
    d.polygon(pts([(x - 2, cy - 7), (x + lean, cy - 7 - flame_h), (x + 2, cy - 7)]), fill=(255, 150, 60))
    d.ellipse(ellipse_box(x, cy - 8, 1.6, 2.2), fill=FLAME)


def draw_body() -> Image.Image:
    layer = new_layer()
    d = ImageDraw.Draw(layer)

    back = [o for o in OBELISKS if o[1] < CY]
    front = [o for o in OBELISKS if o[1] >= CY]

    # Front faces of the plinth (extruded lower edges)
    bottom_edges = TOP_FACE[3:8]
    shades = [0.5, 0.75, 0.9, 0.75, 0.5]
    for (p0, p1), shade in zip(zip(bottom_edges, bottom_edges[1:]), shades):
        face = [p0, p1, (p1[0], p1[1] + PLINTH_DEPTH), (p0[0], p0[1] + PLINTH_DEPTH)]
        fill_textured(layer, face, STONE, shade)
    # Brass trim along the base and at the top edge of the front faces
    for (p0, p1) in zip(bottom_edges, bottom_edges[1:]):
        d.line(pts([(p0[0], p0[1] + PLINTH_DEPTH - 2), (p1[0], p1[1] + PLINTH_DEPTH - 2)]), fill=BRASS_DARK, width=int(s(3)))
        d.line(pts([p0, p1]), fill=OBSIDIAN_LIGHT, width=int(s(2)))
    # Glowing cracks in the front faces
    for x0, x1 in ((CX - 44, CX - 30), (CX + 18, CX + 36)):
        y = PLINTH_BOTTOM + 6
        d.line(pts([(x0, y), ((x0 + x1) / 2, y + 7), (x1, y + 4), (x1 + 3, y + 14)]), fill=EMBER_DIM, width=int(s(1.6)))

    for o in back:
        draw_obelisk(layer, *o, flicker=0.5)

    # Top face
    fill_textured(layer, TOP_FACE, STONE, 1.0)
    d.line(pts(TOP_FACE + [TOP_FACE[0]]), fill=OBSIDIAN_LIGHT, width=int(s(2)))

    # Summoning circle: sunken dark floor, brass rings, rune band
    d.ellipse(ellipse_box(CIRCLE_CX, CIRCLE_CY + 2, CIRCLE_RX + 3, CIRCLE_RY + 3), fill=OBSIDIAN_DARK)
    d.ellipse(ellipse_box(CIRCLE_CX, CIRCLE_CY, CIRCLE_RX, CIRCLE_RY), fill=(28, 16, 20),
              outline=BRASS, width=int(s(3)))
    d.ellipse(ellipse_box(CIRCLE_CX, CIRCLE_CY - 1, CIRCLE_RX - 1, CIRCLE_RY - 1), outline=BRASS_LIGHT, width=int(s(0.8)))
    d.ellipse(ellipse_box(CIRCLE_CX, CIRCLE_CY, CIRCLE_RX - 20, CIRCLE_RY - 17), outline=BRASS_DARK, width=int(s(2)))
    # Dormant engravings: an empty rune band and the heptagram groove
    for inset in (6, 18):
        d.ellipse(ellipse_box(CIRCLE_CX, CIRCLE_CY, CIRCLE_RX - inset, CIRCLE_RY - inset * 0.85), outline=EMBER_DIM, width=int(s(1)))
    draw_heptagram(d, 0, EMBER_DIM, 1.6)

    # Brass studs where the obelisk sockets meet the circle
    for a in range(4):
        sx, sy = on_circle(math.pi / 4 + a * math.pi / 2, CIRCLE_RX, CIRCLE_RY)
        d.ellipse(ellipse_box(sx, sy, 3.5, 3), fill=BRASS, outline=BRASS_DARK, width=int(s(0.8)))

    # Empty brass cradle where the soul orb manifests
    d.ellipse(ellipse_box(CIRCLE_CX, CIRCLE_CY, 9, 6), fill=OBSIDIAN_DARK, outline=BRASS, width=int(s(1.6)))

    for o in front:
        draw_obelisk(layer, *o, flicker=0.5)

    return layer.resize((FRAME_W, FRAME_H), Image.LANCZOS)


def orb_y(t: float) -> float:
    return CIRCLE_CY - 26 + math.sin(2 * math.pi * t) * 3


def draw_awake(frame: int) -> Image.Image:
    """Solid parts drawn while powered: the hovering orb and its shadow on the floor."""
    t = frame / FRAMES
    y = orb_y(t)
    bob = y - (CIRCLE_CY - 26)
    layer = new_layer()
    d = ImageDraw.Draw(layer)
    d.ellipse(ellipse_box(CIRCLE_CX, CIRCLE_CY + 2, 13 - bob * 0.5, 6), fill=(10, 4, 6, 170))
    d.ellipse(ellipse_box(CIRCLE_CX, y, 13, 13), fill=(120, 14, 16))
    d.ellipse(ellipse_box(CIRCLE_CX - 2, y - 2, 9, 9), fill=(180, 30, 26))
    d.ellipse(ellipse_box(CIRCLE_CX - 5, y - 6, 3.5, 2.5), fill=(255, 210, 190))
    return layer.resize((FRAME_W, FRAME_H), Image.LANCZOS)


def draw_glow(frame: int) -> Image.Image:
    """Emissive parts only, drawn additively over the body with draw_as_glow."""
    t = frame / FRAMES
    pulse = 0.65 + 0.35 * math.sin(2 * math.pi * t)
    core = new_layer()
    d = ImageDraw.Draw(core)

    rune_color = tuple(int(c * (0.75 + 0.25 * pulse)) for c in EMBER) + (255,)
    draw_runes(d, t * 2 * math.pi / RUNE_SECTORS, rune_color, 1.4)
    draw_heptagram(d, 0, tuple(int(c * pulse) for c in EMBER) + (255,), 1.2)
    for x0, x1 in ((CX - 44, CX - 30), (CX + 18, CX + 36)):
        y = PLINTH_BOTTOM + 6
        d.line(pts([(x0, y), ((x0 + x1) / 2, y + 7), (x1, y + 4), (x1 + 3, y + 14)]), fill=EMBER, width=int(s(1.2)))

    y = orb_y(t)
    d.ellipse(ellipse_box(CIRCLE_CX - 1, y - 1, 10, 10), fill=SOUL)
    d.ellipse(ellipse_box(CIRCLE_CX - 2, y - 2, 5, 5), fill=(255, 200, 150))

    for i, (x, base_y, height) in enumerate(OBELISKS):
        flicker = 0.5 + 0.5 * math.sin(2 * math.pi * (t * 3 + x / 50 + (0.37 if base_y >= CY else 0)))
        d.ellipse(ellipse_box(x, base_y - height - 10, 2.2, 3.2 + flicker), fill=FLAME)

    halo = new_layer()
    hd = ImageDraw.Draw(halo)
    hd.ellipse(ellipse_box(CIRCLE_CX, y, 26 * pulse + 6, 26 * pulse + 6), fill=(200, 30, 20, int(150 * pulse)))
    hd.ellipse(ellipse_box(CIRCLE_CX, CIRCLE_CY, CIRCLE_RX - 6, CIRCLE_RY - 5), fill=(120, 10, 8, int(60 * pulse)))
    for x, base_y, height in OBELISKS:
        hd.ellipse(ellipse_box(x, base_y - height - 10, 9, 9), fill=(255, 140, 50, 110))
    halo = halo.filter(ImageFilter.GaussianBlur(s(6)))
    halo.alpha_composite(core.filter(ImageFilter.GaussianBlur(s(1.5))))
    halo.alpha_composite(core)
    return halo.resize((FRAME_W, FRAME_H), Image.LANCZOS)


def draw_shadow() -> Image.Image:
    layer = new_layer()
    d = ImageDraw.Draw(layer)
    # Plinth shadow cast to the east
    face = [(x + 14, y + PLINTH_DEPTH + 2) for x, y in TOP_FACE]
    d.polygon(pts(face), fill=(0, 0, 0, 255))
    for x, base_y, height in OBELISKS:
        d.polygon(pts([(x - 8, base_y + 2), (x + 8, base_y + 4),
                       (x + height * 0.95 + 4, base_y + height * 0.18 + 2), (x + height * 0.95, base_y + height * 0.18 - 4)]),
                  fill=(0, 0, 0, 255))
    layer = layer.filter(ImageFilter.GaussianBlur(s(2)))
    return layer.resize((FRAME_W, FRAME_H), Image.LANCZOS)


def sheet(frames: list[Image.Image]) -> Image.Image:
    rows = math.ceil(len(frames) / LINE_LENGTH)
    out = Image.new("RGBA", (FRAME_W * LINE_LENGTH, FRAME_H * rows), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        out.paste(f, ((i % LINE_LENGTH) * FRAME_W, (i // LINE_LENGTH) * FRAME_H))
    return out


def make_icon(body: Image.Image, awake: Image.Image, glow: Image.Image) -> Image.Image:
    body = body.copy()
    body.alpha_composite(awake)
    rgb = ImageChops.add(body.convert("RGB"), glow.convert("RGB"))
    alpha = ImageChops.lighter(body.getchannel("A"), glow.getchannel("A"))
    rgb.putalpha(alpha)
    bbox = alpha.point(lambda a: 255 if a > 24 else 0).getbbox()
    x0, y0, x1, y1 = bbox
    side = max(x1 - x0, y1 - y0)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    crop = rgb.crop((int(cx - side / 2), int(cy - side / 2), int(cx + side / 2), int(cy + side / 2)))
    sizes = [64, 32, 16, 8]
    out = Image.new("RGBA", (sum(sizes), 64), (0, 0, 0, 0))
    x = 0
    for size in sizes:
        out.paste(crop.resize((size, size), Image.LANCZOS), (x, 0))
        x += size
    return out


def make_thumbnail(body: Image.Image, shadow: Image.Image, awake: Image.Image, glow: Image.Image) -> Image.Image:
    size = 144
    bg = Image.new("RGBA", (FRAME_W, FRAME_H), (24, 16, 20, 255))
    vignette = Image.new("RGBA", (FRAME_W, FRAME_H), (0, 0, 0, 0))
    ImageDraw.Draw(vignette).ellipse([20, 40, FRAME_W - 20, FRAME_H], fill=(120, 20, 16, 140))
    bg.alpha_composite(vignette.filter(ImageFilter.GaussianBlur(40)))
    shade = Image.new("RGBA", shadow.size, (0, 0, 0, 0))
    shade.putalpha(shadow.getchannel("A").point(lambda a: a // 2))
    bg.alpha_composite(shade)
    bg.alpha_composite(body)
    bg.alpha_composite(awake)
    rgb = ImageChops.add(bg.convert("RGB"), Image.composite(glow.convert("RGB"), Image.new("RGB", glow.size), glow.getchannel("A")))
    return rgb.resize((size, size), Image.LANCZOS)


def main() -> None:
    entity_dir = REPO_ROOT / "graphics" / "entity"
    icon_dir = REPO_ROOT / "graphics" / "icons"
    body = draw_body()
    awakes = [draw_awake(i) for i in range(FRAMES)]
    glows = [draw_glow(i) for i in range(FRAMES)]
    body.save(entity_dir / "faustian-fabricator.png", optimize=True)
    sheet(awakes).save(entity_dir / "faustian-fabricator-awake.png", optimize=True)
    sheet(glows).save(entity_dir / "faustian-fabricator-glow.png", optimize=True)
    shadow = draw_shadow()
    shadow.save(entity_dir / "faustian-fabricator-shadow.png", optimize=True)
    make_thumbnail(body, shadow, awakes[0], glows[0]).save(REPO_ROOT / "thumbnail.png", optimize=True)
    make_icon(body, awakes[0], glows[0]).save(icon_dir / "faustian-fabricator.png", optimize=True)
    print(f"frame {FRAME_W}x{FRAME_H}, {FRAMES} frames, line_length {LINE_LENGTH}, shift {SHIFT}")


if __name__ == "__main__":
    main()
