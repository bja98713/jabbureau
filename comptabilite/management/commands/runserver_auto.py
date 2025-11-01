import socket
from django.core.management.base import BaseCommand
from django.core.management import call_command


def is_port_free(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.2)
        return s.connect_ex((host, port)) != 0


class Command(BaseCommand):
    help = "Run Django dev server on the first free port (tries 8000..8010)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--host",
            default="127.0.0.1",
            help="Host interface to bind (default: 127.0.0.1)",
        )
        parser.add_argument(
            "--start",
            type=int,
            default=8000,
            help="Starting port (default: 8000)",
        )
        parser.add_argument(
            "--end",
            type=int,
            default=8010,
            help="Ending port inclusive (default: 8010)",
        )
        parser.add_argument(
            "--noreload",
            action="store_true",
            help="Disable auto-reloader (passes --noreload to runserver)",
        )

    def handle(self, *args, **options):
        host = options["host"]
        start = options["start"]
        end = options["end"]
        noreload = options["noreload"]

        port = None
        for p in range(start, end + 1):
            if is_port_free(host, p):
                port = p
                break

        if port is None:
            self.stderr.write(self.style.ERROR(f"No free port found between {start} and {end}"))
            return 1

        addr = f"{host}:{port}"
        self.stdout.write(self.style.SUCCESS(f"Starting development server at http://{addr}/"))

        runserver_kwargs = {}
        if noreload:
            runserver_kwargs["use_reloader"] = False

        # Delegate to Django's runserver
        call_command("runserver", addr, **runserver_kwargs)
