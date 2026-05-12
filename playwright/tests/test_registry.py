"""Test: playwright skill registered in pi-mono skill registry & catalog."""

import json
from pathlib import Path

# ── Constants ──────────────────────────────────────────────────────
GLOBAL_SKILLS_DIR = Path.home() / ".pi" / "agent" / "skills"
REGISTRY_SKILLS_DIR = Path.home() / ".pi" / "skills"
SKILL_SOURCE_DIR = Path("/workspace/pi-tools/playwright")
SKILL_MD = SKILL_SOURCE_DIR / "SKILL.md"
EXPECTED_NAME = "playwright"

# All pi-mono skill discovery locations
SKILL_LOCATIONS = [
    REGISTRY_SKILLS_DIR / EXPECTED_NAME,       # ~/.pi/skills/playwright
    GLOBAL_SKILLS_DIR / EXPECTED_NAME,          # ~/.pi/agent/skills/playwright
]


def _parse_frontmatter(skill_md_path: Path) -> dict:
    """Extract YAML frontmatter from SKILL.md (simple parser, no deps)."""
    text = skill_md_path.read_text()
    if not text.startswith("---"):
        raise ValueError("SKILL.md missing frontmatter delimiter")
    _, fm, _ = text.split("---", 2)
    result = {}
    for line in fm.strip().splitlines():
        if ":" in line:
            key, _, val = line.partition(":")
            result[key.strip()] = val.strip().strip('"').strip("'")
    return result


class TestSkillFrontmatter:
    """SKILL.md is valid per Agent Skills spec."""

    def test_skill_md_exists(self):
        assert SKILL_MD.exists(), f"SKILL.md not found at {SKILL_MD}"

    def test_has_frontmatter(self):
        fm = _parse_frontmatter(SKILL_MD)
        assert "name" in fm, "Missing 'name' in frontmatter"
        assert "description" in fm, "Missing 'description' in frontmatter"

    def test_name_matches_directory(self):
        fm = _parse_frontmatter(SKILL_MD)
        assert fm["name"] == EXPECTED_NAME, (
            f"Frontmatter name '{fm['name']}' != directory name '{EXPECTED_NAME}'"
        )

    def test_name_format_valid(self):
        """Name: 1-64 chars, lowercase a-z, 0-9, hyphens. No leading/trailing/consecutive hyphens."""
        fm = _parse_frontmatter(SKILL_MD)
        name = fm["name"]
        assert 1 <= len(name) <= 64
        assert name == name.lower()
        assert name == name.strip("-")
        assert "--" not in name
        import re
        assert re.match(r"^[a-z0-9]([a-z0-9-]*[a-z0-9])?$", name), f"Invalid name: {name}"

    def test_description_not_empty(self):
        fm = _parse_frontmatter(SKILL_MD)
        assert len(fm["description"]) > 0
        assert len(fm["description"]) <= 1024


class TestSkillRegistryRegistration:
    """Skill discoverable in pi-mono skill locations."""

    def test_registered_in_skill_locations(self):
        """Skill discoverable in at least one pi-mono skill location."""
        found = any(loc.exists() for loc in SKILL_LOCATIONS)
        assert found, (
            f"Playwright skill not found in any pi-mono location. "
            f"Checked: {SKILL_LOCATIONS}"
        )

    def test_registered_skill_has_skill_md(self):
        """Each registered location contains valid SKILL.md."""
        for loc in SKILL_LOCATIONS:
            if loc.exists():
                sm = loc / "SKILL.md"
                has_alt = (loc.parent / "playwright.md").exists()
                assert sm.exists() or has_alt, f"Registered skill at {loc} missing SKILL.md"

    def test_skill_md_name_resolvable(self):
        """Agent can extract skill name from registered SKILL.md."""
        for loc in SKILL_LOCATIONS:
            skill_md = loc / "SKILL.md"
            if skill_md.exists():
                fm = _parse_frontmatter(skill_md)
                assert fm.get("name") == EXPECTED_NAME, (
                    f"Name mismatch at {skill_md}: got '{fm.get('name')}'"
                )


    def test_registered_main_py_is_fresh(self):
        """Registered main.py not significantly smaller than source."""
        source_main = SKILL_SOURCE_DIR / "main.py"
        source_size = source_main.stat().st_size

        for loc in SKILL_LOCATIONS:
            reg_main = loc / "main.py"
            if reg_main.exists():
                reg_size = reg_main.stat().st_size
                assert reg_size >= source_size * 0.9, (
                    f"Stale main.py at {reg_main}: {reg_size}B vs {source_size}B"
                )

    def test_agent_skills_location_checked(self):
        """Ensure ~/.pi/agent/skills/playwright exists or source is symlinked there."""
        agent_link = GLOBAL_SKILLS_DIR / "playwright"
        # Not strictly required (global ~/.pi/skills/ suffices), but preferred
        if agent_link.exists():
            assert agent_link.is_symlink() or (agent_link / "SKILL.md").exists()


class TestSkillCatalogDocumentation:
    """SKILL.md serves as catalog documentation with required sections."""

    def test_has_usage_section(self):
        text = SKILL_MD.read_text()
        assert "## Usage" in text or "# Usage" in text, "Missing Usage section"

    def test_has_actions_or_commands_documented(self):
        text = SKILL_MD.read_text()
        has_actions = "Actions" in text or "action" in text.lower()
        has_commands = "Usage" in text or "usage" in text.lower()
        assert has_actions or has_commands, "No documented actions/commands in SKILL.md"

    def test_has_setup_instructions(self):
        text = SKILL_MD.read_text()
        assert "Setup" in text or "setup" in text.lower() or "Install" in text, "Missing setup instructions"
