import asyncio
import os
from typing import Any, Dict
from dotenv import load_dotenv
from langgraph.graph import StateGraph, START, END

try:
    from agent.global_state import GlobalState
    from agent.graph1 import reasoning_function
    from agent.graph2 import movies_extract
    from agent.graph3 import tmdb_resolver_function
except ImportError:
    from global_state import GlobalState
    from graph1 import reasoning_function
    from graph2 import movies_extract
    from graph3 import tmdb_resolver_function

load_dotenv()


def build_pipeline():
    """
    Builds and compiles the bingeWatch LangGraph pipeline:
    START -> theme_extractor (Node 1) -> movie_curator (Node 2) -> tmdb_resolver (Node 3) -> END
    """
    builder = StateGraph(GlobalState)

    # 1. Register Nodes
    builder.add_node("theme_extractor", reasoning_function)
    builder.add_node("movie_curator", movies_extract)
    builder.add_node("tmdb_resolver", tmdb_resolver_function)

    # 2. Wire Linear Flow Edges
    builder.add_edge(START, "theme_extractor")
    builder.add_edge("theme_extractor", "movie_curator")
    builder.add_edge("movie_curator", "tmdb_resolver")
    builder.add_edge("tmdb_resolver", END)

    # 3. Compile Graph
    return builder.compile()


# Compiled LangGraph application instance
pipeline_app = build_pipeline()


async def run_pipeline(movie_watched: str) -> Dict[str, Any]:
    """
    Executes the recommendation workflow end-to-end for a given movie title.
    """
    initial_state: GlobalState = {
        "movie_watched": movie_watched
    }
    final_state = await pipeline_app.ainvoke(initial_state)
    return final_state


if __name__ == "__main__":
    import json
    import sys

    movie = sys.argv[1] if len(sys.argv) > 1 else "Interstellar"
    print(f"🎬 Starting bingeWatch pipeline for: '{movie}'\n")

    result = asyncio.run(run_pipeline(movie))

    print("\n✅ Pipeline execution completed:")
    print(json.dumps(result, indent=2))
