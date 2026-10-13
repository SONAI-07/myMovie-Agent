from typing import Any, Dict, List, Optional, TypedDict


class GlobalState(TypedDict, total=False):
    movie_watched: str
    primary_theme: str
    dominant_emotion: str
    cinematic_style: Optional[str]
    curated_movies: List[Dict[str, Any]]
    final_streaming_links: List[Dict[str, Any]]
