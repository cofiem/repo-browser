"""Domain models for PGP data."""

from __future__ import annotations

import enum
import typing

import attrs

from intrigue.utils import get_name_under

INDICATOR = "-----"
HEADER_PREFIX = f"{INDICATOR}BEGIN PGP "
HEADER_SUFFIX = INDICATOR
FOOTER_PREFIX = f"{INDICATOR}END PGP "
FOOTER_SUFFIX = INDICATOR

NAME_SIGNED_MESSAGE = "SIGNED MESSAGE"
NAME_SIGNATURE = "SIGNATURE"


@enum.unique
class PacketTag(enum.Enum):
    """
    Enumeration of available OpenPGP packet tags.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-4.3
    """

    RESERVED_0 = 0
    """Reserved - a packet tag MUST NOT have this value"""
    PUBLIC_KEY_ENCRYPTED_SESSION_KEY = 1
    """Public-Key Encrypted Session Key Packet"""
    SIGNATURE = 2
    """Signature Packet"""
    SYMMETRIC_KEY_ENCRYPTED_SESSION_KEY = 3
    """Symmetric-Key Encrypted Session Key Packet"""
    ONE_PASS_SIGNATURE = 4
    """One-Pass Signature Packet"""
    SECRET_KEY = 5
    """Secret-Key Packet"""
    PUBLIC_KEY = 6
    """Public-Key Packet"""
    SECRET_SUBKEY = 7
    """Secret-Subkey Packet"""
    COMPRESSED_DATA = 8
    """Compressed Data Packet"""
    SYMMETRICALLY_ENCRYPTED_DATA = 9
    """Symmetrically Encrypted Data Packet"""
    MARKER_PACKET = 10
    """Marker Packet"""
    LITERAL_DATA_PACKET = 11
    """Literal Data Packet"""
    TRUST_PACKET = 12
    """Trust Packet"""
    USER_ID_PACKET = 13
    """User ID Packet"""
    PUBLIC_SUBKEY = 14
    """Public-Subkey Packet"""
    USER_ATTRIBUTE = 17
    """User Attribute Packet"""
    SYMMETRICALLY_ENCRYPTED_AND_INTEGRITY_PROTECTED_DATA = 18
    """Sym. Encrypted and Integrity Protected Data Packet"""
    MODIFICATION_DETECTION_CODE = 19
    """Modification Detection Code Packet"""
    OCB_Encrypted_Data = 20
    """OCB Encrypted Data Packet"""
    RESERVED_21 = 21
    """Reserved"""
    RESERVED_26 = 26
    """Reserved (CMS Encrypted Session Key Packet)"""
    PRIVATE_60 = 60
    """Private or Experimental Values"""
    PRIVATE_61 = 61
    """Private or Experimental Values"""
    PRIVATE_62 = 62
    """Private or Experimental Values"""
    PRIVATE_63 = 63
    """Private or Experimental Values"""


@attrs.frozen
class NativePacket:
    """
    A PGP Message Packet.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-4
    """

    tag: PacketTag
    """The type of packet."""
    length: int
    """The length of the header and the body."""
    header: bytes
    """The raw header value."""
    body: bytes
    """The raw body value."""


