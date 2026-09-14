"""Compare paragraph selection with atomic facts on the same frozen cases."""
import json
import hashlib
from datetime import datetime, timezone
import uuid
from reconstruction_dashboard import source_hashes
from run_neural import ROOT, DEFAULT_MODEL, invoke
from document_dataset import dataset
from document_summary import summarize
from atomic_audit import audit_atomic


def sources():
    result=source_hashes()
    for name in ('atomic_audit.py','run_atomic.py'):
        result[name]=hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
    return result


def main():
    folder=ROOT/'results'/('atomic-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ-')+uuid.uuid4().hex[:8])
    folder.mkdir(parents=True)
    print(f'Evidence: {folder}',flush=True)
    config={'workers':[{'name':'cuda','kind':'local','device':'cuda',
                       'python':str(ROOT/'.venv-neural/Scripts/python.exe'),'model':str(DEFAULT_MODEL)}], 'dataset':dataset()}
    (folder/'config.json').write_text(json.dumps(config),encoding='utf-8')
    status={'status':'running'}
    (folder/'status.json').write_text(json.dumps(status),encoding='utf-8')
    try:
        before=sources()
        invoke(['cargo','build','--release','--locked','--offline','--bin','atomic_probe'],folder/'build.stdout.log',folder/'build.stderr.log',180)
        binary=ROOT/'target/release/atomic_probe.exe'
        manifest={'sources_sha256':before,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),
                  'config_sha256':hashlib.sha256((folder/'config.json').read_bytes()).hexdigest()}
        (folder/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        invoke([str(binary),str(folder/'config.json')],folder/'events.jsonl',folder/'worker.stderr.log',300)
        events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
        audit_atomic(events)
        summary=summarize(events,('selected','atomic'))
        summary['warmup_tokens']=next(e['data']['data']['evaluated_tokens'] for e in events if e['kind']=='warmup')
        if before!=sources():
            raise ValueError('Sources changed during run')
        report={'run_id':folder.name,'manifest':manifest,'events':events,'summary':summary,
                'scope':'Controlled annotated facts; granularity/rendering comparison, not distributed neural inference'}
        (folder/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        status={'status':'completed','summary':summary}
        print(json.dumps(summary,indent=2),flush=True)
    except Exception as error:
        status={'status':'failed','error':str(error)}
        raise
    finally:
        (folder/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')


if __name__=='__main__':
    main()
