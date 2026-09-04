"""WhatsApp (via l'app Desktop installee, protocole whatsapp://).

WhatsApp ne permet a aucune app tierce d'envoyer un message ou de lancer un
appel de facon totalement automatique (protection anti-spam de Meta). Ces
outils ouvrent la conversation avec le contenu pre-rempli : l'envoi ou le
declenchement de l'appel reste un clic manuel de l'utilisateur.
"""
import os
import re
import urllib.parse

from core.registre import outil


def _normaliser_numero(numero: str) -> str:
    """Garde uniquement le + et les chiffres (format international attendu)."""
    return re.sub(r"[^\d+]", "", numero or "")


def _annonce_message(args):
    return f"Je prepare un message WhatsApp pour {args.get('numero', '')}."


@outil(
    nom="preparer_whatsapp_message",
    mcp_expose=True,
    description="Ouvre WhatsApp Desktop sur la conversation d'un numero, avec un "
                "message deja ecrit dans le champ de saisie. L'envoi reste un clic "
                "manuel de l'utilisateur (WhatsApp ne permet pas l'envoi automatique). "
                "A utiliser pour 'envoie un message whatsapp a...', 'prepare un "
                "whatsapp pour...'.",
    parametres={
        "type": "object",
        "properties": {
            "numero": {"type": "string",
                       "description": "Numero au format international, ex : +33612345678."},
            "message": {"type": "string", "description": "Texte du message a preparer."},
        },
        "required": ["numero", "message"],
    },
)
def preparer_whatsapp_message(numero: str, message: str = "") -> str:
    num = _normaliser_numero(numero)
    if not num:
        return "Numero invalide. Donne-le au format international, ex : +33612345678."
    url = f"whatsapp://send?phone={num}&text={urllib.parse.quote(message or '')}"
    try:
        os.startfile(url)
        return (f"J'ai ouvert WhatsApp sur la conversation avec {num}, message pret. "
                "Il ne reste qu'a cliquer sur envoyer.")
    except Exception as e:
        return f"Impossible d'ouvrir WhatsApp : {e}"


@outil(
    nom="preparer_whatsapp_appel",
    mcp_expose=True,
    description="Ouvre WhatsApp Desktop sur la conversation d'un numero, prete pour "
                "lancer un appel. Le declenchement de l'appel reste un clic manuel de "
                "l'utilisateur (WhatsApp ne permet pas de lancer un appel automatiquement). "
                "A utiliser pour 'appelle sur whatsapp', 'lance un appel whatsapp a...'.",
    parametres={
        "type": "object",
        "properties": {
            "numero": {"type": "string",
                       "description": "Numero au format international, ex : +33612345678."},
        },
        "required": ["numero"],
    },
)
def preparer_whatsapp_appel(numero: str) -> str:
    num = _normaliser_numero(numero)
    if not num:
        return "Numero invalide. Donne-le au format international, ex : +33612345678."
    url = f"whatsapp://send?phone={num}"
    try:
        os.startfile(url)
        return (f"J'ai ouvert WhatsApp sur la conversation avec {num}. "
                "Clique sur l'icone d'appel pour lancer l'appel.")
    except Exception as e:
        return f"Impossible d'ouvrir WhatsApp : {e}"
