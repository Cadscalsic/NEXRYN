from runtime.cache.concept_lifecycle_cache import ConceptLifecycleCache


def test_concept_lifecycle_cache_reuses_unchanged_inputs():
    cache = ConceptLifecycleCache()
    ledger = {
        "concepts": [{
            "concept": "growth",
            "used_task_count": 3,
            "independent_success_rate": 0.9,
            "records": [{"success": True}],
        }]
    }
    truth = {"evaluations": [{"concept": "growth", "promotion_score": 0.8}]}

    key = cache.key(ledger, truth, report_level="normal")
    cache.put(key, {"concepts": [{"concept": "growth"}]})
    cached = cache.get(key)

    assert cached["concept_lifecycle_cache_hit"] is True
    assert cache.report()["concept_lifecycle_cache_hits"] == 1
