import numpy as np
from PIL import Image, ImageDraw, ImageFilter

src_path = '/home/mygis/Рабочий стол/Meshy_AI_cyberpunk_robot_full_body.png'
im = Image.open(src_path).convert('RGBA')
W, H = im.size

# Exact native pixel coordinates on the 864x1536 image
outer_poly_native = [
    # Crown & back of helmet
    (455, 44), (478, 39), (502, 40), (525, 47), (544, 60), (557, 78), (562, 98),
    # Back of ear ring module
    (563, 118), (560, 138), (552, 154),
    # Back of neck cables down to right shoulder
    (556, 176), (565, 200), (576, 220), (588, 228),
    # Right shoulder top & outer ring (viewer's right)
    (618, 228), (652, 232), (680, 243), (700, 259), (712, 280),
    (715, 298), (713, 318),
    # Right bicep & elbow ring outer edge
    (710, 336), (712, 360), (715, 395), (718, 430),
    (720, 448), (719, 466), (713, 480), (702, 488), (686, 488),
    # Right forearm bottom edge back to waist
    (668, 484), (664, 495), (648, 494), (620, 485), (590, 478), (578, 476),
    # Right waist & hip outer contour
    (576, 500), (584, 525), (606, 558), (624, 594), (637, 636),
    (639, 680), (640, 740), (642, 800), (634, 845), (629, 868),
    # Right knee & knee ring
    (635, 890), (644, 916), (644, 938), (636, 956),
    # Right calf outer edge (full armor curve out to x=692)
    (655, 980), (676, 1015), (690, 1055), (692, 1090), (686, 1130),
    (676, 1185), (672, 1235),
    # Right ankle ring & right foot down to y=1446
    (682, 1255), (698, 1272), (700, 1300), (694, 1318), (697, 1355),
    (698, 1392), (692, 1412), (678, 1425), (660, 1442), (632, 1446),
    (596, 1445), (580, 1435), (579, 1412), (588, 1380), (602, 1340),
    (614, 1300), (618, 1255),
    # Right leg inner contour going up to crotch
    (618, 1200), (611, 1140), (600, 1080), (588, 1020), (576, 975),
    (562, 940), (556, 895), (544, 835), (520, 770), (498, 706),
    # Crotch & left leg inner contour going down to left heel
    (480, 704), (472, 760), (466, 825), (465, 880), (478, 912),
    (477, 942), (463, 975), (482, 1015), (492, 1055), (486, 1095),
    (470, 1145), (459, 1195), (462, 1225), (474, 1248), (474, 1275),
    (470, 1295), (480, 1320), (479, 1344),
    # Left foot sole & toe (viewer's left)
    (440, 1348), (390, 1358), (330, 1365), (290, 1363), (280, 1350),
    (283, 1332), (302, 1316), (340, 1295), (376, 1270), (392, 1245),
    # Left leg outer contour going up to waist
    (398, 1200), (392, 1130), (382, 1060), (381, 1005), (390, 965),
    (373, 930), (369, 895), (378, 855), (369, 790), (360, 720),
    (360, 655), (368, 600), (386, 560), (412, 528), (422, 495), (422, 476),
    # Full left forearm, wrist & fingers under the laptop (down to y=522!)
    (412, 492), (396, 508), (375, 519), (348, 522), (318, 522),
    (290, 520), (272, 513), (250, 505), (230, 500), (215, 494),
    (206, 484), (202, 468), (192, 460), (188, 448),
    # Laptop screen left & top & right edges
    (167, 444), (110, 290), (243, 289), (300, 440),
    # Fingers on keyboard & left upper arm up to shoulder
    (336, 439), (350, 424), (358, 415), (369, 390), (377, 360),
    (382, 330), (385, 306), (392, 288), (404, 272), (422, 260),
    (442, 252), (462, 247), (478, 250),
    # Front of neck & exact facial profile (chin, lips, nose, brow, forehead)
    (482, 240), (479, 224), (468, 232), (458, 229), (449, 219),
    (444, 212), (439, 206), (438, 198), (429, 194), (428, 182),
    (424, 170), (425, 160), (418, 155), (412, 148), (405, 125),
    (404, 100), (412, 76), (430, 56)
]

