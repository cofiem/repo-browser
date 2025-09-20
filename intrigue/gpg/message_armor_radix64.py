import base64
import logging
import struct
import typing

from beartype import beartype

from intrigue.gpg import models
from intrigue.utils import load_data_item

logger = logging.getLogger(__name__)


@beartype
def read(content: bytes) -> models.Message:
    """Read bytes content."""
    try:
        data = content.decode(encoding="utf-8").splitlines()
    except UnicodeDecodeError as e:
        raise models.InvalidMessageArmorRadix64FormatException(
            "Content is not UTF-8 text."
        ) from e
    return message_lines(data)


@beartype
def message_lines(data: typing.Iterable[str]) -> models.Message:
    """Read a PGP message."""
    message = models.Message()
    if not data:
        return message

    logger.debug("Reading OpenPGP message.")

    packets = []

    current_lines = []
    for line in data:
        # check for the start of a message
        begin_message = packet_header(line)
        if begin_message:
            # if there are already current lines,
            # store the current packet and start a new one
            if current_lines:
                message = packet_lines(current_lines)
                packets.append(message)

            # reset the current lines
            current_lines = []

        # check for the end of a message
        end_message = packet_footer(line)
        if end_message:
            # add the current line,
            # store the current packet and start a new one
            if current_lines:
                current_lines.append(line)
                message = packet_lines(current_lines)
                packets.append(message)

            # reset the current lines
            current_lines = []

        else:
            # add the line to the current lines
            current_lines.append(line)

    # If there are remaining current lines,
    # store the current packet.
    # This is needed in case the footer is missing.
    if current_lines:
        message = packet_lines(current_lines)
        packets.append(message)

    return models.Message(items=packets)


@beartype
def packet_header(line: str) -> typing.Optional[str]:
    return _packet_boundary(line, models.HEADER_PREFIX, models.HEADER_SUFFIX)


@beartype
def packet_footer(line: str) -> typing.Optional[str]:
    return _packet_boundary(line, models.FOOTER_PREFIX, models.FOOTER_SUFFIX)


@beartype
def _packet_boundary(line: str, prefix: str, suffix: str) -> typing.Optional[str]:
    prefix_len = len(prefix)
    suffix_len = len(suffix)
    if line.startswith(prefix) and line.endswith(suffix):
        name = line[prefix_len:-suffix_len].strip()
        which = prefix.strip().strip("-")
        logger.debug("Found packet boundary '%s' (%s).", name, which)
        return name
    return None


@beartype
def packet_lines(lines: typing.Iterable[str]) -> models.ArmoredSection:
    """Read a packet."""
    if not lines:
        return models.ArmoredSection()

    logger.debug("Reading OpenPGP packet.")

    seen_header_sep = False
    seen_end = False
    is_encoded = None

    text_lines = []
    encoded_count = 0

    packet_data = {}

    for line in lines:
        # there should only be empty lines after the footer
        if seen_end and line.strip():
            raise models.InvalidMessageArmorRadix64FormatException(
                f"Found content after end of message: '{line}'."
            )

        # check for the start of a message
        begin_message = packet_header(line)
        if packet_data.get("name") and begin_message:
            raise models.InvalidMessageArmorRadix64FormatException(
                "Found a second header - "
                f"first: '{packet_data.get('name')}' second: '{begin_message}'."
            )

        elif not packet_data.get("name") and begin_message:
            packet_data["name"] = begin_message
            is_encoded = packet_data.get("name") != models.NAME_SIGNED_MESSAGE
            continue

        # check for the end of a message
        end_message = packet_footer(line)
        if end_message:
            seen_end = True
            continue

        # check for the blank line indicating the end of the headers
        if not line.strip():
            logger.debug("Found blank line.")
            seen_header_sep = True
            continue

        if not seen_header_sep:
            key, value = line.split(":", maxsplit=1)
            key = (key or "").strip()
            value = (value or "").strip()
            if not key or not value:
                raise models.InvalidMessageArmorRadix64FormatException(
                    f"Invalid OpenPGP field: '{line}'."
                )
            if key in packet_data:
                raise models.InvalidMessageArmorRadix64FormatException(
                    f"Duplicate OpenPGP field: '{line}'."
                )
            packet_data[key] = value
            continue

        # crc line
        if line.startswith("="):
            if packet_data.get("checksum"):
                raise models.InvalidMessageArmorRadix64FormatException(
                    "Found a second crc - "
                    f"first: '{packet_data.get('checksum')}' second: '{line}'."
                )

            packet_data["checksum"] = decode_crc(line)
            continue

        # clear text
        if not is_encoded and line.startswith("- "):
            # "When reversing dash-escaping,
            # an implementation MUST strip the string
            #    "- " if it occurs at the beginning of a line
            logger.debug("Removed leading '- ' from clear text line.")
            text_lines.append(line[2:])
            continue

        if not is_encoded and line.startswith("-"):
            # "SHOULD warn on "-" and any character
            # other than a space at the beginning of a line."
            msg1 = "The second char on a line that starts with '-' must be a space."
            msg2 = f"Found invalid line '{line}'."
            logger.warning("%s %s", msg1, msg2)
            text_lines.append(line)
            continue

        if not is_encoded:
            text_lines.append(line)
            continue

        # encoded text
        if is_encoded:
            line_data = decode_base64(line)
            encoded_count += 1
            if not packet_data.get("data"):
                packet_data["data"] = line_data
            else:
                packet_data["data"] += line_data
            continue

        raise models.InvalidMessageArmorRadix64FormatException(line)

    if is_encoded:
        logger.debug(f"Read {encoded_count} encoded lines.")
    else:
        logger.debug(f"Read {len(text_lines)} clear text lines.")

    # include clear text if available
    if text_lines and not is_encoded:
        logger.debug("Setting clear text to message data.")
        packet_data["data"] = b"\n".join([i.encode("utf-8") for i in text_lines])

    # verify crc if available
    if packet_data.get("checksum"):
        verify_crc(packet_data["data"], packet_data["checksum"])

    result = load_data_item(models.ArmoredSection, packet_data)
    return result


@beartype
def decode_crc(value: str) -> int:
    """
    Decode expected CRC value.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-6.1
    """
    line = value.strip()[1:]
    crc_raw = decode_base64(line)
    crc_unpacked = struct.unpack("!L", b"\0" + crc_raw)
    crc_value = crc_unpacked[0]

    logger.debug(f"Decoded CRC '{crc_value}'.")
    return crc_value


@beartype
def verify_crc(message_data: bytes, expected_crc: int):
    actual_crc = calculate_crc(message_data)
    if not expected_crc == actual_crc:
        raise models.InvalidMessageArmorRadix64CheckException(
            f"CRC does not match. Expected '{expected_crc}' actual '{actual_crc}'."
        )
    logger.debug(f"Successfully verified CRC '{actual_crc}'.")


@beartype
def decode_base64(value: str):
    """
    Decode a radix-65 encoded value.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-6
    """

    line_encoded = value.encode(encoding="utf-8")
    line_decoded = base64.b64decode(line_encoded, validate=True)
    return line_decoded


@beartype
def calculate_crc(value: bytes) -> int:
    """
    Calculate 24-bit Cyclic Redundancy Check.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-6.1
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

    logger.debug("Calculated CRC '%s'.", result)
    return result


# def verify_signed_message(
#         self,
#         signed_message: models.SignedMessagePacket,
#         signature: models.SignaturePacket,
#         public_key: models.PublicKeyPacket,
# ) -> None:
#     """Verify a signed message."""
#     # TODO
#     raise NotImplementedError()
