from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser

# Create your models here.

class UserManager(BaseUserManager):
    def create_user(self, userID, password=None, **extra):
        user = self.model(
            userID = userID,
            **extra,
        )

        user.set_password(password)
        user.save()
        return user
    
    def create_superuser(self, userID, password=None, **extra):
        extra.setdefault('is_admin', True)

        user = self.create_user(
            userID = userID,
            password=password,
            **extra
        )

        return user
    
class User(AbstractBaseUser):
    userID = models.CharField('ID', max_length=100, unique=True)
    name = models.CharField('name', max_length=50)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'userID'
    REQUIRED_FIELDS = ['name']

    def __str__(self):
        return self.name

    def has_perm(self, perm, obj=None):
        return True
    

    def has_module_perms(self, app_label):
        return True
    
    @property
    def is_staff(self):
        return self.is_admin
    