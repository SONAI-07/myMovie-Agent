from typing import Annotated, TypedDict, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages


class GlobalState(TypedDict):

    movie_watched : str

    primary_theme : str
    dominant_emotion: str
    cinematic_style : str

    curated_movies : List[str]
