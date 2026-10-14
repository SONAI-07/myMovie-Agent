from typing import Any, List, Optional, Union
from pydantic import BaseModel, Field, model_validator


class MovieRecommendation(BaseModel):
    title: str = Field(description="Exact title of the film")
    release_year: Optional[Union[int, str]] = Field(
        default=None,
        description="Release year of the film"
    )
    thematic_connection: str = Field(
        description="A compelling explanation of why cinephiles love to dive into this movie after the watched film"
    )
    spark_reason: Optional[str] = Field(
        default=None,
        description="The unexpected spark or psychological hook this movie delivers"
    )


class CuratedList(BaseModel):
    """
    Curated list of 3 to 5 movies.
    Accepts various casing conventions from different LLM completions.
    """
    Recommended_Movies: List[MovieRecommendation] = Field(
        default_factory=list,
        description="A list containing 3 to 5 curated movies that add a spark after watching the given film."
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_keys(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Check for alternative keys if Recommended_Movies is missing
            for key in ["recommended_movies", "movies", "curated_movies", "recommendations"]:
                if key in data and data[key]:
                    data["Recommended_Movies"] = data[key]
                    break
        elif isinstance(data, list):
            return {"Recommended_Movies": data}
        return data
