import argparse
import sys
from .model import LocalModel
from .server import serve


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--device", choices=["cuda", "cpu"], default="cuda")
    args = parser.parse_args()
    try:
        model = LocalModel(args.model, args.device)
        serve(model, sys.stdin, sys.stdout)
    except Exception as error:
        print(f"Neural worker failed: {type(error).__name__}: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
