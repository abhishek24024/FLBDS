"""Evidence schema for grounded Mechanism Cards."""

from typing import Optional
from pydantic import BaseModel, Field, model_validator


class EvidenceSpan(BaseModel):
    """An exact textual or visual citation grounding a causal claim in source literature."""

    source_doc_id: str = Field(
        ...,
        description="Unique identifier of the source document (e.g. PMC id, DOI, or patent publication number)",
    )
    text_span: str = Field(
        ...,
        min_length=1,
        description="Exact quoted text span from the source document",
    )
    char_start: int = Field(
        ...,
        ge=0,
        description="0-based character start offset in the source document",
    )
    char_end: int = Field(
        ...,
        ge=0,
        description="0-based character end offset in the source document",
    )
    figure_roi: Optional[str] = Field(
        default=None,
        description="Optional figure identifier or region-of-interest coordinates (e.g., Fig 2B [x1,y1,x2,y2])",
    )
    citation: Optional[str] = Field(
        default=None,
        description="Formal bibliographic citation, DOI link, or patent publication metadata",
    )

    @model_validator(mode="after")
    def validate_offsets(self) -> "EvidenceSpan":
        if self.char_end < self.char_start:
            raise ValueError(
                f"char_end ({self.char_end}) must be greater than or equal to char_start ({self.char_start})"
            )
        return self
