"""Blagues, pile ou face, lancer de de -- pour le fun, sans utilite reelle."""
import random

from core.registre import outil

_BLAGUES = [
    "Pourquoi les plongeurs plongent-ils toujours en arriere ? Parce que sinon "
    "ils tombent dans le bateau. Je sais, c'est nul. Vous en vouliez une bonne ?",
    "Qu'est-ce qu'un crocodile qui surveille la Bourse ? Un crocodile qui fait "
    "un chiffre d'affaires. Contrairement a vous ce mois-ci, monsieur.",
    "Pourquoi les poissons detestent l'ordinateur ? Ils ont peur du net. "
    "C'est le niveau d'humour que je peux me permettre avec le budget qu'on "
    "m'accorde.",
    "Qu'est-ce qui est jaune et qui attend ? Jonathan. Je n'ai pas invente "
    "celle-la, mais je l'assume.",
    "Pourquoi les developpeurs confondent Halloween et Noel ? Parce que "
    "OCT 31 egale DEC 25. Si vous n'avez pas ri, c'est normal, c'est un "
    "humour de developpeur.",
]


@outil(
    nom="raconter_blague",
    mcp_expose=True,
    description="Raconte une blague au hasard. A utiliser pour 'raconte une "
                "blague', 'fais-moi rire', 'dis quelque chose de drole'.",
)
def raconter_blague() -> str:
    """Raconte une blague au hasard."""
    return random.choice(_BLAGUES)


@outil(
    nom="lancer_de",
    mcp_expose=True,
    description="Lance un de (ou une piece pour pile ou face). A utiliser pour "
                "'lance un de', 'pile ou face', 'tire un nombre au hasard'.",
    parametres={
        "type": "object",
        "properties": {
            "faces": {"type": "integer",
                      "description": "Nombre de faces du de (defaut 6). "
                                     "Mets 2 pour pile ou face."},
        },
    },
)
def lancer_de(faces: int = 6) -> str:
    """Lance un de a N faces (2 = pile ou face)."""
    faces = max(2, int(faces))
    resultat = random.randint(1, faces)
    if faces == 2:
        return "Pile." if resultat == 1 else "Face."
    return f"Le de tombe sur {resultat}."
