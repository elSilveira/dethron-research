"""Independent inventory verification for the atomic-evidence experiment."""
import hashlib
import json
from document_audit import audit, require
from document_oracle import atomic_text


def inventory(case):
    atoms, recipes = {}, []
    for route in case['routes']:
        refs = []
        for source in route['sources']:
            encoded = json.dumps(source, sort_keys=True, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
            identity = hashlib.sha256(encoded).hexdigest()
            atoms[identity] = source
            refs.append(identity)
        recipes.append(dict(references=refs, queries=route['queries']))
    return dict(schema=1, unit='one annotated source relation; not a neural model',
                atoms=[dict(hash=k, fact=v) for k, v in sorted(atoms.items())], recipes=recipes, missing_atoms=0)


def audit_atomic(events):
    cases, rows = audit(events, ('selected', 'atomic'))
    for case, row in zip(cases, rows):
        require(row['atomic_text'] == atomic_text(case), 'Changed atomic evidence text')
        require(row['inventory'] == inventory(case), 'Changed atom identity or reconstruction recipe')
    return cases, rows
