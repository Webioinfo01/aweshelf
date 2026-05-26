"""aweswitch config parsing and profile detection."""

import json
import os
from pathlib import Path
from typing import Optional


AWESWITCH_CONFIG = Path("~/.config/aweswitch/config.json")


def aweswitch_config_path() -> Path:
    env = os.environ.get("AWESWITCH_CONFIG")
    if env:
        return Path(env).expanduser()
    return AWESWITCH_CONFIG.expanduser()


def load_aweswitch_config() -> Optional[dict]:
    path = aweswitch_config_path()
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        if isinstance(data.get("profiles"), dict):
            return data
    except (json.JSONDecodeError, OSError):
        pass
    return None


def detect_profile(session_env: dict) -> Optional[str]:
    config = load_aweswitch_config()
    if not config:
        return None

    base_url = session_env.get("ANTHROPIC_BASE_URL", "")
    model = session_env.get("ANTHROPIC_MODEL", "")

    if not base_url and not model:
        return None

    for provider, profiles in config.get("profiles", {}).items():
        if not isinstance(profiles, dict):
            continue
        for name, profile in profiles.items():
            if not isinstance(profile, dict):
                continue
            env = profile.get("env", {})
            p_url = env.get("ANTHROPIC_BASE_URL", "")
            p_model = env.get("ANTHROPIC_MODEL", "")
            if base_url and p_url and base_url == p_url:
                if not model or not p_model or model == p_model:
                    return name
            if model and p_model and model == p_model:
                if not base_url or not p_url:
                    return name

    return None


def profile_exists(profile_name: str) -> bool:
    config = load_aweswitch_config()
    if not config:
        return False
    for provider, profiles in config.get("profiles", {}).items():
        if isinstance(profiles, dict) and profile_name in profiles:
            return True
    return False


def build_resume_command(provider: str, profile_name: Optional[str], session_id: str, raw: bool = False) -> list[str]:
    if raw or not profile_name:
        if provider == "codex":
            return ["codex", "resume", session_id]
        return ["claude", "--resume", session_id]
    return ["aweswitch", profile_name, "--resume", session_id]
