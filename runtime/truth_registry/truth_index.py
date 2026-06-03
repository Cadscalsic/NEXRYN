class TruthIndex:
    def __init__(self):
        self._by_concept = {}
        self._by_token = {}

    def _tokens(self, value):
        return {
            token
            for token in str(value).lower().replace("_", " ").split()
            if token
        }

    def add(self, record):
        self._by_concept[record.concept] = record.truth_id
        for token in self._tokens(record.concept) | self._tokens(record.claim):
            self._by_token.setdefault(token, set()).add(record.truth_id)

    def truth_id_for(self, concept):
        return self._by_concept.get(concept)

    def related_truth_ids(self, concept):
        truth_ids = set()
        for token in self._tokens(concept):
            truth_ids.update(self._by_token.get(token, set()))
        return truth_ids

