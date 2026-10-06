"""Discord artwork keys. Upload these exact names in the Developer Portal."""
from .config import RANK_TIERS

_ROMAN = {'I': '1', 'II': '2', 'III': '3'}


def _asset_key(tier: str) -> str:
    words = tier.lower().split()
    if tier.split()[-1] in _ROMAN:
        words[-1] = _ROMAN[tier.split()[-1]]
    return '_'.join(words)


RANK_ASSETS = {tier: _asset_key(tier) for tier in RANK_TIERS}
