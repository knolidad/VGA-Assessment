"""Render the 20s muted Instagram Reel for Fairway Vibes (1080x1920, 30fps).

Uses the official artwork in assets/. Text sits in the top band, clear of the
Reels UI (bottom ~20% and right edge), so every point reads with sound off.
"""
import subprocess, sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageEnhance

W, H, FPS, DUR = 1080, 1920, 30, 20
HERE = Path(__file__).parent
OUT = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "fairway-vibes-launch.mp4")
FONT = "/usr/share/fonts/opentype/inter/"
def font(name, size): return ImageFont.truetype(FONT + name, size)
BOLD, SEMI = "InterDisplay-Bold.otf", "Inter-SemiBold.otf"

WHITE, MINT, PURPLE, GOLD = (255, 255, 255), (94, 242, 176), (176, 120, 255), (244, 196, 98)

album = Image.open(HERE / "assets/fairway-vibes-cover.png").convert("RGB")
single = Image.open(HERE / "assets/hold-it-down-cover.png").convert("RGB")
poster = Image.open(HERE / "assets/hold-it-down-poster.png").convert("RGB")
logos = poster.crop((100, 1052, 1160, 1128))

ART, ART_Y = 960, 600  # square art frame size and top edge
TEXT_CY = 380          # vertical centre of the caption band

# Each scene: time span, source image, Ken Burns crop boxes (start -> end, in
# source px), caption lines (text, font, size, colour).
SCENES = [
    dict(t=(0.0, 3.4), img=album, crop=((0, 0, 1254, 1254), (60, 40, 1194, 1174)),
         lines=[("NEW ALBUM", BOLD, 128, WHITE), ("OUT NOW", BOLD, 128, MINT)]),
    dict(t=(3.4, 6.8), img=poster, crop=((40, 40, 1214, 1214), (0, 0, 1254, 1254)),
         lines=[("Featuring the hit single", SEMI, 62, WHITE), ("HOLD IT DOWN", BOLD, 124, GOLD)]),
    dict(t=(6.8, 10.2), img=single, crop=((150, 420, 950, 1220), (230, 470, 930, 1170)),
         lines=[("A song about", SEMI, 62, WHITE), ("working hard", BOLD, 124, GOLD)]),
    dict(t=(10.2, 13.6), img=single, crop=((654, 560, 1254, 1160), (734, 620, 1214, 1100)),
         lines=[("and making sure", BOLD, 100, WHITE), ("others are there", BOLD, 100, GOLD)]),
    dict(t=(13.6, 16.8), img=single, crop=((0, 0, 1254, 1254), (30, 30, 1224, 1224)),
         lines=[("Holding it down", BOLD, 108, GOLD), ("for you and for them.", BOLD, 84, WHITE)]),
    dict(t=(16.8, 20.0), img=album, crop=((60, 40, 1194, 1174), (0, 0, 1254, 1254)),
         lines=[("STREAM", BOLD, 112, WHITE), ("FAIRWAY VIBES NOW", BOLD, 96, MINT)], cta=True),
]
XFADE = 0.35

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3
def lerp(a, b, p): return tuple(x + (y - x) * p for x, y in zip(a, b))

# Pre-blurred, darkened backdrops so the vertical frame is filled with the art itself.
def backdrop(img):
    bg = img.resize((H, H)).crop(((H - W) // 2, 0, (H - W) // 2 + W, H))
    bg = bg.filter(ImageFilter.GaussianBlur(40))
    return ImageEnhance.Brightness(bg).enhance(0.38)
BACKDROPS = {id(i): backdrop(i) for i in (album, single, poster)}

art_mask = Image.new("L", (ART, ART), 0)
ImageDraw.Draw(art_mask).rounded_rectangle([0, 0, ART - 1, ART - 1], 36, fill=255)

def scene_layer(sc, t):
    s, e = sc["t"]
    p = min(1.0, (t - s) / (e - s))
    im = BACKDROPS[id(sc["img"])].copy()
    box = lerp(*sc["crop"], p)
    art = sc["img"].resize((ART, ART), Image.LANCZOS, box=box)
    if sc.get("cta"):  # streaming logos from the official poster
        lw = ART - 80
        lg = logos.resize((lw, int(logos.height * lw / logos.width)), Image.LANCZOS)
        shade = Image.new("L", (ART, ART), 0)
        sd = ImageDraw.Draw(shade)
        for y in range(ART - 260, ART):
            sd.line([(0, y), (ART, y)], fill=int(230 * (y - ART + 260) / 260))
        art = Image.composite(Image.new("RGB", art.size, (0, 0, 0)), art, shade)
        la = ease((t - s - 0.6) / 0.5)
        if la > 0:
            spot = art.crop((40, ART - 150, 40 + lw, ART - 150 + lg.height))
            art.paste(Image.blend(spot, lg, la), (40, ART - 150))
    im.paste(art, ((W - ART) // 2, ART_Y), art_mask)

    dr = ImageDraw.Draw(im)
    fonts = [(txt, font(fn, sz), col) for txt, fn, sz, col in sc["lines"]]
    hs = [fo.getbbox(txt)[3] - fo.getbbox(txt)[1] for txt, fo, _ in fonts]
    gap = 30
    y = TEXT_CY - (sum(hs) + gap * (len(hs) - 1)) // 2
    for i, ((txt, fo, col), h) in enumerate(zip(fonts, hs)):
        a = ease((t - s - 0.1 - i * 0.15) / 0.4)
        bb = fo.getbbox(txt)
        x = (W - (bb[2] - bb[0])) // 2 - bb[0]
        yy = y - bb[1] + int(36 * (1 - a))
        layer = Image.new("RGBA", im.size, (0, 0, 0, 0))
        ImageDraw.Draw(layer).text((x, yy), txt, font=fo, fill=col + (int(255 * a),))
        im.paste(layer, (0, 0), layer)
        y += h + gap
    return im

def frame(n):
    t = n / FPS
    for i, sc in enumerate(SCENES):
        s, e = sc["t"]
        if s <= t < e:
            im = scene_layer(sc, t)
            if i > 0 and t - s < XFADE:  # crossfade in from the previous scene
                prev = scene_layer(SCENES[i - 1], t)
                im = Image.blend(prev, im, ease((t - s) / XFADE))
            break
    dr = ImageDraw.Draw(im)
    dr.rectangle([0, 0, int(W * (t + 1 / FPS) / DUR), 8], fill=GOLD)  # progress line
    return im

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-crf", "18", "-preset", "medium", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for n in range(FPS * DUR):
    ff.stdin.write(frame(n).tobytes())
ff.stdin.close(); ff.wait()
print("wrote", OUT)