@attrs.define
class ArmoredSection:
    """
    One ASCII Armor item.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-6.2
    """

    name: typing.Optional[str] = attrs.field(
        default=None, metadata={get_name_under(): {"key": "name"}}
    )
    """The parsed Armor Header Line."""

    data: typing.Optional[bytes] = attrs.field(
        default=None, metadata={get_name_under(): {"key": "data"}}
    )
    """The decoded ASCII-Armored data."""

    checksum: typing.Optional[int] = attrs.field(
        default=None, metadata={get_name_under(): {"key": "checksum"}}
    )
    """The decoded Armor Checksum."""

    header_version: typing.Optional[str] = attrs.field(
        default=None, metadata={get_name_under(): {"key": "Version"}}
    )
    """
    "Version", which states the OpenPGP implementation and version
    used to encode the message.
    """

    header_comment: typing.Optional[str] = attrs.field(
        default=None, metadata={get_name_under(): {"key": "Comment"}}
    )
    """
    "Comment", a user-defined comment.  OpenPGP defines all text to
    be in UTF-8.  A comment may be any UTF-8 string.  However, the
    whole point of armoring is to provide seven-bit-clean data.
    Consequently, if a comment has characters that are outside the
    US-ASCII range of UTF, they may very well not survive transport.
    """

    header_message_id: typing.Optional[str] = attrs.field(
        default=None, metadata={get_name_under(): {"key": "MessageID"}}
    )
    """
    "MessageID", a 32-character string of printable characters. 
    The string must be the same for all parts of a multi-part message 
    that uses the "PART X" Armor Header. MessageID strings should be unique 
    enough that the recipient of the mail can associate all the parts of a 
    message with each other. A good checksum or cryptographic hash function 
    is sufficient. The MessageID SHOULD NOT appear unless it is in a 
    multi-part message. If it appears at all, it MUST be computed from the 
    finished (encrypted, signed, etc.) message in a deterministic fashion, 
    rather than contain a purely random value. This is to allow the legitimate 
    recipient to determine that the MessageID cannot serve as a covert means 
    of leaking cryptographic key information.
    """

    header_hashes_str: typing.Optional[str] = attrs.field(
        default=None, metadata={get_name_under(): {"key": "Hash"}}
    )
    """
    "Hash", a comma-separated list of hash algorithms used in this
    message.  This is used only in cleartext signed messages.
    """

    header_charset: typing.Optional[str] = attrs.field(
        default="UTF-8", metadata={get_name_under(): {"key": "Charset"}}
    )
    """
    "Charset", a description of the character set that the plaintext
    is in.  Please note that OpenPGP defines text to be in UTF-8.  An
    implementation will get best results by translating into and out
    of UTF-8.  However, there are many instances where this is easier
    said than done.  Also, there are communities of users who have no
    need for UTF-8 because they are all happy with a character set
    like ISO Latin-5 or a Japanese character set.  In such instances,
    an implementation MAY override the UTF-8 default by using this
    header key.  An implementation MAY implement this key and any
    translations it cares to; an implementation MAY ignore it and
    assume all text is UTF-8.
    """

    @property
    def is_clear_text(self):
        """Is this armored packet a clear text signed message?"""
        return self.name == NAME_SIGNED_MESSAGE

    @property
    def text(self):
        """Get the armored packet data as UTF-8 text."""
        return self.data.decode(encoding="utf-8")

    @property
    def header_hashes(self):
        return [
            i.strip()
            for i in (self.header_hashes_str or "").split(",")
            if i and i.strip()
        ]


@attrs.frozen
class SignaturePacket(NativePacket):
    """
    A signature packet.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-5.2
    """

    pass


@attrs.frozen
class SignedMessagePacket(NativePacket):
    """
    A cleartext signed message packet.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-7
    """

    pass


@attrs.frozen
class PublicKeyPacket(NativePacket):
    """
    A public key packet.

    Ref: https://datatracker.ietf.org/doc/html/draft-koch-openpgp-2015-rfc4880bis#section-5.5.2
    """

    pass


@attrs.frozen
class Message:
    items: list[ArmoredSection | NativePacket] = attrs.field(factory=list)

    @property
    def signed_message(self):
        return self.get(NAME_SIGNED_MESSAGE)

    @property
    def signature(self):
        return self.get(NAME_SIGNATURE)

    def get(self, name: str):
        found = []
        for item in self.items:
            if not isinstance(item, ArmoredSection):
                continue
            if item.name == name:
                found.append(item)

        if len(found) == 1:
            return found[0]
        elif not found:
            return None
        else:
            raise ValueError(f"Found multiple '{name}'.")


class InvalidMessageArmorRadix64FormatException(ValueError):
    pass


class InvalidMessageArmorRadix64CheckException(ValueError):
    pass


class InvalidMessageNativeFormatException(ValueError):
    pass
