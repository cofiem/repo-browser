from struct import unpack

from hill.data.pgp.item.message import Message


class Packets:
    def read_message(self, message: Message):
        """"""
        packet_header = self.read_header(message.data)
        raise NotImplementedError()

    def read_header(self, data: bytes):
        """"""
        packet_tag = self.read_tag(data)
        raise NotImplementedError()

    def read_tag(self, data: bytes):
        """
        "The first octet of the packet header is called the "Packet Tag".
        It determines the format of the header and denotes the packet contents."
        """
        first_octet = ord(data[0:1])

        # "Bit 7 -- Always one"
        # Bitwise and 128 / 0x80 / 0b1000 0000
        bit7 = first_octet & 0x80
        if bit7 != 0x80:
            raise ValueError()

        # "Bit 6 -- New packet format if set"
        # Bitwise and 64 / 0x40 / 0b0100 0000
        bit6 = first_octet & 0x40
        is_new_format = bit6 == 0x40

        # read the packet tag
        if is_new_format:
            tag, packet_length, header_length = self.read_tag_new(data)
        else:
            tag, packet_length, header_length = self.read_tag_old(data)

    def read_tag_old(self, data: bytes):
        """"""
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
            packet_length = unpack("!H", data[1:3])[0]
            header_length = 3

        elif length_type == 2:
            # "2 - The packet has a four-octet length.  The header is 5 octets long."
            packet_length = unpack("!L", data[1:5])[0]
            header_length = 5

        elif length_type == 3:
            # "3 - The packet is of indeterminate length.  The header is 1 octet long."
            packet_length = None
            header_length = 1

        else:
            raise ValueError()

        return tag, packet_length, header_length

    def read_tag_new(self, data: bytes):
        """"""

        # "Bits 5-0 -- packet tag"
        # Bitwise and 63 / 0x3F / 0b0011 1111
        tag = ord(data[0:1]) & 0x3F

        # "The remainder of the packet header is the length of the packet."
        first_header_octet = ord(data[1:2])
        second_header_octet = ord(data[2:3])

        if first_header_octet < 192:
            # "A one-octet Body Length header encodes packet lengths of up to 191 octets."
            # "This type of length header is recognized because the one octet value is less than 192."
            packet_length = first_header_octet
            header_length = 1

        elif 192 <= first_header_octet <= 223:
            # "A two-octet Body Length header encodes packet lengths of 192 to 8383 octets."
            # "It is recognized because its first octet is in the range 192 to 223."
            packet_length = (
                ((first_header_octet - 192) << 8) + second_header_octet + 192
            )
            header_length = 2

        elif first_header_octet == 255:
            # "A five-octet Body Length header encodes packet lengths of up to
            # 4,294,967,295 (0xFFFFFFFF) octets in length."
            # "A five-octet Body Length header consists of a single octet holding the value 255,
            # followed by a four-octet scalar."
            packet_length = unpack("!L", data[2:6])[0]
            header_length = 5

        elif 244 <= first_header_octet < 255:
            # "When the length of the packet body is not known in advance by the issuer,
            # Partial Body Length headers encode a packet of indeterminate length, effectively making it a stream."
            # "A Partial Body Length header is one octet long and encodes the length of only part of the data packet."
            # This length is a power of 2, from 1 to 1,073,741,824 (2 to the 30th power).
            # It is recognized by its one octet value that is greater than or equal to 224, and less than 255."
            packet_length = 1 << (first_header_octet & 0x1F)
            header_length = 1

            raise NotImplementedError()

        else:
            raise ValueError()

        return tag, packet_length, header_length
