# -*- coding: utf-8 -*-
"""
Gera toda a arte do bichinho-planta (PetPlanta) de forma 100% procedural com
Pillow: nenhuma imagem externa e necessaria. Para cada estado (mood) gera um
GIF em loop infinito, e para cada par de estados gera os frames PNG da
transicao (usados pelo app.js pra trocar de estado em lockstep com o fundo).

Rode este script sempre que quiser regenerar/ajustar a arte:
    python generate_assets.py

Saida: webapp/static/gifs/loop_<mood>.gif
       webapp/static/gifs/transition_<de>_to_<para>.gif      (combinado, so preview)
       webapp/static/gifs/transition_<de>_to_<para>/frame_N.png  (usado pelo app)
       webapp/static/preview.png  (grade com 1 frame de cada mood, so para conferir)
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

import config

OUT_DIR = os.path.join(os.path.dirname(__file__), "static", "gifs")
os.makedirs(OUT_DIR, exist_ok=True)

CANVAS = 220
N_FRAMES = 18
FRAME_MS = 90

BG = {
    "feliz": (224, 247, 217),
    "seca": (250, 240, 205),
    "doente": (238, 230, 214),
    "frio": (213, 238, 250),
    "dormindo": (28, 36, 64),
    "oculos": (255, 244, 188),
    "festa": (255, 198, 224),
}

# cor das folhas (mais saturada/escura) e do "miolo"/cabeca (mais clara), por mood
LEAF_COLOR = {
    "feliz": (66, 162, 73),
    "seca": (168, 173, 84),
    "doente": (138, 132, 70),
    "frio": (84, 156, 150),
    "dormindo": (56, 110, 78),
    "oculos": (76, 178, 70),
    "festa": (66, 162, 73),
}

HEAD_COLOR = {
    "feliz": (118, 200, 100),
    "seca": (198, 198, 120),
    "doente": (172, 168, 110),
    "frio": (140, 198, 188),
    "dormindo": (96, 150, 110),
    "oculos": (134, 212, 96),
    "festa": (118, 200, 100),
}

POT = (150, 95, 60)
POT_DARK = (120, 72, 44)
SOIL = (90, 58, 38)
STEM = (92, 138, 64)

CONFETTI_COLORS = [
    (255, 99, 132), (255, 205, 86), (75, 192, 192),
    (153, 102, 255), (255, 159, 64), (90, 200, 130),
]

try:
    FONT_SM = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
except Exception:
    FONT_SM = ImageFont.load_default()


def lerp_color(c1, c2, t):
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def rotate_point(x, y, deg):
    a = math.radians(deg)
    return (x * math.cos(a) - y * math.sin(a), x * math.sin(a) + y * math.cos(a))


def leaf_local_points(length, width):
    return [
        (0, 6),
        (-width, -length * 0.32),
        (-width * 0.42, -length * 0.82),
        (0, -length),
        (width * 0.42, -length * 0.82),
        (width, -length * 0.32),
    ]


def draw_leaf(draw, base, angle_deg, length, width, color, vein_color):
    pts = []
    for (x, y) in leaf_local_points(length, width):
        rx, ry = rotate_point(x, y, angle_deg)
        pts.append((base[0] + rx, base[1] + ry))
    draw.polygon(pts, fill=color)
    tx, ty = rotate_point(0, -length * 0.86, angle_deg)
    draw.line([base, (base[0] + tx, base[1] + ty)], fill=vein_color, width=2)
    tip = (base[0] + (rotate_point(0, -length, angle_deg)[0]),
           base[1] + (rotate_point(0, -length, angle_deg)[1]))
    return tip


def draw_pot(draw, cx, top_y):
    w_top, w_bot, h = 80, 58, 46
    top_left = (cx - w_top / 2, top_y)
    top_right = (cx + w_top / 2, top_y)
    bot_left = (cx - w_bot / 2, top_y + h)
    bot_right = (cx + w_bot / 2, top_y + h)
    draw.polygon([top_left, top_right, bot_right, bot_left], fill=POT)
    draw.rectangle([cx - w_top / 2 - 4, top_y - 8, cx + w_top / 2 + 4, top_y + 6], fill=POT_DARK)
    draw.ellipse([cx - w_top / 2 + 6, top_y - 4, cx + w_top / 2 - 6, top_y + 10], fill=SOIL)


def draw_bush(draw, center, mood, n, spread, droop, length, width, jitter, sway,
              brown_tips=0, spots=0):
    leaf_color = LEAF_COLOR[mood]
    vein_color = lerp_color(leaf_color, (30, 60, 20), 0.5)
    start = -spread / 2 + droop + sway
    step = spread / (n - 1) if n > 1 else 0
    tips = []
    for i in range(n):
        ang = start + step * i
        ang += jitter[i] if jitter else 0
        leng = length * (1 + 0.08 * math.sin(i * 2.3))
        tip = draw_leaf(draw, center, ang, leng, width, leaf_color, vein_color)
        tips.append((tip, ang, leng))

    if brown_tips:
        brown = (124, 96, 46)
        for (tip, ang, leng) in tips[:brown_tips]:
            bx, by = rotate_point(0, -leng * 0.62, ang)
            back = (center[0] + bx, center[1] + by)
            draw.line([back, tip], fill=brown, width=max(4, int(width * 0.5)))

    if spots:
        spot_color = (95, 74, 40)
        for s in range(spots):
            ang = math.radians(55 * s - 55)
            r = 40 + s * 7
            sx = center[0] + math.cos(ang) * r
            sy = center[1] - 14 + math.sin(ang) * r * 0.55
            draw.ellipse([sx - 6, sy - 5, sx + 6, sy + 5], fill=spot_color)


def draw_eyes_open(draw, cx, cy, spacing=20, r=7):
    for sign in (-1, 1):
        ex = cx + sign * spacing
        draw.ellipse([ex - r, cy - r, ex + r, cy + r], fill=(40, 30, 30))
        draw.ellipse([ex - 2, cy - r, ex + 3, cy - r + 5], fill=(255, 255, 255))


def draw_eyes_closed(draw, cx, cy, spacing=20, w=12):
    for sign in (-1, 1):
        ex = cx + sign * spacing
        draw.arc([ex - w / 2, cy - 6, ex + w / 2, cy + 6], start=10, end=170, fill=(40, 30, 30), width=3)


def draw_eyes_sleepy(draw, cx, cy, spacing=20, w=14):
    for sign in (-1, 1):
        ex = cx + sign * spacing
        draw.line([ex - w / 2, cy, ex + w / 2, cy], fill=(40, 30, 30), width=3)


def draw_eyes_weak(draw, cx, cy, spacing=20, w=12):
    # olhos em espiral fraca / x sutil pra "doente"
    for sign in (-1, 1):
        ex = cx + sign * spacing
        draw.line([ex - w / 2, cy - 5, ex + w / 2, cy + 5], fill=(40, 30, 30), width=3)
        draw.line([ex - w / 2, cy + 5, ex + w / 2, cy - 5], fill=(40, 30, 30), width=3)


def draw_sunglasses(draw, cx, cy, spacing=19):
    lens_w, lens_h = 22, 18
    dark = (24, 24, 28)
    for sign in (-1, 1):
        ex = cx + sign * spacing
        box = [ex - lens_w / 2, cy - lens_h / 2, ex + lens_w / 2, cy + lens_h / 2]
        draw.rounded_rectangle(box, radius=7, fill=dark)
        draw.line(
            [ex - lens_w / 2 + 4, cy - lens_h / 2 + 5, ex + lens_w / 2 - 7, cy - lens_h / 2 + 9],
            fill=(255, 255, 255, 160), width=3,
        )
        arm_dx = 1 if sign > 0 else -1
        draw.line(
            [ex + sign * lens_w / 2, cy - 1, ex + sign * (lens_w / 2 + 9), cy - 6],
            fill=dark, width=4,
        )
    draw.rectangle([cx - 6, cy - 3, cx + 6, cy + 3], fill=dark)


def draw_mouth(draw, cx, cy, kind, t=0.0):
    if kind == "smile":
        draw.arc([cx - 15, cy - 11, cx + 15, cy + 13], start=15, end=165, fill=(40, 30, 30), width=3)
    elif kind == "big_smile":
        draw.arc([cx - 18, cy - 14, cx + 18, cy + 16], start=10, end=170, fill=(40, 30, 30), width=4)
    elif kind == "flat":
        draw.line([cx - 11, cy + 4, cx + 11, cy + 4], fill=(40, 30, 30), width=3)
    elif kind == "frown":
        draw.arc([cx - 13, cy - 5, cx + 13, cy + 13], start=200, end=340, fill=(40, 30, 30), width=3)
    elif kind == "wavy":
        pts = []
        for i in range(9):
            x = cx - 15 + i * 3.7
            y = cy + (3 if i % 2 == 0 else -3)
            pts.append((x, y))
        draw.line(pts, fill=(40, 30, 30), width=3)
    elif kind == "grimace":
        pts = [(cx - 13, cy + 2), (cx - 6, cy - 3), (cx, cy + 3), (cx + 6, cy - 3), (cx + 13, cy + 2)]
        draw.line(pts, fill=(40, 30, 30), width=3)


def draw_blush(draw, cx, cy, spacing=28):
    for sign in (-1, 1):
        ex = cx + sign * spacing
        draw.ellipse([ex - 7, cy - 4, ex + 7, cy + 4], fill=(255, 150, 150))


def draw_party_hat(draw, cx, cy, tilt_deg=0):
    # cone com 3 faixas coloridas + pompom branco na ponta, apoiado em (cx, cy)
    apex_y = -54
    base_y = 4
    base_hw = 26
    bands = [
        (0.0, 0.34, (230, 70, 130)),
        (0.34, 0.67, (255, 210, 60)),
        (0.67, 1.0, (90, 180, 230)),
    ]
    for t0, t1, color in bands:
        y0 = apex_y + (base_y - apex_y) * t0
        y1 = apex_y + (base_y - apex_y) * t1
        w0 = base_hw * t0
        w1 = base_hw * t1
        local = [(-w0, y0), (w0, y0), (w1, y1), (-w1, y1)]
        pts = []
        for (x, y) in local:
            rx, ry = rotate_point(x, y, tilt_deg)
            pts.append((cx + rx, cy + ry))
        draw.polygon(pts, fill=color)

    tip_x, tip_y = rotate_point(0, apex_y, tilt_deg)
    tip = (cx + tip_x, cy + tip_y)
    draw.ellipse([tip[0] - 7, tip[1] - 7, tip[0] + 7, tip[1] + 7], fill=(255, 255, 255))


def draw_confetti(draw, cx_ref, cy_ref, ang, seed_offset=0):
    positions = [(-92, -68), (96, -58), (-104, 14), (102, 22), (-72, 82), (78, 76)]
    for k, (dx, dy) in enumerate(positions):
        bob = math.sin(ang * 2 + k + seed_offset) * 6
        rot = (k * 47 + math.degrees(ang) * 1.7) % 360
        color = CONFETTI_COLORS[k % len(CONFETTI_COLORS)]
        piece_cx, piece_cy = cx_ref + dx, cy_ref + dy + bob
        w, h = 7, 11
        local = [(-w / 2, -h / 2), (w / 2, -h / 2), (w / 2, h / 2), (-w / 2, h / 2)]
        pts = []
        for (x, y) in local:
            rx, ry = rotate_point(x, y, rot)
            pts.append((piece_cx + rx, piece_cy + ry))
        draw.polygon(pts, fill=color)


def frame_for(mood, i, n):
    t = i / n
    ang = 2 * math.pi * t
    img = Image.new("RGB", (CANVAS, CANVAS), BG[mood])
    draw = ImageDraw.Draw(img, "RGBA")

    cx = CANVAS // 2
    pot_top = 156

    bounce = math.sin(ang)
    sway_deg = math.sin(ang) * 4

    # Geometria da folhagem: IGUAL pra todos os estados (mesma base da 'feliz'),
    # so a cor, o rosto e pequenos adornos mudam por mood.
    n_leaves, spread, length, width, droop = 8, 165, 60, 19, 0
    head_cx = cx
    pot_cx = cx
    jitter = None
    sway = sway_deg
    brown_tips, spots = 0, 0
    party_hat = False

    if mood == "dormindo":
        for k, (sx, sy) in enumerate([(36, 36), (172, 26), (192, 64), (20, 86)]):
            tw = (math.sin(ang + k) + 1) / 2
            draw.text((sx, sy), "*", font=FONT_SM, fill=(255, 255, 255, int(110 + 100 * tw)))
        head_cy = 96 + bounce * 3
        sway = 0
        eyes = "closed"
        mouth = "flat"
    elif mood == "frio":
        head_cy = 98
        head_cx = cx + (-2 if i % 2 == 0 else 2)
        jitter = [((-1) ** (k + i)) * 2 for k in range(n_leaves)]
        sway = 0
        eyes = "closed_small"
        mouth = "wavy"
    elif mood == "seca":
        head_cy = 112 + abs(bounce) * 2
        droop = 14
        sway = 0
        brown_tips = 2
        eyes = "sleepy"
        mouth = "frown"
    elif mood == "doente":
        head_cy = 118 + abs(bounce) * 1
        droop = 20
        sway = 0
        brown_tips, spots = 2, 3
        eyes = "weak"
        mouth = "grimace"
    elif mood == "oculos":
        head_cy = 92 - abs(bounce) * 5
        eyes = "sunglasses"
        mouth = "big_smile"
    elif mood == "festa":
        # balanco/bounce bem mais exagerado que o 'feliz' pra parecer dança,
        # e o vaso tambem balanca um pouco (nao so a folhagem).
        dance_ang = ang * 1.4
        dance_bounce = math.sin(dance_ang)
        dance_sway = math.sin(dance_ang) * 16
        head_cy = 86 - abs(dance_bounce) * 13
        head_cx = cx + dance_sway
        pot_cx = cx + dance_sway * 0.35
        sway = 0
        eyes = "open"
        mouth = "big_smile"
        party_hat = True
    else:  # feliz
        head_cy = 94 - abs(bounce) * 6
        eyes = "open"
        mouth = "smile"

    draw_pot(draw, pot_cx, pot_top)

    head_center = (head_cx, head_cy)

    draw.line([(pot_cx, pot_top + 2), (head_cx, head_cy + 30)], fill=STEM, width=9)

    draw_bush(draw, head_center, mood, n_leaves, spread, droop, length, width, jitter,
              sway, brown_tips=brown_tips, spots=spots)

    R = 38
    head_color = HEAD_COLOR[mood]
    draw.ellipse([head_cx - R, head_cy - R, head_cx + R, head_cy + R], fill=head_color)
    hl = lerp_color(head_color, (255, 255, 255), 0.3)
    draw.ellipse([head_cx - R * 0.45, head_cy - R * 0.7, head_cx + R * 0.2, head_cy - R * 0.1], fill=hl)

    eye_cy = head_cy - 4
    mouth_cy = head_cy + 16

    if eyes == "open":
        if (i % n) > n * 0.85:
            draw_eyes_closed(draw, head_cx, eye_cy)
        else:
            draw_eyes_open(draw, head_cx, eye_cy)
    elif eyes == "closed":
        draw_eyes_closed(draw, head_cx, eye_cy)
    elif eyes == "closed_small":
        draw_eyes_closed(draw, head_cx, eye_cy, w=10)
    elif eyes == "sleepy":
        draw_eyes_sleepy(draw, head_cx, eye_cy)
    elif eyes == "weak":
        draw_eyes_weak(draw, head_cx, eye_cy)
    elif eyes == "sunglasses":
        draw_sunglasses(draw, head_cx, eye_cy)

    draw_mouth(draw, head_cx, mouth_cy, mouth, t=ang)

    if mood in ("feliz", "festa"):
        draw_blush(draw, head_cx, mouth_cy - 2)

    if party_hat:
        hat_tilt = math.sin(ang * 1.4) * 10
        draw_party_hat(draw, head_cx, head_cy - 22, tilt_deg=hat_tilt)
        draw_confetti(draw, head_cx, head_cy, ang)

    if mood == "oculos":
        sun_cx, sun_cy, sun_r = 186, 28, 14
        draw.ellipse([sun_cx - sun_r, sun_cy - sun_r, sun_cx + sun_r, sun_cy + sun_r], fill=(255, 200, 60))
        for k in range(8):
            a = math.radians(k * 45 + i * 4)
            x1, y1 = sun_cx + math.cos(a) * (sun_r + 4), sun_cy + math.sin(a) * (sun_r + 4)
            x2, y2 = sun_cx + math.cos(a) * (sun_r + 12), sun_cy + math.sin(a) * (sun_r + 12)
            draw.line([x1, y1, x2, y2], fill=(255, 200, 60), width=2)

    if mood == "frio":
        for k, (sx, sy) in enumerate([(30, 50), (185, 40), (24, 110)]):
            draw.text((sx, sy), "*", font=FONT_SM, fill=(160, 220, 255))

    return img


def build_loop_frames(mood):
    return [frame_for(mood, i, N_FRAMES) for i in range(N_FRAMES)]


def save_gif(frames, path, loop):
    # Constroi UMA paleta de cores compartilhada a partir de todos os frames
    # juntos e quantiza cada frame pra essa mesma paleta. Sem isso, o GIF do
    # Pillow escolhe uma paleta de 256 cores PRA CADA frame individualmente,
    # e como os tons mudam sutilmente quadro a quadro (no crossfade), a
    # cor mais proxima escolhida pode "pular" de frame pra frame - e isso
    # aparece como um flicker/cintilar bem perceptivel.
    w, h = frames[0].size
    strip = Image.new("RGB", (w, h * len(frames)))
    for idx, f in enumerate(frames):
        strip.paste(f.convert("RGB"), (0, idx * h))
    palette_ref = strip.convert("P", palette=Image.ADAPTIVE, colors=256)

    quantized = [f.convert("RGB").quantize(palette=palette_ref, dither=Image.Dither.NONE) for f in frames]

    kwargs = dict(save_all=True, append_images=quantized[1:], duration=FRAME_MS, optimize=False, disposal=2)
    if loop is not None:
        kwargs["loop"] = loop
    quantized[0].save(path, **kwargs)


def build_transition_frames(frame_a_last, frame_b_first, steps=config.TRANSITION_FRAMES):
    frames = []
    for s in range(1, steps + 1):
        t = s / steps
        frames.append(Image.blend(frame_a_last.convert("RGB"), frame_b_first.convert("RGB"), t))
    return frames


def main():
    loops = {}
    for mood in config.MOODS:
        print(f"Gerando loop para '{mood}'...")
        frames = build_loop_frames(mood)
        loops[mood] = frames
        save_gif(frames, os.path.join(OUT_DIR, f"loop_{mood}.gif"), loop=0)

    print("Gerando transicoes entre todos os pares de estados...")
    for a in config.MOODS:
        for b in config.MOODS:
            if a == b:
                continue
            trans = build_transition_frames(loops[a][-1], loops[b][0])

            # GIF combinado (fica disponivel pra preview/uso manual, mas o
            # app NAO usa ele pra tocar a transicao - ver motivo abaixo).
            path = os.path.join(OUT_DIR, f"transition_{a}_to_{b}.gif")
            save_gif(trans, path, loop=None)

            # Cada frame tambem como PNG estatico separado. O app.js troca
            # esses PNGs manualmente, no mesmo loop de requestAnimationFrame
            # que muda a cor de fundo, porque o timing de frame de GIF nativo
            # do navegador NAO e confiavel/sincronizavel com JS (cada engine
            # arredonda/decodifica os delays do seu jeito, sem garantia de
            # ficar em fase com o relogio da pagina). Com PNGs controlados
            # por JS, os dois (cor de fundo e desenho) usam o MESMO relogio.
            frame_dir = os.path.join(OUT_DIR, f"transition_{a}_to_{b}")
            os.makedirs(frame_dir, exist_ok=True)
            for idx, frame in enumerate(trans, start=1):
                frame.convert("RGB").save(os.path.join(frame_dir, f"frame_{idx}.png"))

    cols = 4
    rows = (len(config.MOODS) + cols - 1) // cols
    preview = Image.new("RGB", (CANVAS * cols, CANVAS * rows), (255, 255, 255))
    for idx, mood in enumerate(config.MOODS):
        f = loops[mood][0]
        preview.paste(f, ((idx % cols) * CANVAS, (idx // cols) * CANVAS))
    preview_path = os.path.join(os.path.dirname(__file__), "static", "preview.png")
    preview.save(preview_path)
    print(f"Pronto! GIFs em {OUT_DIR}")
    print(f"Preview (1 frame de cada mood) em {preview_path}")


if __name__ == "__main__":
    main()
