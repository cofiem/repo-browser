import datetime
import logging
import struct

from beartype import beartype

from intrigue.gpg import models

logger = logging.getLogger(__name__)


@beartype
def read(content: bytes) -> models.Message:
    """Read bytes content."""
    items = []

    remaining = content
    while len(remaining) > 0:
        tag, packet_length, header_length = packet_tag(content)
        packet_start = header_length
        packet_end = header_length + packet_length
        body = remaining[packet_start:packet_end]

        remaining = remaining[packet_end:]

        if tag == models.PacketTag.SIGNATURE.value:
            items.append(signature(body))
        elif tag == models.PacketTag.PUBLIC_KEY.value:
            items.append(public_key(body))
        else:
            raise NotImplementedError(
                f"Packet tag {tag} ({models.PacketTag(tag)}) is not supported."
            )

    return models.Message(items=items)


@beartype
def packet_tag(data: bytes):
    """The first octet of the packet header is called the "Packet Tag".
    It determines the format of the header and denotes the packet contents.
    """
    first_octet = ord(data[0:1])

    # "Bit 7 -- Always one"
    # Bitwise and 128 / 0x80 / 0b1000 0000
    bit7 = first_octet & 0x80
    if bit7 != 0x80:
        raise models.InvalidMessageNativeFormatException(
            "Expected bit 7 value to be 1,"
            f"but got '{f'{first_octet:08b}'}'."
        )

    # "Bit 6 -- New packet format if set"
    # Bitwise and 64 / 0x40 / 0b0100 0000
    bit6 = first_octet & 0x40
    is_new_format = bit6 == 0x40

    # read the packet tag
    if is_new_format:
        tag, packet_length, header_length = packet_info_new(data)
    else:
        tag, packet_length, header_length = packet_info_old(data)

    return tag, packet_length, header_length


@beartype
def packet_info_old(data: bytes):
    """Read a packet header in the 'old' format."""
    first_octet = ord(data[0:1])

    # "Bits 1-0 -- length-type"
    # Bitwise and 3 / 0x3 / 0b0000 0011
    length_type = first_octet & 0x3

    # "Bits 5-2 -- packet tag"
    # Bit shift right by 2, then bitwise and 15 / 0xF / 0b0000 1111
    tag = (first_octet >> 2) & 0xF

    if length_type == 0:
        # "0 - The packet has a one-octet length.  The header is 2 octets long."
        packet_length = ord(data[1:2])
        header_length = 2

    elif length_type == 1:
        # "1 - The packet has a two-octet length.  The header is 3 octets long."
        packet_length = struct.unpack("!H", data[1:3])[0]
        header_length = 3

    elif length_type == 2:
        # "2 - The packet has a four-octet length.  The header is 5 octets long."
        packet_length = struct.unpack("!L", data[1:5])[0]
        header_length = 5

    elif length_type == 3:
        # "3 - The packet is of indeterminate length.  The header is 1 octet long."
        packet_length = None
        header_length = 1

    else:
        raise models.InvalidMessageNativeFormatException(f"Length type {length_type} is not supported.")

    return tag, packet_length, header_length


@beartype
def packet_info_new(data: bytes):
    """Read a packet header in the 'new' format."""

    # "Bits 5-0 -- packet tag"
    # Bitwise and 63 / 0x3F / 0b0011 1111
    tag = ord(data[0:1]) & 0x3F

    # "The remainder of the packet header is the length of the packet."
    first_header_octet = ord(data[1:2])
    second_header_octet = ord(data[2:3])

    if first_header_octet < 192:
        # "A one-octet Body Length header encodes
        # packet lengths of up to 191 octets."
        # "This type of length header is recognized
        # because the one octet value is less than 192."
        packet_length = first_header_octet
        header_length = 1

    elif 192 <= first_header_octet <= 223:
        # "A two-octet Body Length header encodes
        # packet lengths of 192 to 8383 octets."
        # "It is recognized because its first octet
        # is in the range 192 to 223."
        packet_length = (
                ((first_header_octet - 192) << 8) + second_header_octet + 192
        )
        header_length = 2

    elif first_header_octet == 255:
        # "A five-octet Body Length header encodes
        # packet lengths of up to
        # 4,294,967,295 (0xFFFFFFFF) octets in length."
        # "A five-octet Body Length header consists
        # of a single octet holding the value 255,
        # followed by a four-octet scalar."
        packet_length = struct.unpack("!L", data[2:6])[0]
        header_length = 5

    elif 244 <= first_header_octet < 255:
        # "When the length of the packet body is not
        # known in advance by the issuer,
        # Partial Body Length headers encode a packet
        # of indeterminate length, effectively making it a stream."
        # "A Partial Body Length header is one octet
        # long and encodes the length of only part of the data packet."
        # This length is a power of 2,
        # from 1 to 1,073,741,824 (2 to the 30th power).
        # It is recognized by its one octet value
        # that is greater than or equal to 224, and less than 255."
        _packet_length = 1 << (first_header_octet & 0x1F)
        _header_length = 1

        raise NotImplementedError("Packet Partial Body Lengths are not supported.")

    else:
        raise models.InvalidMessageNativeFormatException(f"Body length header {first_header_octet} is not supported.")

    return tag, packet_length, header_length


