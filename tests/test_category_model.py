from app.models import Category, User


def test_get_from_id(
    user_1: User,
    user_2: User,
    category_1: Category,
    category_2: Category,
) -> None:
    assert Category.get_from_id(category_1.id, user_1) == category_1
    assert Category.get_from_id(category_2.id, user_2) == category_2
    assert Category.get_from_id(category_1.id, user_2) == None
    assert Category.get_from_id(category_2.id, user_1) == None
