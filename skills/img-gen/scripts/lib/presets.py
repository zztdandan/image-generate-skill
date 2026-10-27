"""Preset catalog — GPT-Image / Nano Banana providers used by img-gen.

Loads configuration from the process environment (`os.environ`). No .env file
is read: the host (agent host, shell, systemd unit, CI) injects the IMG_GEN_* variables
at startup.

Key families:
  GPT family:
    IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY
    IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET
  Banana family:
    IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY
    IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET
  Per-preset overrides:
    IMG_GEN_PRESET_<PRESET_ID_UPPER>_API_KEY / _BASE_URL
  Provider-level key (used by every preset of that provider):
    APIYI_API_KEY, IMG_GEN_APIYI_API_KEY, IMG_GEN_LAOZHANG_API_KEY, ...

## Route model

This skill only knows how to *forward a request to a relay site*; it makes no
statement about what any provider charges. What it does encode is **which route
a request takes and in which order routes are tried**:

  route="proxy"           a relay/aggregator site in front of the model (中转站)
  route="official_relay"  a relay that forwards to the official API (官转)
  route="official"        the official API directly

  tier="default"   daily route, walked in order by `--preset auto`
  tier="standard"  extra / experimental routes, only used when named explicitly
  tier="fallback"  official / official-relay routes, reached with --allow-fallback

Billing and quotas belong to whichever gateway your key points at: check with
that provider, not with this skill.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


# ── Environment configuration ───────────────────────────────────────

def env(key: str, default: str = "") -> str:
    """Read a configuration value from the process environment.

    Unset and blank values are treated the same so an `export VAR=` line cannot
    masquerade as a configured channel.
    """
    return os.environ.get(key) or default


# Every variable the skill can consume, in the order the docs list it. Used by
# `check_env.py` / `img-gen check` to tell the user exactly what is missing.
REQUIRED_ANY_OF = (
    "IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY",
    "IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY",
)
OPTIONAL_KEYS = (
    "IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET",
    "IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET",
    "IMG_GEN_GPT_BASE_URL",
    "IMG_GEN_BANANA_BASE_URL",
    "IMAGE_OUTPUT_DIR",
)

# Printed whenever no channel is configured. Kept here so the CLI, check_env.py
# and the docs all tell the user the same next step.
ENV_SETUP_HINT = (
    "Export the key(s) in the environment that starts the host — "
    "`export IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY=...` (and/or "
    "`IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY=...`) — then re-run. "
    "This skill reads the process environment only and never parses .env files."
)


# ── Data model ──────────────────────────────────────────────────────

QUALITIES_GPT2 = ("auto", "low", "medium", "high")
QUALITIES_GPT25 = ("auto", "low", "medium", "high", "xhigh", "max")


@dataclass(frozen=True)
class Preset:
    preset_id: str
    provider: str
    protocol: str  # "openai_images" | "gemini_generate_content"
    base_url: str
    default_model: str
    modes: tuple[str, ...] = ("generate", "edit")
    stability: str = "stable"
    env_key_family: str = "gpt"  # "gpt" | "banana"
    # How the request reaches the model. Deliberately no billing semantics:
    #   "proxy"          relay / aggregator site in front of the model
    #   "official_relay" relay that forwards to the official API
    #   "official"       official API directly
    route: str = "proxy"
    # "default"  daily route, walked by `--preset auto`
    # "standard" extra / experimental route, only when named explicitly
    # "fallback" official / official-relay route, only with --allow-fallback
    tier: str = "standard"
    qualities: tuple[str, ...] = QUALITIES_GPT2
    # "table30": `size` must be one of the 30 documented slots (or "auto").
    # "legacy": gateway accepts model-specific sizes.
    size_policy: str = "legacy"
    note: str = ""


# ── All registered presets ──────────────────────────────────────────

PRESETS: dict[str, Preset] = {
    # ── GPT-Image 2.5 VIP via apiyi ────────────────────────────────
    # 30 fixed size slots, 6 quality levels, 90–150 s per image,
    # background="transparent" returns real alpha.
    "apiyi_gpt_image_2_5_vip": Preset(
        "apiyi_gpt_image_2_5_vip", "apiyi", "openai_images",
        "https://api.apiyi.com/v1", "gpt-image-2.5-vip",
        tier="default", qualities=QUALITIES_GPT25, size_policy="table30",
        note="别名→sunburst-vip；画质与编辑精度优先的默认线路",
    ),
    "apiyi_gpt_image_2_5_flare_vip": Preset(
        "apiyi_gpt_image_2_5_flare_vip", "apiyi", "openai_images",
        "https://api.apiyi.com/v1", "gpt-image-2.5-flare-vip",
        tier="default", qualities=QUALITIES_GPT25, size_policy="table30",
        note="速度优先的默认线路；画面偏软，适合草稿与批量试稿",
    ),
    "apiyi_gpt_image_2_5_sunburst_vip": Preset(
        "apiyi_gpt_image_2_5_sunburst_vip", "apiyi", "openai_images",
        "https://api.apiyi.com/v1", "gpt-image-2.5-sunburst-vip",
        tier="default", qualities=QUALITIES_GPT25, size_policy="table30",
        note="显式 sunburst-vip 全名；与 gpt-image-2.5-vip 同款",
    ),
    "apiyi_gpt_image_2_vip": Preset(
        "apiyi_gpt_image_2_vip", "apiyi", "openai_images",
        "https://api.apiyi.com/v1", "gpt-image-2-vip",
        tier="default", qualities=QUALITIES_GPT2, size_policy="table30",
        note="上一代 VIP；quality 只到 high（xhigh/max 会被拒）",
    ),
    # ── GPT-Image 2.5 VIP via laozhang ─────────────────────────────
    "laozhang_gpt_image_2_5_flare_vip": Preset(
        "laozhang_gpt_image_2_5_flare_vip", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2.5-flare-vip",
        tier="default", qualities=QUALITIES_GPT25, size_policy="table30",
        note="apiyi 不可用时的备选默认线路；上游饱和时可能 429",
    ),
    "laozhang_gpt_image_2_5_sunburst_vip": Preset(
        "laozhang_gpt_image_2_5_sunburst_vip", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2.5-sunburst-vip",
        tier="default", qualities=QUALITIES_GPT25, size_policy="table30",
        note="laozhang 画质优先 VIP；比 flare 慢",
    ),
    # ── Official-relay routes — fallback chain only ────────────────
    "apiyi_gpt_image_2_5_flare": Preset(
        "apiyi_gpt_image_2_5_flare", "apiyi", "openai_images",
        "https://api.apiyi.com/v1", "gpt-image-2.5-flare",
        route="official_relay", tier="fallback", qualities=QUALITIES_GPT25,
        note="官转 2.5 flare；回退线路",
    ),
    "apiyi_gpt_image_2_5_sunburst": Preset(
        "apiyi_gpt_image_2_5_sunburst", "apiyi", "openai_images",
        "https://api.apiyi.com/v1", "gpt-image-2.5-sunburst",
        route="official_relay", tier="fallback", qualities=QUALITIES_GPT25,
        note="官转 2.5 sunburst；回退线路",
    ),
    "laozhang_gpt_image_2_5_flare": Preset(
        "laozhang_gpt_image_2_5_flare", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2.5-flare",
        route="official_relay", tier="fallback", qualities=QUALITIES_GPT25,
        note="官转 2.5 flare；回退线路",
    ),
    "laozhang_gpt_image_2_5_sunburst": Preset(
        "laozhang_gpt_image_2_5_sunburst", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2.5-sunburst",
        route="official_relay", tier="fallback", qualities=QUALITIES_GPT25,
        note="官转 2.5 sunburst；回退线路",
    ),
    # ── Older / other GPT Image 2 presets ──────────────────────────
    "laozhang_gpt_image_2_vip": Preset(
        "laozhang_gpt_image_2_vip", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2-vip",
        tier="standard", qualities=QUALITIES_GPT2, size_policy="table30",
        note="上一代 VIP；保留给既有配置",
    ),
    "laozhang_gpt_image_2_default": Preset(
        "laozhang_gpt_image_2_default", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2",
        route="official_relay", tier="fallback", qualities=QUALITIES_GPT2,
        note="官转 gpt-image-2；回退线路",
    ),
    "laozhang_gpt_image_2_enterprise": Preset(
        "laozhang_gpt_image_2_enterprise", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2",
        route="official_relay", tier="fallback", qualities=QUALITIES_GPT2,
        note="企业通道官转 gpt-image-2；回退线路",
    ),
    "laozhang_gpt_image_2_sora_official": Preset(
        "laozhang_gpt_image_2_sora_official", "laozhang", "openai_images",
        "https://api.laozhang.ai/v1", "gpt-image-2",
        route="official_relay", tier="fallback", qualities=QUALITIES_GPT2,
        note="Sora 官方通道的 gpt-image-2；回退线路",
    ),
    "openai_gpt_image_2": Preset(
        "openai_gpt_image_2", "openai", "openai_images",
        "https://api.openai.com/v1", "gpt-image-2",
        route="official", tier="fallback", qualities=QUALITIES_GPT2,
        note="官方直连；只在需要官方字段行为时使用",
    ),
    "apiyi_gpt_image_2": Preset(
        "apiyi_gpt_image_2", "apiyi", "openai_images",
        "https://api.apiyi.com/v1", "gpt-image-2",
        route="official_relay", tier="fallback", qualities=QUALITIES_GPT2,
        note="官转 gpt-image-2；回退线路",
    ),
    "right_codes_gpt_image_2": Preset(
        "right_codes_gpt_image_2", "right_codes", "openai_images",
        "https://www.right.codes/draw/v1", "gpt-image-2",
        tier="standard", qualities=QUALITIES_GPT2,
    ),
    "right_codes_gpt_image_2_vip": Preset(
        "right_codes_gpt_image_2_vip", "right_codes", "openai_images",
        "https://www.right.codes/draw/v1", "gpt-image-2-vip",
        stability="experimental", tier="standard",
        qualities=QUALITIES_GPT2, size_policy="table30",
    ),
    "right_codes_nano_with_image_api_images": Preset(
        "right_codes_nano_with_image_api_images", "right_codes", "openai_images",
        "https://www.right.codes/draw/v1", "nano-banana-2",
        tier="standard",
    ),
    "copperai_gpt_image_2": Preset(
        "copperai_gpt_image_2", "copperai", "openai_images",
        "https://api.copperai.dev/v1", "gpt-image-2",
        stability="experimental", tier="standard",
        qualities=QUALITIES_GPT2,
    ),
    # ── Nano Banana 2 presets (Gemini generateContent protocol) ──
    "laozhang_nano_banana_pro": Preset(
        "laozhang_nano_banana_pro", "laozhang", "gemini_generate_content",
        "https://api.laozhang.ai", "gemini-3-pro-image-preview",
        env_key_family="banana", tier="standard",
    ),
    "apiyi_nano_banana_2": Preset(
        "apiyi_nano_banana_2", "apiyi", "gemini_generate_content",
        "https://api.apiyi.com", "gemini-3.1-flash-image-preview",
        env_key_family="banana", tier="standard",
    ),
    "google_nano_banana": Preset(
        "google_nano_banana", "google", "gemini_generate_content",
        "https://generativelanguage.googleapis.com", "gemini-3.1-flash-image-preview",
        env_key_family="banana", route="official", tier="standard",
    ),
}


# ── Auto-selection chains ───────────────────────────────────────────
#
# `--preset auto` (the CLI default) walks DEFAULT_CHAIN in order and only
# falls through on transport/quota/saturation errors (403/429/5xx/timeout),
# never on a 400 parameter rejection.
#
# DEFAULT_CHAIN: the relay sites the skill routes to by default. apiyi first,
# then laozhang as an equivalent alternative when apiyi's key is out of quota.
#
# FALLBACK_CHAIN: official / official-relay routes. Only appended when the
# caller passes --allow-fallback, i.e. after every default route has failed
# or the task provably needs a field only the official relay exposes.

DEFAULT_CHAIN: tuple[str, ...] = (
    "apiyi_gpt_image_2_5_vip",
    "apiyi_gpt_image_2_5_flare_vip",
    "laozhang_gpt_image_2_5_sunburst_vip",
    "laozhang_gpt_image_2_5_flare_vip",
)

FALLBACK_CHAIN: tuple[str, ...] = (
    "apiyi_gpt_image_2_5_sunburst",
    "apiyi_gpt_image_2_5_flare",
    "laozhang_gpt_image_2_5_sunburst",
    "laozhang_gpt_image_2_5_flare",
    "laozhang_gpt_image_2_default",
)

DEFAULT_PRESET = "apiyi_gpt_image_2_5_vip"

# Human-readable route labels reused by CLI output and docs. Intentionally
# says nothing about what any gateway charges.
TIER_LABELS = {
    "default": "default route",
    "standard": "alternate / experimental",
    "fallback": "fallback (official / official-relay)",
}


# ── Size / aspect-ratio mapping ─────────────────────────────────────

SIZE_MAP: dict[str, dict[str, dict[str, int]]] = {
    "1K": {
        "1:1":  {"gpt": (1280, 1280), "nano": (1024, 1024)},
        "2:3":  {"gpt": (848, 1280),  "nano": (848, 1264)},
        "3:2":  {"gpt": (1280, 848),  "nano": (1264, 848)},
        "3:4":  {"gpt": (960, 1280),  "nano": (896, 1200)},
        "4:3":  {"gpt": (1280, 960),  "nano": (1200, 896)},
        "4:5":  {"gpt": (1024, 1280), "nano": (928, 1152)},
        "5:4":  {"gpt": (1280, 1024), "nano": (1152, 928)},
        "9:16": {"gpt": (720, 1280),  "nano": (768, 1376)},
        "16:9": {"gpt": (1280, 720),  "nano": (1376, 768)},
        "21:9": {"gpt": (1280, 544),  "nano": (1584, 672)},
    },
    "2K": {
        "1:1":  {"gpt": (2048, 2048), "nano": (2048, 2048)},
        "2:3":  {"gpt": (1360, 2048), "nano": (1696, 2528)},
        "3:2":  {"gpt": (2048, 1360), "nano": (2528, 1696)},
        "3:4":  {"gpt": (1536, 2048), "nano": (1792, 2400)},
        "4:3":  {"gpt": (2048, 1536), "nano": (2400, 1792)},
        "4:5":  {"gpt": (1632, 2048), "nano": (1856, 2304)},
        "5:4":  {"gpt": (2048, 1632), "nano": (2304, 1856)},
        "9:16": {"gpt": (1152, 2048), "nano": (1536, 2752)},
        "16:9": {"gpt": (2048, 1152), "nano": (2752, 1536)},
        "21:9": {"gpt": (2048, 864),  "nano": (3168, 1344)},
    },
    "4K": {
        "1:1":  {"gpt": (2880, 2880), "nano": (4096, 4096)},
        "2:3":  {"gpt": (2336, 3520), "nano": (3392, 5056)},
        "3:2":  {"gpt": (3520, 2336), "nano": (5056, 3392)},
        "3:4":  {"gpt": (2480, 3312), "nano": (3584, 4800)},
        "4:3":  {"gpt": (3312, 2480), "nano": (4800, 3584)},
        "4:5":  {"gpt": (2560, 3216), "nano": (3712, 4608)},
        "5:4":  {"gpt": (3216, 2560), "nano": (4608, 3712)},
        "9:16": {"gpt": (2160, 3840), "nano": (3072, 5504)},
        "16:9": {"gpt": (3840, 2160), "nano": (5504, 3072)},
        "21:9": {"gpt": (3840, 1632), "nano": (6336, 2688)},
    },
}

VALID_SIZES = list(SIZE_MAP.keys())
VALID_RATIOS = sorted(SIZE_MAP["1K"].keys())


def resolve_size(tier: str, ratio: str, protocol: str) -> tuple[int, int]:
    """Return (width, height) for the given tier + ratio + protocol."""
    key = "gpt" if protocol == "openai_images" else "nano"
    return SIZE_MAP[tier][ratio][key]


# The 30 documented `size` slots (10 ratios × 3 tiers). On table30 presets
# only these strings are guaranteed to come back at the requested pixel size;
# anything else is silently re-aligned by the upstream gateway.
TABLE30_SIZES: tuple[str, ...] = tuple(
    f"{w}x{h}"
    for tier in ("1K", "2K", "4K")
    for w, h in (v["gpt"] for v in SIZE_MAP[tier].values())
)


def check_size_table30(size: str) -> str | None:
    """Return an error message when `size` is not one of the 30 slots."""
    if size in TABLE30_SIZES or size == "auto":
        return None
    return (
        f"size {size!r} is not one of the 30 documented slots for this preset "
        f"(or 'auto'); it may be silently re-aligned upstream. "
        f"Use one of: {', '.join(TABLE30_SIZES)}"
    )


# ── Configuration detection (from the environment) ──────────────────

def detect_gpt_config() -> dict | None:
    """Detect the active GPT (OpenAI Images) preset from the environment."""
    preset_id = (
        env("IMG_GEN_GPT_IMAGE_2_OFFICIAL_PRESET")
        or DEFAULT_PRESET
    )
    api_key = resolve_preset_api_key(preset_id)
    if not api_key:
        return None
    preset = PRESETS.get(preset_id)
    base_url = resolve_preset_base_url(preset_id) or env("IMG_GEN_GPT_BASE_URL")
    return {
        "api_key": api_key,
        "preset_id": preset_id,
        "base_url": base_url,
        "model": preset.default_model if preset else None,
        "preset": preset,
        "ok": bool(base_url),
    }


def detect_banana_config() -> dict | None:
    """Detect the active Nano Banana (Gemini) preset from the environment."""
    preset_id = env("IMG_GEN_NANO_BANANA_2_OFFICIAL_PRESET")
    api_key = resolve_preset_api_key(preset_id)
    if not api_key:
        return None
    preset = PRESETS.get(preset_id)
    base_url = resolve_preset_base_url(preset_id) or env("IMG_GEN_BANANA_BASE_URL")
    return {
        "api_key": api_key,
        "preset_id": preset_id,
        "base_url": base_url,
        "model": preset.default_model if preset else None,
        "preset": preset,
        "ok": bool(base_url),
    }


# ── Per-preset / provider-level override resolution ─────────────────
#
# Resolution order for a key:
#   1. IMG_GEN_PRESET_<PRESET_ID_UPPER>_API_KEY      (exact preset)
#   2. provider candidates (see PROVIDER_KEY_ENV_CANDIDATES)
#   3. family key (IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY / banana)
#
# Step 2 matters for new presets that share a provider account with an
# already-configured sibling (e.g. apiyi VIP models reuse the apiyi key),
# so adding a preset never requires duplicating a secret into the host env.

PROVIDER_KEY_ENV_CANDIDATES: dict[str, tuple[str, ...]] = {
    "apiyi": (
        "APIYI_API_KEY",  # name required by apiyi docs
        "IMG_GEN_APIYI_API_KEY",
        "IMG_GEN_PRESET_APIYI_GPT_IMAGE_2_5_FLARE_API_KEY",
        "IMG_GEN_PRESET_APIYI_GPT_IMAGE_2_API_KEY",
    ),
    "laozhang": ("IMG_GEN_LAOZHANG_API_KEY",),
}


def resolve_preset_api_key(preset_id: str) -> str:
    """Per-preset key, then provider-level key, then family key."""
    prefix = "IMG_GEN_PRESET_" + preset_id.upper().replace("-", "_")
    key = env(f"{prefix}_API_KEY")
    if key:
        return key
    p = PRESETS.get(preset_id)
    if p is None:
        return ""
    for env_name in PROVIDER_KEY_ENV_CANDIDATES.get(p.provider, ()):
        key = env(env_name)
        if key:
            return key
    if p.env_key_family == "banana":
        return env("IMG_GEN_NANO_BANANA_2_OFFICIAL_API_KEY")
    return env("IMG_GEN_GPT_IMAGE_2_OFFICIAL_API_KEY")


def resolve_preset_base_url(preset_id: str) -> str:
    """Per-preset base URL override; falls back to the preset's own base_url."""
    prefix = "IMG_GEN_PRESET_" + preset_id.upper().replace("-", "_")
    base = env(f"{prefix}_BASE_URL")
    if base:
        return base
    p = PRESETS.get(preset_id)
    return p.base_url if p else ""


def list_available_presets() -> list[str]:
    """Return which preset IDs have an API key in the environment."""
    return [pid for pid in PRESETS if resolve_preset_api_key(pid)]


def build_auto_chain(allow_fallback: bool = False, protocol: str | None = None) -> list[str]:
    """Return the ordered preset IDs `--preset auto` should try."""
    chain = list(DEFAULT_CHAIN)
    if allow_fallback:
        chain += list(FALLBACK_CHAIN)
    if protocol:
        chain = [pid for pid in chain if PRESETS.get(pid) and PRESETS[pid].protocol == protocol]
    return [pid for pid in chain if resolve_preset_api_key(pid)]


def validate_quality(preset_id: str, quality: str | None) -> str | None:
    """Return an error message when `quality` is not accepted by the preset."""
    if not quality:
        return None
    p = PRESETS.get(preset_id)
    if p is None:
        return None
    if quality not in p.qualities:
        return (
            f"quality {quality!r} is not accepted by {preset_id} "
            f"({p.default_model}); accepted: {', '.join(p.qualities)}"
        )
    return None


def get_output_dir() -> str:
    """Return the default image output directory."""
    return env("IMAGE_OUTPUT_DIR") or os.path.expanduser("~/images")
