"""Compute translation per object instead of a dominant global vector."""

from __future__ import annotations


class RelativeTranslationEngine:
    def compute(self, input_objects: list[dict], output_objects: list[dict]) -> dict:
        matched = self._match(input_objects, output_objects)
        translations = {}
        for source, target in matched:
            source_id = str(source.get("id", source.get("object_id", "")))
            translations[source_id] = self._translation(source, target)
        return translations

    def _match(self, input_objects, output_objects):
        unmatched = list(output_objects or [])
        matches = []
        for source in input_objects or []:
            best = None
            best_score = -1.0
            for target in unmatched:
                score = self._score(source, target)
                if score > best_score:
                    best = target
                    best_score = score
            if best is not None:
                unmatched.remove(best)
                matches.append((source, best))
        return matches

    def _score(self, source, target):
        score = 0.0
        if source.get("color") == target.get("color"):
            score += 0.4
        if source.get("size") == target.get("size"):
            score += 0.2
        if source.get("canonical_shape_signature") == target.get("canonical_shape_signature"):
            score += 0.3
        score += max(0.0, 0.1 - self._distance(source, target) * 0.01)
        return score

    def _translation(self, source, target):
        source_center = source.get("center", source.get("centroid", {})) or {}
        target_center = target.get("center", target.get("centroid", {})) or {}
        if isinstance(source_center, dict):
            sr = source_center.get("row", 0.0)
            sc = source_center.get("col", 0.0)
        else:
            sr, sc = source_center
        if isinstance(target_center, dict):
            tr = target_center.get("row", 0.0)
            tc = target_center.get("col", 0.0)
        else:
            tr, tc = target_center
        return (int(round(float(tr) - float(sr))), int(round(float(tc) - float(sc))))

    def _distance(self, source, target):
        dr, dc = self._translation(source, target)
        return abs(dr) + abs(dc)


relative_translation_engine = RelativeTranslationEngine()


__all__ = [
    "RelativeTranslationEngine",
    "relative_translation_engine",
]
