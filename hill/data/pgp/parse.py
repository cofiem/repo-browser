from pathlib import Path
from typing import Optional


class Parse:

    # "five (5) dashes ('-', 0x2D)"
    header_line_delim = "-----"
    header_line_start = "BEGIN"
    header_line_end = "END"
    header_line_pgp = "PGP"
    header_line_clear_text = "SIGNED MESSAGE"
    header_line_signature = "SIGNATURE"
    header_line_public_key = "PUBLIC KEY BLOCK"
    header_line_encoded = [header_line_signature, header_line_public_key]
    header_sep = ":"

    def read_file(self, path: Path):
        return self.read_str(path.read_text(encoding="utf-8"))

    def read_str(self, content: str):
        return self.read_lines(content.splitlines())

    def read_document(self, lines: list[str]):
        """Read a document."""
        doc_name = None
        doc_headers = {}
        doc_data = []
        doc_crc = None
        doc_data_crc = None
        doc_crc_result = False

        seen_header_blank_line = False
        seen_header_end = False

        for line in lines:
            line_tidy = self.line_tidy(line)

            # "An Armor Header Line, appropriate for the type of data"
            name_start, name_text = self.name(line_tidy)
            if name_start is True and name_text is not None:
                if doc_name:
                    raise ValueError(
                        f"The name was already set to '{doc_name}', but another name was found '{name_text}'."
                    )
                doc_name = name_text
                continue
            elif not seen_header_end and name_start is False and name_text == doc_name:
                seen_header_end = True
                continue
            elif name_start is not None:
                raise ValueError(f"Unexpected header line '{line}'.")

            # "A blank (zero-length, or containing only whitespace) line"
            if not seen_header_blank_line and not line_tidy:
                seen_header_blank_line = True
                continue

            # "Armor Headers"
            if not seen_header_blank_line:
                header_key, header_value = self.header(line_tidy)
                if header_key:
                    header_value = doc_headers.get(header_key, "") + " " + header_value
                    doc_headers[header_key] = header_value.strip()
                    continue

            if line_tidy:
                # "OpenPGP's Radix-64 encoding is composed of two parts: a base64
                #    encoding of the binary data and a checksum.
                # The checksum is a 24-bit Cyclic Redundancy Check (CRC) converted to
                #    four characters of radix-64 encoding by the same MIME base64
                #    transformation, preceded by an equal sign (=).  The CRC is computed
                #    by using the generator 0x864CFB and an initialization of 0xB704CE.
                #    The accumulation is done on the data before it is converted to
                #    radix-64, rather than on the converted data.
                # The checksum with its leading equal sign MAY appear on the first line
                #    after the base64 encoded data."
                is_encoded = doc_name in self.header_line_encoded
                is_crc_line = line_tidy.startswith("=")
                if doc_crc:
                    raise ValueError(f"Found unexpected line after CRC line: '{line}'.")

                elif not is_encoded:
                    if line_tidy.startswith("- "):
                        # "When reversing dash-escaping, an implementation MUST strip the string
                        #    "- " if it occurs at the beginning of a line
                        line_tidy = line_tidy[2:]
                    elif line_tidy.startswith("-"):
                        # TODO: "SHOULD warn on "-" and any character other than a space at the beginning of a line."
                        pass
                    doc_data.append(line_tidy)

                elif is_encoded and not is_crc_line:
                    line_data = self.decode_radix64(line_tidy + "\r\n")
                    doc_data.append(line_data)

                else:
                    doc_crc = self.get_crc(line_tidy)
                continue

        if doc_crc is not None:
            doc_data_all = b"".join(doc_data)
            doc_data_crc = self.run_crc(doc_data_all)
            doc_crc_result = doc_data_crc == doc_crc
            if not doc_crc_result:
                raise ValueError(
                    f"Expected CRC '{doc_crc}' actual CRC '{doc_data_crc}'."
                )

        # TODO
        # "As with binary signatures on text documents, a cleartext signature is
        #    calculated on the text using canonical <CR><LF> line endings.  The
        #    line ending (i.e., the <CR><LF>) before the '-----BEGIN PGP
        #    SIGNATURE-----' line that terminates the signed text is not
        #    considered part of the signed text."

        pass

    # Radix-64 is identical to the "Base64" encoding described from MIME, with the addition of an optional 24-bit CRC. The checksum is calculated on the input data before encoding; the checksum is then encoded with the same Base64 algorithm and, using an additional "=" symbol as separator, appended to the encoded output data.

    def name(self, line: str):
        """
        An Armor Header Line consists of the appropriate header line text
        surrounded by five (5) dashes ('-', 0x2D) on either side of the
        header line text.  The header line text is chosen based upon the type
        of data that is being encoded in Armor, and how it is being encoded.

        Args:
            line: Parse this line as An Armor Header Line.

        Returns:
            The return value is a two-tuple containing
                whether the name is a start or end, and the parsed name.
                Both are :obj:`None` if the name could not be parsed.
        """

        line_tidy = self.line_tidy(line)

        # "surrounded by five (5) dashes ('-', 0x2D) on either side of the header line text"
        if not line_tidy.startswith(self.header_line_delim):
            return None, None
        if not line_tidy.endswith(self.header_line_delim):
            return None, None

        # "appropriate header line text"
        line_tidy = line_tidy.strip("-")
        name = self.name_start(line_tidy)
        if name:
            return True, name
        name = self.name_end(line_tidy)
        if name:
            return False, name

        # header line is formatted correctly, but not recognised
        return None, None

    def name_start(self, line: str) -> Optional[str]:
        """
        Extract the start header line.

        Args:
            line: a line of the document.

        Returns:
            The start header line if present, otherwise None.
        """

        line_tidy = self.line_tidy(line)
        delimiter_start = f"{self.header_line_start} {self.header_line_pgp} "
        if line_tidy.startswith(delimiter_start):
            offset = len(delimiter_start)
            return line_tidy[offset:]
        return None

    def name_end(self, line: str):
        """
        Extract the end header line.

        Args:
            line: a line of the document.

        Returns:
            The end header line if present, otherwise None.
        """

        line_tidy = self.line_tidy(line)
        delimiter_start = f"{self.header_line_end} {self.header_line_pgp} "
        if line_tidy.startswith(delimiter_start):
            offset = len(delimiter_start)
            return line_tidy[offset:]
        return None

    def header(self, line: str):
        """
        Extract a header key and value.

        Args:
            line: a line of the document.

        Returns:
            The header key and value if present, otherwise None, None.
        """

        line_tidy = self.line_tidy(line)
        if self.header_sep not in line_tidy:
            return None, None
        key, value = line_tidy.split(self.header_sep, maxsplit=1)
        return key.strip(), value.strip()