@beartype
def signature_sub_packet_info(content: bytes):
    """In Signature packets, the subpacket data set is preceded by
    a two-octet scalar count of the length in octets of all the subpackets.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-5.2.3.1
    """
    first_header_octet = ord(content[0:1])
    second_header_octet = ord(content[1:2])

    if first_header_octet < 192:
        length_len = 1
        sub_packet_len = first_header_octet
    elif 192 <= first_header_octet < 255:
        length_len = 2
        sub_packet_len = (
                ((first_header_octet - 192) << 8) + (second_header_octet) + 192
        )
    elif first_header_octet == 255:
        length_len = 5
        sub_packet_len = _to_int(content[1:5])
    else:
        raise ValueError("Invalid sub-packet header.")

    sub_packet_type = _to_int(content[length_len: length_len + 1])
    return length_len, sub_packet_len, sub_packet_type


@beartype
def signature(content: bytes):
    """A Signature packet describes a binding between some public key and some data.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-5.2

    Args:
        content:

    Returns:

    """
    if not content:
        raise ValueError("Must provide content.")

    version = content[0]
    if version == 0x04:
        return signature_v4(content)
    else:
        raise NotImplementedError(f"Signature version {version} is not supported.")


@beartype
def signature_v4(content: bytes):
    """A version 4 Signature.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-5.2.3

    Args:
        content:

    Returns:

    """
    if not content:
        raise ValueError("Must provide content.")

    # One-octet version number (4).
    version_start = 0
    version_len = 1
    version_end = version_start + version_len
    version = content[version_start:version_end]

    if version != b"\x04":
        raise ValueError(f"Must be a v4 signature, got {version}.")

    # One-octet signature type.
    sig_type_start = version_end
    sig_type_len = 1
    sig_type_end = sig_type_start + sig_type_len
    sig_type = content[sig_type_start:sig_type_end]

    # One-octet public-key algorithm.
    public_key_alg_start = sig_type_end
    public_key_alg_len = 1
    public_key_alg_end = public_key_alg_start + public_key_alg_len
    public_key_alg = content[public_key_alg_start:public_key_alg_end]

    # One-octet hash algorithm.
    hash_algorithm_start = public_key_alg_end
    hash_algorithm_len = 1
    hash_algorithm_end = hash_algorithm_start + hash_algorithm_len
    hash_algorithm = content[hash_algorithm_start:hash_algorithm_end]

    # Two-octet scalar octet count for following hashed subpacket data.
    hashed_count_start = hash_algorithm_end
    hashed_count_len = 2
    hashed_count_end = hashed_count_start + hashed_count_len
    hashed_data_len = _to_int(content[hashed_count_start:hashed_count_end])

    # Hashed subpacket data set (zero or more subpackets).
    hashed_data_start = hashed_count_end
    hashed_data_end = hashed_data_start + hashed_data_len
    hashed_data = content[hashed_data_start:hashed_data_end]

    # Two-octet scalar octet count for the following unhashed subpacket data.
    unhashed_cnt_start = hashed_data_end
    unhashed_cnt_len = 2
    unhashed_cnt_end = unhashed_cnt_start + unhashed_cnt_len
    unhashed_data_len = _to_int(content[unhashed_cnt_start:unhashed_cnt_end])

    # Unhashed subpacket data set (zero or more subpackets).
    unhashed_data_start = unhashed_cnt_end
    unhashed_data_end = unhashed_data_start + unhashed_data_len
    unhashed_data = content[unhashed_data_start:unhashed_data_end]

    # Two-octet field holding the left 16 bits of the signed hash value.
    signed_hash_value_start = unhashed_data_end
    signed_hash_value_len = 2
    signed_hash_value_end = signed_hash_value_start + signed_hash_value_len
    signed_hash_value = content[signed_hash_value_start:signed_hash_value_end]

    # One or more multiprecision integers comprising the signature.
    #        This portion is algorithm specific, as described above.
    remaining = content[signed_hash_value_end:]

    # read subpackets
    hashed_sub_packets = signature_sub_packets(hashed_data)
    unhashed_sub_packets = signature_sub_packets(unhashed_data)

    # TODO
    return {
        'version': version,
        'sig_type': sig_type,
        'public_key_alg': public_key_alg,
        'hash_algorithm': hash_algorithm,
        'hashed_data_len': hashed_data_len,
        'signed_hash_value': signed_hash_value,
        'hashed_sub_packets': hashed_sub_packets,
        'unhashed_sub_packets': unhashed_sub_packets,
        'remaining': remaining,
    }


