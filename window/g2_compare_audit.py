"""Recompute each contact outcome from signed packet evidence and verify final output."""
import base64
import hashlib
import json

from dethron_gateway.erasure import reconstruct
from dethron_gateway.parts import validate
from dethron_gateway.protocol import data_envelope, receipt_envelope
from dethron_gateway.wire import authenticate
from g2_compare_contract import expected_completion


def audit(root):
    m = json.loads((root/'manifest.json').read_text())
    rows = [json.loads(s) for s in (root/'timeline.jsonl').read_text().splitlines()]
    contacts = [r for r in rows if r['event'] == 'contact_evidence']
    stops = [r for r in rows if r['event'] == 'crash' and r['node'] == 'O']
    if len(stops) != 1 or len(contacts) != len(m['case']['contacts']):
        raise ValueError('missing origin shutdown or contact evidence')
    if stops[0]['time'] >= contacts[0]['time'] or [r['relay'] for r in contacts] != m['case']['contacts']:
        raise ValueError('invalid contact order')
    content = None
    for position, row in enumerate(contacts, 1):
        chunks, whole = {}, []
        for name, digest in row['packets'].items():
            if name != __import__('pathlib').Path(name).name:
                raise ValueError('invalid packet name')
            raw = (root/'D'/'packets'/name).read_bytes()
            if hashlib.sha256(raw).hexdigest() != digest:
                raise ValueError('packet evidence modified')
            obj = authenticate(raw, bytes.fromhex(m['source']['public_key']),
                               m['destination']['destination'], m['expires']-1)
            allowed = [m['inputs'][n] for n in m['case']['contacts'][:position]]
            if obj not in allowed:
                raise ValueError('packet from an unavailable contact')
            body = base64.b64decode(obj['payload'], validate=True)
            if m['case']['mode'] == 'whole':
                whole.append(body)
            else:
                manifest, index, data = validate(body)
                if manifest != m['object']:
                    raise ValueError('unexpected object manifest')
                chunks[index] = data
        content = whole[0] if whole else (reconstruct(m['object'], chunks) if chunks else None)
        if any(hashlib.sha256(b).hexdigest() != m['object']['digest'] for b in whole):
            raise ValueError('whole mismatch')
        expected = expected_completion(m['case']['mode'], m['case']['scenario'], position)
        if (content is not None) != expected or row['receiver']['completed'] is not expected:
            raise ValueError('incorrect contact completion')
        if m['case']['mode'] != 'whole' and len(chunks) != position:
            raise ValueError('missing unique authenticated parts')
    output, receipt = root/'D'/'output.bin', root/'D'/'completion.lxmf'
    if content is None:
        if output.exists() or receipt.exists():
            raise ValueError('false completion')
    else:
        if output.read_bytes() != content or hashlib.sha256(content).hexdigest() != m['object']['digest']:
            raise ValueError('output mismatch')
        obj = authenticate(receipt.read_bytes(), bytes.fromhex(m['destination']['public_key']),
                           m['source']['destination'], m['expires']-1)
        original = data_envelope(m['source']['destination'], m['destination']['destination'], content,
                                 m['expires'], m['object']['id'])
        if obj != receipt_envelope(original):
            raise ValueError('invalid completion receipt')
    return {'passed': True, 'completed': content is not None, 'contacts_audited': len(contacts)}
