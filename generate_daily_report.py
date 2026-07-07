from __future__ import annotations

from report_engine import build_report_bundle, write_outputs


def main() -> int:
    bundle = build_report_bundle()
    paths = write_outputs(bundle)
    print(f"Wrote {paths['markdown']}")
    print(f"Wrote {paths['html']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
