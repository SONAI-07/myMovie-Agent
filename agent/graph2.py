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


async def movies_extract(state: GlobalState) -> Dict[str, Any]:
    """
    Node 2: Curates 3 movies with the same emotional and thematic resonance.
    """
    movie_watched = state.get("movie_watched", "Unknown")
    primary_theme = state.get("primary_theme", "Unknown")
    dominant_emotion = state.get("dominant_emotion", "Unknown")
    cinematic_style = state.get("cinematic_style", "Unknown")

    print(f"[Node 2] Curating movies matching theme: '{primary_theme}', emotion: '{dominant_emotion}'")

    llm = ChatSarvam(model="sarvam-105b", reasoning_effort="high")
    structured_output = llm.with_structured_output(CuratedList)

    prompt = (
        "You are an elite, world-class film curator and cinephile. Your job is to recommend "
        "movies based on deep psychological resonance, narrative themes, and emotional impact "
        "rather than just matching surface-level genres.\n\n"
        f"A user just finished watching the movie: '{movie_watched}'.\n"
        "Based on previous analysis, this movie has the following profile:\n"
        f"- Primary Theme: {primary_theme}\n"
        f"- Dominant Emotion: {dominant_emotion}\n"
        f"- Cinematic Style: {cinematic_style}\n\n"
        "YOUR OBJECTIVE:\n"
        "Curate a list of EXACTLY 3 highly acclaimed movies that share this exact thematic "
        "and emotional DNA. The recommended movies should make the user feel the same way "
        f"'{movie_watched}' did, even if they are set in a completely different time period or setting.\n\n"
        "STRICT CONSTRAINTS:\n"
        f"1. DO NOT recommend '{movie_watched}' or any of its direct sequels/prequels.\n"
        "2. You must provide the 100% accurate release year for each movie (this is critical for our database lookup).\n"
        "3. Prioritize cinematic quality and strong storytelling.\n"
        "4. Provide a brief, one-sentence 'thematic_connection' explaining exactly why this new movie matches the dominant emotion and theme of the watched movie.\n"
    )

    try:
        response: CuratedList = await structured_output.ainvoke(prompt)
        curated = [
            m.model_dump() if hasattr(m, "model_dump") else dict(m)
            for m in response.Recommended_Movies
        ]
        return {
            "curated_movies": curated
        }

    except Exception as e:
        print(f"Error during movie curation: {e}")
        # Return a safe fallback list so subsequent nodes do not crash
        return {
            "curated_movies": []
        }


class Agent_2:
    movies_extract = staticmethod(movies_extract)







