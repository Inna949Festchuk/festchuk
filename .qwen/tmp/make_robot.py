import numpy as np
from PIL import Image, ImageDraw, ImageFilter

im = Image.open('/home/mygis/Рабочий стол/image_4b757873-f73c-438e-bfa3-364ab8a757f0_0.webp').convert('RGBA')
w, h = im.size

outer_poly = [
    # Top of head
    (216, 18), (227, 19), (238, 24), (245, 33), (249, 44), (248, 56),
    (244, 67), (247, 81), (253, 95), (259, 102),
    # Right shoulder (viewer's right)
    (275, 102), (291, 104), (303, 109), (311, 118), (315, 130),
    # Right upper arm & elbow
    (313, 146), (315, 165), (317, 183), (318, 198), (315, 210), (308, 215),
    # Forearm bottom edge back to waist
    (290, 214), (273, 212), (258, 211),
    # Right waist & hip
    (256, 223), (259, 234), (269, 248), (276, 265), (281, 284),
    (281, 308), (278, 336), (276, 362), (278, 382),
    # Right knee
    (282, 396), (285, 412), (281, 428),
    # Right calf / shin outer edge
    (289, 442), (298, 462), (301, 482), (299, 504), (296, 530), (295, 552),
    # Right ankle & foot
    (303, 562), (307, 575), (305, 588), (306, 604), (305, 619), (299, 626),
    (282, 629), (266, 628), (260, 622), (261, 610), (266, 594), (272, 578),
    (274, 560),
    # Right leg inner edge going up to crotch
    (275, 535), (271, 505), (266, 475), (261, 448), (255, 428),
    (250, 412), (247, 395), (241, 368), (230, 340), (222, 316),
    # Crotch to left leg inner edge going down
    (213, 313), (208, 340), (206, 368), (206, 392), (211, 408), (210, 422),
    (204, 438), (212, 456), (214, 474), (207, 500), (203, 526), (205, 544),
    (209, 558), (208, 574), (211, 586), (210, 595),
    # Left foot bottom & toe (viewer's left)
    (190, 596), (160, 599), (135, 599), (126, 593), (127, 584),
    (140, 576), (158, 566), (173, 555), (178, 542),
    # Left leg outer edge going up
    (178, 518), (174, 490), (169, 464), (168, 442), (173, 426),
    (166, 410), (165, 392), (168, 376), (165, 350), (163, 320),
    (164, 290), (168, 266), (176, 250), (185, 236), (187, 213),
    # Under left arm / laptop base
    (176, 214), (162, 224), (144, 225), (128, 221), (114, 217),
    (102, 214), (94, 207), (87, 198),
    # Laptop screen left edge
    (74, 197), (67, 178), (58, 154), (49, 130),
    # Laptop screen top edge
    (78, 129), (107, 129),
    # Laptop screen right edge down to keyboard/hands
    (118, 160), (130, 196), (149, 196),
    # Left arm / shoulder going up to neck
    (160, 180), (168, 156), (171, 136), (176, 120), (187, 112), (201, 107),
    # Neck & face profile
    (205, 96), (200, 92), (197, 86), (193, 81), (191, 75), (192, 69),
    (184, 64), (181, 54), (182, 42), (189, 30), (200, 22), (210, 19)
]

hole_right_arm = [
    (276, 145), (281, 147), (283, 166), (284, 183), (274, 183), (273, 164)
]

# Upscale 2x for crisp detail (768x1366)
up = 2
W, H = w * up, h * up
im_hi = im.resize((W, H), Image.Resampling.LANCZOS)

# High-res anti-aliased mask, slightly eroded (1px at 2x) so it stays 100% inside the armor edge
scale = 4
mask_4x = Image.new('L', (w * scale, h * scale), 0)
draw_4x = ImageDraw.Draw(mask_4x)
draw_4x.polygon([(x * scale, y * scale) for x, y in outer_poly], fill=255)
draw_4x.polygon([(x * scale, y * scale) for x, y in hole_right_arm], fill=0)
mask_hi = mask_4x.resize((W, H), Image.Resampling.LANCZOS)
mask_core = mask_hi.filter(ImageFilter.MinFilter(3))
mask_smooth = mask_core.filter(ImageFilter.GaussianBlur(radius=0.85))

# Multi-pass sharpening for razor-sharp armor seams & facial structure
im_sharp = im_hi.filter(ImageFilter.UnsharpMask(radius=2.2, percent=165, threshold=2))
rgb = np.array(im_sharp, dtype=np.float32)[..., :3] / 255.0
alpha = np.array(mask_smooth, dtype=np.float32) / 255.0
# Clean cutoff for tiny sub-1% alpha noise
alpha = np.where(alpha < 0.02, 0.0, alpha)

R, G, B = rgb[..., 0], rgb[..., 1], rgb[..., 2]

# Separate glowing energy channels from metallic armor
lum = 0.299 * R + 0.587 * G + 0.114 * B
neon_strength = np.clip((R - B) * 1.65 + np.maximum(0.0, R - 0.52) * 1.15, 0.0, 1.0)
neon_core = np.clip((R - 0.65) * 2.8 + (G - 0.22) * 1.6, 0.0, 1.0) * np.clip(neon_strength * 1.5, 0.0, 1.0)

