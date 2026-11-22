from bs4 import BeautifulSoup

NON_CONTENT_TAGS = ("script", "style", "noscript", "svg", "template", "iframe")


def _clean(text):
    return " ".join(text.split())


def parse_page(html):
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(NON_CONTENT_TAGS):
        tag.decompose()

    title = _clean(soup.title.get_text(" ", strip=True)) if soup.title else ""

    meta = soup.find("meta", attrs={"name": "description"})
    description = ""
    if meta and meta.has_attr("content"):
        description = _clean(meta["content"])

    headings = {"h1": [], "h2": [], "h3": []}
    for level in ("h1", "h2", "h3"):
        for tag in soup.find_all(level):
            text = _clean(tag.get_text(" ", strip=True))
            if text:
                headings[level].append(text)

    text = _clean(soup.get_text(" ", strip=True))

    return {
        "title": title,
        "description": description,
        "headings": headings,
        "text": text,
    }
