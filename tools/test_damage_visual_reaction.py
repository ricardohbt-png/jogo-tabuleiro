import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import server as S


def _reaction_for(target, amount, damage_type="fire"):
    room = S.GameRoom("DAMAGE-VISUAL")
    target = {"id": "target", "pos": [4, 5], **target}
    adjusted = room._apply_damage_types(amount, [damage_type], target)
    room._registrar_dano_combate(target, adjusted, [damage_type])
    return adjusted, room._combat_damage_events[-1]


def test_resistance_marks_damage_event():
    adjusted, event = _reaction_for({
        "resistances": [{"type": "fire", "reduction": 2}],
    }, 6)
    assert adjusted == 4
    assert event.get("damage_reaction") == "resisted"


def test_vulnerability_marks_damage_event():
    adjusted, event = _reaction_for({
        "weaknesses": [{"type": "fire", "bonus_flat": 2}],
    }, 6)
    assert adjusted == 8
    assert event.get("damage_reaction") == "vulnerable"


def test_unrelated_damage_increase_does_not_mark_vulnerability():
    adjusted, event = _reaction_for({
        "min_damage": 1,
    }, 6)
    assert adjusted == 6
    assert event.get("damage_reaction") is None


def test_visual_reaction_requires_matching_damage_type():
    room = S.GameRoom("DAMAGE-VISUAL")
    target = {
        "id": "target", "pos": [4, 5],
        "weaknesses": [{"type": "fire", "bonus_flat": 2}],
    }
    adjusted = room._apply_damage_types(6, ["fire"], target)
    room._registrar_dano_combate(target, adjusted, ["cold"])
    assert room._combat_damage_events[-1].get("damage_reaction") is None


if __name__ == "__main__":
    for test in (
        test_resistance_marks_damage_event,
        test_vulnerability_marks_damage_event,
        test_unrelated_damage_increase_does_not_mark_vulnerability,
        test_visual_reaction_requires_matching_damage_type,
    ):
        test()
    print("damage visual reaction: 4 passed")
