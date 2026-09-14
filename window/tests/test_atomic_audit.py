import copy
import unittest
from test_document_summary import DocumentSummaryTests
from atomic_audit import audit_atomic, inventory
from document_oracle import atomic_text, INSTRUCTION


class AtomicAuditTests(unittest.TestCase):
    def events(self):
        events=DocumentSummaryTests().evidence()
        for e in events:
            if e['kind']!='case':
                continue
            r=e['data']
            r['atomic_text']=atomic_text(r)
            r['inventory']=inventory(r)
            m=r['modes'][0]
            m['mode']='atomic'
            m['request']['prompts']=[f"{INSTRUCTION}\n\n{r['atomic_text']}\n\nQuestion: {r['question']}\nJSON answer:"]
        return events

    def test_atomic_prompts_and_fact_hashes_are_verified(self):
        events=self.events()
        audit_atomic(events)
        altered=copy.deepcopy(events)
        altered[2]['data']['inventory']['atoms'][0]['hash']='bad'
        with self.assertRaises(ValueError):
            audit_atomic(altered)
        altered=copy.deepcopy(events)
        altered[2]['data']['atomic_text']='Expected answer: Mira'
        with self.assertRaises(ValueError):
            audit_atomic(altered)
