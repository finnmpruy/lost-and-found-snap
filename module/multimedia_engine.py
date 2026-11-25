import io
import os
import hashlib
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter, ImageOps

UPLOAD_DIR = os.path.join("uploads", "processed")
POSTER_DIR = os.path.join("uploads", "posters")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(POSTER_DIR, exist_ok=True)

CATEGORY_COLORS = {
    "Dompet": "#7C4A2D",
    "KTM / Kartu Identitas": "#3B5984",
    "Elektronik / Aksesoris": "#4C3B78",
    "Tas / Ransel": "#3E6B5C",
    "Kunci": "#7A6A28",
    "Lainnya": "#4B5563",
}


def _load_font(size: int, bold: bool = False):
    candidates = [
        "arialbd.ttf" if bold else "arial.ttf",
        "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def generate_sha256_hash(seed_text: str, image_bytes: bytes = b"") -> str:
    hasher = hashlib.sha256()
    hasher.update(seed_text.encode("utf-8"))
    if image_bytes:
        hasher.update(image_bytes)
    hasher.update(str(datetime.now().timestamp()).encode("utf-8"))
    return hasher.hexdigest()


def open_uploaded_photo(data: bytes) -> Image.Image:
    with Image.open(io.BytesIO(data)) as source:
        return ImageOps.exif_transpose(source).convert("RGB")


def apply_privacy_blur(img: Image.Image, blur_boxes: list) -> Image.Image:
    if not blur_boxes:
        return img

    w, h = img.size
    result = img.copy()
    for box in blur_boxes:
        x1 = max(0, int(w * box[0]))
        y1 = max(0, int(h * box[1]))
        x2 = min(w, int(w * box[2]))
        y2 = min(h, int(h * box[3]))
        if x2 > x1 + 4 and y2 > y1 + 4:
            region = result.crop((x1, y1, x2, y2))
            blurred_region = region.filter(ImageFilter.GaussianBlur(radius=18))
            result.paste(blurred_region, (x1, y1, x2, y2))
    return result


def apply_alpha_watermark(img: Image.Image, text: str = "LOST & FOUND TEL-U") -> Image.Image:
    base = img.convert("RGBA")
    w, h = base.size
    overlay = Image.new("RGBA", (w * 2, h * 2), (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    font_size = max(18, w // 22)
    font = _load_font(font_size, bold=True)

    step_x = int(font_size * 11)
    step_y = int(font_size * 4.5)
    for y in range(0, h * 2, step_y):
        for x in range(0, w * 2, step_x):
            draw.text((x, y), text, fill=(255, 255, 255, 55), font=font)

    rotated = overlay.rotate(28, resample=Image.BICUBIC, expand=False)
    cx, cy = rotated.size[0] // 2, rotated.size[1] // 2
    left = cx - (w // 2)
    top = cy - (h // 2)
    cropped_wm = rotated.crop((left, top, left + w, top + h))
    
    if cropped_wm.size != base.size:
        cropped_wm = cropped_wm.resize(base.size, Image.Resampling.LANCZOS)

    combined = Image.alpha_composite(base, cropped_wm)
    return combined.convert("RGB")


def process_uploaded_image(
    uploaded_bytes: bytes,
    brightness: float = 1.0,
    contrast: float = 1.0,
    blur_boxes: list = None,
    enable_watermark: bool = True,
    target_format: str = "WebP",
) -> dict:
    original_size_kb = round(len(uploaded_bytes) / 1024, 1)
    img = open_uploaded_photo(uploaded_bytes)
    orig_w, orig_h = img.size

    # 1. Pertahankan rasio & resolusi asli (hanya batasi sisi terpanjang max 1280px jika terlalu raksasa)
    max_side = 1280
    if max(orig_w, orig_h) > max_side:
        img.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)

    # 2. Brightness & Contrast
    if brightness != 1.0:
        img = ImageEnhance.Brightness(img).enhance(brightness)
    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)

    # 3. Manual Privacy Blur sesuai area pilihan pengguna
    if blur_boxes:
        img = apply_privacy_blur(img, blur_boxes)

    # 4. Watermark Alpha Blending
    if enable_watermark:
        img = apply_alpha_watermark(img, "LOST & FOUND TEL-U")

    # 5. Kompresi Adaptif (< 150 KB & diupayakan turun di bawah ukuran asli, rasio tetap utuh)
    fmt = target_format.upper()
    if fmt not in ("WEBP", "JPEG", "PNG"):
        fmt = "WEBP"

    target_max_bytes = min(150 * 1024, int(len(uploaded_bytes) * 0.85))
    target_max_bytes = max(target_max_bytes, 15 * 1024)
    out_buffer = io.BytesIO()

    if fmt == "PNG":
        quantized = img.quantize(colors=256, method=Image.Quantize.MEDIANCUT)
        resized = quantized.copy()
        resized.save(out_buffer, format="PNG", optimize=True)
        while len(out_buffer.getvalue()) > target_max_bytes and max(resized.size) > 480:
            new_w = int(resized.width * 0.85)
            new_h = int(resized.height * 0.85)
            resized = quantized.resize((new_w, new_h), Image.Resampling.LANCZOS)
            out_buffer = io.BytesIO()
            resized.save(out_buffer, format="PNG", optimize=True)
        final_dim = f"{resized.width}x{resized.height}"
    else:
        quality = 78
        img.save(out_buffer, format=fmt, quality=quality, optimize=True)
        while len(out_buffer.getvalue()) > target_max_bytes and quality > 25:
            quality -= 8
            out_buffer = io.BytesIO()
            img.save(out_buffer, format=fmt, quality=quality, optimize=True)
        final_dim = f"{img.width}x{img.height}"

    compressed_bytes = out_buffer.getvalue()
    compressed_size_kb = round(len(compressed_bytes) / 1024, 1)

    return {
        "preview_image": Image.open(io.BytesIO(compressed_bytes)),
        "compressed_bytes": compressed_bytes,
        "original_size_kb": original_size_kb,
        "compressed_size_kb": compressed_size_kb,
        "original_dim": f"{orig_w}x{orig_h}",
        "final_dim": final_dim,
        "format": target_format,
    }


def generate_placeholder_card(
    kategori: str,
    nama_barang: str,
    deskripsi: str,
    lokasi: str,
) -> bytes:
    """Membuat kartu gambar otomatis 1:1 sesuai mockup Galeri 6.1 ketika pelapor tidak mengunggah foto."""
    size = 720
    bg_hex = CATEGORY_COLORS.get(kategori, "#4B5563")
    img = Image.new("RGB", (size, size), bg_hex)
    draw = ImageDraw.Draw(img, "RGBA")

    # Aksen lingkaran halus di pojok kanan atas sesuai mockup
    draw.ellipse((size - 320, -80, size + 80, 320), fill=(255, 255, 255, 28))

    font_cat = _load_font(26, bold=True)
    font_title = _load_font(46, bold=True)
    font_desc = _load_font(24, bold=False)
    font_loc = _load_font(22, bold=True)

    # Kategori di kiri atas
    draw.text((48, 48), kategori, fill=(255, 255, 255, 230), font=font_cat)

    # Judul barang (wrap sederhana)
    words = nama_barang.split()
    lines, current = [], ""
    for w in words:
        test = f"{current} {w}".strip()
        if len(test) <= 18:
            current = test
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)

    y_cursor = 310
    for line in lines[:2]:
        draw.text((48, y_cursor), line, fill=(255, 255, 255, 255), font=font_title)
        y_cursor += 56

    # Deskripsi singkat
    short_desc = deskripsi[:68] + ("..." if len(deskripsi) > 68 else "")
    draw.text((48, y_cursor + 16), short_desc, fill=(255, 255, 255, 220), font=font_desc)

    # Lokasi di bagian bawah
    draw.text((48, size - 76), f"Terakhir: {lokasi}", fill=(255, 255, 255, 245), font=font_loc)

    buf = io.BytesIO()
    img.save(buf, format="WEBP", quality=80)
    return buf.getvalue()


def save_image_bytes(image_bytes: bytes, hash_id: str, ext: str) -> str:
    filename = f"{hash_id[:16]}.{ext.lower()}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    with open(filepath, "wb") as f:
        f.write(image_bytes)
    return filepath


def generate_digital_poster(laporan: dict) -> bytes:
    """Membuat poster digital 1 lembar PNG sesuai mockup 6.3 dengan rasio foto proporsional."""
    W, H = 800, 1080
    poster = Image.new("RGB", (W, H), "#FFFFFF")
    draw = ImageDraw.Draw(poster)

    is_hilang = str(laporan["jenis_laporan"]).strip().lower() in ("hilang", "kehilangan")
    banner_color = "#B91C1C" if is_hilang else "#15803D"
    banner_text = "BARANG HILANG" if is_hilang else "BARANG DITEMUKAN"

    # Header Banner
    draw.rectangle((40, 40, W - 40, 165), fill=banner_color)
    font_banner = _load_font(54, bold=True)
    draw.text((68, 72), banner_text, fill="#FFFFFF", font=font_banner)

    # Foto / Kartu Barang di tengah (proporsional tanpa gepeng)
    box_size = 520
    box_x = (W - box_size) // 2
    box_y = 205
    draw.rectangle((box_x, box_y, box_x + box_size, box_y + box_size), fill="#F8FAFC")

    item_img = Image.open(laporan["image_path"]).convert("RGB")
    item_img.thumbnail((box_size, box_size), Image.Resampling.LANCZOS)
    paste_x = box_x + (box_size - item_img.width) // 2
    paste_y = box_y + (box_size - item_img.height) // 2
    poster.paste(item_img, (paste_x, paste_y))

    # Detail Teks
    font_title = _load_font(38, bold=True)
    font_sub = _load_font(24, bold=False)
    draw.text((140, 755), laporan["nama_barang"], fill="#111827", font=font_title)
    draw.text((140, 810), f"Terakhir di {laporan['lokasi_terakhir']}", fill="#4B5563", font=font_sub)

    desc = laporan["deskripsi_ciri"]
    desc_wrapped = desc[:58] + ("..." if len(desc) > 58 else "")
    draw.text((140, 848), desc_wrapped, fill="#4B5563", font=font_sub)
    draw.text((140, 892), f"Pelapor: {laporan['nama_pelapor']} ({laporan['kelas']})", fill="#6B7280", font=font_sub)

    # Footer Bar Gelap sesuai mockup 6.3
    draw.rectangle((40, H - 105, W - 40, H - 40), fill="#111827")
    font_footer = _load_font(22, bold=True)
    short_hash = f"#{laporan['hash_sha256'][:10]}"
    draw.text((68, H - 85), "LOST & FOUND TEL-U", fill="#FFFFFF", font=font_footer)
    draw.text((W - 220, H - 85), short_hash, fill="#D1D5DB", font=font_footer)

    buf = io.BytesIO()
    poster.save(buf, format="PNG")
    return buf.getvalue()