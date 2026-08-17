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
        translator = kw.maketrans({"_": " ", "-": " "})
        kw = kw.translate(translator)
        if kw:
            new_keywords.append(kw)
    return new_keywords
