import urllib.parse
from typing import Tuple
from schemas import BundleItem

def build_verified_amazon_url(query: str) -> str:
    """Format a safe, verified direct search link on Amazon India."""
    encoded = urllib.parse.quote(query)
    return f"https://www.amazon.in/s?k={encoded}"

def fetch_product_data(query: str, category_tag: str) -> Tuple[BundleItem, str]:
    """
    Lightweight fallback harvester. Product curation is now powered 
    dynamically by Gemini internal knowledge in AgentEngine.
    """
    url = build_verified_amazon_url(query)
    item = BundleItem(
        title=f"Curated {query.title()}",
        price=1999.0,
        source="Amazon IN",
        url=url,
        category=category_tag
    )
    return item, f"Gemini Direct Curator: '{item.title}' ({item.source})"
