class DependencyHierarchy:
    """Models parent/child dependency chains for causal governance."""

    def __init__(self):
        self.parents = {}
        self.children = {}

    def add_dependency(self, parent, child):
        self.parents.setdefault(child, set()).add(parent)
        self.children.setdefault(parent, set()).add(child)
        return self

    def ancestors(self, dependency):
        found = []
        stack = sorted(self.parents.get(dependency, set()))
        while stack:
            parent = stack.pop()
            if parent in found:
                continue
            found.append(parent)
            stack.extend(sorted(self.parents.get(parent, set())))
        return found

    def descendants(self, dependency):
        found = []
        stack = sorted(self.children.get(dependency, set()))
        while stack:
            child = stack.pop()
            if child in found:
                continue
            found.append(child)
            stack.extend(sorted(self.children.get(child, set())))
        return found

    def chain_for(self, dependency):
        return [*reversed(self.ancestors(dependency)), dependency]

    def report(self):
        return {
            "system": "dependency_hierarchy",
            "parents": {
                key: sorted(value)
                for key, value in self.parents.items()
            },
            "children": {
                key: sorted(value)
                for key, value in self.children.items()
            },
        }


__all__ = [
    "DependencyHierarchy",
]
