"""Tests for seeds functionality."""

from backend.seeds import list_narrative_names, load_seeds


def test_load_seeds_shape() -> None:
    """Test that loaded seeds have correct structure."""
    s = load_seeds()
    assert "narratives" in s
    assert isinstance(s["narratives"], list)
    assert all(
        {"name", "terms", "allowNameMatch", "block"} <= set(n.keys())
        for n in s["narratives"]
    )


def test_list_narrative_names_nonempty() -> None:
    """Test that narrative names list is non-empty and contains strings."""
    names = list_narrative_names()
    assert isinstance(names, list)
    assert all(isinstance(x, str) for x in names)
