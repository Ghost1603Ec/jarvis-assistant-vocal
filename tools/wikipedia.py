"""Wikipedia hors-ligne (fichier ZIM via libzim) : recherche et lecture d'articles.

Necessite data/wikipedia/wikipedia_fr_all_mini_*.zim (voir config.yaml :
wikipedia.zim si tu veux un chemin different du defaut)."""
import glob
from pathlib import Path

from core.config import reglage
from core.registre import outil

_ARCHIVE = None
_INTROUVABLE = ("Le fichier Wikipedia hors-ligne est introuvable. Verifie qu'il "
                "est bien dans data/wikipedia/.")


def _chemin_zim():
    """Chemin du .zim : config explicite, sinon le premier trouve dans data/wikipedia/."""
    p = reglage("wikipedia.zim", "")
    if p and Path(p).exists():
        return p
    base = Path(__file__).resolve().parent.parent / "data" / "wikipedia"
    trouves = sorted(glob.glob(str(base / "wikipedia_fr_all_mini_*.zim")))
    return trouves[-1] if trouves else None


def _archive():
    """Ouvre le fichier ZIM une seule fois (mise en cache)."""
    global _ARCHIVE
    if _ARCHIVE is not None:
        return _ARCHIVE
    chemin = _chemin_zim()
    if not chemin:
        return None
    try:
        from libzim.reader import Archive
        _ARCHIVE = Archive(chemin)
    except Exception:
        _ARCHIVE = None
    return _ARCHIVE


def _chercher_titre(archive, terme, nb=5):
    """Cherche les entrees dont le titre correspond, renvoie une liste d'Entry."""
    from libzim.search import Query, Searcher
    searcher = Searcher(archive)
    recherche = searcher.search(Query().set_query(terme))
    resultats = []
    for chemin in recherche.getResults(0, nb):
        try:
            entree = archive.get_entry_by_path(chemin)
            if entree.is_redirect:
                entree = entree.get_redirect_entry()
            resultats.append(entree)
        except Exception:
            continue
    return resultats


@outil(
    nom="chercher_wikipedia",
    mcp_expose=True,
    description="Cherche un article dans la base Wikipedia hors-ligne (fonctionne "
                "sans internet) et renvoie son texte a resumer a voix haute. A "
                "utiliser pour toute question encyclopedique : definitions, "
                "personnages historiques, sciences, geographie, etc.",
    parametres={
        "type": "object",
        "properties": {
            "sujet": {"type": "string", "description": "Le sujet ou terme a chercher"},
        },
        "required": ["sujet"],
    },
    lent=True,
    phrase_attente="Je regarde dans Wikipedia.",
)
def chercher_wikipedia(sujet: str) -> str:
    """Cherche un article dans le ZIM Wikipedia et renvoie son texte (pour resume par le LLM)."""
    archive = _archive()
    if archive is None:
        return _INTROUVABLE

    try:
        entrees = _chercher_titre(archive, sujet, nb=3)
    except Exception as e:
        return f"Recherche Wikipedia impossible : {e}"

    if not entrees:
        return f"Aucun article trouve pour '{sujet}'."

    entree = entrees[0]
    try:
        item = entree.get_item()
        html = bytes(item.content).decode("utf-8", errors="ignore")
    except Exception as e:
        return f"Impossible de lire l'article : {e}"

    try:
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "sup", "table"]):
            tag.decompose()
        texte = " ".join(soup.get_text(separator=" ").split())
    except Exception:
        texte = html

    titre = entree.title or sujet
    return f"Article Wikipedia « {titre} » : {texte[:2000]}"
