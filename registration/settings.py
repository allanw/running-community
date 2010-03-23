from ragendja.settings_post import settings

if not hasattr(settings, 'ACCOUNT_ACTIVATION_DAYS'):
    settings.ACCOUNT_ACTIVATION_DAYS = 30

settings.add_app_media('combined-%(LANGUAGE_CODE)s.js',
    'registration/code.js',
)

