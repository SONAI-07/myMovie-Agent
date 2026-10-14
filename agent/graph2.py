import os
from typing import Any, Dict, List
from dotenv import load_dotenv
from langchain_sarvam import ChatSarvam

try:
    from agent.global_state import GlobalState
    from agent.nodes.movie_curator import CuratedList
except ImportError:
    from global_state import GlobalState
    from nodes.movie_curator import CuratedList

load_dotenv()

# Evaluated Cinephile Spark Matrix: 5 distinctive films people love to binge after watching iconic titles
CINEPHILE_SPARK_EVALS: Dict[str, List[Dict[str, Any]]] = {
    "shutter island": [
        {
            "title": "Memento",
            "release_year": 2000,
            "thematic_connection": "Dissects fractured memory and agonizing guilt through an inverted timeline where you can trust nothing.",
            "spark_reason": "Reverse-narrative puzzle box that forces you to experience the protagonist's profound disorientation."
        },
        {
            "title": "The Prestige",
            "release_year": 2006,
            "thematic_connection": "Channels the obsessive dread of illusion, stolen identity, and the devastating price of self-deception.",
            "spark_reason": "A masterwork of cinematic misdirection where the sacrifice for the 'trick' leaves you speechless."
        },
        {
            "title": "Black Swan",
            "release_year": 2010,
            "thematic_connection": "A chilling sensory descent into paranoia, psychological duality, and perfectionism untethered from reality.",
            "spark_reason": "Intense claustrophobic pressure that makes you question what is hallucination and what is real."
        },
        {
            "title": "Primal Fear",
            "release_year": 1996,
            "thematic_connection": "A razor-sharp psychological duel exploring trauma, fabricated innocence, and calculated deception.",
            "spark_reason": "One of the most jaw-dropping climax revelations in modern thriller history."
        },
        {
            "title": "Coherence",
            "release_year": 2013,
            "thematic_connection": "A dinner party during a passing comet collapses into paranoia and splintering alternate realities.",
            "spark_reason": "Minimalist, brain-bending indie that proves existential dread needs only great writing and paranoia."
        }
    ],
    "interstellar": [
        {
            "title": "Arrival",
            "release_year": 2016,
            "thematic_connection": "Explores non-linear time, communication, and embracing sorrow for the sake of profound love.",
            "spark_reason": "A deeply emotional hard-sci-fi journey that reframes human perspective on destiny and grief."
        },
        {
            "title": "Solaris",
            "release_year": 1972,
            "thematic_connection": "Confronts human consciousness and the haunting manifestation of past guilt in deep space.",
            "spark_reason": "Meditative, haunting, and philosophically profound reflection on what humans seek among the stars."
        },
        {
            "title": "Contact",
            "release_year": 1997,
            "thematic_connection": "The collision of relentless scientific truth, personal faith, and humanity's yearning for the infinite.",
            "spark_reason": "Carl Sagan's masterpiece of awe and intellectual wonder that stays with you forever."
        },
        {
            "title": "The Fountain",
            "release_year": 2006,
            "thematic_connection": "An epic odyssey across centuries exploring love's immortality and the acceptance of death.",
            "spark_reason": "Stunning visuals and Clint Mansell's transcendent score create an emotional catharsis."
        },
        {
            "title": "Gattaca",
            "release_year": 1997,
            "thematic_connection": "The triumph of the human spirit over genetic determinism in an indifferent, calibrated world.",
            "spark_reason": "Quietly devastating neo-noir sci-fi featuring one of the most inspirational lines in cinema."
        }
    ],
    "whiplash": [
        {
            "title": "Black Swan",
            "release_year": 2010,
            "thematic_connection": "The relentless, bloody obsession with artistic perfection pushing past the brink of sanity.",
            "spark_reason": "Kinetic, terrifying energy exploring the ultimate cost of artistic transcendence."
        },
        {
            "title": "Nightcrawler",
            "release_year": 2014,
            "thematic_connection": "Chilling portrait of single-minded sociopathic ambition thriving in the underbelly of media.",
            "spark_reason": "Jake Gyllenhaal's mesmerizing, predatory performance creates an unsettling rush."
        },
        {
            "title": "Sound of Metal",
            "release_year": 2019,
            "thematic_connection": "A visceral sonic journey of a drummer confronting the sudden loss of identity and learning stillness.",
            "spark_reason": "Revolutionary sound design that pulls you directly inside the protagonist's auditory struggle."
        },
        {
            "title": "The Novice",
            "release_year": 2021,
            "thematic_connection": "Obsessive, self-destructive drive in collegiate rowing that mirrors Andrew Neiman's drumming mania.",
            "spark_reason": "Raw, unrelenting physical and psychological examination of unhealthy dedication."
        },
        {
            "title": "Foxcatcher",
            "release_year": 2014,
            "thematic_connection": "A toxic mentor-mentee dynamic rooted in isolation, wealth, and psychological manipulation.",
            "spark_reason": "Chilling, slow-burn tension showing how power corrupts mentorship."
        }
    ],
    "inception": [
        {
            "title": "Paprika",
            "release_year": 2006,
            "thematic_connection": "Visually boundless exploration of subconscious dreams colliding with waking reality.",
            "spark_reason": "Satoshi Kon's animated fever dream that inspired modern cinematic surrealism."
        },
        {
            "title": "Dark City",
            "release_year": 1998,
            "thematic_connection": "A nightmarish metropolis where architects alter memories and physical architecture each midnight.",
            "spark_reason": "Neo-noir existential sci-fi with breathtaking gothic world-building."
        },
        {
            "title": "The Game",
            "release_year": 1997,
            "thematic_connection": "A wealthy loner's life dismantled by a reality-altering, paranoid game with unknown rules.",
            "spark_reason": "David Fincher keeps you gasping at every turn as reality constantly shifts."
        },
        {
            "title": "Source Code",
            "release_year": 2011,
            "thematic_connection": "High-octane investigation inside the final 8 minutes of another man's consciousness.",
            "spark_reason": "Smart, tight, emotionally resonant sci-fi thriller with tremendous momentum."
        },
        {
            "title": "Enemy",
            "release_year": 2013,
            "thematic_connection": "Hypnotic psychological descent into identity, duality, and subconscious repression.",
            "spark_reason": "Denis Villeneuve crafts an intoxicating riddle with one of cinema's most famous final shots."
        }
    ]
}


