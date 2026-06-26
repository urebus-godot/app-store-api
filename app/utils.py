from typing import Annotated, Sequence, Optional
from string import punctuation

from fastapi import Query

from app.models.app import AppDB

def format_keywords(keywords: Sequence[str]) -> list[str]:
    new_keywords = []
    for kw in keywords:
        kw = kw.strip()
        kw = kw.lower()
        kw = kw.format_map(
            {c: "" for c in punctuation}
            )
    return new_keywords


def filter_apps(apps: list[AppDB], search_query: str) -> list[AppDB]:
    search_keywords = format_keywords(search_query.split())
    apps = [
        app for app in apps 
        for kw in search_keywords
        if kw in format_keywords(app.keywords)
    ]
    return apps


SearchQuery = Annotated[
    str, Query(default=None, description="Enter keywords separated by 1 space")
]
