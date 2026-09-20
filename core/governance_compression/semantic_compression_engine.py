# ============================================
# NEXRYN SEMANTIC COMPRESSION ENGINE
# OPTIMIZED / CACHED VERSION
# ============================================

from datetime import datetime
import hashlib
import json


class SemanticCompressionEngine:

    TOKEN_MAP = {
        "identity": "identity",
        "object": "object",
        "preservation": "preservation",
        "preserve": "preservation",
        "topological": "topology",
        "topology": "topology",
        "growth": "growth",
        "grow": "growth",
        "shape": "shape",
        "color": "color",
        "motion": "motion",
        "translation": "motion",
        "symbolic": "symbolic",
        "remapping": "remap",
        "bridge": None,
        "concept": None,
    }

    CANONICAL_ORDER = [
        "preservation",
        "growth",
        "topology",
        "identity",
        "object",
        "shape",
        "color",
        "motion",
        "symbolic",
        "remap",
    ]

    MAX_CONCEPTS_NORMAL = 128
    MAX_CONCEPTS_FAST = 32

    def __init__(self):
        self.encoding_cache = {}
        self.last_signature = None
        self.last_report = None
        self.cache_hits = 0
        self.cache_misses = 0

    def _stable_hash(self, payload):
        try:
            encoded = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            encoded = str(payload)

        return hashlib.sha256(encoded.encode("utf-8")).hexdigest()

    def _fast_mode(self, context):
        return (
            context.get("episode_completed") is True
            or context.get("shutdown_mode") == "fast"
            or context.get("post_success_mode") == "fast"
            or context.get("post_success_shutdown", {}).get("enabled") is True
        )

    def tokenize(self, concept):
        return [
            token
            for token in str(concept)
            .replace("-", "_")
            .split("_")
            if token
        ]

    def canonical_encode(self, concept):
        key = str(concept)

        if key in self.encoding_cache:
            return self.encoding_cache[key]

        factors = []

        for token in self.tokenize(concept):
            mapped = self.TOKEN_MAP.get(
                token.lower(),
                token.lower(),
            )

            if mapped is None:
                continue

            if mapped not in factors:
                factors.append(mapped)

        ordered = [
            factor
            for factor in self.CANONICAL_ORDER
            if factor in factors
        ]

        ordered.extend([
            factor
            for factor in factors
            if factor not in ordered
        ])

        if {
            "preservation",
            "growth",
            "topology",
        }.issubset(set(ordered)):
            ordered = [
                "preservation",
                "growth",
                "topology",
            ]

        encoded = ".".join(ordered)

        self.encoding_cache[key] = encoded

        if len(self.encoding_cache) > 4096:
            self.encoding_cache = dict(
                list(self.encoding_cache.items())[-2048:]
            )

        return encoded

    def collect_concepts(self, context):
        concepts = []
        seen = set()

        def add(value):
            if value is None:
                return

            concept = str(value).strip()

            if not concept:
                return

            if concept in seen:
                return

            seen.add(concept)
            concepts.append(concept)

        neuro = context.get("conceptive_neurogenesis_report", {})
        for item in neuro.get("generated_concepts", []):
            if isinstance(item, dict):
                add(item.get("concept"))
            else:
                add(item)

        lifecycle = context.get("concept_lifecycle_report", {})
        registry = lifecycle.get("registry", {})
        for item in registry.get("concepts", []):
            if isinstance(item, dict):
                add(item.get("concept"))
            else:
                add(item)

        semantic_memory = context.get("semantic_virtual_memory_report", {})
        for key in [
            "active_cognition",
            "latent_cognition",
            "archived_cognition",
        ]:
            for item in semantic_memory.get(key, []):
                if isinstance(item, dict):
                    add(item.get("concept"))
                else:
                    add(item)

        return concepts

    def _signature(self, concepts, fast_mode):
        return self._stable_hash({
            "concepts": concepts,
            "fast_mode": fast_mode,
        })

    def _cache_report(self):
        total = self.cache_hits + self.cache_misses

        return {
            "system": "semantic_compression_cache",
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "cache_hit_rate": round(self.cache_hits / total, 4) if total else 0.0,
            "encoding_cache_size": len(self.encoding_cache),
        }

    def run_cycle(self, context=None):
        context = context or {}

        concepts = self.collect_concepts(context)
        fast_mode = self._fast_mode(context)

        max_concepts = (
            self.MAX_CONCEPTS_FAST
            if fast_mode
            else self.MAX_CONCEPTS_NORMAL
        )

        concepts = concepts[:max_concepts]

        signature = self._signature(concepts, fast_mode)

        if self.last_signature == signature and self.last_report is not None:
            self.cache_hits += 1
            report = dict(self.last_report)
            report["semantic_compression_cache_hit"] = True
            report["semantic_compression_cache_report"] = self._cache_report()
            report["timestamp"] = str(datetime.utcnow())
            return report

        self.cache_misses += 1

        encodings = []

        for concept in concepts:
            canonical = self.canonical_encode(concept)

            encodings.append({
                "concept": concept,
                "canonical_encoding": canonical,
                "factor_count": (
                    len(canonical.split("."))
                    if canonical
                    else 0
                ),
            })

        report = {
            "system": "semantic_compression_engine",
            "encoding_mode": "symbolic_factorization",
            "encodings": encodings,
            "encoded_count": len(encodings),
            "fast_mode": fast_mode,
            "semantic_compression_cache_hit": False,
            "semantic_compression_cache_report": self._cache_report(),
            "timestamp": str(datetime.utcnow()),
        }

        self.last_signature = signature
        self.last_report = dict(report)

        return report