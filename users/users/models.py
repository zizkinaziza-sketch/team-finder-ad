import random
import uuid
from io import BytesIO

from django.contrib.auth.base_user import AbstractBaseUser, BaseUserManager
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import models
from PIL import Image, ImageDraw, ImageFont


AVATAR_COLORS = [
    "#4A90D9", "#5FAD82", "#E07B4F", "#8B6AC2",
    "#D97575", "#5BA3A0", "#C97AAD", "#7B9E6B",
]

FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    "/Library/Fonts/Arial Bold.ttf",
]


def _generate_avatar(name):
    letter = (name[0] if name else "?").upper()
    color = random.choice(AVATAR_COLORS)
    size = 200
    img = Image.new("RGB", (size, size), color)
    draw = ImageDraw.Draw(img)

    font = None
    for path in FONT_PATHS:
        try:
            font = ImageFont.truetype(path, size // 2)
            break
        except (IOError, OSError):
            continue
    if font is None:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), letter, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2 - bbox[0]
    y = (size - text_h) // 2 - bbox[1]
    draw.text((x, y), letter, fill="white", font=font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    filename = f"avatars/avatar_{uuid.uuid4()}.png"
    saved_path = default_storage.save(filename, ContentFile(buf.read()))
    return saved_path


class UserManager(BaseUserManager):
    def create_user(self, email, name, surname, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, name=name, surname=surname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, surname, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_active", True)
        return self.create_user(email, name, surname, password, **extra_fields)


class User(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=124)
    surname = models.CharField(max_length=124)
    avatar = models.ImageField(upload_to="avatars/", blank=True)
    phone = models.CharField(max_length=12, unique=True, blank=True, null=True)
    github_url = models.URLField(blank=True)
    about = models.TextField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    favorites = models.ManyToManyField(
        "projects.Project",
        blank=True,
        related_name="interested_users",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name", "surname"]

    objects = UserManager()

    def __str__(self):
        return f"{self.name} {self.surname} <{self.email}>"

    def has_perm(self, perm, obj=None):
        return self.is_staff

    def has_module_perms(self, app_label):
        return self.is_staff

    def save(self, *args, **kwargs):
        if not self.avatar:
            self.avatar.name = _generate_avatar(self.name)
        super().save(*args, **kwargs)
