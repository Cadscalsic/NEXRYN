class PromotionRegistry:
    """Keeps strategy promotion idempotent across runtime cycles."""

    def __init__(self):
        self._promotions = {}

    def register(self, promotion):
        strategy = promotion.get("strategy", "unknown")

        if strategy in self._promotions:
            return self._promotions[strategy], False

        self._promotions[strategy] = promotion
        return promotion, True

    def contains(self, strategy):
        return strategy in self._promotions

    def promotions(self):
        return list(self._promotions.values())


__all__ = [
    "PromotionRegistry",
]
