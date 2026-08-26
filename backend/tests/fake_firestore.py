"""A minimal in-memory Firestore double.

Covers exactly the surface incidents_store.py and activity_log.py use
(collection/document/set/get/update/add/where/order_by/limit/stream) so
orchestrator tests run fully offline and deterministically, without a real
Firestore project or network calls.
"""

from __future__ import annotations


class _ArrayUnionMarker:
    def __init__(self, values):
        self.values = values


class FakeSnapshot:
    def __init__(self, data: dict | None):
        self._data = data

    @property
    def exists(self) -> bool:
        return self._data is not None

    def to_dict(self) -> dict | None:
        return dict(self._data) if self._data is not None else None


class FakeDocRef:
    def __init__(self, store: dict, doc_id: str, collections: dict):
        self._store = store
        self._id = doc_id
        self._collections = collections

    def set(self, data: dict) -> None:
        self._store[self._id] = dict(data)

    def get(self) -> FakeSnapshot:
        return FakeSnapshot(self._store.get(self._id))

    def update(self, fields: dict) -> None:
        current = self._store.setdefault(self._id, {})
        for key, value in fields.items():
            # Matches both our own marker and google.cloud.firestore's real
            # ArrayUnion transform object (orchestrator.py imports the real
            # `firestore` module directly, so this must recognize both).
            if type(value).__name__ == "ArrayUnion" and hasattr(value, "values"):
                existing = current.get(key, [])
                current[key] = existing + [v for v in value.values if v not in existing]
            else:
                current[key] = value

    def collection(self, name: str) -> "FakeCollection":
        key = (self._id, name)
        return self._collections.setdefault(key, FakeCollection())


class FakeCollection:
    def __init__(self):
        self._docs: dict[str, dict] = {}
        self._sub_collections: dict = {}
        self._auto_id = 0

    def document(self, doc_id: str) -> FakeDocRef:
        return FakeDocRef(self._docs, doc_id, self._sub_collections)

    def add(self, data: dict) -> tuple:
        self._auto_id += 1
        doc_id = f"auto_{self._auto_id}"
        self._docs[doc_id] = dict(data)
        return (None, FakeDocRef(self._docs, doc_id, self._sub_collections))

    def where(self, field: str, op: str, value) -> "FakeQuery":
        return FakeQuery(list(self._docs.values())).where(field, op, value)

    def order_by(self, field: str, direction=None) -> "FakeQuery":
        return FakeQuery(list(self._docs.values())).order_by(field, direction)

    def limit(self, n: int) -> "FakeQuery":
        return FakeQuery(list(self._docs.values())).limit(n)

    def stream(self):
        return [FakeSnapshot(d) for d in self._docs.values()]


class FakeQuery:
    def __init__(self, docs: list[dict]):
        self._docs = docs

    def where(self, field: str, op: str, value) -> "FakeQuery":
        if op == "==":
            filtered = [d for d in self._docs if d.get(field) == value]
        else:
            raise NotImplementedError(op)
        return FakeQuery(filtered)

    def order_by(self, field: str, direction=None) -> "FakeQuery":
        reverse = direction == "DESCENDING" or (direction is not None and "DESC" in str(direction))
        return FakeQuery(sorted(self._docs, key=lambda d: d.get(field, ""), reverse=reverse))

    def limit(self, n: int) -> "FakeQuery":
        return FakeQuery(self._docs[:n])

    def stream(self):
        return [FakeSnapshot(d) for d in self._docs]


class FakeFirestoreClient:
    """Drop-in stand-in for google.cloud.firestore.Client, top-level collections only."""

    class Query:
        DESCENDING = "DESCENDING"

    ArrayUnion = _ArrayUnionMarker

    def __init__(self):
        self._collections: dict[str, FakeCollection] = {}

    def collection(self, name: str) -> FakeCollection:
        return self._collections.setdefault(name, FakeCollection())
