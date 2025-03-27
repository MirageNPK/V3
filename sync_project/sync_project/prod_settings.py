from pathlib import Path
import os
# from dotenv import load_dotenv

# load_dotenv()
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# BOT_TOKEN = os.getenv("BOT_TOKEN")
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7*b!offfgff)0t_xgmi)gt$9k4i@pfgfggggfsssdkxk+=my%*d^1)!z4w&ad$*nsbtj'
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost', '*']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'notion_db',
        'USER': 'db_admin',
        'PASSWORD': 'Petro1207$',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

