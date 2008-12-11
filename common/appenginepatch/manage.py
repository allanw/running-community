# -*- coding: utf-8 -*-
if __name__ == '__main__':
    from common.appenginepatch.aecmd import setup_env
    setup_env(manage_py_env=True)

    # Recompile translation files
    from mediautils.compilemessages import updatemessages
    updatemessages()

    # Regenerate media files
    import sys
    from mediautils.generatemedia import updatemedia, generatemedia
    if len(sys.argv) < 2 or sys.argv[1] not in ('generatemedia', 'update'):
        updatemedia()

    if len(sys.argv) >= 2 and sys.argv[1] == 'update':
        generatemedia(False)

    import settings
    from django.core.management import execute_manager
    execute_manager(settings)
