from ragendja.settings_post import *
add_app_media(globals(), 'combined-%(LANGUAGE_DIR)s.css',
    'blueprintcss/reset.css',
    'blueprintcss/typography.css',
    'blueprintcss/forms.css',
    'blueprintcss/grid.css',
    'blueprintcss/lang-%(LANGUAGE_DIR)s.css',
)
add_app_media(globals(), 'combined-print-%(LANGUAGE_DIR)s.css',
    'blueprintcss/print.css',
)
add_app_media(globals(), 'ie.css',
    'blueprintcss/ie.css',
)
