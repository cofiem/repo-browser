import attrs
import parsel
import logging

logger = logging.getLogger(__name__)

@attrs.frozen
class HtmlListing:
    """A html page that lists the contents of a directory."""

    url: str
    links: list[str]

    @classmethod
    def from_html(cls, url: str, html: str) -> "HtmlListing":
        selector = parsel.Selector(text=html)

        links = []

        logger.debug("html listing links on %s", url)
        seen_parent = False
        options = ["..", "../", "parent directory"]
        for link in selector.css("a"):
            name = link.css("::text").get().strip().casefold()
            link_url = link.attrib["href"]
            logger.debug("html listing link: %s - %s", name, link_url)
            if not seen_parent and name not in options and link_url not in options:
                logger.debug("html listing link ignore: %s - %s", name, link_url)
                continue
            elif name in options or link_url in options:
                seen_parent = True
                logger.debug("html listing link parent: %s - %s", name, link_url)
                continue
            elif link_url.startswith("http") and not link_url.startswith(self.url):
                logger.debug("html listing link ignore external: %s - %s", name, link_url)
                continue
            else:
                links.append(link_url.strip().strip("/"))

        if seen_parent is not True:
            raise ValueError("Unknown html directory listing format.")

        return HtmlListing(url=url, links=links)