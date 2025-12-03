from django.apps import AppConfig

class VentasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ventas'

    def ready(self):
        print("⚡ Cargando señales de VENTAS...")
        import ventas.signals
