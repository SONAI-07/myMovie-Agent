import os

from dotenv import load_dotenv
from state import GlobalState
from nodes.theme_extractor import theme_extractor
from typing import TypedDict
from pydantic import BaseModel, Field
from langchain_sarvam import ChatSarvam


load_dotenv()


class Agent_2:

 async def movies_extract (state:GlobalState)-> dict:

  llm = ChatSarvam(model="105B",reasoning="high")
  structured_output = llm.with_structured_output(theme_extractor)

  prompt=(
   "You are an elite, world-class film curator and cinephile. Your job is to recommend "
   "movies based on deep psychological resonance, narrative themes, and emotional impact "
   "rather than just matching surface-level genres.\n\n"

   "A user just finished watching the movie: '{movie_watched}'.\n"
   "Based on previous analysis, this movie has the following profile:\n"
   "- Primary Theme: {primary_theme}\n"
   "- Dominant Emotion: {dominant_emotion}\n"
   "- Cinematic Style: {cinematic_style}\n\n"

   "YOUR OBJECTIVE:\n"
   "Curate a list of EXACTLY 3 highly acclaimed movies that share this exact thematic "
   "and emotional DNA. The recommended movies should make the user feel the same way "
   "'{movie}' did, even if they are set in a completely different time period or setting.\n\n"

   "STRICT CONSTRAINTS:\n"
   "1. DO NOT recommend '{movie}' or any of its direct sequels/prequels.\n"
   "2. You must provide the 100% accurate release year for each movie (this is critical for our database lookup).\n"
   "3. Prioritize cinematic quality and strong storytelling.\n"
   "4. Provide a brief, one-sentence 'thematic_connection' explaining exactly why this new movie matches the dominant emotion and theme of the watched movie.\n"
  )

  try:

     response: List = await structured_output.ainvoke(prompt)

     return {

        "curated_movies": response.data
     }

  except Exception as e:

     print(f"Error during movie curation: {e}")

   # Return a safe fallback state so the LangGraph execution does not crash
     return {
      "curated_movies": "Error in movie curation"
     }







