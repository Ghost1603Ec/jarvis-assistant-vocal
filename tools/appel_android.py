"""Appel telephonique direct sur le telephone Android de l'utilisateur (via ADB).

Contrairement a tools/appels.py (Twilio, Jarvis parle a la place de l'utilisateur),
ici Jarvis compose juste le numero sur le VRAI telephone de l'utilisateur -- c'est
LUI qui parle ensuite. Necessite le debogage sans fil ADB deja appairé
(Parametres > Options developpeur > Debogage sans fil).

SECURITE : confirmation vocale obligatoire avant chaque appel (mecanisme Phase 0,
comme tools/appels.py). mcp_expose=False, et ajoute a _N3 dans core/registre.py :
jamais declenchable a distance via le pont iPhone, quoi qu'il arrive.
"""
import difflib
import re
import subprocess

from core.registre import outil
from core.util import sans_accents

_URI_CONTACTS = "content://com.android.contacts/data/phones"


def _decouvrir_service_mdns():
    """Cherche un service ADB decouvert par mDNS (debogage sans fil deja appaire)."""
    try:
        res = subprocess.run(["adb", "mdns", "services"], capture_output=True,
                             text=True, timeout=10)
    except Exception:
        return None
    for ligne in res.stdout.splitlines():
        if "_adb-tls-connect._tcp" in ligne:
            parts = ligne.split()
            if parts:
                return parts[0]
    return None


def assurer_connexion_adb():
    """A appeler au demarrage de Jarvis : tente de (re)etablir la connexion ADB
    avec le telephone. Non bloquant, ne leve jamais -- si indisponible,
    appeler_contact renverra simplement une erreur au moment de l'usage."""
    try:
        subprocess.run(["adb", "start-server"], capture_output=True, timeout=10)
        res = subprocess.run(["adb", "devices"], capture_output=True,
                             text=True, timeout=10)
        if any("\tdevice" in l for l in res.stdout.splitlines()):
            print("[appel_android] telephone deja connecte via ADB.")
            return
        service = _decouvrir_service_mdns()
        if service:
            subprocess.run(["adb", "connect", service], capture_output=True, timeout=10)
            print(f"[appel_android] connexion ADB tentee via {service}.")
        else:
            print("[appel_android] aucun telephone ADB detecte (debogage sans "
                  "fil probablement inactif ou telephone hors reseau).")
    except Exception as e:
        print(f"[appel_android] verification ADB impossible : {e}")


def _lister_appareils():
    """Renvoie la liste des identifiants d'appareils ADB actuellement 'device'."""
    try:
        res = subprocess.run(["adb", "devices"], capture_output=True,
                              text=True, timeout=5)
    except Exception:
        return []
    appareils = []
    for ligne in res.stdout.strip().splitlines()[1:]:
        ligne = ligne.strip()
        if "\t" not in ligne:
            continue
        ident, etat = ligne.split("\t")
        if etat == "device":
            appareils.append(ident)
    return appareils


def _cible_adb():
    """Choisit l'appareil a cibler : prefere l'identifiant mDNS (stable meme si
    l'IP ou le port changent) plutot que l'IP:port brut."""
    appareils = _lister_appareils()
    if not appareils:
        return None
    for a in appareils:
        if "_adb-tls-connect._tcp" in a:
            return a
    return appareils[0]


def _adb(*args):
    """Lance une commande adb sur l'appareil cible. Leve si aucun appareil connecte."""
    cible = _cible_adb()
    if cible is None:
        raise RuntimeError("Aucun telephone Android connecte via ADB "
                            "(verifie le debogage sans fil).")
    base = ["adb", "-s", cible]
    return subprocess.run(base + list(args), capture_output=True,
                          text=True, timeout=10)


def _lister_contacts():
    """Renvoie [(nom, numero), ...] depuis les contacts du telephone."""
    res = _adb("shell", "content", "query", "--uri", _URI_CONTACTS,
               "--projection", "display_name:data1")
    if res.returncode != 0:
        return []
    motif = re.compile(r"display_name=(.*), data1=(.*)$")
    contacts = []
    for ligne in res.stdout.splitlines():
        m = motif.search(ligne)
        if m:
            nom, numero = m.group(1).strip(), m.group(2).strip()
            if nom and numero:
                contacts.append((nom, numero))
    return contacts


def _chercher_contact(nom_demande):
    """Recherche floue (accents/emoji tolerants) du contact le plus proche."""
    contacts = _lister_contacts()
    cible = sans_accents(nom_demande.strip().lower())

    meilleur, score_max = None, 0.0
    for nom, numero in contacts:
        norme = sans_accents(nom.lower())
        if cible == norme:
            return (nom, numero)
        if cible in norme or norme in cible:
            score = 0.9
        else:
            score = difflib.SequenceMatcher(None, cible, norme).ratio()
        if score > score_max:
            meilleur, score_max = (nom, numero), score
    return meilleur if score_max >= 0.6 else None


@outil(
    nom="appeler_contact",
    mcp_expose=False,
    confirmation=False,
    description="Compose un appel telephonique SUR LE VRAI TELEPHONE de "
                "l'utilisateur (pas Jarvis qui parle -- c'est l'utilisateur qui "
                "va parler). A utiliser pour 'appelle X', 'telephone a X'.",
    parametres={
        "type": "object",
        "properties": {
            "nom": {
                "type": "string",
                "description": "Nom du contact a appeler, tel que dit par "
                               "l'utilisateur (ex: 'Marie', 'Papa').",
            },
        },
        "required": ["nom"],
    },
)
def appeler_contact(nom: str) -> str:
    """Cherche le contact et lance l'appel via ADB (ACTION_CALL)."""
    try:
        trouve = _chercher_contact(nom)
    except RuntimeError as e:
        return str(e)

    if trouve is None:
        return f"Contact introuvable : {nom}."

    nom_trouve, numero = trouve
    numero_propre = numero.replace(" ", "")

    try:
        res = _adb("shell", "am", "start", "-a", "android.intent.action.CALL",
                   "-d", f"tel:{numero_propre}",
                   "-p", "com.google.android.dialer")
    except RuntimeError as e:
        return str(e)

    sortie = (res.stdout or "") + (res.stderr or "")
    if res.returncode != 0 or "Error" in sortie:
        return (f"Le telephone a refuse l'appel vers {nom_trouve} "
                f"({sortie.strip()[:150]}).")
    return f"Appel de {nom_trouve} en cours."