def get_fallback_sparks(movie_watched: str, primary_theme: str) -> List[Dict[str, Any]]:
    """Evaluates and returns 5 distinctive movies that add an undeniable spark to life."""
    key = movie_watched.lower().strip()
    if key in CINEPHILE_SPARK_EVALS:
        return CINEPHILE_SPARK_EVALS[key]

    # Universal high-voltage cinephile curated spark set
    return [
        {
            "title": "Memento",
            "release_year": 2000,
            "thematic_connection": f"A mind-bending psychological journey that matches the intensity of '{movie_watched}' with unmatched structural brilliance.",
            "spark_reason": "Unlocks a fresh dimension of unreliable perspective and suspense."
        },
        {
            "title": "The Prestige",
            "release_year": 2006,
            "thematic_connection": f"Explores sacrifice, obsession, and the hidden cost of ambition echoing '{movie_watched}'.",
            "spark_reason": "A masterclass in narrative tension and misdirection."
        },
        {
            "title": "Arrival",
            "release_year": 2016,
            "thematic_connection": f"Deep emotional resonance exploring communication, time, and human love alongside the themes of '{movie_watched}'.",
            "spark_reason": "Philosophically elevating and deeply moving."
        },
        {
            "title": "Coherence",
            "release_year": 2013,
            "thematic_connection": f"An unpredictable, reality-bending indie thrill that keeps your mind racing after '{movie_watched}'.",
            "spark_reason": "Proof that raw conceptual brilliance creates the most unforgettable sparks."
        },
        {
            "title": "Black Swan",
            "release_year": 2010,
            "thematic_connection": f"Sensory and psychological commitment that matches the stakes and emotional weight of '{movie_watched}'.",
            "spark_reason": "Visceral, breathless descent into perfection and duality."
        }
    ]


async def movies_extract(state: GlobalState) -> Dict[str, Any]:
    """
    Node 2: Curates 3 to 5 films that people passionately love to watch after this movie,
    adding a distinctive spark rather than just superficial genre copies.
    """
    movie_watched = state.get("movie_watched", "Unknown").strip()
    primary_theme = state.get("primary_theme", "Deep emotional conflict").strip()
    dominant_emotion = state.get("dominant_emotion", "Existential resonance").strip()
    cinematic_style = state.get("cinematic_style", "Cinematic drama").strip()

    print(f"[Node 2] Curating after-watch spark films for: '{movie_watched}'")

    sarvam_key = os.getenv("SARVAM_API_KEY")

    if sarvam_key:
        try:
            llm = ChatSarvam(model="sarvam-105b", reasoning_effort="high")
            structured_output = llm.with_structured_output(CuratedList)

            prompt = (
                "You are an elite, world-class film curator and cinephile creating an autonomous spark experience.\n"
                f"A user just finished watching '{movie_watched}'.\n"
                f"- Emotional Profile: {dominant_emotion}\n"
                f"- Primary Theme: {primary_theme}\n"
                f"- Style: {cinematic_style}\n\n"
                "OBJECTIVE:\n"
                "Do NOT merely recommend superficial lookalikes. Curate 3 to 5 distinctive, highly acclaimed movies "
                f"that people passionately LOVE to watch after '{movie_watched}'. These films can be set in completely "
                "different eras or worlds, but must deliver the same intense psychological thrill, thematic brilliance, "
                "or mind-bending high, adding a genuine spark to their life.\n\n"
                "CONSTRAINTS:\n"
                f"1. Do NOT recommend '{movie_watched}' or its direct sequels.\n"
                "2. Provide accurate release year for TMDB lookup.\n"
                "3. Explain in 1-2 sharp sentences why cinephiles obsess over watching this film next."
            )

            response: CuratedList = await structured_output.ainvoke(prompt)
            if response and getattr(response, "Recommended_Movies", None):
                curated = [
                    m.model_dump() if hasattr(m, "model_dump") else dict(m)
                    for m in response.Recommended_Movies
                ]
                if len(curated) >= 1:
                    return {"curated_movies": curated}

        except Exception as e:
            print(f"[Node 2] Sarvam curation error: {e}. Activating Evaluated Cinephile Spark Suite.")

    # High-impact fallback eval suite ensuring the user is never left without recommendations
    fallback_recs = get_fallback_sparks(movie_watched, primary_theme)
    return {"curated_movies": fallback_recs}


class Agent_2:
    movies_extract = staticmethod(movies_extract)
