from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
from functools import lru_cache
import logging
from typing import Dict, List
from duckduckgo_search import DDGS
import tiktoken
import trafilatura
from trafilatura.settings import DEFAULT_CONFIG


class ContentGenerator:
    def __init__(self, max_results: int = 3, token_limit: int = 9000):
        self.max_results = max_results

        self.token_limit = token_limit
        self.token_encoding = tiktoken.get_encoding("o200k_base")

        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }

        self.extract_config = deepcopy(DEFAULT_CONFIG)
        self.extract_config["DEFAULT"].update(
            {
                "DOWNLOAD_TIMEOUT": "5",
                "SLEEP_TIME": "0.5",
                "MAX_REDIRECTS": "0",
            }
        )

        self.logger = logging.getLogger(__name__)

    @lru_cache(maxsize=100)
    def search(self, query: str) -> List[Dict[str, str]]:
        try:
            return list(DDGS().text(query, max_results=self.max_results))
        except Exception as e:
            # Optimizing for speed so letting DDGS hit rate limit
            self.logger.error(f"Error searching: {e}")
            return []

    def _get_token_count(self, content: str) -> int:
        return len(self.token_encoding.encode(content))

    def _truncate_content(self, content: str, token_limit: int) -> str:
        tokens = self.token_encoding.encode(content)
        return self.token_encoding.decode(tokens[:token_limit])

    def _extract_content(self, url: str) -> str:
        try:
            fetched_url = trafilatura.fetch_url(url, config=self.extract_config)
            if fetched_url:
                return (
                    trafilatura.extract(
                        fetched_url,
                        include_comments=False,
                        include_images=False,
                        include_tables=False,
                        include_links=False,
                        no_fallback=True,
                        config=self.extract_config,
                    )
                    or ""
                )
        except Exception as e:
            self.logger.error(f"Error fetching content: {e}")
        return ""

    def get_content(
        self, search_queries: List[str], top_keywords
    ) -> List[Dict[str, str]]:
        visited_urls = set()
        content_results = []
        queued_urls = []
        remaining_tokens = self.token_limit

        for query in search_queries:
            search_results = self.search(query)

            for result in search_results:
                url = result["href"]
                if url not in visited_urls:
                    visited_urls.add(url)
                    queued_urls.append((url, result))

        with ThreadPoolExecutor() as executor:
            # Map URLs to futures
            future_to_url = {
                executor.submit(self._extract_content, url): (url, result)
                for url, result in queued_urls
            }

            # Collect results as they complete
            for future in as_completed(future_to_url):
                url, result = future_to_url[future]
                try:
                    content = future.result()
                    curr_content = {
                        "title": result["title"],
                        "url": url,
                        "snippet": result["body"],
                        "content": content,
                        "keyword_count": sum(
                            content.lower().count(keyword.lower())
                            for keyword in top_keywords
                        ),
                    }

                    # Determine if we can add the content
                    remaining_tokens -= self._get_token_count(content)
                    if remaining_tokens < 0:
                        self.logger.warning("Token limit reached")
                        break

                    content_results.append(curr_content)
                except Exception as e:
                    self.logger.error(f"Error fetching content: {e}")

        return sorted(content_results, key=lambda x: x["keyword_count"], reverse=True)