# Render polygon at 4x supersampling (3456x6144) for smooth anti-aliased edges
ss = 4
mask_ss = Image.new('L', (W * ss, H * ss), 0)
draw_ss = ImageDraw.Draw(mask_ss)
draw_ss.polygon([(x * ss, y * ss) for x, y in outer_poly_native], fill=255)
mask = mask_ss.resize((W, H), Image.Resampling.LANCZOS)
mask = mask.filter(ImageFilter.GaussianBlur(radius=0.8))

alpha = np.array(mask, dtype=np.float32) / 255.0
alpha = np.where(alpha < 0.015, 0.0, alpha)

# Gentle, natural unsharp mask on original image
im_crisp = im.convert('RGB').filter(ImageFilter.UnsharpMask(radius=1.1, percent=80, threshold=2))
rgb = np.array(im_crisp, dtype=np.float32) / 255.0

R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]

# Faithful color-space transformation preserving original shading, volume & details 1:1
warm_excess = np.clip(R - np.maximum(G, B), 0.0, 1.0)
orange_core = np.clip(np.minimum(R, G * 1.35) - B, 0.0, 1.0) * np.clip(R - 0.35, 0.0, 1.0)

R_base = np.power(R, 0.86) * 0.88
G_base = np.power(G, 0.84) * 1.08 + warm_excess * 0.78 + orange_core * 0.55
B_base = np.power(B, 0.82) * 1.18 + warm_excess * 0.92 + orange_core * 0.65

yy, xx = np.mgrid[0:H, 0:W]
yn = yy / float(H)
xn = xx / float(W)

laptop_zone = np.clip(1.0 - np.hypot((xn - 0.22) * 3.4, (yn - 0.24) * 4.5), 0.0, 1.0)
line_intensity = np.clip((R - 0.38) * 2.2, 0.0, 1.0) * np.clip(warm_excess * 2.5, 0.0, 1.0)
magenta_keep = np.clip(laptop_zone * 0.85 + (1.0 - line_intensity) * 0.55, 0.0, 1.0)

out_R = R_base * (1.0 - warm_excess * (1.0 - magenta_keep * 0.85)) + orange_core * 0.75
out_G = np.clip(G_base * (1.0 - 0.45 * laptop_zone * warm_excess), 0.0, 1.0)
out_B = np.clip(B_base, 0.0, 1.0)

rgb_graded = np.stack([out_R, out_G, out_B], axis=-1)
rgb_graded = np.clip(rgb_graded * 1.12 + 0.015, 0.0, 1.0)

# Progressive vertical dissolution for the second half of the body (gradual, NOT complete):
y_norm = np.linspace(0.0, 1.0, H)[:, None]
fade_start = 0.48
fade_end = 0.94
min_opacity = 0.35
t = np.clip((y_norm - fade_start) / (fade_end - fade_start), 0.0, 1.0)
fade_curve = min_opacity + (1.0 - min_opacity) * (0.5 * (1.0 + np.cos(np.pi * t)))

final_alpha = np.clip(alpha * fade_curve, 0.0, 1.0)

valid = (final_alpha > 0.0)[..., None]
out_rgb = rgb_graded * valid

rgba_out = np.dstack([
    (out_rgb[..., 0] * 255).astype(np.uint8),
    (out_rgb[..., 1] * 255).astype(np.uint8),
    (out_rgb[..., 2] * 255).astype(np.uint8),
    (final_alpha * 255).astype(np.uint8),
])

out_img = Image.fromarray(rgba_out, mode='RGBA')
bbox = out_img.getbbox()
out_cropped = out_img.crop(bbox)
print('Saved native-contour cyber-robot.webp, size:', out_cropped.size)

out_cropped.save('/home/mygis/Документы/festchuk/frontend/public/assets/cyber-robot.webp', 'WEBP', lossless=True, quality=100, method=6)
