import base64
from pathlib import Path
from struct import unpack
from typing import Optional, Iterable

from hill.data.common.logger import Logger
from hill.data.pgp.item.container import Container
from hill.data.pgp.item.message import Message


class Messages:

    INDICATOR = "-----"
    HEADER_PREFIX = f"{INDICATOR}BEGIN PGP "
    HEADER_SUFFIX = INDICATOR
    FOOTER_PREFIX = f"{INDICATOR}END PGP "
    FOOTER_SUFFIX = INDICATOR

    def __init__(self, logger: Logger):
        self._logger = logger

    def read_file(self, path: Path) -> Container:
        return self.read_container_content(path.read_text(encoding="utf-8"))

    def read_container_content(self, content: str) -> Container:
        return self.read_container_lines(content.splitlines())

    def read_container_lines(self, lines: Iterable[str]) -> Container:
        container = Container()
        if not lines:
            return container

        self._logger.info("Reading container.")

        current_lines = []
        for line_raw in lines:
            line = line_raw

            # check for the start of a message
            begin_message = self.read_message_header(line)
            if begin_message:
                # if there are already current lines, read message, add
                if current_lines:
                    message = self.read_message_lines(current_lines)
                    container.messages.append(message)

                # reset the current lines
                current_lines = []

            # check for the end of a message
            end_message = self.read_message_footer(line)
            if end_message:
                # add the current line, read message, add message
                if current_lines:
                    current_lines.append(line)
                    message = self.read_message_lines(current_lines)
                    container.messages.append(message)

                # reset the current lines
                current_lines = []

            else:
                # add the line to the current lines
                current_lines.append(line)

        # if there are remaining current lines, read message, add
        # this is needed in case the footer is missing
        if current_lines:
            message = self.read_message_lines(current_lines)
            container.messages.append(message)

        return container

    def read_message_content(self, content: str) -> Message:
        return self.read_message_lines(content.splitlines())

    def read_message_lines(self, lines: Iterable[str]) -> Message:
        """
        Read a message.

        Radix-64 is identical to the "Base64" encoding described from MIME,
        with the addition of an optional 24-bit CRC.

        The checksum is calculated on the input data before encoding;
        the checksum is then encoded with the same Base64 algorithm and,
        using an additional "=" symbol as separator, appended to the encoded output data.

        "OpenPGP's Radix-64 encoding is composed of two parts: a base64
        encoding of the binary data and a checksum.

        The checksum is a 24-bit Cyclic Redundancy Check (CRC) converted to
        four characters of radix-64 encoding by the same MIME base64
        transformation, preceded by an equal sign (=).  The CRC is computed
        by using the generator 0x864CFB and an initialization of 0xB704CE.
        The accumulation is done on the data before it is converted to
        radix-64, rather than on the converted data.

        The checksum with its leading equal sign MAY appear on the first line
        after the base64 encoded data."
        """
        result = Message()
        if not lines:
            return result

        self._logger.info("Reading message.")

        seen_header_sep = False
        seen_end = False
        is_encoded = None

        text_lines = []
        encoded_count = 0

        for line_raw in lines:
            line = line_raw

            # there should only be empty lines after the footer
            if seen_end and line.strip():
                raise ValueError(f"Found content after end of message: '{line}'.")

            # check for the start of a message
            begin_message = self.read_message_header(line)
            if result.name and begin_message:
                raise ValueError(
                    f"Found a second header: 1) '{result.name}'; 2) '{begin_message}'."
                )
            elif not result.name and begin_message:
                result.name = begin_message
                self._logger.info(f"Found message begin line '{begin_message}'.")
                is_encoded = result.name != "SIGNED MESSAGE"
                continue

            # check for the end of a message
            end_message = self.read_message_footer(line)
            if end_message:
                self._logger.info(f"Found message end line '{end_message}'.")
                seen_end = True
                continue

            # check for the blank line indicating the end of the headers
            if not line.strip():
                self._logger.info("Found blank line.")
                seen_header_sep = True
                continue

            if not seen_header_sep:
                key, value = line.split(":", maxsplit=1)
                self.update_message(result, key, value)
                continue

            # crc line
            if line.startswith("="):
                if result.checksum:
                    raise ValueError(
                        f"Found a second crc: 1) '{result.checksum}'; 2) '{line}'."
                    )
                result.checksum = self.decode_crc(line)
                continue

            # clear text
            if not is_encoded and line.startswith("- "):
                # "When reversing dash-escaping, an implementation MUST strip the string
                #    "- " if it occurs at the beginning of a line
                self._logger.info("Removed leading '- ' from clear text line.")
                text_lines.append(line[2:])
                continue

            if not is_encoded and line.startswith("-"):
                # "SHOULD warn on "-" and any character other than a space at the beginning of a line."
                self._logger.warning(
                    f"The second character on a line that starts with '-' must be a space '{line}'."
                )
                text_lines.append(line)
                continue

            if not is_encoded:
                text_lines.append(line)
                continue

            # encoded text
            if is_encoded:
                line_data = self.decode_base64(line)
                encoded_count += 1
                if not result.data:
                    result.data = line_data
                else:
                    result.data += line_data
                continue

        if is_encoded:
            self._logger.info(f"Read {encoded_count} encoded lines.")
        else:
            self._logger.info(f"Read {len(text_lines)} clear text lines.")

        # include clear text if available
        if text_lines and not is_encoded:
            self._logger.info("Setting clear text to message data.")
            result.data = b"".join([i.encode("utf-8") for i in text_lines])

        # verify crc if available
        if result.checksum:
            self.verify_crc(result.data, result.checksum)

        return result

    def update_message(self, message: Message, key: str, value: str) -> None:
        self._logger.info(f"Updating message header '{key}'.")
        if key == "Version":
            message.header_version = value.strip()
        elif key == "Comment":
            message.header_comment = value.strip()
        elif key == "MessageID":
            message.header_message_id = value.strip()
        elif key == "Hash":
            message.header_hashes = [i.strip() for i in value.split(",") if i]
        elif key == "Charset":
            message.header_charset = value.strip()
        else:
            raise ValueError(f"Unknown message header '{key}={value}'.")

    def read_message_header(self, line: str) -> Optional[str]:
        if "BEGIN PGP" not in line:
            return None
        return self.read_message_separator(line)

    def read_message_footer(self, line: str) -> Optional[str]:
        if "END PGP" not in line:
            return None
        return self.read_message_separator(line)

    def read_message_separator(self, line: str) -> Optional[str]:
        name = line
        if not name or "-" not in name:
            return None

        left_begin = "-----BEGIN PGP "
        left_begin_len = len(left_begin)
        left_end = "-----END PGP "
        left_end_len = len(left_end)
        if name.startswith(left_begin):
            name = name[left_begin_len:]
        elif name.startswith(left_end):
            name = name[left_end_len:]
        else:
            return None

        right_text = "-----"
        right_len = len(right_text)
        if not name.endswith(right_text):
            return None
        name = name[0:-right_len]
        return name

    def decode_base64(self, value: str):
        """
        Decode a radix-65 encoded value.

        Ref: https://datatracker.ietf.org/doc/html/rfc4880#section-6
        """

        line_encoded = value.encode(encoding="utf-8")
        line_decoded = base64.b64decode(line_encoded, validate=True)
        return line_decoded

    def calculate_crc(self, value: bytes) -> int:
        """
        Calculate 24-bit Cyclic Redundancy Check.

        Ref: https://datatracker.ietf.org/doc/html/rfc4880#section-6.1
        """

        init = 0xB704CE
        poly = 0x1864CFB
        check = 0x1000000
        mask = 0xFFFFFF

        crc = init
        for i in range(len(value)):
            start = i
            end = i + 1
            crc ^= (ord(value[start:end]) & 255) << 16
            for count in range(8):
                crc <<= 1
                if crc & check:
                    crc ^= poly
        result = crc & mask

        self._logger.info(f"Calculated CRC '{result}'.")
        return result

    def decode_crc(self, value: str) -> int:
        """
        Decode expected CRC value.

        Ref: https://datatracker.ietf.org/doc/html/rfc4880#section-6.1
        """
        line = value.strip()[1:]
        crc_raw = self.decode_base64(line)
        crc_unpacked = unpack("!L", b"\0" + crc_raw)
        crc_value = crc_unpacked[0]

        self._logger.info(f"Decoded CRC '{crc_value}'.")
        return crc_value

    def verify_crc(self, message_data: bytes, expected_crc: int):
        actual_crc = self.calculate_crc(message_data)
        if not expected_crc == actual_crc:
            msg = [
                "CRC does not match.",
                f"Expected '{expected_crc}' actual '{actual_crc}'.",
            ]
            raise ValueError(" ".join(msg))
        self._logger.info(f"Successfully verified CRC '{actual_crc}'.")
