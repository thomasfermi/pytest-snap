import json

from pytest_snap.round import round_floats_in_text


def test_round_floats_in_text():
    assert round_floats_in_text("Value is 3.14159", 3) == "Value is 3.14"
    assert round_floats_in_text("Avogadro: 6.022e23", 4) == "Avogadro: 6.022e+23"
    assert round_floats_in_text("Avogadro: 6.022e23", 1) == "Avogadro: 6e+23"
    assert round_floats_in_text("Temp: 1.92°F", 2) == "Temp: 1.9°F"
    assert round_floats_in_text("Coords: -12345.6789", 3) == "Coords: -1.23e+04"
    assert (
        round_floats_in_text("Mixed: 3.14159, 2.71828e0, 0.00012345", 2)
        == "Mixed: 3.1, 2.7, 0.00012"
    )


def test_round_floats_with_ip_does_no_rounding():
    assert round_floats_in_text("IP: 192.168.0.1", 2) == "IP: 192.168.0.1"


def test_round_floats_with_time_stamp_does_no_rounding():
    assert (
        round_floats_in_text("Timestamp: 2023-04-01T12:34:56.789", 2)
        == "Timestamp: 2023-04-01T12:34:56.789"
    )


def test_round_with_list_of_timestamps_does_no_rounding():
    ts_list = [
        "1998-03-31T00:00:00Z",
        "1998-04-30T00:00:00Z",
        "1998-05-31T00:00:00Z",
        "1998-06-30T00:00:00Z",
        "1998-07-31T00:00:00Z",
    ]
    ts_list_str = json.dumps(ts_list)
    assert round_floats_in_text(ts_list_str, 3) == ts_list_str


def test_round_floats_with_URL_does_no_rounding():
    assert (
        round_floats_in_text("URL: https://example.com/path?query=123.456", 2)
        == "URL: https://example.com/path?query=123.456"
    )


def test_round_floats_also_rounds_ints():
    assert round_floats_in_text("Just an int: 987654321", 3) == "Just an int: 9.88e+08"
