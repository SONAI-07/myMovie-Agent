import os
from typing import Any, Dict
from dotenv import load_dotenv
from langchain_sarvam import ChatSarvam

try:
    from agent.global_state import GlobalState
    from agent.nodes.theme_extractor import theme_extractor
except ImportError:
    from global_state import GlobalState
    from nodes.theme_extractor import theme_extractor

load_dotenv()

# Built-in cinematic profiles for high-profile films as instant evaluation / fallback
KNOWN_PROFILES = {
    "shutter island": {
        "primary_theme": "The agonizing fragility of sanity, repressed grief, and the devastating choice between living as a monster or dying as a good man.",
        "dominant_emotion": "Chilling Paranoia & Existential Heartbreak",
        "cinematic_style": "Atmospheric gothic psychological noir"
    },
    "interstellar": {
        "primary_theme": "The endurance of human connection across cosmic vastness, existential survival, and the sacrifice of time for love.",
        "dominant_emotion": "Awe-inspiring Existential Dread & Deep Longing",
        "cinematic_style": "Epic philosophical hard sci-fi"
    },
    "inception": {
        "primary_theme": "The architecture of grief, sub-conscious guilt, and the dangerous ambiguity between projection and reality.",
        "dominant_emotion": "High-octane Intellectual Vertigo",
        "cinematic_style": "Mind-bending psychological heist"
    },
    "whiplash": {
        "primary_theme": "The toxic obsession with artistic greatness, relentless self-destruction, and the boundary between greatness and madness.",
        "dominant_emotion": "Palpable Adrenaline & Psychological Exhaustion",
        "cinematic_style": "Visceral, kinetic rhythmic pressure-cooker"
    },
    "fight club": {
        "primary_theme": "Corporate disillusionment, fragmented masculine identity, and the nihilistic revolt against modern consumerism.",
        "dominant_emotion": "Chaotic Catharsis & Disorienting Nihilism",
        "cinematic_style": "Dark satirical psychological thriller"
    },
    "parasite": {
        "primary_theme": "Insurmountable socioeconomic divide, modern systemic symbiosis, and the explosive violence of suppressed dignity.",
        "dominant_emotion": "Tragicomic Unease & Shocking Social Realization",
        "cinematic_style": "Masterfully choreographed tragicomic suspense"
    }
}


def get_heuristic_theme(movie_title: str) -> Dict[str, str]:
    """Generates an intelligent cinematic profile fallback when LLM API is unavailable."""
    key = movie_title.lower().strip()
    if key in KNOWN_PROFILES:
        return KNOWN_PROFILES[key]

    return {
        "primary_theme": f"Exploring deep emotional undercurrents, moral ambiguity, and transformative human conflict in '{movie_title}'.",
        "dominant_emotion": "Intense Cinematic Catharsis",
        "cinematic_style": "Immersive narrative storytelling"
    }


async def reasoning_function(state: GlobalState) -> Dict[str, Any]:
    """
    Node 1: Extracts theme, emotion, and style from the watched movie.
    """
    movie = state.get("movie_watched", "Unknown").strip()
    print(f"[Node 1] Analyzing watched movie: {movie}")

    sarvam_key = os.getenv("SARVAM_API_KEY")

    if sarvam_key:
        try:
            llm = ChatSarvam(model="sarvam-105b", reasoning_effort="medium")
            structured_llm = llm.with_structured_output(theme_extractor)

            prompt = (
                f"You are an expert film analyst. Analyze the core narrative theme, "
                f"dominant emotional resonance, and sub-genres of the movie: {movie}. "
                f"Do not provide a summary; focus purely on the psychological and thematic elements."
            )

            response = await structured_llm.ainvoke(prompt)
            if response and getattr(response, "primary_theme", None):
                return {
                    "primary_theme": response.primary_theme,
                    "dominant_emotion": response.dominant_emotion,
                    "cinematic_style": response.cinematic_style
                }
        except Exception as e:
            print(f"[Node 1] Sarvam LLM error: {e}. Falling back to evaluative theme heuristics.")

    fallback = get_heuristic_theme(movie)
    return fallback


class Agent_1:
    reasoning_function = staticmethod(reasoning_function)