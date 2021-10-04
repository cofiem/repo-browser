from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from hill.data.apt.apt_client import AptClient
from hill.data.common.http_client import HttpClient
from hill.data.common.local_cache import LocalCache, LocalCacheTime
from hill.data.common.logger import Logger
from hill.data.pgp.manage.messages import Messages
from hill.data.database.importer import Importer as DbImporter


class Command(BaseCommand):
    help = "Import an APT repository."

    def add_arguments(self, parser):
        parser.add_argument("url")
        parser.add_argument("--public-key-url")
        parser.add_argument("--public-key-file")

    def handle(self, *args, **options):
        archive_url = options.get("url")
        pub_key_url = options.get("public_key_url")
        pub_key_file = options.get("public_key_file")

        if not archive_url:
            raise CommandError("Invalid apt repository url.")

        if pub_key_url and pub_key_file:
            raise CommandError("Provide only one of public key url or file.")

        logger = Logger(cmd=self)
        cache = LocalCache()
        http_client = HttpClient(logger=logger, cache=cache)
        messages = Messages(logger)

        if pub_key_url:
            content = http_client.get(pub_key_url, LocalCacheTime.KEEP)
            message = messages.read_container_content(content)
        elif pub_key_file:
            message = messages.read_file(Path(pub_key_file))
        else:
            logger.warning(
                "CAUTION! No public key supplied. Downloaded files will not be verified."
            )
            message = None

        logger.info(f"Importing apt repository from url '{archive_url}'.")

        client = AptClient(logger, http_client, archive_url, message)
        releases, packages, contents, translations = client.get()

        importer = DbImporter()
        importer.run(releases, packages, contents, translations)

        logger.info("Finished importing apt repository.")
