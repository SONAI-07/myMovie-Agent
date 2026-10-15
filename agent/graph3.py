import asyncio
import os
from typing import Any, Dict, List
import urllib.parse
import aiohttp
from dotenv import load_dotenv

try:
    from agent.global_state import GlobalState
except ImportError:
    from global_state import GlobalState

load_dotenv()

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_BASE_URL = "https://api.themoviedb.org/3"

# Map ISO region codes to JustWatch localized URL paths
JUSTWATCH_REGION_MAP = {
    "us": "us",
    "in": "in",
    "gb": "uk",
    "uk": "uk",
    "ca": "ca",
    "au": "au",
    "de": "de",
    "fr": "fr",
    "es": "es",
    "jp": "jp"
}


def build_zero_key_justwatch_link(title: str, region: str = "US") -> str:
    """
    Constructs a direct JustWatch search and watch provider deep-link
    without requiring any TMDB API key or third-party authentication.
    """
    reg_key = region.lower().strip()
    slug = JUSTWATCH_REGION_MAP.get(reg_key, "us")
    encoded_query = urllib.parse.quote_plus(title.strip())
    return f"https://www.justwatch.com/{slug}/search?q={encoded_query}"


async def fetch_streaming_data(session: aiohttp.ClientSession, movie: dict, region: str = "US") -> dict:
    """
    Concurrently resolves streaming links for a movie.
    Uses TMDB API when an API key is available; otherwise, automatically generates
    a Zero-Key JustWatch deep-link so users always have functional streaming buttons.
    """
    movie_data = dict(movie)
    title = movie_data.get("title", "").strip()
    year = movie_data.get("release_year")

    # Instant Zero-Key Fallback: No TMDB API key configured
    zero_key_link = build_zero_key_justwatch_link(title, region)
    if not TMDB_API_KEY:
        movie_data["streaming_link"] = zero_key_link
        return movie_data

    headers = {
        "Authorization": f"Bearer {TMDB_API_KEY}",
        "accept": "application/json"
    }

    # STEP 1: Search for TMDB movie ID
    search_url = f"{TMDB_BASE_URL}/search/movie"
    params = {"query": title}
    if year:
        params["year"] = str(year)

    try:
        async with session.get(search_url, headers=headers, params=params, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status != 200:
                movie_data["streaming_link"] = zero_key_link
                return movie_data

            data = await response.json()
            results = data.get("results", [])
            if not results:
                movie_data["streaming_link"] = zero_key_link
                return movie_data

            movie_id = results[0].get("id")

        # STEP 2: Fetch the watch providers for this movie_id
        providers_url = f"{TMDB_BASE_URL}/movie/{movie_id}/watch/providers"

        async with session.get(providers_url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
            if response.status != 200:
                movie_data["streaming_link"] = zero_key_link
                return movie_data

            prov_data = await response.json()
            region_data = prov_data.get("results", {}).get(region.upper())

            if region_data and region_data.get("link"):
                # Use TMDB's direct JustWatch deep-link
                movie_data["streaming_link"] = region_data["link"]
            else:
                # Seamless fallback if provider info is missing for that region
                movie_data["streaming_link"] = zero_key_link

    except Exception as e:
        print(f"[Node 3] TMDB lookup failed for '{title}': {e}. Using Zero-Key JustWatch link.")
        movie_data["streaming_link"] = zero_key_link

    return movie_data


async def tmdb_resolver_function(state: GlobalState) -> Dict[str, Any]:
    """
    Node 3: Resolves streaming links for all curated movies concurrently.
    Guarantees every recommendation receives a working, clickable streaming link.
    """
    curated_movies = state.get("curated_movies", [])
    region = state.get("region") or os.getenv("DEFAULT_REGION", "US")

    print(f"[Node 3] Resolving streaming links for {len(curated_movies)} movies (Region: {region})")

    if not curated_movies:
        return {"final_streaming_links": []}

    # If TMDB_API_KEY is omitted, synchronously generate Zero-Key links without network overhead
    if not TMDB_API_KEY:
        resolved_movies = [
            {**dict(movie), "streaming_link": build_zero_key_justwatch_link(movie.get("title", ""), region)}
            for movie in curated_movies
        ]
        return {"final_streaming_links": resolved_movies}

    # Otherwise concurrently query TMDB API
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_streaming_data(session, movie, region=region)
            for movie in curated_movies
        ]
        resolved_movies = await asyncio.gather(*tasks)

    return {"final_streaming_links": resolved_movies}


class Agent_3:
    tmdb_resolver_function = staticmethod(tmdb_resolver_function)