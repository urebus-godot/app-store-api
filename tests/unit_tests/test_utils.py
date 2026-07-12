from collections.abc import Callable

import pytest


class TestSearch:
    @pytest.mark.parametrize(
        argnames=["keywords", "expected_keywords"],
        argvalues=[
            [
                [
                    " test  ",
                    "KeywordS     ",
                    "   Ju$T_T3$t_W#rds",
                    "***",
                    "!123",
                    "  ",
                ],
                ["test", "keywords", "ju$t_t3$t_w#rds", "***", "!123", ""],
            ]
        ],
    )
    async def test_format_keywords(
        self,
        format_kws: Callable[[list[str]], list[str]],
        keywords: list[str],
        expected_keywords: list[str],
    ):
        formatted_keywords = format_kws(keywords)
        assert formatted_keywords == expected_keywords
