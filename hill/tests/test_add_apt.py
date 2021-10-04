import logging

from hill.tests.base_test_case import BaseTestCase
from io import StringIO
from django.core.management import call_command


class AddAptTestCase(BaseTestCase):

    urls = [
        # debian https
        "https://ftp.debian.org/debian/",
        "https://mirror.internet.asn.au/pub/debian/",
        # debian http
        # "http://mirror.aarnet.edu.au/pub/debian/",
        # ubuntu https
        "https://mirror.internet.asn.au/pub/ubuntu/archive/",
        "https://mirror.realcompute.io/ubuntu/",
        "https://mirror.datamossa.io/ubuntu/archive/",
        "https://ubuntu.mirror.digitalpacific.com.au/archive/",
        # ubuntu http
        # "http://mirror.netspace.net.au/pub/ubuntu/",
        # "http://ftp.iinet.net.au/pub/ubuntu/",
        # "http://mirror.aarnet.edu.au/pub/ubuntu/archive/",
        # "http://mirror.internode.on.net/pub/ubuntu/ubuntu/",
        # "http://mirror.intergrid.com.au/ubuntu/",
        # "http://ubuntu.mirror.serversaustralia.com.au/ubuntu/",
        # "http://mirror.overthewire.com.au/ubuntu/",
        # "http://archive.ubuntu.com/ubuntu/",
        # docker https
        "https://download.docker.com/linux/ubuntu/",
        # linux mint http
        # "http://packages.linuxmint.com",
    ]

    def setUp(self):
        self.maxDiff = None
        self._level = logging.INFO

    def test_command_output(self):
        for url in self.urls:
            with self.subTest(url=url):
                output = StringIO()
                call_command("add_apt", url, stdout=output)
                self.assertEqual(
                    output.getvalue().splitlines(),
                    [
                        "CAUTION! No public key supplied. Downloaded files will not be verified.",
                        f"Importing apt repository from url '{url}'.",
                        f"Found no distribution names.",
                        f"Found no flat repository files.",
                        "Finished importing apt repository.",
                    ],
                )
