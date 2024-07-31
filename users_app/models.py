import random
from datetime import timedelta
from django.contrib.auth.models import AbstractUser
from django.core.validators import FileExtensionValidator
from django.db import models
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
from shared_app.models import BaseModel


class AuthStatus(models.TextChoices):
    new = "new", "New"
    done = "done", "Done"


class AuthType(models.TextChoices):
    email = "email", "Email"
    phone = "phone", "Phone"


class Gender(models.TextChoices):
    male = "male", "Male"
    female = "female", "Female"


class UserStatus(models.TextChoices):
    active = "active", "Active"
    inactive = "inactive", "Inactive"


class Country(models.TextChoices):
    # Uzbekistan
    tashkent = "Toshkent", "Tashkent"
    andijan = "Andijon", "Andijan"
    bukhara = "Buxoro", "Bukhara"
    fergana = "Farg'ona", "Fergana"
    jizzakh = "Jizzax", "Jizzakh"
    namangan = "Namangan", "Namangan"
    navoiy = "Navoiy", "Navoiy"
    kashkadarya = "Qashqadaryo", "Kashkadarya"
    samarkand = "Samarqand", "Samarkand"
    syrdarya = "Sirdaryo", "Syrdarya"
    surkhandarya = "Surxondaryo", "Surkhandarya"
    karakalpakstan = "Qoraqalpog'iston", "Karakalpakstan"
    khorezm = "Xorazm", "Khorezm"

    # Kazakhstan
    astana = "Астана", "Astana"
    almaty = "Алматы", "Almaty"
    shymkent = "Шымкент", "Shymkent"
    aktobe = "Ақтөбе", "Aktobe"
    abay = "Абай", "Abay"
    akmola = "Ақмола", "Akmola"
    atyrau = "Атырау", "Atyrau"
    west_kazakhstan = "Батыс Қазақстан", "West Kazakhstan"
    zhambyl = "Жамбыл", "Zhambyl"
    zhetysu = "Жетісу", "Zhetysu"
    karagandy = "Қарағанды", "Karagandy"
    kostanay = "Қостанай", "Kostanay"
    kizilorda = "Қызылорда", "Kyzylorda"
    mangistau = "Маңғыстау", "Mangistau"
    pavlodar = "Павлодар", "Pavlodar"
    north_kazakhstan = "Солтүстік Қазақстан", "North Kazakhstan"
    turkistan = "Түркістан", "Turkistan"
    ulytau = "Ұлытау", "Ulytau"
    east_kazakhstan = "Шығыс Қазақстан", "East Kazakhstan"

    # Kyrgyzstan
    bishkek = "Бишкек", "Bishkek"
    osh = "Ош", "Osh"
    jalal_abad = "Жалал-Абад", "Jalal-Abad"
    Issyk_Kul = "Ысык-Көл", "Issyk_Kul"
    naryn = "Нарын", "Naryn"
    talas = "Талас", "Talas"
    batken = "Баткен", "Batken"
    chuy = "Чүй", "chuy"

    # Tajikistan
    djibouti = "Djibouti", "Djibouti"

    # Turkmenistan
    ashgabat = "Ashgabat", "Ashgabat"


class CustomUser(AbstractUser, BaseModel):
    """username, first_name, last_name, email, phone_number, date_joined, photo, date_of_birth, gender, auth_type,
    province, bio"""
    username = models.CharField(null=True, unique=True, blank=True, max_length=20)
    bio = models.TextField(null=True, blank=True)
    province = models.CharField(choices=Country.choices, null=True, blank=True, max_length=20)
    email = models.EmailField(null=True, unique=True, blank=True)
    phone_number = models.CharField(max_length=13, unique=True, null=True, blank=True)
    photo = models.ImageField(
        upload_to="users_pictures/",
        default="users_pictures/default_photo.png",
        validators=[FileExtensionValidator(allowed_extensions=["jpg", "jpeg", "png", "heif", "svg"])],
    )
    date_of_birth = models.DateField(editable=True, null=True, blank=True)
    gender = models.CharField(choices=Gender.choices, null=True, blank=True, max_length=6)
    auth_type = models.CharField(choices=AuthType.choices, default=AuthType.email, max_length=5)
    auth_status = models.CharField(choices=AuthStatus.choices, default=AuthStatus.new, max_length=5)

    def __str__(self):
        return self.username

    def __repr__(self):
        return self.username

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def hashing_password(self):
        if not self.password.startswith("pbkdf2_sha256"):
            self.set_password(self.password)

    def create_verify_code(self, verify_type):
        code = "".join([str(random.randint(0, 9)) for _ in range(4)])
        CustomUserConfirmation.objects.create(
            user_id=self.id, verify_type=verify_type, code=code
        )
        return code

    def token(self):
        refresh = RefreshToken.for_user(self)
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }

    def save(self, *args, **kwargs):
        self.hashing_password()
        super(CustomUser, self).save(*args, **kwargs)


class CustomUserConfirmation(BaseModel):
    """verify_type, code, user, expiration_time, is_confirmed"""

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name="verify_code"
    )
    code = models.CharField(max_length=4)
    verify_type = models.CharField(max_length=7, choices=AuthType.choices)
    expiration_time = models.DateTimeField(null=True)
    is_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return str(f"{self.user.__str__()} {self.code}")

    def save(self, *args, **kwargs):
        if self.verify_type == AuthType.email:
            self.expiration_time = timezone.now() + timedelta(minutes=5)
        else:
            self.expiration_time = timezone.now() + timedelta(minutes=2)
        super(CustomUserConfirmation, self).save(*args, **kwargs)


class Follow(BaseModel):
    follower = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='follower')
    following = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='following')

    class Meta:
        unique_together = ('follower', 'following')

    def __str__(self):
        return f'{self.follower} follows to {self.following}'

    def save(self, *args, **kwargs):
        if Tab.objects.filter(follower=self.follower, following=self.following).exists():
            raise ValidationError("Follower and following must be unique")
        super().save(*args, **kwargs)


class Tab(BaseModel):
    """owner, category_name, tab_sequence_number"""
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="note_categories")
    name = models.CharField(max_length=20)
    tab_sequence_number = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"'{self.name}' category belong to {self.owner}"

    class Meta:
        unique_together = ('owner', 'name')

    def save(self, *args, **kwargs):
        if Tab.objects.filter(owner=self.owner, name=self.name).exists():
            raise ValidationError("Tabs must be unique")
        super().save(*args, **kwargs)


class Note(BaseModel):
    """owner, body, isPinned, note_sequence_number, category, created_time, updated_time"""
    owner = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="notes", null=True, )
    body = models.TextField()
    isPinned = models.BooleanField(default=False)
    note_sequence_number = models.IntegerField(null=True, blank=True)
    category = models.ForeignKey(Tab, on_delete=models.CASCADE, related_name="notes", null=True, blank=True)

    def __str__(self):
        return f"'{self.body}' note belongs to {self.owner}"

    class Meta:
        unique_together = ('owner', 'body')

    def save(self, *args, **kwargs):
        if self.category is not None and self.category not in self.owner.note_categories.all():
            raise ValidationError("Note owner must be the same as NoteCategory owner.")
        super().save(*args, **kwargs)
