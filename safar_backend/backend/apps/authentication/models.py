import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.contrib.gis.db import models as gis_models
from django.core.validators import EmailValidator
from django.utils.translation import gettext_lazy as _
from apps.core_apps.general import BaseModel
from phonenumber_field.modelfields import PhoneNumberField
from apps.geographic_data.models import Country, Region, City
from apps.core_apps.utility import validate_metadata

def upload_avatar(instance, filename):
    random_uuid = uuid.uuid4().hex
    path = f'avatar/{random_uuid}'
    extension = filename.split('.')[-1] if '.' in filename else 'jpg'
    return f'{path}.{extension}'

class UserManager(BaseUserManager):
    from apps.core_apps.utility import generate_unique_username
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_("The Email field must be set"))
        email = self.normalize_email(email)
        username = self.generate_unique_username(email)
        extra_fields.setdefault("username", username)
        
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if not extra_fields.get("is_staff"):
            raise ValueError(_("Superuser must have is_staff=True."))
        if not extra_fields.get("is_superuser"):
            raise ValueError(_("Superuser must have is_superuser=True."))

        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, BaseModel):
    email = models.EmailField(unique=True, max_length=255, validators=[EmailValidator()], verbose_name=_("Email Address"))
    username = models.CharField(max_length=30, blank=True, verbose_name=_("Username"))
    first_name = models.CharField(max_length=30, blank=True, verbose_name=_("First Name"))
    last_name = models.CharField(max_length=30, blank=True, verbose_name=_("Last Name"))
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=50, default="UTC")
    preferred_language = models.CharField(max_length=10, default="en", verbose_name=_("Preferred Language"))
    preferred_currency = models.CharField(max_length=10, default="USD", verbose_name=_("Preferred Currency"))
    is_online = models.BooleanField(default=False, verbose_name=_("Online Status"))
    is_active = models.BooleanField(default=True, verbose_name=_("Active"))
    is_staff = models.BooleanField(default=False, verbose_name=_("Staff Status"))
    is_2fa_enabled = models.BooleanField(default=False, verbose_name=_("Two-Factor Authentication Enabled"))

    role = models.CharField(
        max_length=25,
        choices=[
            ("guest", _("Guest")),
            ("owner", _("Owner")),
            ("organization", _("Real Estate Organization")),
            ("developer", _("Developer"))
        ],
        default="guest",
        verbose_name=_("User Role")
    )

    is_profile_public = models.BooleanField(default=False)
    following = models.ManyToManyField("self", symmetrical=False, related_name="followers", blank=True)
    points = models.PositiveIntegerField(default=0)
    membership_level = models.CharField( max_length=20, choices=[("bronze", "Bronze"), ("silver", "Silver"), ("gold", "Gold")], default="bronze")

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active']),
            models.Index(fields=['role']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['email'],
                condition=models.Q(is_deleted=False),
                name='unique_active_email',
            )
        ]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email

    def __str__(self):
        return self.get_full_name()

class UserProfile(BaseModel):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.ImageField(upload_to=upload_avatar, null=True, blank=True)
    bio = models.TextField(blank=True)
    phone_number = PhoneNumberField(blank=True, null=True, verbose_name=_("Phone Number"))
    location = gis_models.PointField(geography=True, null=True, blank=True, verbose_name="Geolocation")
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    region = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    postal_code = models.CharField(max_length=20, blank=True, verbose_name=_("Postal Code"))
    address = models.CharField(max_length=255, blank=True, verbose_name=_("Address"))
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField( max_length=20,
        choices=[
            ("male", _("Male")),
            ("female", _("Female")),
            ("prefer_not_to_say", _("Prefer Not to Say"))
        ],
        default="prefer_not_to_say",
        blank=True,
        verbose_name=_("Gender")
    )

    travel_history = models.JSONField(default=list, blank=True)
    travel_interests = models.JSONField(default=list, blank=True)
    language_proficiency = models.JSONField(default=dict, blank=True)
    preferred_countries = models.ManyToManyField(Country, blank=True, related_name="preferred_by_users")
    last_active = models.DateTimeField(null=True, blank=True)
    search_history = models.JSONField(default=list, blank=True)
    privacy_consent = models.BooleanField(default=False, verbose_name=_("Privacy Consent"))
    consent_date = models.DateTimeField(null=True, blank=True, verbose_name=_("Consent Date"))
    notification_push_token = models.CharField(max_length=255, null=True, blank=True)
    wants_push_notifications = models.BooleanField(default=True)
    wants_sms_notifications = models.BooleanField(default=False)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        validators=[validate_metadata]
    )

    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['phone_number']),
        ]

    def __str__(self):
        return f"Profile of {self.user.get_full_name()}"
