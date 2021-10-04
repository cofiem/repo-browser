import logging

from hill.data.common.logger import Logger
from hill.data.pgp.manage.messages import Messages
from hill.tests.base_test_case import BaseTestCase


class PgpTestCase(BaseTestCase):
    def setUp(self):
        self.maxDiff = None
        self._level = logging.INFO

    def test_container(self):
        content = self._read_text("debian-11-InRelease.txt")

        with self.assertLogs(level=self._level) as log_context:
            logger = Logger(log=logging.getLogger())
            messages = Messages(logger)

            container = messages.read_container_content(content)
            self.assertEqual(len(container.messages), 2)

            signed_message = container.messages[0]
            self.assertEqual(signed_message.name, "SIGNED MESSAGE")

            signature = container.messages[1]
            self.assertEqual(signature.name, "SIGNATURE")

        self.assertEqual(
            log_context.output,
            [
                "INFO:root:Reading container.",
                "INFO:root:Reading message.",
                "INFO:root:Found message begin line 'SIGNED MESSAGE'.",
                "INFO:root:Updating message header 'Hash'.",
                "INFO:root:Found blank line.",
                "INFO:root:Read 1178 clear text lines.",
                "INFO:root:Setting clear text to message data.",
                "INFO:root:Reading message.",
                "INFO:root:Found message begin line 'SIGNATURE'.",
                "INFO:root:Found blank line.",
                "INFO:root:Decoded CRC '5403619'.",
                "INFO:root:Found message end line 'SIGNATURE'.",
                "INFO:root:Read 48 encoded lines.",
                "INFO:root:Calculated CRC '5403619'.",
                "INFO:root:Successfully verified CRC '5403619'.",
            ],
        )

    def test_signature(self):
        content = self._read_text("debian-11-Release.gpg")

        with self.assertLogs(level=self._level) as log_context:
            logger = Logger(log=logging.getLogger())
            messages = Messages(logger)

            message = messages.read_message_content(content)
            self.assertEqual(message.name, "SIGNATURE")

        self.assertEqual(
            log_context.output,
            [
                "INFO:root:Reading message.",
                "INFO:root:Found message begin line 'SIGNATURE'.",
                "INFO:root:Found blank line.",
                "INFO:root:Decoded CRC '12022781'.",
                "INFO:root:Found message end line 'SIGNATURE'.",
                "INFO:root:Read 48 encoded lines.",
                "INFO:root:Calculated CRC '12022781'.",
                "INFO:root:Successfully verified CRC '12022781'.",
            ],
        )

    def test_public_key(self):
        content = self._read_text("debian-11-archive-key.asc")

        with self.assertLogs(level=self._level) as log_context:
            logger = Logger(log=logging.getLogger())
            messages = Messages(logger)

            message = messages.read_message_content(content)
            self.assertEqual(message.name, "PUBLIC KEY BLOCK")
        self.assertEqual(
            log_context.output,
            [
                "INFO:root:Reading message.",
                "INFO:root:Found message begin line 'PUBLIC KEY BLOCK'.",
                "INFO:root:Found blank line.",
                "INFO:root:Decoded CRC '11728271'.",
                "INFO:root:Found message end line 'PUBLIC KEY BLOCK'.",
                "INFO:root:Read 182 encoded lines.",
                "INFO:root:Calculated CRC '11728271'.",
                "INFO:root:Successfully verified CRC '11728271'.",
            ],
        )
