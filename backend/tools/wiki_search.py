"""
MARS Tool — Wikipedia Search.

Provides factual, encyclopedic background on a topic.
Uses the `wikipedia` PyPI package which calls the Wikipedia API.
"""
import logging

logger = logging.getLogger(__name__)


def wiki_search(topic: str, sentences: int = 8) -> str:
    """
    Fetch a Wikipedia summary for a given topic.

    Args:
        topic: Topic name to search for.
        sentences: Number of sentences to return (default: 8).

    Returns:
        Summary string or descriptive error message.
    """
    try:
        import wikipedia

        wikipedia.set_lang("en")
        # Disable auto-suggest as it can sometimes lead to incorrect page matches
        summary = wikipedia.summary(topic, sentences=sentences, auto_suggest=False)
        page = wikipedia.page(topic, auto_suggest=False)
        return (
            f"Wikipedia: {page.title}\n"
            f"URL: {page.url}\n\n"
            f"{summary}"
        )

    except Exception as exc:
        logger.warning("wiki_search failed for '%s': %s", topic, exc)
        return f"Wikipedia search failed for '{topic}': {exc}"
