class Packet:
    """
    A PGP Message Packet.

    Ref: https://datatracker.ietf.org/doc/html/rfc4880#section-4
    """

    header: str
    body: str

    def __str__(self):
        return self.header
