from app.services.todo_service import parse_natural_datetime


def test_parse_natural_datetime():
    value = parse_natural_datetime("明天 08:30")
    assert value is not None
    assert value.hour == 8 and value.minute == 30

