from __future__ import annotations

import argparse
from pathlib import Path

from hubspot_publish import DEFAULT_CONFIG_PATH, HubSpotPublishError, config_exists, publish_bundle
from report_engine import build_report_bundle, write_outputs


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate the Old Bass River daily report.")
    parser.add_argument("--publish-hubspot", action="store_true", help="Publish the generated HTML to HubSpot using hubspot_publish.json")
    parser.add_argument(
        "--publish-hubspot-if-configured",
        action="store_true",
        help="Publish to HubSpot only when hubspot_publish.json exists. Otherwise skip cleanly.",
    )
    parser.add_argument(
        "--hubspot-config",
        default=str(DEFAULT_CONFIG_PATH),
        help="Path to the HubSpot publish config JSON file.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    bundle = build_report_bundle()
    paths = write_outputs(bundle)
    print(f"Wrote {paths['markdown']}")
    print(f"Wrote {paths['html']}")

    should_publish = args.publish_hubspot or args.publish_hubspot_if_configured
    config_path = Path(args.hubspot_config)

    if not should_publish:
        return 0

    if args.publish_hubspot_if_configured and not config_exists(config_path):
        print(f"HubSpot publish skipped because config was not found at {config_path}")
        return 0

    try:
        result = publish_bundle(bundle, config_path)
    except HubSpotPublishError as exc:
        print(f"HubSpot publish failed: {exc}")
        return 1

    print(f"HubSpot {result.action}: id={result.object_id}")
    if result.url:
        print(f"HubSpot URL: {result.url}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
