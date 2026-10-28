import math
import re
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from nltk.corpus import stopwords

STOPWORDS_PT = set(stopwords.words("portuguese"))
STOPWORDS_EN = set(stopwords.words("english"))

STOPWORDS = STOPWORDS_PT | STOPWORDS_EN


def RemoverAcentos(Texto: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFD", Texto) if unicodedata.category(c) != "Mn"
    )


def DividirTextoEmPalavras(Texto: str, RemoverStopWords: bool = True, AplicarRemocaoAcentos: bool = True):
    Texto = Texto.lower()
    if AplicarRemocaoAcentos:
        Texto = RemoverAcentos(Texto)
    Tokens = re.findall(r"[a-z0-9]+", Texto) if AplicarRemocaoAcentos else re.findall(r"\w+", Texto)
    if RemoverStopWords:
        sw = {RemoverAcentos(w) for w in STOPWORDS} if AplicarRemocaoAcentos else STOPWORDS
        Tokens = [t for t in Tokens if t not in sw and len(t) > 1]
    return Tokens


def RadicalizarPalavra(Token: str) -> str:
    for suf in ("mente", "coes", "cao", "ando", "endo", "indo", "ados", "idos",
                "adas", "idas", "ado", "ido", "ada", "ida", "oes", "es", "s"):
        if Token.endswith(suf) and len(Token) - len(suf) >= 4:
            return Token[: -len(suf)]
    return Token


def PreProcesso(Texto: str, Opc: dict):
    Tokens = DividirTextoEmPalavras(
        Texto,
        RemoverStopWords=Opc.get("StopWords", True),
        AplicarRemocaoAcentos=Opc.get("Acentos", True),
    )
    if Opc.get("Radicaliar", True):
        Tokens = [RadicalizarPalavra(t) for t in Tokens]
    return Tokens

def CalculoDeVetorTFIDF(DocumentosTokens):
    n = len(DocumentosTokens)
    df = Counter()
    for Toks in DocumentosTokens:
        df.update(set(Toks))

    idf = {t: math.log((1 + n) / (1 + d)) + 1 for t, d in df.items()}
    vectors = []
    for Toks in DocumentosTokens:
        tf = Counter(Toks)
        total = len(Toks) or 1
        vectors.append({t: (c / total) * idf[t] for t, c in tf.items()})
    return vectors


def Cosseno(v1: dict, v2: dict) -> float:
    if not v1 or not v2:
        return 0.0
    Pequeno, Grande = (v1, v2) if len(v1) < len(v2) else (v2, v1)
    dot = sum(w * Grande.get(t, 0.0) for t, w in Pequeno.items())
    n1 = math.sqrt(sum(w * w for w in v1.values()))
    n2 = math.sqrt(sum(w * w for w in v2.values()))
    return dot / (n1 * n2) if n1 and n2 else 0.0


def Jaccard(t1, t2) -> float:
    s1, s2 = set(t1), set(t2)
    if not s1 and not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


def Ngrams(Tokens, n):
    return Counter(tuple(Tokens[i:i + n]) for i in range(len(Tokens) - n + 1))


def SobreposicaoNgram(t1, t2, n=2) -> float:
    g1, g2 = Ngrams(t1, n), Ngrams(t2, n)
    if not g1 or not g2:
        return 0.0
    inter = sum((g1 & g2).values())
    return 2 * inter / (sum(g1.values()) + sum(g2.values()))


def TrechosComuns(TextoA: str, TextoB: str, min_words=4, limit=10):
    pa = re.findall(r"\S+", TextoA)
    pb = re.findall(r"\S+", TextoB)
    Normalizar = lambda p: RemoverAcentos(re.sub(r"\W+", "", p.lower()))
    na, nb = [Normalizar(p) for p in pa], [Normalizar(p) for p in pb]
    sm = SequenceMatcher(None, na, nb, autojunk=False)
    Blocos = [b for b in sm.get_matching_blocks() if b.size >= min_words]
    Blocos.sort(key=lambda b: b.size, reverse=True)
    return [
        {"text": " ".join(pa[b.a:b.a + b.size]), "words": b.size}
        for b in Blocos[:limit]
    ]


def TermosComunsPrincipal(v1: dict, v2: dict, k=10):
    Compartilhado = set(v1) & set(v2)
    Ordenacao = sorted(Compartilhado, key=lambda t: v1[t] * v2[t], reverse=True)
    return Ordenacao[:k]


def Classificacao(Score: float) -> str:
    if Score >= 0.85:
        return "Praticamente idênticos"
    if Score >= 0.60:
        return "Muito similar"
    if Score >= 0.35:
        return "Moderadamente similar"
    if Score >= 0.15:
        return "Pouco similar"
    return "Sem similaridade"


PESOS = {"Cosseno": 0.5, "Jaccard": 0.2, "SobreposicaoNgram": 0.3}


def CompararTexto(TextoA: str, TextoB: str, Opc: dict | None = None) -> dict:
    Opc = Opc or {}
    ta, tb = PreProcesso(TextoA, Opc), PreProcesso(TextoB, Opc)
    va, vb = CalculoDeVetorTFIDF([ta, tb])
    cos = Cosseno(va, vb)
    jac = Jaccard(ta, tb)
    ngr = SobreposicaoNgram(ta, tb, 2)
    SimilaridadeCombinada = PESOS["Cosseno"] * cos + PESOS["Jaccard"] * jac + PESOS["SobreposicaoNgram"] * ngr
    return {
        "Cosseno": round(cos, 4),
        "Jaccard": round(jac, 4),
        "SobreposicaoNgram": round(ngr, 4),
        "SimilaridadeCombinada": round(SimilaridadeCombinada, 4),
        "Classificacao": Classificacao(SimilaridadeCombinada),
        "TermosComuns": TermosComunsPrincipal(va, vb),
        "TrechosComuns": TrechosComuns(TextoA, TextoB),
        "Estatisticas": {
            "TokensA": len(ta), "TokensB": len(tb),
            "UniqueA": len(set(ta)), "UniqueB": len(set(tb)),
            "TermosUnicos": len(set(ta) & set(tb)),
        },
    }


def CompararMultiplos(texts: list[str], Opc: dict | None = None) -> dict:
    Opc = Opc or {}
    Toks = [PreProcesso(t, Opc) for t in texts]
    Vetor = CalculoDeVetorTFIDF(Toks)
    n = len(texts)
    Matriz = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
    Pares = []
    for i in range(n):
        for j in range(i + 1, n):
            c = Cosseno(Vetor[i], Vetor[j])
            j_ = Jaccard(Toks[i], Toks[j])
            b = SobreposicaoNgram(Toks[i], Toks[j], 2)
            SimilaridadeCombinada = PESOS["Cosseno"] * c + PESOS["Jaccard"] * j_ + PESOS["SobreposicaoNgram"] * b
            Matriz[i][j] = Matriz[j][i] = round(SimilaridadeCombinada, 4)
            Pares.append({"a": i, "b": j, "Score": round(SimilaridadeCombinada, 4), "Classificacao": Classificacao(SimilaridadeCombinada)})
    Pares.sort(key=lambda p: p["Score"], reverse=True)
    return {"Matriz": Matriz, "Classificacao": Pares}
