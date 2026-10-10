import os

from dotenv import load_dotenv
from state import GlobalState
from nodes.theme_extractor import theme_extractor


from typing import TypedDict
from pydantic import BaseModel, Field
from langchain_sarvam import ChatSarvam

# Load environment variables (Ensures SARVAM_API_KEY is available)
load_dotenv()


class Agent_1 :


 async def reasoning_function(state: GlobalState) -> dict:
    """
    Node 1: Extracts theme, emotion, and style.
    """

    movie = state.get("movie_watched", "Unknown")
    print(f"Movie Watched: {movie}")


    llm = ChatSarvam(model="sarvam-105b", reasoning_effort="medium")

    # Bind the Pydantic schema to force a JSON-structured object return
    structured_llm = llm.with_structured_output(theme_extractor)


    prompt = (
        f"You are an expert film analyst. Analyze the core narrative theme, "
        f"dominant emotional resonance, and sub-genres of the movie: {movie}. "
        f"Do not provide a summary; focus purely on the psychological and thematic elements."
    )

    try:
        # Invoke the bound model asynchronously
        response = await structured_llm.ainvoke(prompt)

        # Return ONLY the dictionary fields you want to update in the GlobalState
        return {
            "primary_theme": response.primary_theme,
            "dominant_emotion": response.dominant_emotion,
            "cinematic_style": response.cinematic_style
        }

    except Exception as e:
        print(f"Error during theme extraction: {e}")
        # Return a safe fallback state so the LangGraph execution does not crash
        return {
            "primary_theme": "Error parsing theme",
            "dominant_emotion": "Error parsing emotion",
            "cinematic_style": "Error parsing style"
        }