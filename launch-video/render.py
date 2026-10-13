"""Render the 20s muted Instagram Reel for Fairway Vibes (1080x1920, 30fps)."""
import math, subprocess, sys
from PIL import Image, ImageDraw, ImageFont

W, H, FPS, DUR = 1080, 1920, 30, 20
OUT = sys.argv[1] if len(sys.argv) > 1 else "fairway-vibes-launch.mp4"
FONT = "/usr/share/fonts/opentype/inter/"
def f(name, size): return ImageFont.truetype(FONT + name, size)

BG_TOP, BG_BOT = (12, 46, 30), (4, 20, 12)
GREEN, CREAM, GOLD = (126, 214, 120), (246, 241, 226), (238, 196, 92)

# (start, end, [(text, font, size, color)], accent_bar)
SCENES = [
    (0.0, 3.2,  [("NEW ALBUM", "InterDisplay-Bold.otf", 120, GOLD),
                 ("OUT NOW", "InterDisplay-Bold.otf", 120, GOLD),
                 ("from Fairway Frequency", "Inter-SemiBold.otf", 64, CREAM)]),
    (3.2, 6.8,  [("Fairway Frequency", "Inter-SemiBold.otf", 64, CREAM),
                 ("presents", "Inter-Medium.otf", 54, GREEN),
                 ("FAIRWAY", "InterDisplay-Bold.otf", 180, CREAM),
                 ("VIBES", "InterDisplay-Bold.otf", 180, GOLD)]),
    (6.8, 10.4, [("Featuring the hit", "Inter-SemiBold.otf", 66, CREAM),
                 ("HOLD IT", "InterDisplay-Bold.otf", 170, GOLD),
                 ("DOWN", "InterDisplay-Bold.otf", 170, GOLD)]),
    (10.4, 13.8,[("A song about", "Inter-SemiBold.otf", 66, CREAM),
                 ("working hard", "InterDisplay-Bold.otf", 120, GREEN),
                 ("and showing up", "InterDisplay-Bold.otf", 104, CREAM),
                 ("for others", "InterDisplay-Bold.otf", 104, CREAM)]),
    (13.8, 16.8,[("Holding it down", "InterDisplay-Bold.otf", 110, GOLD),
                 ("for you", "InterDisplay-Bold.otf", 110, CREAM),
                 ("and for them.", "InterDisplay-Bold.otf", 110, CREAM)]),
    (16.8, 20.0,[("STREAM", "InterDisplay-Bold.otf", 150, CREAM),
                 ("FAIRWAY VIBES", "InterDisplay-Bold.otf", 128, GOLD),
                 ("NOW", "InterDisplay-Bold.otf", 150, CREAM),
                 ("Fairway Frequency", "Inter-SemiBold.otf", 60, GREEN)]),
]

def ease(x): x = max(0.0, min(1.0, x)); return 1 - (1 - x) ** 3

bg = Image.new("RGB", (W, H))
d = ImageDraw.Draw(bg)
for y in range(H):
    t = y / H
    d.line([(0, y), (W, y)], fill=tuple(int(a + (b - a) * t) for a, b in zip(BG_TOP, BG_BOT)))
# subtle fairway stripes
stripe = Image.new("RGB", (W, H)); sd = ImageDraw.Draw(stripe)
for i in range(-4, 14):
    x = i * 160
    sd.polygon([(x, H), (x + 80, H), (x + 80 + 900, 0), (x + 900, 0)], fill=(255, 255, 255))
bg = Image.blend(bg, Image.composite(stripe, bg, stripe.convert("L")), 0.025)

def wave(draw, t, alpha):
    """Animated 'frequency' equalizer bars near the bottom of the safe zone."""
    n, bw, gap = 27, 22, 14
    x0 = (W - (n * bw + (n - 1) * gap)) // 2
    base = 1440
    for i in range(n):
        h = 30 + 110 * abs(math.sin(t * 3.1 + i * 0.55)) * (0.55 + 0.45 * math.sin(i * 0.37 + t))
        c = tuple(int(v * alpha + bg_v * (1 - alpha)) for v, bg_v in zip(GREEN, BG_BOT))
        draw.rounded_rectangle([x0 + i * (bw + gap), base - h, x0 + i * (bw + gap) + bw, base], 8, fill=c)

def frame(n):
    t = n / FPS
    im = bg.copy(); dr = ImageDraw.Draw(im)
    wave(dr, t, 0.55)
    for s, e, lines in SCENES:
        if not (s <= t < e): continue
        last = e == DUR
        fade_out = 1.0 if last else ease((e - t) / 0.25)
        fonts = [(txt, f(fn, sz), col) for txt, fn, sz, col in lines]
        heights = [fo.getbbox(txt)[3] - fo.getbbox(txt)[1] for txt, fo, _ in fonts]
        gap = 34
        y = 880 - (sum(heights) + gap * (len(fonts) - 1)) // 2
        for i, ((txt, fo, col), h) in enumerate(zip(fonts, heights)):
            p = ease((t - s - i * 0.12) / 0.4) * fade_out  # staggered rise-in
            col = tuple(int(c * p + b * (1 - p)) for c, b in zip(col, BG_TOP))
            bb = fo.getbbox(txt)
            x = (W - (bb[2] - bb[0])) // 2 - bb[0]
            dr.text((x, y - bb[1] + int(40 * (1 - p))), txt, font=fo, fill=col)
            y += h + gap
        if last:  # CTA underline pulse
            w = int(520 * ease((t - s - 0.5) / 0.5))
            dr.rounded_rectangle([(W - w) // 2, y + 10, (W + w) // 2, y + 22], 6, fill=GOLD)
    # progress line at top of safe zone
    dr.rectangle([0, 0, int(W * t / DUR), 8], fill=GOLD)
    return im

ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
    "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-c:v", "libx264", "-pix_fmt", "yuv420p",
    "-crf", "18", "-preset", "medium", "-movflags", "+faststart", OUT], stdin=subprocess.PIPE)
for n in range(FPS * DUR):
    ff.stdin.write(frame(n).tobytes())
ff.stdin.close(); ff.wait()
print("wrote", OUT)