@beartype
def signature_sub_packets(content: bytes):
    """A subpacket data set consists of zero or more Signature subpackets.
    In Signature packets, the subpacket data set is preceded by a two-octet
    scalar count of the length in octets of all the subpackets.
    A pointer incremented by this number will skip over the subpacket data set.
    Each subpacket consists of a subpacket header and a body.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-5.2.3.1

    Args:
        content:

    Returns:

    """
    items = []

    remaining = content
    while len(remaining) > 0:
        length_len, item_len, item_type = signature_sub_packet_info(content)
        sub_packet_start = length_len
        sub_packet_end = length_len + item_len
        body = remaining[sub_packet_start:sub_packet_end]

        remaining = remaining[sub_packet_end:]

        if item_type == 2:
            items.append(
                (item_type, "Signature Creation Time", _to_datetime(body))
            )
        elif item_type == 16:
            items.append((item_type, "Issuer", body))
        elif item_type == 33:
            items.append(
                (
                    item_type,
                    "Issuer Fingerprint",
                    {"version": body[0:1], "fingerprint": body[1:]},
                )
            )
        else:
            raise NotImplementedError(
                f"Subpacket tag {item_type} is not supported."
            )

    return items


@beartype
def public_key(content: bytes):
    if not content:
        raise ValueError("Must provide content.")

    version = content[0]
    if version == 0x04:
        return public_key_v4(content)
    else:
        raise NotImplementedError(f"Public key version {version} is not supported.")


@beartype
def public_key_v4(content: bytes):
    """A version 4 Public Key packet."""
    if not content:
        raise ValueError("Must provide content.")

    # One-octet version number (4).
    version_start = 0
    version_len = 1
    version_end = version_start + version_len
    version = content[version_start:version_end]

    # A four-octet number denoting the time that the key was created.
    created_start = version_end
    created_len = 4
    created_end = created_start + created_len
    created = _to_datetime(content[created_start:created_end])

    # A one-octet number denoting the public-key algorithm of this key.
    public_key_alg_start = created_end
    public_key_alg_len = 1
    public_key_alg_end = public_key_alg_start + public_key_alg_len
    public_key_alg = content[public_key_alg_start:public_key_alg_end]

    # A series of multiprecision integers comprising the key material
    remaining = content[public_key_alg_end:]
    mpi_length, mpi_value = _to_mpi(remaining)

    # TODO
    return {
        'version': version,
        'created': created,
        'public_key_alg': public_key_alg,
        'mpi_length': mpi_length,
        'mpi_value': mpi_value,
    }


@beartype
def _to_int(content: bytes) -> int:
    n = content
    if len(content) == 2:
        result = (n[0] << 8) + n[1]
    elif len(content) == 4:
        result = (n[0] << 24) + (n[1] << 16) + (n[2] << 8) + n[3]
    else:
        result = int.from_bytes(content, byteorder="big", signed=False)
    return result


@beartype
def _to_mpi(content: bytes):
    length = _to_int(content[0:2])
    value = _to_int(content[2:])
    return length, value


@beartype
def _to_text(content: bytes, encoding: str = "utf-8") -> str:
    return content.decode(encoding=encoding)


@beartype
def _to_datetime(content: bytes) -> datetime.datetime:
    seconds = _to_int(content)
    return datetime.datetime.fromtimestamp(seconds, tz=datetime.timezone.utc)
