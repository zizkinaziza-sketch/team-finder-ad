import random
import re
import uuid
from io import BytesIO

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from PIL import Image, ImageDraw, ImageFont

AVATAR_SIZE = 200

COLOR_BLUE = "#4A90D9"
COLOR_GREEN = "#5FAD82"
COLOR_ORANGE = "#E07B4F"
COLOR_PURPLE = "#8B6AC2"
COLOR_RED = "#D97575"
COLOR_TEAL = "#5BA3A0"
COLOR_PINK = "#C97AAD"
COLOR_OLIVE = "#7B9E6B"

AVATAR_COLORS = [
    COLOR_BLUE,
    COLOR_GREEN,
    COLOR_ORANGE,
    COLOR_PURPLE,
    COLOR_RED,
    COLOR_TEAL,
    COLOR_PINK,
    COLOR_OLIVE,
]

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]

PHONE_PATTERN = re.compile(r"^(8\d{10}|\+7\d{10})$")


def generate_avatar(name):
    letter = (name[0] if name else "?").upper()
    color = random.choice(AVATAR_COLORS)
    img = Image.new("RGB", (AVATAR_SIZE, AVATAR_SIZE), color)
    draw = ImageDraw.Draw(img)

    font = None
    for path in FONT_PATHS:
        try:
            font = ImageFont.truetype(path, AVATAR_SIZE // 2)
            break
        except (IOError, OSError):
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (AVATAR_SIZE - text_w) // 2 - bbox[0]
    y = (AVATAR_SIZE - text_h) // 2 - bbox[1]
    draw.text((x, y), letter, fill="white", font=font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    filename = f"avatars/avatar_{uuid.uuid4()}.png"
    saved_path = default_storage.save(filename, ContentFile(buf.read()))
    return saved_path


def normalize_phone(phone):
    if phone.startswith("8"):
        return "+7" + phone[1:]
    return phone


def validate_phone_format(phone):
    if not PHONE_PATTERN.match(phone):
        raise ValidationError(
            "Телефон должен быть в формате 8XXXXXXXXXX или +7XXXXXXXXXX"
        )
