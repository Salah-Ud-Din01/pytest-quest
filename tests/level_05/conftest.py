import pytest


@pytest.fixture
def hero():
    from dungeon.hero import Hero

    return Hero("Ada")


@pytest.fixture
def rich_hero(hero):
    hero.gold = 100
    return hero


@pytest.fixture
def backpack():
    from dungeon.inventory import Inventory

    return Inventory()


@pytest.fixture
def shop():
    from dungeon.inventory import Item
    from dungeon.shop import Listing, Shop

    return Shop(
        [
            Listing(Item("potion", 0.5, 10), price=20, stock=2),
            Listing(Item("anvil", 50.0, 4), price=5, stock=1),
        ]
    )