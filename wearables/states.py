from enum import Enum
import asyncio
from .contracts import identifier, WearableError


class State(str, Enum):
    OFFLINE = 'OFFLINE'
    IDLE = 'IDLE'
    LISTENING = 'LISTENING'
    THINKING = 'THINKING'
    LOOKING = 'LOOKING'
    SPEAKING = 'SPEAKING'
    EXECUTING = 'EXECUTING'
    ERROR = 'ERROR'


class StateMachine:
    """One device, one current turn; generation invalidates late work."""
    def __init__(self, device_id):
        self.device_id = identifier(device_id)
        self.state = State.OFFLINE
        self.generation = 0
        self.turn_id = None
        self.events = []
        self._sequence = 0
        self._subscribers = set()

    async def subscribe(self):
        """Bounded, nonblocking state subscriptions; consumers receive latest state."""
        queue = asyncio.Queue(maxsize=1)
        self._subscribers.add(queue)
        if self.events: queue.put_nowait(dict(self.events[-1]))
        try:
            while True: yield await queue.get()
        finally: self._subscribers.discard(queue)

    def emit(self, state):
        self.state = State(state)
        self.events.append({'sequence': self.generation_sequence, 'device_id': self.device_id,
                            'turn_id': self.turn_id, 'state': self.state.value})
        self._sequence += 1
        self.events = self.events[-100:]
        for queue in self._subscribers:
            if queue.full(): queue.get_nowait()
            queue.put_nowait(dict(self.events[-1]))

    @property
    def generation_sequence(self):
        return self._sequence

    def connect(self):
        self.generation += 1
        self.turn_id = None
        self.emit(State.IDLE)

    def cancel(self, offline=False):
        self.generation += 1
        self.emit(State.OFFLINE if offline else State.IDLE)
        self.turn_id = None

    def begin(self, turn_id):
        if self.state != State.IDLE:
            raise WearableError('BUSY' if self.state != State.OFFLINE else 'OFFLINE')
        self.turn_id = identifier(turn_id)
        self.generation += 1
        self.emit(State.LISTENING)
        return self.generation

    def check(self, generation):
        if generation != self.generation:
            raise WearableError('CANCELLED')

    def move(self, state, generation):
        self.check(generation)
        state = State(state)
        transitions = {State.LISTENING: {State.THINKING}, State.THINKING: {State.LOOKING, State.SPEAKING, State.EXECUTING},
                       State.LOOKING: {State.THINKING}, State.EXECUTING: {State.THINKING, State.IDLE},
                       State.SPEAKING: {State.IDLE}}
        if state != State.ERROR and state not in transitions.get(self.state, set()):
            raise WearableError('INVALID_TRANSITION')
        self.emit(state)
