import re
import nltk

try:
    from nltk.corpus import stopwords
    STOP = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    from nltk.corpus import stopwords
    STOP = set(stopwords.words("english"))

TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z\-]+")

def tokenize(text: str) -> list[str]:
    """
    Converte texto para minúsculas, remove pontuação/stopwords e retorna tokens.
    """
    text = text.lower()
    tokens = TOKEN_RE.findall(text)
    return [t for t in tokens if t not in STOP and len(t) > 2]
