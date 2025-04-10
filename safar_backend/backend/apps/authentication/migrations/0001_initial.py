# Generated by Django 5.1.7 on 2025-04-10 06:22

import apps.authentication.models
import apps.core_apps.utility
import django.contrib.gis.db.models.fields
import django.core.validators
import django.db.models.deletion
import phonenumber_field.modelfields
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('auth', '0012_alter_user_first_name_max_length'),
        ('geographic_data', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='last login')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='superuser status')),
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('email', models.EmailField(max_length=255, unique=True, validators=[django.core.validators.EmailValidator()], verbose_name='Email Address')),
                ('username', models.CharField(blank=True, max_length=30, verbose_name='Username')),
                ('first_name', models.CharField(blank=True, max_length=30, verbose_name='First Name')),
                ('last_name', models.CharField(blank=True, max_length=30, verbose_name='Last Name')),
                ('language', models.CharField(default='en', max_length=10)),
                ('timezone', models.CharField(default='UTC', max_length=50)),
                ('preferred_language', models.CharField(default='en', max_length=10, verbose_name='Preferred Language')),
                ('preferred_currency', models.CharField(default='USD', max_length=10, verbose_name='Preferred Currency')),
                ('is_online', models.BooleanField(default=False, verbose_name='Online Status')),
                ('is_active', models.BooleanField(default=True, verbose_name='Active')),
                ('is_staff', models.BooleanField(default=False, verbose_name='Staff Status')),
                ('is_2fa_enabled', models.BooleanField(default=False, verbose_name='Two-Factor Authentication Enabled')),
                ('role', models.CharField(choices=[('guest', 'Guest'), ('owner', 'Owner'), ('organization', 'Real Estate Organization'), ('developer', 'Developer')], default='guest', max_length=25, verbose_name='User Role')),
                ('is_profile_public', models.BooleanField(default=False)),
                ('points', models.PositiveIntegerField(default=0)),
                ('membership_level', models.CharField(choices=[('bronze', 'Bronze'), ('silver', 'Silver'), ('gold', 'Gold')], default='bronze', max_length=20)),
                ('following', models.ManyToManyField(blank=True, related_name='followers', to=settings.AUTH_USER_MODEL)),
                ('groups', models.ManyToManyField(blank=True, help_text='The groups this user belongs to. A user will get all permissions granted to each of their groups.', related_name='user_set', related_query_name='user', to='auth.group', verbose_name='groups')),
                ('user_permissions', models.ManyToManyField(blank=True, help_text='Specific permissions for this user.', related_name='user_set', related_query_name='user', to='auth.permission', verbose_name='user permissions')),
            ],
            options={
                'verbose_name': 'User',
                'verbose_name_plural': 'Users',
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_deleted', models.BooleanField(db_index=True, default=False)),
                ('avatar', models.ImageField(blank=True, null=True, upload_to=apps.authentication.models.upload_avatar)),
                ('bio', models.TextField(blank=True)),
                ('phone_number', phonenumber_field.modelfields.PhoneNumberField(blank=True, max_length=128, null=True, region=None, verbose_name='Phone Number')),
                ('location', django.contrib.gis.db.models.fields.PointField(blank=True, geography=True, null=True, srid=4326, verbose_name='Geolocation')),
                ('postal_code', models.CharField(blank=True, max_length=20, verbose_name='Postal Code')),
                ('address', models.CharField(blank=True, max_length=255, verbose_name='Address')),
                ('date_of_birth', models.DateField(blank=True, null=True)),
                ('gender', models.CharField(blank=True, choices=[('male', 'Male'), ('female', 'Female'), ('prefer_not_to_say', 'Prefer Not to Say')], default='prefer_not_to_say', max_length=20, verbose_name='Gender')),
                ('travel_history', models.JSONField(blank=True, default=list)),
                ('travel_interests', models.JSONField(blank=True, default=list)),
                ('language_proficiency', models.JSONField(blank=True, default=dict)),
                ('last_active', models.DateTimeField(blank=True, null=True)),
                ('search_history', models.JSONField(blank=True, default=list)),
                ('privacy_consent', models.BooleanField(default=False, verbose_name='Privacy Consent')),
                ('consent_date', models.DateTimeField(blank=True, null=True, verbose_name='Consent Date')),
                ('notification_push_token', models.CharField(blank=True, max_length=255, null=True)),
                ('wants_push_notifications', models.BooleanField(default=True)),
                ('wants_sms_notifications', models.BooleanField(default=False)),
                ('metadata', models.JSONField(blank=True, default=dict, validators=[apps.core_apps.utility.validate_metadata])),
                ('city', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='geographic_data.city')),
                ('country', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='geographic_data.country')),
                ('preferred_countries', models.ManyToManyField(blank=True, related_name='preferred_by_users', to='geographic_data.country')),
                ('region', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='geographic_data.region')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'User Profile',
                'verbose_name_plural': 'User Profiles',
            },
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['email'], name='authenticat_email_d74434_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['is_active'], name='authenticat_is_acti_099f68_idx'),
        ),
        migrations.AddIndex(
            model_name='user',
            index=models.Index(fields=['role'], name='authenticat_role_7fb088_idx'),
        ),
        migrations.AddConstraint(
            model_name='user',
            constraint=models.UniqueConstraint(condition=models.Q(('is_deleted', False)), fields=('email',), name='unique_active_email'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['user'], name='authenticat_user_id_35f8a3_idx'),
        ),
        migrations.AddIndex(
            model_name='userprofile',
            index=models.Index(fields=['phone_number'], name='authenticat_phone_n_9f34a0_idx'),
        ),
    ]
