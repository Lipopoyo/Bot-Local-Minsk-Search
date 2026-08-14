from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

BASE = Path(__file__).resolve().parent.parent
FONT_DIR = BASE / "assets" / "fonts"

BLUE = "#159BFF"
BLUE2 = "#55C7FF"
WHITE = "#F5FAFF"
MUTED = "#8FA9C4"
BG = "#050C17"
PANEL = "#071426"

def load_font(size: int, bold: bool = False):
    names = (
        ["DejaVuSans-Bold.ttf", "Arial-Bold.ttf"]
        if bold else
        ["DejaVuSans.ttf", "Arial.ttf"]
    )
    paths = [FONT_DIR / n for n in names] + [
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else
             "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ]
    for p in paths:
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()

def glow_line(layer, xy, fill=BLUE, width=3, glow=12):
    glow_layer = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow_layer)
    gd.line(xy, fill=fill, width=width)
    glow_layer = glow_layer.filter(ImageFilter.GaussianBlur(glow))
    layer.alpha_composite(glow_layer)
    ImageDraw.Draw(layer).line(xy, fill=fill, width=width)

def draw_pin(layer, cx, cy):
    # Neon LM pin
    glow = Image.new("RGBA", layer.size, (0, 0, 0, 0))
    gd = ImageDraw.Draw(glow)
    gd.ellipse((cx-55, cy-55, cx+55, cy+55), outline=(21,155,255,210), width=7)
    gd.ellipse((cx-18, cy-18, cx+18, cy+18), fill=(21,155,255,240))
    glow = glow.filter(ImageFilter.GaussianBlur(18))
    layer.alpha_composite(glow)

    d = ImageDraw.Draw(layer)
    d.ellipse((cx-44, cy-44, cx+44, cy+44), fill="#06111F", outline=BLUE2, width=4)
    d.polygon([(cx-28, cy+32), (cx, cy+78), (cx+28, cy+32)], fill="#06111F", outline=BLUE2)
    d.text((cx, cy-8), "LM", anchor="mm", font=load_font(30, True), fill=WHITE)
    d.ellipse((cx-9, cy+68, cx+9, cy+86), fill=BLUE)

def make_card(map_path: str, place_name: str, lat: float, lon: float, output: str) -> str:
    W, H = 1080, 1350
    canvas = Image.new("RGBA", (W, H), BG)
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))

    # Map panel
    m = Image.open(map_path).convert("RGB")
    m = m.resize((1000, 690), Image.Resampling.LANCZOS)
    canvas.paste(m, (40, 205))

    # Dark-blue tint over the map
    tint = Image.new("RGBA", (W, H), (0, 20, 50, 35))
    canvas = Image.alpha_composite(canvas, tint)

    d = ImageDraw.Draw(layer)

    # Outer frame
    d.rounded_rectangle((22, 22, W-22, H-22), radius=18, outline=BLUE, width=3)
    d.line((42, 180, W-42, 180), fill=BLUE, width=2)
    d.line((42, 930, W-42, 930), fill=BLUE, width=2)

    # Header branding
    d.text((58, 48), "LOCAL", font=load_font(34, True), fill=WHITE)
    d.text((58, 86), "MINSK", font=load_font(46, True), fill=BLUE)
    d.text((58, 142), "SEARCH", font=load_font(26, True), fill=WHITE)
    d.text((760, 72), "MINSK / BELARUS", font=load_font(18, True), fill=MUTED)

    # Marker at the center of the map panel
    draw_pin(layer, W//2, 540)

    # Bottom panel
    d.rounded_rectangle((40, 960, W-40, 1290), radius=18, fill=PANEL, outline=BLUE, width=2)

    d.rounded_rectangle((65, 985, 335, 1028), radius=10, outline=BLUE, width=2)
    d.ellipse((82, 1000, 94, 1012), fill=BLUE)
    d.text((110, 991), "LOCATION FOUND", font=load_font(17, True), fill=BLUE)

    # Place name with adaptive font
    name_size = 40 if len(place_name) <= 18 else 26 if len(place_name) <= 26 else 18
    d.text((65, 1055), place_name, font=load_font(name_size, True), fill=WHITE)

    d.text((68, 1125), f"{lat:.5f}° N   {lon:.5f}° E", font=load_font(20, True), fill=MUTED)

    now = datetime.now()
    d.text((650, 1010), "DATE", font=load_font(17, True), fill=BLUE)
    d.text((650, 1040), now.strftime("%d.%m.%Y"), font=load_font(29, True), fill=WHITE)
    d.text((650, 1100), "TIME", font=load_font(17, True), fill=BLUE)
    d.text((650, 1130), now.strftime("%H:%M"), font=load_font(29, True), fill=WHITE)

    d.line((65, 1180, 1015, 1180), fill="#12324F", width=2)
    d.text((65, 1210), "FIND PLACES. EXPLORE MINSK.", font=load_font(17, True), fill=MUTED)
    d.text((750, 1210), "LOCAL MINSK SEARCH", font=load_font(17, True), fill=BLUE)

    # Corner tech brackets
    for x, y, sx, sy in [(40, 205, 1, 1), (1040, 205, -1, 1), (40, 895, 1, -1), (1040, 895, -1, -1)]:
        d.line((x, y, x+sx*45, y), fill=BLUE, width=4)
        d.line((x, y, x, y+sy*45), fill=BLUE, width=4)

    canvas = Image.alpha_composite(canvas, layer)
    canvas.convert("RGB").save(output, "JPEG", quality=94, optimize=True)
    return output
