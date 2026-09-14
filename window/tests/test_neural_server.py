import io
import json
import unittest
from neural_worker.server import serve


class ExplicitTestDouble:
    metadata = {"test_double": True, "load_count": 1}

    def execute(self, request):
        if request["id"] == "fails":
            raise RuntimeError("intentional test exception")
        return {"test_only": True}


class ServerTests(unittest.TestCase):
    def test_one_handshake_correlated_results_and_explicit_failures(self):
        def request(identity):
            return json.dumps({"schema": 1, "id": identity, "op": "generate",
                               "prompts": ["test"], "max_new_tokens": 1})
        source = io.StringIO("\n".join([request("one"), request("fails"), request("two")]))
        target = io.StringIO()
        serve(ExplicitTestDouble(), source, target)
        records = [json.loads(line) for line in target.getvalue().splitlines()]
        self.assertEqual([r["kind"] for r in records], ["ready", "result", "error", "result"])
        self.assertEqual([r["id"] for r in records[1:]], ["one", "fails", "two"])
        self.assertNotIn("data", records[2])
        self.assertEqual(records[3]["sequence"], 3)
