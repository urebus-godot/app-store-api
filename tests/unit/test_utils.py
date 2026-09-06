from app.utils.search import format_keywords


class TestSearch:
    async def test_format_keywords(self):
        keywords = [
            " test  ",
            "KeywordS     ",
            "   Ju$T_T3$t_W#rds",
            "!123",
            "  ",
            "My--Game--Kws"
        ]
        expected_keywords = [
            "test", "keywords", 
            "ju$t t3$t w#rds",
            "!123", "my  game  kws"
        ]
        formatted_keywords = format_keywords(keywords)
        assert formatted_keywords == expected_keywords
