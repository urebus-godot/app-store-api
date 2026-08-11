
import pytest

from app.utils.search import format_keywords



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
                    "My--Game--Kws"
                ],
                [
                    "test", "keywords", 
                    "ju$t t3$t w#rds", "***", 
                    "!123", "my  game  kws"
                    ],
            ]
        ],
    )
    async def test_format_keywords(
        self,
        keywords: list[str],
        expected_keywords: list[str],
    ):
        formatted_keywords = format_keywords(keywords)
        assert formatted_keywords == expected_keywords
