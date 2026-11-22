import re
from collections import Counter

STOPWORDS = frozenset(
    """
    a about above after again against all am an and any are aren't as at be because
    been before being below between both but by can cannot could couldn't did didn't
    do does doesn't doing don't down during each few for from further had hadn't has
    hasn't have haven't having he he'd he'll he's her here here's hers herself him
    himself his how how's i i'd i'll i'm i've if in into is isn't it it's its itself
    let's me more most mustn't my myself no nor not of off on once only or other
    ought our ours ourselves out over own same shan't she she'd she'll she's should
    shouldn't so some such than that that's the their theirs them themselves then
    there there's these they they'd they'll they're they've this those through to
    too under until up very was wasn't we we'd we'll we're we've were weren't what
    what's when when's where where's which while who who's whom why why's will with
    won't would wouldn't you you'd you'll you're you've your yours yourself yourselves
    also just like get got one two new us way may might much many
    """.split()
)

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9'’\-]*")


def tokenize(text):
    tokens = []
    for match in TOKEN_RE.finditer(text.lower()):
        token = match.group(0).strip("'-")
        if token and token not in STOPWORDS and not token.isdigit():
            tokens.append(token)
    return tokens


def _ngrams(tokens, n):
    return [tuple(tokens[i : i + n]) for i in range(len(tokens) - n + 1)]


def _format(counter, top):
    parts = []
    for gram, count in counter.most_common(top):
        text = gram if isinstance(gram, str) else " ".join(gram)
        parts.append(f"{text} ({count})")
    return ", ".join(parts)


def analyze_text(text, top=20):
    tokens = tokenize(text)
    words = Counter(tokens)
    bigrams = Counter(_ngrams(tokens, 2))
    trigrams = Counter(_ngrams(tokens, 3))
    return {
        "char_count": len(text),
        "word_count": len(tokens),
        "top_words": _format(words, top),
        "top_bigrams": _format(bigrams, top),
        "top_trigrams": _format(trigrams, top),
        "words": words,
        "bigrams": bigrams,
        "trigrams": trigrams,
    }
