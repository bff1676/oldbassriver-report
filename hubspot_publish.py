from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

ROOT = Path(__file__).parent
DEFAULT_CONFIG_PATH = ROOT / "hubspot_publish.json"
EXAMPLE_CONFIG_PATH = ROOT / "hubspot_publish.example.json"
DEFAULT_ENDPOINT = "https://api.hubapi.com/cms/v3/blogs/posts"


class HubSpotPublishError(RuntimeError):
    pass


@dataclass
class HubSpotPublishResult:
    action: str
    object_id: str
    url: str | None
    raw: dict[str, Any]


def config_exists(path: Path | None = None) -> bool:
    return (path or DEFAULT_CONFIG_PATH).exists()


def load_config(path: Path | None = None) -> dict[str, Any]:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        raise HubSpotPublishError(
            f"HubSpot config not found at {config_path}. Copy {EXAMPLE_CONFIG_PATH.name} to {config_path.name} and fill it in."
        )

    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise HubSpotPublishError(f"HubSpot config is not valid JSON: {exc}") from exc

    token = str(config.get("access_token", "")).strip()
    if not token:
        raise HubSpotPublishError("HubSpot config is missing access_token.")

    target = str(config.get("target", "blog_post")).strip() or "blog_post"
    if target != "blog_post":
        raise HubSpotPublishError(
            f"Unsupported HubSpot target '{target}'. Current implementation supports 'blog_post'."
        )

    post_config = config.get("blog_post") or {}
    if not post_config.get("content_group_id"):
        raise HubSpotPublishError("HubSpot config is missing blog_post.content_group_id.")
    if not post_config.get("author_id"):
        raise HubSpotPublishError("HubSpot config is missing blog_post.author_id.")

    endpoint = str(config.get("endpoint", DEFAULT_ENDPOINT)).strip() or DEFAULT_ENDPOINT
    config["target"] = target
    config["endpoint"] = endpoint.rstrip("/")
    return config


def publish_bundle(bundle: dict[str, Any], path: Path | None = None) -> HubSpotPublishResult:
    config = load_config(path)
    post_config = config["blog_post"]
    payload = build_blog_post_payload(bundle, post_config)
    post_id = str(post_config.get("post_id", "")).strip()

    endpoint = config["endpoint"]
    method = "PATCH" if post_id else "POST"
    url = f"{endpoint}/{post_id}" if post_id else endpoint

    response = requests.request(
        method,
        url,
        headers={
            "Authorization": f"Bearer {config['access_token']}",
            "Content-Type": "application/json",
        },
        json=payload,
        timeout=45,
    )

    if response.status_code >= 400:
        detail = response.text.strip()
        raise HubSpotPublishError(f"HubSpot publish failed ({response.status_code}): {detail}")

    try:
        data = response.json()
    except ValueError:
        data = {"response_text": response.text}

    return HubSpotPublishResult(
        action="updated" if post_id else "created",
        object_id=str(data.get("id") or post_id or "unknown"),
        url=data.get("url") or data.get("publishedUrl") or data.get("absoluteUrl"),
        raw=data,
    )


def build_blog_post_payload(bundle: dict[str, Any], post_config: dict[str, Any]) -> dict[str, Any]:
    generated_at: datetime = bundle["generated_at"]
    title = render_template(
        str(post_config.get("title_template") or "Old Bass River Fishing Report - {long_date}"),
        generated_at,
    )
    slug = render_template(
        str(post_config.get("slug_template") or "fishing-reports/{iso_date}"),
        generated_at,
        slug_safe=True,
    )
    meta_description = render_template(
        str(
            post_config.get("meta_description_template")
            or "Daily Old Bass River fishing report for {long_date}, including local spots, conditions, tides, and fishing news."
        ),
        generated_at,
    )

    payload: dict[str, Any] = {
        "name": title,
        "slug": slug,
        "state": str(post_config.get("state", "DRAFT")).upper(),
        "contentGroupId": int(post_config["content_group_id"]),
        "blogAuthorId": int(post_config["author_id"]),
        "postBody": bundle["html"],
        "metaDescription": meta_description,
    }

    tag_ids = [int(tag_id) for tag_id in post_config.get("tag_ids", []) if str(tag_id).strip()]
    if tag_ids:
        payload["tagIds"] = tag_ids

    campaign = str(post_config.get("campaign", "")).strip()
    if campaign:
        payload["campaign"] = campaign

    featured_image = str(post_config.get("featured_image", "")).strip()
    if featured_image:
        payload["featuredImage"] = featured_image

    publish_date = str(post_config.get("publish_date", "")).strip()
    if publish_date:
        payload["publishDate"] = publish_date

    language = str(post_config.get("language", "")).strip()
    if language:
        payload["language"] = language

    return payload


def render_template(template: str, generated_at: datetime, slug_safe: bool = False) -> str:
    values = {
        "date": generated_at.strftime("%B %d, %Y"),
        "long_date": generated_at.strftime("%B %d, %Y"),
        "iso_date": generated_at.strftime("%Y-%m-%d"),
        "month": generated_at.strftime("%m"),
        "year": generated_at.strftime("%Y"),
        "weekday": generated_at.strftime("%A"),
    }
    rendered = template.format(**values)
    return slugify(rendered) if slug_safe else rendered


def slugify(value: str) -> str:
    slug = value.lower().strip()
    slug = re.sub(r"[^a-z0-9/\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = re.sub(r"/+", "/", slug)
    return slug.strip("-/")
