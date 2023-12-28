import operator
from backend.utils.query_to_filters import query_to_filters


def test_empty_query_string():
    assert query_to_filters("") == []


def test_simple_query_string():
    assert query_to_filters("name=John") == [
        {"field": "name", "value": "John", "op": operator.eq}
    ]


def test_query_string_with_operators():
    query = "age[gt]=30&salary[lt]=5000"
    expected = [
        {"field": "age", "value": "30", "op": operator.gt},
        {"field": "salary", "value": "5000", "op": operator.lt},
    ]
    assert query_to_filters(query) == expected


def test_query_with_control_fields():
    query = "name=John&page=2"
    expected = [{"field": "name", "value": "John", "op": operator.eq}]
    assert query_to_filters(query) == expected


def test_query_with_url_encoded_characters():
    query = "name=John+Doe&city=New%20York"
    expected = [
        {"field": "name", "value": "John Doe", "op": operator.eq},
        {"field": "city", "value": "New York", "op": operator.eq},
    ]
    assert query_to_filters(query) == expected
