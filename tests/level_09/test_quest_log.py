import pytest

from dungeon.hero import Hero
from dungeon.quests import Quest, QuestError, QuestLog, QuestState


def make_quest(**overrides):
    values = {
        "title": "Rats",
        "objectives": ["kill rat", "bring tail"],
        "reward_xp": 250,
        "reward_gold": 30,
    }
    values.update(overrides)
    return Quest(**values)


@pytest.fixture
def hero():
    return Hero("Ada")


@pytest.fixture
def log():
    return QuestLog()


def test_max_active_must_be_positive():
    with pytest.raises(ValueError):
        QuestLog(max_active=0)


def test_an_offered_quest_is_available(log):
    quest = make_quest()
    log.offer(quest)
    assert log.get("Rats") is quest
    assert quest.state is QuestState.AVAILABLE


def test_duplicate_titles_are_refused(log):
    log.offer(make_quest())
    with pytest.raises(QuestError, match="already in the log"):
        log.offer(make_quest())


def test_a_quest_needs_an_objective(log):
    with pytest.raises(QuestError, match="at least one objective"):
        log.offer(make_quest(objectives=[]))


def test_unknown_quest_is_an_error(log):
    with pytest.raises(QuestError, match="unknown quest"):
        log.get("Nope")


def test_remaining_lists_open_objectives_in_order():
    quest = make_quest(objectives=["a", "b", "c"])
    quest.done.add("b")
    assert quest.remaining == ["a", "c"]


def test_accepting_makes_a_quest_active(log, hero):
    quest = make_quest()
    log.offer(quest)
    assert log.accept(hero, "Rats") is quest
    assert quest.state is QuestState.ACTIVE
    assert log.active() == [quest]


def test_a_quest_can_only_be_accepted_once(log, hero):
    log.offer(make_quest())
    log.accept(hero, "Rats")
    with pytest.raises(QuestError, match="is active"):
        log.accept(hero, "Rats")


def test_hero_needs_the_required_level(log, hero):
    quest = make_quest(required_level=2)
    log.offer(quest)
    with pytest.raises(QuestError, match="must be level 2"):
        log.accept(hero, "Rats")
    assert quest.state is QuestState.AVAILABLE


def test_hero_at_exactly_the_required_level_may_accept(log):
    quest = make_quest(required_level=2)
    log.offer(quest)
    log.accept(Hero("Ada", level=2), "Rats")
    assert quest.state is QuestState.ACTIVE


def test_at_most_max_active_quests_at_once(hero):
    log = QuestLog(max_active=2)
    for title in ("Q1", "Q2", "Q3"):
        log.offer(make_quest(title=title))
    log.accept(hero, "Q1")
    log.accept(hero, "Q2")
    with pytest.raises(QuestError, match="already 2 active"):
        log.accept(hero, "Q3")
    assert log.get("Q3").state is QuestState.AVAILABLE


def test_a_finished_objective_is_not_the_last_one(log, hero):
    quest = make_quest()
    log.offer(quest)
    log.accept(hero, "Rats")
    assert log.complete_objective("Rats", "kill rat") is False
    assert quest.state is QuestState.ACTIVE
    assert quest.remaining == ["bring tail"]


def test_the_last_objective_completes_the_quest(log, hero):
    quest = make_quest()
    log.offer(quest)
    log.accept(hero, "Rats")
    log.complete_objective("Rats", "kill rat")
    assert log.complete_objective("Rats", "bring tail") is True
    assert quest.state is QuestState.COMPLETED


def test_objectives_need_an_active_quest(log):
    log.offer(make_quest())
    with pytest.raises(QuestError, match="not active"):
        log.complete_objective("Rats", "kill rat")


def test_unknown_objective_is_refused(log, hero):
    log.offer(make_quest())
    log.accept(hero, "Rats")
    with pytest.raises(QuestError, match="not part of"):
        log.complete_objective("Rats", "dance")


def test_turning_in_pays_gold_and_xp(log, hero):
    quest = make_quest()
    log.offer(quest)
    log.accept(hero, "Rats")
    log.complete_objective("Rats", "kill rat")
    log.complete_objective("Rats", "bring tail")
    levels = log.turn_in(hero, "Rats")
    assert levels == 2
    assert hero.gold == 30
    assert hero.xp == 50
    assert quest.state is QuestState.TURNED_IN


def test_only_completed_quests_can_be_turned_in(log, hero):
    log.offer(make_quest())
    log.accept(hero, "Rats")
    with pytest.raises(QuestError, match="not completed"):
        log.turn_in(hero, "Rats")
    assert hero.gold == 0
    assert hero.xp == 0


def test_abandoning_wipes_progress(log, hero):
    quest = make_quest()
    log.offer(quest)
    log.accept(hero, "Rats")
    log.complete_objective("Rats", "kill rat")
    log.abandon("Rats")
    assert quest.state is QuestState.AVAILABLE
    assert quest.done == set()
    assert quest.remaining == ["kill rat", "bring tail"]


def test_abandon_needs_an_active_quest(log):
    log.offer(make_quest())
    with pytest.raises(QuestError, match="not active"):
        log.abandon("Rats")


def test_time_only_moves_forward(log):
    with pytest.raises(ValueError):
        log.tick(0)


def test_quests_without_a_deadline_never_fail(log, hero):
    quest = make_quest()
    log.offer(quest)
    log.accept(hero, "Rats")
    assert log.tick(100) == []
    assert quest.state is QuestState.ACTIVE
    assert quest.deadline is None


def test_a_deadline_counts_down(log, hero):
    quest = make_quest(deadline=5)
    log.offer(quest)
    log.accept(hero, "Rats")
    assert log.tick(2) == []
    assert quest.deadline == 3
    assert quest.state is QuestState.ACTIVE


def test_a_quest_fails_when_the_deadline_hits_zero(log, hero):
    quest = make_quest(deadline=2)
    log.offer(quest)
    log.accept(hero, "Rats")
    assert log.tick(2) == [quest]
    assert quest.state is QuestState.FAILED


def test_a_quest_fails_when_the_deadline_is_overshot(log, hero):
    quest = make_quest(deadline=1)
    log.offer(quest)
    log.accept(hero, "Rats")
    assert log.tick(3) == [quest]
    assert quest.state is QuestState.FAILED


def test_tick_ignores_quests_that_are_not_active(log):
    quest = make_quest(deadline=1)
    log.offer(quest)
    assert log.tick() == []
    assert quest.state is QuestState.AVAILABLE
    assert quest.deadline == 1


def test_summary_counts_quests_per_state(log, hero):
    for title in ("Q1", "Q2", "Q3"):
        log.offer(make_quest(title=title))
    log.accept(hero, "Q1")
    assert log.summary() == {
        "available": 2,
        "active": 1,
        "completed": 0,
        "turned_in": 0,
        "failed": 0,
    }