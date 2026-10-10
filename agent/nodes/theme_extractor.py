from pydantic import BaseModel, Field
from typing import Optional
from langchain_core.messages import HumanMessages


class theme_extractor(BaseModel):

  primary_theme: str = Field (description ="The central emotional or philosophical theme of the movie,"
                            "avoiding generic genre tags")


  dominant_emotion : str = Field (description="A specific emotional state the viewer is left with"
                                           "(e.g.- Existential dread, Heartwarming nostalgia).")

  cinematic_style : Optional[str]= Field (default=None,
                                          description="Optional cinematic style or pacing "
                                        "(e.g., Fast-paced thriller, Slow-burn character study)."
                                          )
