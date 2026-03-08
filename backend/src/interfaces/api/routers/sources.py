"""Sources router — /api/v1/sources"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status

from backend.src.domain.entities.source import Source
from backend.src.interfaces.api.dependencies import get_source_repo
from backend.src.interfaces.api.schemas.source import (
    SourceCreateRequest,
    SourceResponse,
    SourceUpdateRequest,
)
from backend.src.infrastructure.database.repositories.source_repo import (
    SQLSourceRepository,
)

router = APIRouter(prefix="/sources", tags=["sources"])


@router.get("", response_model=list[SourceResponse])
async def list_sources(
    active_only: bool = Query(default=False, description="Return only active sources"),
    repo: SQLSourceRepository = Depends(get_source_repo),
) -> list[SourceResponse]:
    """List all sources, optionally filtering by active status."""
    sources = await repo.list_active() if active_only else await repo.list_all()
    return [SourceResponse.model_validate(s.__dict__) for s in sources]


@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(
    source_id: uuid.UUID,
    repo: SQLSourceRepository = Depends(get_source_repo),
) -> SourceResponse:
    """Retrieve a single source by UUID."""
    source = await repo.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    return SourceResponse.model_validate(source.__dict__)


@router.post("", response_model=SourceResponse, status_code=status.HTTP_201_CREATED)
async def create_source(
    body: SourceCreateRequest,
    repo: SQLSourceRepository = Depends(get_source_repo),
) -> SourceResponse:
    """Create a new news source."""
    source = Source(
        name=body.name,
        url=body.url,
        feed_url=body.feed_url,
        source_type=body.source_type,
        language=body.language,
        fetch_interval=body.fetch_interval,
        is_active=True,
    )
    saved = await repo.save(source)
    return SourceResponse.model_validate(saved.__dict__)


@router.put("/{source_id}", response_model=SourceResponse)
async def update_source(
    source_id: uuid.UUID,
    body: SourceUpdateRequest,
    repo: SQLSourceRepository = Depends(get_source_repo),
) -> SourceResponse:
    """Update an existing source (partial updates supported)."""
    source = await repo.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")

    if body.name is not None:
        source.name = body.name
    if body.url is not None:
        source.url = body.url
    if body.feed_url is not None:
        source.feed_url = body.feed_url
    if body.source_type is not None:
        source.source_type = body.source_type
    if body.language is not None:
        source.language = body.language
    if body.fetch_interval is not None:
        source.fetch_interval = body.fetch_interval
    if body.is_active is not None:
        source.is_active = body.is_active

    updated = await repo.update(source)
    return SourceResponse.model_validate(updated.__dict__)


@router.delete("/{source_id}", status_code=status.HTTP_204_NO_CONTENT, response_model=None)
async def delete_source(
    source_id: uuid.UUID,
    repo: SQLSourceRepository = Depends(get_source_repo),
) -> None:
    """Delete a source by UUID."""
    source = await repo.get_by_id(source_id)
    if source is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Source not found")
    await repo.delete(source_id)
