# flake8: noqa: E402
import os
import sys

# Make sure reverie/backend_server is importable for tests
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import datetime

from persona.persona import Persona


class DummyMemory:
    def __init__(self, *args, **kwargs):
        pass

    def save(self, *args, **kwargs):
        pass


class DummyScratch:
    def __init__(self, *args, **kwargs):
        self.curr_time = None
        self.curr_tile = None
        self.act_address = None

    def save(self, *args, **kwargs):
        pass


class DummyMaze:
    pass


def _make_dummy_mem_classes():
    # helper to reduce repetition in tests
    return DummyMemory, DummyScratch


def test_move_first_day(monkeypatch):
    # Patch memory constructors to avoid file IO
    import persona.persona as pp
    monkeypatch.setattr(pp, 'MemoryTree', DummyMemory)
    monkeypatch.setattr(pp, 'AssociativeMemory', DummyMemory)
    monkeypatch.setattr(pp, 'Scratch', DummyScratch)

    p = Persona('TestPersona', folder_mem_saved='/tmp')

    # Set up spies/mocks for cognitive steps
    called = {}


    def fake_perceive(self, maze):
        called['perceive'] = True
        return ['event']


    def fake_retrieve(self, perceived):
        called['retrieve'] = perceived
        return {'info': 'retrieved'}


    def fake_plan(self, maze, personas, new_day, retrieved):
        # For first call we expect new_day == 'First day'
        called['new_day'] = new_day
        called['retrieved'] = retrieved
        return 'dummy_plan'


    def fake_reflect(self):
        called['reflect'] = True


    def fake_execute(self, maze, personas, plan):
        called['plan'] = plan
        return ('next_tile', 'emoji', 'desc')

    monkeypatch.setattr(p, 'perceive', fake_perceive.__get__(p, Persona))
    monkeypatch.setattr(p, 'retrieve', fake_retrieve.__get__(p, Persona))
    monkeypatch.setattr(p, 'plan', fake_plan.__get__(p, Persona))
    monkeypatch.setattr(p, 'reflect', fake_reflect.__get__(p, Persona))
    monkeypatch.setattr(p, 'execute', fake_execute.__get__(p, Persona))

    maze = DummyMaze()
    personas = {}
    curr_tile = (1, 2)
    curr_time = datetime.datetime(2023, 1, 1, 9, 0, 0)

    result = p.move(maze, personas, curr_tile, curr_time)

    assert result == ('next_tile', 'emoji', 'desc')
    assert isinstance(p.scratch, DummyScratch)
    assert p.scratch.curr_tile == curr_tile
    assert p.scratch.curr_time == curr_time
    assert called['new_day'] == 'First day'


def test_move_new_day(monkeypatch):
    import persona.persona as pp
    monkeypatch.setattr(pp, 'MemoryTree', DummyMemory)
    monkeypatch.setattr(pp, 'AssociativeMemory', DummyMemory)
    monkeypatch.setattr(pp, 'Scratch', DummyScratch)

    p = Persona('TestPersona2', folder_mem_saved='/tmp')

    # Pre-set scratch.curr_time to yesterday
    p.scratch.curr_time = datetime.datetime(2023, 1, 1, 9, 0, 0)


    def fake_perceive(self, maze):
        return []

    def fake_retrieve(self, perceived):
        return {}

    def fake_plan(self, maze, personas, new_day, retrieved):
        return 'plan2' if new_day == 'New day' else 'wrong'

    def fake_reflect(self):
        pass

    def fake_execute(self, maze, personas, plan):
        return ('nt', 'e', 'd')

    monkeypatch.setattr(p, 'perceive', fake_perceive.__get__(p, Persona))
    monkeypatch.setattr(p, 'retrieve', fake_retrieve.__get__(p, Persona))
    monkeypatch.setattr(p, 'plan', fake_plan.__get__(p, Persona))
    monkeypatch.setattr(p, 'reflect', fake_reflect.__get__(p, Persona))
    monkeypatch.setattr(p, 'execute', fake_execute.__get__(p, Persona))

    maze = DummyMaze()
    personas = {}
    curr_tile = (3, 4)
    curr_time = datetime.datetime(2023, 1, 2, 10, 0, 0)  # next day

    result = p.move(maze, personas, curr_tile, curr_time)
    assert result == ('nt', 'e', 'd')
    assert p.scratch.curr_time == curr_time
    assert p.scratch.curr_tile == curr_tile