# Armor tone curve: bright, crisp, metallic silver-indigo-cyan
armor_lum = np.power(np.clip(lum, 0.0, 1.0), 0.64) * 1.24 + 0.07
armor_lum = np.clip(0.5 + (armor_lum - 0.44) * 1.18, 0.06, 0.94)

armor_R = armor_lum * 0.70 + np.power(armor_lum, 2.2) * 0.22
armor_G = armor_lum * 0.86 + np.power(armor_lum, 1.7) * 0.16
armor_B = armor_lum * 1.05 + np.power(armor_lum, 1.3) * 0.14

# Purple/magenta ambient reflections on armor bevels (--neon-purple #BC13FE)
purple_bevel = np.clip((B - G) * 1.9, 0.0, 1.0) * (1.0 - neon_strength * 0.6)
armor_R += purple_bevel * 0.28
armor_G -= purple_bevel * 0.03
armor_B += purple_bevel * 0.34

# Site Dual-Neon Energy Palette (--neon-cyan #00F3FF + --neon-magenta #FF2BD6 / --neon-purple #BC13FE):
yy, xx = np.mgrid[0:H, 0:W]
yn = yy / float(H)
xn = xx / float(W)

laptop_zone = np.clip(1.0 - np.hypot((xn - 0.26) * 2.2, (yn - 0.27) * 3.5), 0.0, 1.0)
side_purple_zone = np.clip(0.32 * np.sin(yn * 8.5 - xn * 4.0) + 0.24 + laptop_zone * 0.45, 0.0, 0.68)

neon_R = side_purple_zone * 0.88 + neon_core * 0.85
neon_G = (1.0 - side_purple_zone * 0.72) * 0.96 + neon_core * 0.38
neon_B = 1.0

blend = np.clip(neon_strength * 1.38, 0.0, 1.0)
out_R = armor_R * (1.0 - blend) + neon_R * blend
out_G = armor_G * (1.0 - blend) + neon_G * blend
out_B = armor_B * (1.0 - blend) + neon_B * blend

# Soft internal neon glow around energy lines (masked strictly to robot interior)
neon_layer = np.stack([
    np.clip(neon_R * blend * alpha, 0.0, 1.0),
    np.clip(neon_G * blend * alpha, 0.0, 1.0),
    np.clip(neon_B * blend * alpha, 0.0, 1.0)
], axis=-1)
neon_pil = Image.fromarray((neon_layer * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(radius=5.0))
neon_bloom = np.array(neon_pil, dtype=np.float32) / 255.0

out_R = np.clip(out_R + neon_bloom[..., 0] * 0.40, 0.0, 1.0)
out_G = np.clip(out_G + neon_bloom[..., 1] * 0.48, 0.0, 1.0)
out_B = np.clip(out_B + neon_bloom[..., 2] * 0.54, 0.0, 1.0)

# Detail micro-contrast pass
graded_pil = Image.fromarray((np.stack([out_R, out_G, out_B], axis=-1) * 255).astype(np.uint8))
graded_pil = graded_pil.filter(ImageFilter.UnsharpMask(radius=1.3, percent=130, threshold=2))

# Progressive vertical dissolution of the lower body (gradual, NOT to 0%):
# Upper half (0..48% height): 100% opaque
# Lower half (48%..95% height): smoothly dissolves down to 25% opacity (never disappears completely)
y_norm = np.linspace(0.0, 1.0, H)[:, None]
fade_start = 0.48
fade_end = 0.94
min_opacity = 0.36
t = np.clip((y_norm - fade_start) / (fade_end - fade_start), 0.0, 1.0)
fade_curve = min_opacity + (1.0 - min_opacity) * (0.5 * (1.0 + np.cos(np.pi * t)))

holo_boost = (1.0 - fade_curve) * 0.35
graded_np = np.array(graded_pil, dtype=np.float32) / 255.0
graded_np[..., 0] = np.clip(graded_np[..., 0] + holo_boost * 0.10, 0.0, 1.0)
graded_np[..., 1] = np.clip(graded_np[..., 1] + holo_boost * 0.30, 0.0, 1.0)
graded_np[..., 2] = np.clip(graded_np[..., 2] + holo_boost * 0.48, 0.0, 1.0)

final_alpha = np.clip(alpha * fade_curve, 0.0, 1.0)

# Zero out RGB where alpha == 0 for clean WebP compression
zero_mask = (final_alpha > 0.0)[..., None]
graded_np = graded_np * zero_mask

rgba_out = np.dstack([
    (graded_np[..., 0] * 255).astype(np.uint8),
    (graded_np[..., 1] * 255).astype(np.uint8),
    (graded_np[..., 2] * 255).astype(np.uint8),
    (final_alpha * 255).astype(np.uint8),
])

out_img = Image.fromarray(rgba_out, mode='RGBA')
bbox = out_img.getbbox()
out_cropped = out_img.crop(bbox)
out_cropped.save('/home/mygis/Документы/feshchuk/frontend/public/assets/cyber-robot.webp', 'WEBP', quality=96, method=6)
print('Saved clean cyber-robot.webp, size:', out_cropped.size)
