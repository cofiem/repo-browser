from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Message:
    """
    One ASCII Armor item.

    Ref: https://datatracker.ietf.org/doc/html/rfc4880#section-6.2
    """

    name: Optional[str] = None
    """The parsed Armor Header Line."""

    data: Optional[bytes] = None
    """The decoded ASCII-Armored data."""

    checksum: Optional[int] = None
    """The decoded Armor Checksum."""

    header_version: Optional[str] = None
    """
    "Version", which states the OpenPGP implementation and version
    used to encode the message.
    """

    header_comment: Optional[str] = None
    """
    "Comment", a user-defined comment.  OpenPGP defines all text to
    be in UTF-8.  A comment may be any UTF-8 string.  However, the
    whole point of armoring is to provide seven-bit-clean data.
    Consequently, if a comment has characters that are outside the
    US-ASCII range of UTF, they may very well not survive transport.
    """

    header_message_id: Optional[str] = None
    """
    "MessageID", a 32-character string of printable characters.  The
    string must be the same for all parts of a multi-part message
    that uses the "PART X" Armor Header.  MessageID strings should be
    unique enough that the recipient of the mail can associate all
    the parts of a message with each other.  A good checksum or
    cryptographic hash function is sufficient.
    
    The MessageID SHOULD NOT appear unless it is in a multi-part
    message.  If it appears at all, it MUST be computed from the
    finished (encrypted, signed, etc.) message in a deterministic
    fashion, rather than contain a purely random value.  This is to
    allow the legitimate recipient to determine that the MessageID
    cannot serve as a covert means of leaking cryptographic key
    information.
    """

    header_hashes: Optional[list[str]] = field(default_factory=list)
    """
    "Hash", a comma-separated list of hash algorithms used in this
    message.  This is used only in cleartext signed messages.
    """

    header_charset: Optional[str] = "UTF-8"
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

    def __str__(self):
        result = [
            self.name,
            f"data length: '{len(self.data)}'",
        ]
        if self.header_version:
            result.append(f"Version: '{self.header_version}'")
        elif self.header_comment:
            result.append(f"Comment: '{self.header_comment}'")
        elif self.header_charset:
            result.append(f"Charset: '{self.header_charset}'")
        return ", ".join(result)
