from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.accounts'

    def ready(self):
        # Set SQLite WAL mode on every new connection to prevent "database is locked"
        from django.db.backends.signals import connection_created

        def set_sqlite_wal(sender, connection, **kwargs):
            if connection.vendor == 'sqlite':
                connection.cursor().execute('PRAGMA journal_mode=WAL;')
                connection.cursor().execute('PRAGMA synchronous=NORMAL;')
                connection.cursor().execute('PRAGMA busy_timeout=30000;')

        connection_created.connect(set_sqlite_wal)
