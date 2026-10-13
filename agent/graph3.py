import asyncio
import os
from typing import Any, Dict, List
import aiohttp
from dotenv import load_dotenv

try:
    from agent.global_state import GlobalState
except ImportError:
    from global_state import GlobalState

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"


async def fetch_streaming_data(session: aiohttp.ClientSession, movie: dict, region: str = "US") -> dict:
    """
    Helper function to concurrently fetch the TMDB ID and then the Watch Providers.
    """
    movie_data = dict(movie)
    title = movie_data.get("title")
    year = movie_data.get("release_year")

    if not TMDB_API_KEY:
        movie_data["streaming_link"] = "TMDB_API_KEY not configured"
        return movie_data

    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "accept": "application/json"
    }

    # STEP 1: Search for the movie ID using title and release year for an exact match
    search_url = f"{TMDB_BASE_URL}/search/movie"
    params = {"query": title}
    if year:
        params["year"] = year

    try:
        async with session.get(search_url, headers=headers, params=params) as response:
            if response.status != 200:
                movie_data["streaming_link"] = f"TMDB Search API Error ({response.status})"
                return movie_data

            data = await response.json()
            results = data.get("results", [])

            if not results:
                movie_data["streaming_link"] = "Not Found in TMDB"
                return movie_data

            movie_id = results[0].get("id")

        # STEP 2: Fetch the watch providers using the resolved movie_id
        providers_url = f"{TMDB_BASE_URL}/movie/{movie_id}/watch/providers"

        async with session.get(providers_url, headers=headers) as response:
            if response.status != 200:
                movie_data["streaming_link"] = f"TMDB Providers API Error ({response.status})"
                return movie_data

            prov_data = await response.json()

            # TMDB categorizes streaming links by country code (e.g., US, IN, GB).
            region_data = prov_data.get("results", {}).get(region)

            if region_data and "link" in region_data:
                # TMDB provides a JustWatch link displaying regional streaming platforms
                movie_data["streaming_link"] = region_data["link"]
            else:
                movie_data["streaming_link"] = f"No streaming link available for region: {region}"

    except Exception as e:
        print(f"Error resolving streaming data for '{title}': {e}")
        movie_data["streaming_link"] = f"Error: {e}"

    return movie_data


async def tmdb_resolver_function(state: GlobalState) -> Dict[str, Any]:
    """
    Node 3: Resolves streaming links for the curated movies.
    Fully optimized using asynchronous HTTP requests.
    """
    curated_movies = state.get("curated_movies", [])
    print(f"[Node 3] Resolving streaming links for {len(curated_movies)} movies")

    # Defensive check: if Node 2 produced no movies, safely exit
    if not curated_movies:
        return {"final_streaming_links": []}

    # Open a single ClientSession and run all TMDB lookups concurrently
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_streaming_data(session, movie, region="US")
            for movie in curated_movies
        ]
        resolved_movies = await asyncio.gather(*tasks)

    return {"final_streaming_links": resolved_movies}


class Agent_3:
    tmdb_resolver_function = staticmethod(tmdb_resolver_function)