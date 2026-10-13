import pytest

from dungeon import bard, config
from dungeon.hero import Hero


def test_bard_is_not_worried_at_exactly_a_quarter(capsys):
    bard.sing_of(Hero("Ada", hp=25))
    _, err = capsys.readouterr()
    assert err == ""


def test_difficulty_defaults_to_normal(monkeypatch):
    monkeypatch.delenv("DUNGEON_DIFFICULTY", raising=False)
    assert config.difficulty() == "normal"


def test_difficulty_ignores_case_and_spaces(monkeypatch):
    monkeypatch.setenv("DUNGEON_DIFFICULTY", "  HaRd ")
    assert config.difficulty() == "hard"


def test_unknown_difficulty_is_refused(monkeypatch):
    monkeypatch.setenv("DUNGEON_DIFFICULTY", "nightmare")
    with pytest.raises(ValueError, match="unknown difficulty"):
        config.difficulty()


@pytest.mark.parametrize(
    "difficulty, base, expected",
    [
        pytest.param("easy", 100, 50, id="easy-halves"),
        pytest.param("normal", 100, 100, id="normal-keeps"),
        pytest.param("hard", 100, 200, id="hard-doubles"),
        pytest.param("easy", 1, 1, id="never-below-one"),
    ],
)
def test_monster_hp_follows_difficulty(monkeypatch, difficulty, base, expected):
    monkeypatch.setenv("DUNGEON_DIFFICULTY", difficulty)
    assert config.monster_hp(base) == expected