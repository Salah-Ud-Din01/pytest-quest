import random

import pytest

from dungeon import dice, portal, raven
from dungeon.hero import Hero
from dungeon.inventory import Inventory, Item
from dungeon.shop import Listing, OutOfStockError, Shop


def make_shop():
    return Shop([Listing(Item("potion", 0.5, 10), price=20, stock=2)])


# dice
def test_roll_stays_between_one_and_the_number_of_sides():
    for seed in range(50):
        assert 1 <= dice.roll(6, random.Random(seed)) <= 6


def test_the_same_seed_gives_the_same_roll():
    assert dice.roll(20, random.Random(7)) == dice.roll(20, random.Random(7))


def test_a_die_needs_at_least_two_sides():
    with pytest.raises(ValueError):
        dice.roll(1)


def test_roll_notation_adds_the_modifier():
    total = dice.roll_notation("2d6+3", random.Random(7))
    assert 5 <= total <= 15
    assert total == dice.roll_notation("2d6+3", random.Random(7))


# hero
def test_max_hp_must_be_positive():
    with pytest.raises(ValueError):
        Hero("Ada", max_hp=0)


def test_healing_a_negative_amount_is_refused():
    with pytest.raises(ValueError):
        Hero("Ada").heal(-5)


def test_negative_xp_is_refused():
    with pytest.raises(ValueError):
        Hero("Ada").gain_xp(-5)


# inventory
def test_max_weight_must_be_positive():
    with pytest.raises(ValueError):
        Inventory(max_weight=0)


def test_quantity_must_be_at_least_one():
    with pytest.raises(ValueError):
        Inventory().add(Item("potion", 0.1), quantity=0)


def test_removing_more_than_you_carry_is_refused():
    with pytest.raises(LookupError):
        Inventory().remove("potion")


def test_removing_some_keeps_the_rest():
    backpack = Inventory()
    backpack.add(Item("potion", 0.1), quantity=3)
    assert backpack.remove("potion", 2) == Item("potion", 0.1)
    assert backpack.count("potion") == 1


def test_removing_everything_empties_the_slot():
    backpack = Inventory()
    backpack.add(Item("potion", 0.1))
    backpack.remove("potion")
    assert backpack.count("potion") == 0
    assert "potion" not in backpack


def test_total_value_length_and_contains():
    backpack = Inventory()
    backpack.add(Item("potion", 0.1, 5), quantity=2)
    backpack.add(Item("sword", 3.0, 20))
    assert backpack.total_value == 30
    assert len(backpack) == 3
    assert "potion" in backpack
    assert "dragon" not in backpack


# portal (faking the platform, so it works on Windows too)
def test_portal_describes_the_destination_off_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    assert "Valhalla" in portal.open_portal("Valhalla")


def test_portal_is_refused_on_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    with pytest.raises(portal.PortalError):
        portal.open_portal("Valhalla")


# raven
def test_raven_needs_at_least_one_attempt():
    with pytest.raises(ValueError):
        raven.send_raven("Ada", "Hello", attempts=0)


# shop
def test_a_listing_cannot_have_a_negative_price():
    with pytest.raises(ValueError):
        Shop().add_listing(Listing(Item("potion", 0.5, 10), price=-1))


def test_a_listing_cannot_have_negative_stock():
    with pytest.raises(ValueError):
        Shop().add_listing(Listing(Item("potion", 0.5, 10), price=1, stock=-1))


def test_price_of_a_listed_item():
    assert make_shop().price_of("potion") == 20


def test_price_of_an_unlisted_item_is_refused():
    with pytest.raises(OutOfStockError):
        make_shop().price_of("anvil")


def test_stock_of_an_unlisted_item_is_zero():
    assert make_shop().stock_of("anvil") == 0