#!/usr/bin/env python3
"""
フッターウォーターマーク焼き込みユーティリティ

PIL.ImageDraw で画像中央下に固定文字列 "TEKION Slide Generator v4" を焼き込む。
画像生成パイプライン (generate_slide_with_retry.py / providers/openai.py) で
PNG 保存前に各スライド画像へ適用され、以降の全ての配布物（PNG/PPTX/PDF）に
ブランド透かしが乗る。

設計: project/docs/skill/footer-watermark-spec.md
"""
import sys
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont


FOOTER_TEXT = "TEKION Slide Generator v4"
FOOTER_COLOR = (156, 163, 175, 255)  # Gray-400 / RGBA
FOOTER_FONT_PATH = "/System/Library/Fonts/Helvetica.ttc"
FOOTER_FONT_SIZE_RATIO = 0.015        # 画像高さに対する比率
FOOTER_BOTTOM_MARGIN_RATIO = 0.012    # 画像高さに対する下端余白比率（中央下ギリギリ）

_default_font_warned = False


def _load_font(font_path: str, font_size: int) -> ImageFont.ImageFont:
    """指定パスから TTF を読み込み、失敗時は PIL デフォルトフォントへフォールバック。"""
    global _default_font_warned
    try:
        return ImageFont.truetype(font_path, font_size)
    except (OSError, IOError):
        if not _default_font_warned:
            sys.stderr.write(
                f"[footer_utils] warning: font not found at {font_path}, "
                f"using PIL default font\n"
            )
            _default_font_warned = True
        return ImageFont.load_default()


def apply_footer(
    img: Image.Image,
    text: str = FOOTER_TEXT,
    color: tuple = FOOTER_COLOR,
    font_path: str = FOOTER_FONT_PATH,
) -> Image.Image:
    """画像のコピーに左下フッターを焼き込んで返す。元画像は変更しない。

    Args:
        img: 入力 PIL Image
        text: 焼き込む文字列（デフォルト: FOOTER_TEXT）
        color: RGBA タプル
        font_path: TTF/TTC フォントパス（見つからない場合は default fallback）

    Returns:
        フッター焼き込み済みの PIL Image（元画像とは別オブジェクト）
    """
    out = img.copy()

    if out.mode not in ("RGB", "RGBA"):
        out = out.convert("RGBA")

    draw = ImageDraw.Draw(out)

    font_size = max(1, int(out.height * FOOTER_FONT_SIZE_RATIO))
    font = _load_font(font_path, font_size)

    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    margin_y = int(out.height * FOOTER_BOTTOM_MARGIN_RATIO)
    x = (out.width - text_w) // 2
    y = out.height - margin_y - text_h

    fill = color if out.mode == "RGBA" else color[:3]
    draw.text((x, y), text, font=font, fill=fill)

    return out


def apply_footer_to_bytes(
    image_bytes: bytes,
    output_format: str = "PNG",
    text: str = FOOTER_TEXT,
) -> bytes:
    """画像バイト列にフッターを焼き込んで新しいバイト列を返す。

    画像生成 API が返した raw bytes をそのまま受け取り、
    フッター適用後のバイト列を返すラッパー。

    Args:
        image_bytes: 入力画像のバイト列（PNG/JPEG 等、PIL が開ける形式）
        output_format: 出力フォーマット（デフォルト: PNG）
        text: 焼き込む文字列

    Returns:
        フッター焼き込み済みのバイト列
    """
    src = Image.open(BytesIO(image_bytes))
    src.load()
    out = apply_footer(src, text=text)

    if output_format.upper() in ("JPEG", "JPG") and out.mode == "RGBA":
        out = out.convert("RGB")

    buf = BytesIO()
    out.save(buf, format=output_format)
    return buf.getvalue()
