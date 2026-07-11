from typing import Annotated

from fastapi import Query

from app.models.app import AppDB

SearchQuery = Annotated[
    str,
    Query(
        default=None,
        description="Enter keywords separated by 1 space",
        max_length=300,
    ),
]


def format_keywords(keywords: list[str]) -> list[str]:
    new_keywords = []
    for kw in keywords:
        kw = kw.strip()
        kw = kw.lower()
        new_keywords.append(kw)
        # translator = kw.maketrans('', '', punctuation)
        # kw = kw.translate(translator)
        # kw = ''.join(char for char in kw if char not in punctuation)
    return new_keywords


def filter_apps(apps: list[AppDB], search_query: str) -> list[AppDB]:
    search_keywords = format_keywords(search_query.split())
    apps = [
        app
        for app in apps
        for kw in search_keywords
        if kw in format_keywords(app.keywords)
    ]
    return apps
