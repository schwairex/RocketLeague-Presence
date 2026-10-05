import json
import pytest


def parser(**kwargs):
    from rocket_league_rpc.stats_client import JsonStreamParser
    return JsonStreamParser(**kwargs)


@pytest.mark.parametrize('chunk_size', [1, 2, 7, 4096])
def test_split_concatenated_unicode_and_string_braces(chunk_size):
    messages = [
        {'Event': 'UpdateState', 'Data': {'Name': 'Çağrı 🚀', 'Nested': {'text': 'a } { " \\ end'}}},
        {'Event': 'RoundStarted', 'Data': {}},
    ]
    wire = b'garbage\n' + b''.join(json.dumps(m, ensure_ascii=False).encode() for m in messages)
    p = parser()
    result = []
    for index in range(0, len(wire), chunk_size):
        result.extend(p.feed(wire[index:index+chunk_size]))
    assert result == messages


def test_malformed_complete_objects_and_invalid_utf8_do_not_poison_next_message():
    p = parser()
    assert p.feed(b'{bad}{"a":"\xff"}{"Event":"MatchDestroyed","Data":{}}') == [
        {'Event': 'MatchDestroyed', 'Data': {}}
    ]


def test_incomplete_object_is_buffered_and_oversized_object_resets():
    p = parser(max_buffer=64)
    assert p.feed(b'{"Event":') == []
    assert p.feed(b'"A","Data":{}}') == [{'Event': 'A', 'Data': {}}]
    assert p.feed(b'{"x":"' + b'a'*100) == []
    assert p.feed(b'{"Event":"B","Data":{}}') == [{'Event': 'B', 'Data': {}}]

