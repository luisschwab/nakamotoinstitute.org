from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic.types import PositiveInt
from sqlalchemy.ext.asyncio import AsyncSession

from sni.constants import LocaleType
from sni.database import get_db
from sni.shared.feed import FeedFormat
from sni.shared.responses import AtomResponse, RSSResponse
from sni.shared.schemas import SlugParamModel

from . import service
from .feed import generate_mempool_feed
from .schemas import (
    MempoolPostIndexModel,
    MempoolPostModel,
    MempoolSeriesFullModel,
    MempoolSeriesModel,
)

series_router = APIRouter()


@series_router.get("", response_model=list[MempoolSeriesModel])
async def get_all_mempool_series(
    locale: LocaleType = "en", db: AsyncSession = Depends(get_db)
) -> Any:
    return await service.get_all_series_by_locale(db_session=db, locale=locale)


@series_router.get("/params", response_model=list[SlugParamModel])
async def get_mempool_series_params(db: AsyncSession = Depends(get_db)) -> Any:
    return await service.get_series_params(db_session=db)


@series_router.get("/{slug}", response_model=MempoolSeriesFullModel)
async def get_mempool_series(
    slug: str, locale: LocaleType = "en", db: AsyncSession = Depends(get_db)
) -> Any:
    series = await service.get_series(slug, db_session=db, locale=locale)
    if not series:
        raise HTTPException(status_code=404, detail="Mempool series not found")

    posts = await service.get_series_posts(
        series.blog_series.id, db_session=db, locale=locale
    )

    return {"series": series, "posts": posts}


router = APIRouter()
router.include_router(series_router, prefix="/series")


@router.get("", response_model=list[MempoolPostIndexModel])
async def get_mempool_posts(
    locale: LocaleType = "en", db: AsyncSession = Depends(get_db)
) -> Any:
    return await service.get_all_posts_by_locale(db_session=db, locale=locale)


@router.get("/latest", response_model=list[MempoolPostIndexModel])
async def get_latest_mempool_post(
    locale: LocaleType = "en", num: PositiveInt = 3, db: AsyncSession = Depends(get_db)
) -> Any:
    posts = await service.get_latest_posts(db_session=db, locale=locale, num=num)
    if not posts:
        raise HTTPException(status_code=404, detail="Mempool post not found")

    return posts


@router.get("/params", response_model=list[SlugParamModel])
async def get_mempool_params(db: AsyncSession = Depends(get_db)) -> Any:
    return await service.get_params(db_session=db)


@router.get("/feed", response_class=Response)
async def generate_feed(
    locale: LocaleType = "en",
    format: FeedFormat = FeedFormat.rss,
    db: AsyncSession = Depends(get_db),
) -> Any:
    posts = await service.get_all_posts_by_locale(db_session=db, locale=locale)
    feed = generate_mempool_feed(posts, locale, format)

    if format == FeedFormat.rss:
        return RSSResponse(content=feed.rss_str(pretty=True))
    else:
        return AtomResponse(content=feed.atom_str(pretty=True))


@router.get("/{slug}", response_model=MempoolPostModel)
async def get_mempool_post(
    slug: str, locale: LocaleType = "en", db: AsyncSession = Depends(get_db)
) -> Any:
    post = await service.get_post(slug, db_session=db, locale=locale)
    if not post:
        raise HTTPException(status_code=404, detail="Mempool post not found")

    return post
