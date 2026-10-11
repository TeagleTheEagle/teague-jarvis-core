"""Music by nickname from the owner's own files (release 1.0.16, item 5; docs/MUSIC.md): the player with Windows'
media interface replaced by a recorder (no sound in the tests), the owner's list, the spoken commands, and the
whole path through a real local Core: the routes, the command answered by the Core itself, the tool, the owner's
switch and the emergency stop.
"""
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import music
import permissions
import providers
from music import Desk, Library, MusicError, Player
from store import Store
from test_device_gateway import DONE, ENV, DeviceCase, calls

SONGS = ('Shoot to Thrill.mp3', 'Back in Black.mp3', 'Thunderstruck.wav', 'notes.txt', 'broken.mp3', '.hidden.mp3')


class FakeMci:
    """Records every command and behaves like winmm for the few the player sends."""

    def __init__(self):
        self.commands = []
        self.open_file = None
        self.mode = None
        self.volume = None

    def send(self, command):
        self.commands.append(command)
        if command.startswith('open '):
            path = command.split('"')[1]
            if Path(path).name == 'broken.mp3':
                raise MusicError('Cannot open the file.')
            self.open_file, self.mode = path, 'stopped'
            return ''
        if self.open_file is None:
            raise MusicError('No device is open.')
        first = command.split(' ', 1)[0]
        if first in ('play', 'resume'):
            self.mode = 'playing'
        elif first == 'pause':
            self.mode = 'paused'
        elif first == 'stop':
            self.mode = 'stopped'
        elif first == 'close':
            self.open_file = self.mode = None
        elif first == 'setaudio':
            self.volume = int(command.rsplit(' ', 1)[1])
        elif first == 'status':
            return {'mode': self.mode, 'position': '1000', 'length': '180000'}[command.rsplit(' ', 1)[1]]
        elif first != 'set':
            raise MusicError('Unknown command.')
        return ''

    def ended(self):
        self.mode = 'stopped'  # the song ran out


def fill(folder):
    folder.mkdir(parents=True, exist_ok=True)
    for name in SONGS:
        (folder / name).write_bytes(b'x')


class MusicCase(unittest.TestCase):
    def setUp(self):
        folder = tempfile.TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.root = Path(folder.name)
        self.folder = self.root / 'music'
        fill(self.folder)
        self.store = Store(self.root / 'data')
        self.mci = FakeMci()
        self.player = Player(self.mci)
        self.desk = Desk(self.store, self.folder, self.player)
        self.library = self.desk.library


class LibraryTests(MusicCase):
    def test_files_and_nicknames(self):
        self.assertEqual(self.library.files(), ['Back in Black.mp3', 'broken.mp3', 'Shoot to Thrill.mp3', 'Thunderstruck.wav'])
        self.assertEqual(self.library.nicknames(), [])
        rows = self.library.add(' workshop warrior ', 'Shoot to Thrill.mp3')
        self.assertEqual([(r['nickname'], r['file'], r['title'], r['present']) for r in rows], [('workshop warrior', 'Shoot to Thrill.mp3', 'Shoot to Thrill', True)])
        for nickname, file in (('', 'Shoot to Thrill.mp3'), ('x' * 61, 'Shoot to Thrill.mp3'), ('<b>', 'Shoot to Thrill.mp3'), (None, 'Shoot to Thrill.mp3'),
                               ('fine', 'notes.txt'), ('fine', 'missing.mp3'), ('fine', '../x.mp3'), ('fine', None)):
            with self.assertRaises(MusicError):
                self.library.add(nickname, file)
        self.library.add('workshop warrior', 'Back in Black.mp3')  # a nickname points at one file: the newer choice wins
        self.assertEqual(self.library.nicknames()[0]['file'], 'Back in Black.mp3')
        (self.folder / 'Back in Black.mp3').unlink()
        self.assertFalse(self.library.nicknames()[0]['present'])  # the file went: said, not hidden
        self.assertEqual(self.library.remove('workshop warrior'), [])
        with self.assertRaises(MusicError):
            self.library.remove('workshop warrior')
        self.assertEqual(Library(self.store, self.root / 'nowhere').files(), [])

    def test_resolving_what_was_said(self):
        self.library.add('Workshop Warrior', 'Shoot to Thrill.mp3')
        self.library.add('gone', 'Back in Black.mp3')
        (self.folder / 'Back in Black.mp3').unlink()
        for said in ('workshop warrior', 'Workshop Warrior!', 'the workshop, warrior', 'warrior', 'workshop warrior now'):
            self.assertEqual(self.library.resolve(said), (self.folder / 'Shoot to Thrill.mp3', 'Shoot to Thrill.mp3', 'Workshop Warrior'), said)
        self.assertEqual(self.library.resolve('shoot to thrill'), (self.folder / 'Shoot to Thrill.mp3', 'Shoot to Thrill.mp3', None))
        self.assertEqual(self.library.resolve('THRILL'), (self.folder / 'Shoot to Thrill.mp3', 'Shoot to Thrill.mp3', None))
        self.assertEqual(self.library.resolve('thunderstruck')[1], 'Thunderstruck.wav')
        for said in ('gone', 'back in black', 'highway to hell', '', None, 'notes', 'it', 'the', 'a', 'to', 'play it'):
            self.assertIsNone(self.library.resolve(said), said)  # a nickname whose file is gone, and filler words, resolve to nothing
        # Words, not letters: a short nickname is not found inside other words, and one word of a nickname is not the nickname.
        self.library.add('ice', 'Thunderstruck.wav')
        self.library.add('back', 'Shoot to Thrill.mp3')
        self.assertEqual(self.library.resolve('ice')[1], 'Thunderstruck.wav')
        for said in ('nice music', 'rice', 'something nice for dinner', 'back the last message', 'practice'):
            self.assertIsNone(self.library.resolve(said), said)
        self.assertEqual(self.library.resolve('back')[2], 'back')  # the whole nickname, said alone, is found
        # The same nickname in another case is the same nickname.
        self.library.add('workshop warrior', 'Thunderstruck.wav')
        self.assertEqual([r['nickname'] for r in self.library.nicknames() if r['nickname'].lower() == 'workshop warrior'], ['workshop warrior'])
        self.assertEqual(self.library.resolve('Workshop Warrior')[1], 'Thunderstruck.wav')
        self.assertEqual(self.library.remove(' WORKSHOP WARRIOR ') and [r['nickname'] for r in self.library.nicknames()], ['back', 'gone', 'ice'])
        for bad in (['x'], 5, None, ''):
            with self.assertRaises(MusicError):
                self.library.remove(bad)
        self.assertTrue(self.folder.is_dir())
        made = Library(self.store, self.root / 'new' / 'music')
        self.assertTrue(made.folder.is_dir())  # the folder is made, so the owner can copy files into the path the panel shows


class PlayerTests(MusicCase):
    def test_play_pause_resume_stop_and_volume(self):
        self.assertEqual(self.player.status()['state'], 'nothing')
        opened = self.player.play(self.folder / 'Shoot to Thrill.mp3', 'workshop warrior')
        self.assertEqual((opened['title'], opened['nickname'], opened['file']), ('Shoot to Thrill', 'workshop warrior', 'Shoot to Thrill.mp3'))
        now = self.player.status()
        self.assertEqual((now['state'], now['title'], now['nickname'], now['file'], now['position_ms'], now['length_ms'], now['volume']),
                         ('playing', 'Shoot to Thrill', 'workshop warrior', 'Shoot to Thrill.mp3', 1000, 180000, 80))
        opened = next(c for c in self.mci.commands if c.startswith('open '))
        self.assertIn('type mpegvideo alias jarvismusic', opened)
        self.assertIn(f'set {music.ALIAS} time format milliseconds', self.mci.commands)
        self.assertEqual(self.mci.volume, 800)
        self.assertIn(f'play {music.ALIAS} from 0', self.mci.commands)
        self.assertEqual(self.player.pause()['title'], 'Shoot to Thrill')  # pause and resume hand back the song they acted on
        self.assertEqual(self.player.status()['state'], 'paused')
        with self.assertRaises(MusicError):
            self.player.pause()
        self.assertEqual(self.player.resume()['title'], 'Shoot to Thrill')
        self.assertEqual(self.player.status()['state'], 'playing')
        with self.assertRaises(MusicError):
            self.player.resume()
        self.assertEqual(self.player.set_volume(50), 50)
        self.assertEqual(self.mci.volume, 500)
        for bad in (-1, 101, 50.5, '50', True):
            with self.assertRaises(MusicError):
                self.player.set_volume(bad)
        was = self.player.stop()
        self.assertEqual(was['title'], 'Shoot to Thrill')
        self.assertEqual((self.player.status()['state'], self.mci.open_file), ('nothing', None))
        self.assertIsNone(self.player.stop())

    def test_a_song_that_ended_a_file_that_cannot_open_and_a_replacement(self):
        self.player.play(self.folder / 'Shoot to Thrill.mp3')
        self.mci.mode = 'seeking'  # a passing state right after play: still open, counted as playing
        self.assertEqual(self.player.status()['state'], 'playing')
        self.mci.mode = 'playing'
        self.mci.ended()
        self.assertEqual(self.player.status()['state'], 'nothing')
        self.assertIn(f'close {music.ALIAS}', self.mci.commands)  # closed when found ended
        # The emergency stop: nothing opens while it holds, and a stop that lands during the opening wins.
        held = [True]
        self.player.blocked = lambda: held[0]
        with self.assertRaises(MusicError) as refused:
            self.player.play(self.folder / 'Shoot to Thrill.mp3')
        self.assertEqual(str(refused.exception), permissions.STOPPED_MESSAGE)
        self.assertIsNone(self.player.now)
        held[0] = False
        self.player.play(self.folder / 'Shoot to Thrill.mp3')
        self.player.stop()
        self.player.blocked = None
        with self.assertRaises(MusicError) as refused:
            self.player.play(self.folder / 'broken.mp3')
        self.assertEqual(str(refused.exception), 'Cannot open the file.')
        self.assertIsNone(self.player.now)
        self.player.play(self.folder / 'Shoot to Thrill.mp3')
        self.player.play(self.folder / 'Thunderstruck.wav')  # a new song replaces the one playing
        self.assertEqual(self.player.status()['title'], 'Thunderstruck')
        self.assertEqual(self.mci.commands.count(f'close {music.ALIAS}'), 3)  # the ended song, the stop above, the replacement


class CommandTests(unittest.TestCase):
    def test_the_phrases_the_core_answers_itself(self):
        for said, expected in (
            ('play workshop warrior', ('play', 'workshop warrior')),
            ('Jarvis, play workshop warrior', ('play', 'workshop warrior')),
            ('Hey Jarvis play the song Shoot to Thrill please.', ('play', 'Shoot to Thrill')),
            ('play Back in Black!', ('play', 'Back in Black')),
            ('stop the music', ('stop', None)), ('Jarvis, stop playing', ('stop', None)), ('music off', ('stop', None)), ('turn off the song', ('stop', None)),
            ('pause', ('pause', None)), ('pause the music please', ('pause', None)),
            ('resume', ('resume', None)), ('continue the music', ('resume', None)), ('unpause', ('resume', None)),
            ('volume up', ('volume', 'up')), ('music volume down', ('volume', 'down')), ('turn it up', ('volume', 'up')), ('louder', ('volume', 'up')), ('quieter', ('volume', 'down')),
            ('volume 40', ('volume', 40)), ('set the volume to 65 percent', ('volume', 65)), ('music volume to 250', ('volume', 100)),
            ("what's playing", ('status', None)), ('what song is this?', ('status', None)), ('which song is this', ('status', None)),
        ):
            self.assertEqual(music.command(said), expected, said)  # with a song open, every form counts
        for said in ('play a video about cats', 'play video cats', 'spotify play shoot to thrill', 'play shoot to thrill on youtube', 'play workshop warrior on spotify',
                     'play', 'stop all', 'stop everything', 'emergency stop', 'what time is it', 'display the play', 'play ' + 'x' * 300, '', None,
                     'pause the inspection', 'what is this', 'what is this?'):
            self.assertIsNone(music.command(said), said)
        # With nothing open, the bare words are not music ("continue" asks for the rest of an answer; "louder" may be about
        # JARVIS's voice); the forms that name the music still are.
        for said in ('pause', 'resume', 'continue', 'unpause', 'volume up', 'the volume down', 'turn it up', 'louder', 'quieter', 'volume 40'):
            self.assertIsNone(music.command(said, open=False), said)
        for said, expected in (('pause the music', ('pause', None)), ('continue the song', ('resume', None)), ('stop the music', ('stop', None)),
                               ('music volume up', ('volume', 'up')), ('turn the music up', ('volume', 'up')), ('set the volume to 40', ('volume', 40)),
                               ('music volume 30', ('volume', 30)), ("what's playing", ('status', None)), ('play workshop warrior', ('play', 'workshop warrior'))):
            self.assertEqual(music.command(said, open=False), expected, said)


class DeskTests(MusicCase):
    def test_actions_and_their_messages(self):
        remembered = []
        self.desk.remember_volume = remembered.append
        empty = Desk(self.store, self.root / 'empty', FakeMciPlayer())
        self.assertIn('music folder is empty', empty.list_message())
        self.library.add('workshop warrior', 'Shoot to Thrill.mp3')
        listing = self.desk.act({'action': 'list'})
        self.assertEqual((listing['status'], listing['files'][2], listing['nicknames'][0]['nickname'], listing['now']['state']), ('completed', 'Shoot to Thrill.mp3', 'workshop warrior', 'nothing'))
        self.assertEqual(listing['message'], 'Your songs: workshop warrior, Back in Black, broken, Thunderstruck.')
        with self.assertRaises(MusicError) as refused:
            self.desk.act({'action': 'play', 'query': 'highway to hell'})
        self.assertTrue(str(refused.exception).startswith('No song called highway to hell. Your songs: '))
        with self.assertRaises(MusicError) as refused:
            self.desk.act({'action': 'play', 'query': 'x' * 500})
        self.assertLess(len(str(refused.exception)), 200)  # a long query is cut in the reply
        with self.assertRaises(MusicError):
            self.desk.act({'action': 'play'})
        self.assertEqual(self.desk.act({'action': 'play', 'query': 'Workshop Warrior'})['message'], 'Playing Shoot to Thrill.')
        self.assertEqual(self.desk.act({'action': 'status'})['message'], 'Playing Shoot to Thrill (your nickname workshop warrior).')
        self.assertEqual(self.desk.act({'action': 'pause'})['message'], 'Paused Shoot to Thrill.')
        self.assertEqual(self.desk.act({'action': 'status'})['message'], 'Paused: Shoot to Thrill (your nickname workshop warrior).')
        self.assertEqual(self.desk.act({'action': 'resume'})['message'], 'Resuming Shoot to Thrill.')
        self.assertEqual((self.desk.act({'action': 'volume', 'volume': 'up'})['volume'], self.desk.act({'action': 'volume', 'volume': 'up'})['volume']), (90, 100))
        self.assertEqual(self.desk.act({'action': 'volume', 'volume': 35})['message'], 'Music volume 35 percent.')
        self.assertEqual(remembered, [90, 100, 35])
        self.assertEqual(self.desk.act({'action': 'stop'})['message'], 'Stopped Shoot to Thrill.')
        self.assertEqual(self.desk.act({'action': 'stop'})['message'], 'Nothing was playing.')
        self.assertEqual(self.desk.act({'action': 'status'})['message'], 'Nothing is playing.')
        with self.assertRaises(MusicError):
            self.desk.act({'action': 'dance'})


def FakeMciPlayer():
    return Player(FakeMci())


class CoreTests(DeviceCase):
    """A real local Core (test_device_gateway.DeviceCase) with the media interface replaced."""

    def setUp(self):
        super().setUp()
        self.mci = FakeMci()
        self.app.music.player.mci = self.mci
        fill(self.app.music.library.folder)

    def finished(self, run_id):
        """Every event of the question once it is done (the route waits for news after the cursor)."""
        seen, collected = -1, {}
        for _ in range(60):
            status, events = self.owner('/api/runs/' + run_id + '/events?after=' + str(seen))
            self.assertEqual(status, 200, events)
            for event in events['events']:
                collected[event['event']] = event['data']
                seen = max(seen, event['id'])
            if events['done']:
                return collected
        self.fail('The question did not finish.')

    def ask(self, text):
        with patch.dict(os.environ, {}, clear=True):  # no AI key: only what the Core answers itself
            status, started = self.owner('/api/chat', {'text': text, 'conversation': 'music-test'})
            self.assertEqual(status, 200, started)
            return self.finished(started['run_id'])

    def test_the_route_and_the_spoken_commands(self):
        status, listing = self.owner('/api/music')
        self.assertEqual(status, 200, listing)
        self.assertEqual((listing['files'][2], listing['nicknames'], listing['now']['state'], listing['volume']), ('Shoot to Thrill.mp3', [], 'nothing', 80))
        self.assertTrue(listing['folder'].endswith('music'))
        self.assertEqual(self.send('/api/music', None, {})[0], 401)  # the owner's route
        status, answer = self.owner('/api/music', {'action': 'add', 'nickname': 'workshop warrior', 'file': 'Shoot to Thrill.mp3'})
        self.assertEqual((status, answer['message'], answer['nicknames'][0]['nickname']), (200, 'Nickname saved.', 'workshop warrior'))
        self.assertEqual(self.owner('/api/music', {'action': 'add', 'nickname': 'x', 'file': 'nope.mp3'})[0], 400)
        # The spoken command, answered by the Core itself: no AI key is configured in this test.
        events = self.ask('Jarvis, play workshop warrior')
        self.assertEqual(events['assistant.completed']['text'], 'Playing Shoot to Thrill.')
        self.assertEqual(self.mci.mode, 'playing')
        self.assertEqual(self.ask('pause')['assistant.completed']['text'], 'Paused Shoot to Thrill.')
        self.assertEqual(self.ask("what's playing")['assistant.completed']['text'], 'Paused: Shoot to Thrill (your nickname workshop warrior).')
        self.assertEqual(self.ask('resume the music')['assistant.completed']['text'], 'Resuming Shoot to Thrill.')
        self.assertEqual(self.ask('volume up')['assistant.completed']['text'], 'Music volume 90 percent.')
        self.assertEqual(self.app.store.settings()['music_volume'], 90)  # kept in Settings
        self.assertEqual(self.ask('stop the music')['assistant.completed']['text'], 'Stopped Shoot to Thrill.')
        self.assertEqual(self.mci.open_file, None)
        # A "play" that matches no song is not a music command: the ordinary answer (here the Core's local-mode line).
        text = self.ask('play highway to hell')['assistant.completed']['text']
        self.assertNotIn('Playing', text)
        self.assertFalse(any(c.startswith('open ') and 'highway' in c for c in self.mci.commands))
        # With nothing playing, the bare words are ordinary questions too; "continue" asks for the rest of an answer.
        for said in ('continue', 'pause', 'volume up', 'louder'):
            events = self.ask(said)
            self.assertNotIn('run.failed', events, said)
            self.assertNotIn('Nothing is', events['assistant.completed']['text'], said)
        self.assertEqual(self.ask('pause the music')['run.failed']['message'], 'Nothing is playing.')  # named: music, and said plainly
        # The volume saved through Settings reaches the player too.
        self.assertEqual(self.owner('/api/settings', {'music_volume': 30})[0], 200)
        self.assertEqual(self.owner('/api/music')[1]['volume'], 30)
        self.owner('/api/music', {'action': 'play', 'query': 'workshop warrior'})
        self.assertEqual(self.mci.volume, 300)
        self.owner('/api/music', {'action': 'stop'})
        self.assertTrue(self.app.music.library.folder.is_dir())
        # The panel's own buttons.
        status, answer = self.owner('/api/music', {'action': 'play', 'query': 'thunderstruck'})
        self.assertEqual((status, answer['message'], answer['now']['title']), (200, 'Playing Thunderstruck.', 'Thunderstruck'))
        self.assertEqual(self.owner('/api/music', {'action': 'volume', 'volume': 20})[1]['volume'], 20)
        self.assertEqual(self.owner('/api/music', {'action': 'stop'})[1]['now']['state'], 'nothing')
        self.assertEqual(self.owner('/api/music', {'action': 'remove', 'nickname': ['x']})[0], 400)
        self.assertEqual(self.owner('/api/music', {'action': 'remove', 'nickname': 'workshop warrior'})[1]['nicknames'], [])
        self.assertEqual(self.owner('/api/music', {'action': 'play', 'query': 'broken'})[0], 400)
        actions = [r['action'] for r in self.app.store.logs()]
        self.assertIn('music nickname added: workshop warrior', actions)
        self.assertIn('play_music', actions)

    def test_the_switch_the_tool_and_the_stop(self):
        self.owner('/api/music', {'action': 'add', 'nickname': 'workshop warrior', 'file': 'Shoot to Thrill.mp3'})
        # The owner's switch: Off refuses the spoken command and the model's call, the owner's own button still works.
        self.assertEqual(self.owner('/api/permissions', {'tool': 'play_music', 'mode': 'off'})[0], 200)
        events = self.ask('play workshop warrior')
        self.assertIn('switched off', events['run.failed']['message'])  # a refused command fails the question, as every refused command does
        self.assertEqual(self.mci.mode, None)
        self.assertEqual(self.owner('/api/music', {'action': 'play', 'query': 'workshop warrior'})[0], 200)
        self.owner('/api/music', {'action': 'stop'})
        self.owner('/api/permissions', {'tool': 'play_music', 'mode': 'ask'})
        text = self.ask('play workshop warrior')['assistant.completed']['text']
        self.assertIn('Waiting for approval', text)
        self.assertEqual(self.mci.mode, None)
        self.assertEqual([a['tool'] for a in self.app.approvals.values()], ['play_music'])
        self.owner('/api/permissions', {'tool': 'play_music', 'mode': 'default'})
        self.app.approvals.clear()
        # The AI model may call the tool for a phrasing the Core did not recognise.
        replies = [calls('play_music', action='play', query='workshop warrior'), DONE]
        with patch.dict(os.environ, ENV, clear=True), patch.object(providers, 'request', side_effect=lambda *a, **k: replies.pop(0)):
            status, started = self.owner('/api/chat', {'text': 'put on something by AC/DC', 'conversation': 'music-ai'})
            self.assertEqual(status, 200, started)
            events = self.finished(started['run_id'])
        self.assertIn('tool.completed', events)
        self.assertEqual(self.mci.mode, 'playing')
        # The emergency stop stops the music with everything else; RESUME does not restart it.
        self.app.emergency_stop('pc', 'test')
        self.assertEqual((self.mci.mode, self.app.music.player.now), (None, None))
        self.app.resume('pc')
        self.assertEqual(self.app.music.player.status()['state'], 'nothing')
        # Not for another device: the PC's speakers.
        self.assertEqual(permissions.decide('play_music', {'action': 'play'}, wearable=True, writes=True)[0], 'refuse')
        self.assertIsNone(self.app.music_command('play workshop warrior', run=type('R', (), {'wearable': True})()))

    def test_the_permission_row(self):
        rule = permissions.TABLE['play_music']
        self.assertEqual((rule.effect, rule.reach, rule.receipt, rule.wearable, rule.read_actions), (permissions.CHANGES, permissions.PC, True, False, ('status', 'list')))
        self.assertEqual(permissions.modes_for('play_music'), (permissions.DEFAULT, permissions.ASK, permissions.OFF))
        self.assertEqual(permissions.effect('play_music', {'action': 'status'}), permissions.READS)
        self.assertEqual(permissions.effect('play_music', {'action': 'play'}), permissions.CHANGES)


class StartupSongTests(DeviceCase):
    """The start-up song (owner, 2026-10-07: "when jarvis boots he says his morning hello message then the mp3
    plays"): a setting, shown in the listing, played on the window's request once the sign-in greeting is spoken."""

    def setUp(self):
        super().setUp()
        self.mci = FakeMci()
        self.app.music.player.mci = self.mci
        fill(self.app.music.library.folder)

    def test_no_song_set_means_silence(self):
        status, answer = self.owner('/api/music', {'action': 'startup'})
        self.assertEqual((status, answer), (200, {'played': False, 'message': ''}))
        self.assertIsNone(self.mci.mode)
        self.assertEqual((self.owner('/api/music')[1]['startup'], self.owner('/api/music')[1]['startup_present']), ('', False))

    def test_the_setting_is_a_nickname_or_a_file_name(self):
        self.assertEqual(self.owner('/api/settings', {'music_startup': '..\\secrets.mp3'})[0], 400)
        self.assertEqual(self.owner('/api/settings', {'music_startup': 'a/b.mp3'})[0], 400)
        self.assertEqual(self.owner('/api/settings', {'music_startup': ' padded '})[0], 400)
        self.assertEqual(self.owner('/api/settings', {'music_startup': 7})[0], 400)
        self.assertEqual(self.owner('/api/settings', {'music_startup': 'Shoot to Thrill.mp3'})[0], 200)
        listing = self.owner('/api/music')[1]
        self.assertEqual((listing['startup'], listing['startup_present']), ('Shoot to Thrill.mp3', True))
        self.assertEqual(self.owner('/api/settings', {'music_startup': 'gone song'})[0], 200)
        self.assertEqual(self.owner('/api/music')[1]['startup_present'], False)

    def test_the_song_plays_on_request_after_the_greeting(self):
        self.owner('/api/music', {'action': 'add', 'nickname': 'workshop warrior', 'file': 'Shoot to Thrill.mp3'})
        self.owner('/api/settings', {'music_startup': 'workshop warrior'})
        status, answer = self.owner('/api/music', {'action': 'startup'})
        self.assertEqual((status, answer), (200, {'played': True, 'message': 'Playing Shoot to Thrill.'}))
        self.assertEqual(self.mci.mode, 'playing')
        self.owner('/api/music', {'action': 'stop'})
        # The setting may name the file itself (as the panel's list does): the exact file name resolves.
        self.assertEqual(self.app.music.library.resolve('Shoot to Thrill.mp3')[1:], ('Shoot to Thrill.mp3', 'workshop warrior'))
        self.assertIsNone(self.app.music.library.resolve('Shoot to Thrill.mp3 '[:-1] + 'x'))
        self.owner('/api/settings', {'music_startup': 'Back in Black.mp3'})
        status, answer = self.owner('/api/music', {'action': 'startup'})
        self.assertEqual((status, answer), (200, {'played': True, 'message': 'Playing Back in Black.'}))
        self.owner('/api/music', {'action': 'stop'})
        # A file that is gone: said, nothing played.
        self.owner('/api/settings', {'music_startup': 'vanished.mp3'})
        status, answer = self.owner('/api/music', {'action': 'startup'})
        self.assertEqual((status, answer['played'], answer['message']), (200, False, 'The start-up song vanished.mp3 is not in the music folder.'))
        self.assertIsNone(self.mci.mode)

    def test_nothing_starts_while_the_emergency_stop_holds(self):
        self.owner('/api/settings', {'music_startup': 'Shoot to Thrill.mp3'})
        self.assertEqual(self.owner('/api/emergency-stop', {})[0], 200)
        status, answer = self.owner('/api/music', {'action': 'startup'})
        self.assertEqual((status, answer['played']), (200, False))
        self.assertTrue(answer['message'])
        self.assertIsNone(self.mci.mode)
        self.owner('/api/resume', {})

    def test_quiet_hours_keep_it_silent_and_the_tool_switch_does_not_bind_the_owners_own_setting(self):
        self.owner('/api/settings', {'music_startup': 'shoot to thrill.MP3', 'quiet_hours': True})   # the file name, whatever its case
        self.assertEqual(self.owner('/api/music')[1]['startup_present'], True)
        self.assertEqual(self.owner('/api/music', {'action': 'startup'})[1], {'played': False, 'message': ''})
        self.assertIsNone(self.mci.mode)
        self.owner('/api/settings', {'quiet_hours': False})
        # The start-up song is the owner's own standing setting, like a click on PLAY: the switch for JARVIS's own
        # calls ("Play music from your files", Off here) does not bind it; the emergency stop and quiet hours do.
        self.app.set_permission('play_music', permissions.OFF)
        self.assertEqual(self.owner('/api/music', {'action': 'startup'})[1], {'played': True, 'message': 'Playing Shoot to Thrill.'})
        self.assertEqual(self.mci.mode, 'playing')
        self.owner('/api/music', {'action': 'stop'})
        self.app.set_permission('play_music', permissions.DEFAULT)
        # A file name longer than 100 characters is a file name still.
        self.assertEqual(self.owner('/api/settings', {'music_startup': 'x' * 200 + '.mp3'})[0], 200)
        self.assertEqual(self.owner('/api/settings', {'music_startup': 'x' * 300 + '.mp3'})[0], 400)


class OneThreadForTheMediaInterfaceTests(unittest.TestCase):
    """2026-10-07: Windows ties a song opened through its media interface to the thread that opened it; the Core
    answers each request on its own thread, so 1.0.16 could not stop a song from the request after the one that
    started it ("Playing Daddy's Home." then "Nothing was playing." while the song played on). Every command now goes
    through one long-lived thread of the player's own."""

    def test_every_command_runs_on_the_same_long_lived_thread(self):
        import threading
        mci = music.Mci()
        mci.winmm = object()   # not used: the command itself is replaced below
        seen = []
        mci._send_here = lambda command: (seen.append((command, threading.current_thread().name)), 'ok')[1]
        results = []
        workers = [threading.Thread(target=lambda n=n: results.append(mci.send(f'command {n}'))) for n in range(3)]
        for w in workers:
            w.start()
        for w in workers:
            w.join()
        results.append(mci.send('command main'))
        self.assertEqual(results, ['ok'] * 4)
        self.assertEqual(sorted(c for c, _ in seen), ['command 0', 'command 1', 'command 2', 'command main'])
        self.assertEqual({name for _, name in seen}, {music.Mci.THREAD})
        self.assertTrue(mci.thread.is_alive() and mci.thread.daemon)

    def test_an_error_on_the_worker_reaches_the_caller_and_the_worker_lives_on(self):
        mci = music.Mci()
        mci.winmm = object()
        def send_here(command):
            if command == 'bad':
                raise MusicError('The specified device is not open or is not recognized by MCI.')
            return 'fine'
        mci._send_here = send_here
        with self.assertRaises(MusicError):
            mci.send('bad')
        self.assertEqual(mci.send('good'), 'fine')

    def test_off_windows_the_answer_is_plain(self):
        mci = music.Mci()
        mci.winmm = None
        with self.assertRaises(MusicError):
            mci.send('status x mode')

    def test_a_stalled_interface_is_refused_at_once_until_it_answers_and_the_emergency_stop_never_waits_on_it(self):
        import threading, time
        mci = music.Mci()
        mci.winmm = object()
        mci.WAIT = 0.2
        release = threading.Event()
        def send_here(command):
            if command.startswith('open'):
                release.wait(5)   # the stalled command
            return 'ok'
        mci._send_here = send_here
        player = Player(mci)
        with self.assertRaises(music.MediaTimeout):   # the open does not come back in time
            player.play(Path('C:/music/song.mp3'))
        self.assertIsNone(player.now)
        self.assertTrue(player.stale_alias and mci.stuck)
        with self.assertRaises(music.MediaTimeout):   # refused at once, not after another wait
            mci.send('status jarvismusic mode')
        started = time.monotonic()
        self.assertIsNone(player.stop(lock_timeout=0.5))   # nothing on the books, nothing sent, no waiting
        self.assertLess(time.monotonic() - started, 0.3)
        release.set()
        for _ in range(50):   # the late answer frees the interface
            if not mci.stuck:
                break
            time.sleep(0.02)
        self.assertEqual(mci.send('status jarvismusic mode'), 'ok')
        # The next play closes the alias the late open may have left behind, before it opens.
        seen = []
        mci._send_here = lambda command: (seen.append(command), 'ok')[1]
        player.play(Path('C:/music/song.mp3'))
        self.assertEqual(seen[0], f'close {music.ALIAS}')
        self.assertTrue(seen[1].startswith('open '))
        self.assertFalse(player.stale_alias)
        # A caller holding the player's lock while the interface stalls: the emergency stop's bounded stop gives up in time.
        mci._send_here = lambda command: (release.clear(), release.wait(5), 'ok')[2]
        holder = threading.Thread(target=lambda: player.mode())
        holder.start(); time.sleep(0.05)
        started = time.monotonic()
        self.assertIsNone(player.stop(lock_timeout=0.2))
        self.assertLess(time.monotonic() - started, 1.0)
        release.set(); holder.join(5)

    @unittest.skipUnless(os.name == 'nt', 'Windows media interface')
    def test_a_song_opened_on_a_thread_that_ended_can_still_be_seen_and_stopped(self):
        """The owner's case against the real media interface: a one-second silent tone (volume 0)."""
        import math, struct, threading, wave
        with tempfile.TemporaryDirectory() as folder:
            tone = Path(folder) / 'tone.wav'
            with wave.open(str(tone), 'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(8000)
                w.writeframes(b''.join(struct.pack('<h', int(2000 * math.sin(2 * math.pi * 440 * i / 8000))) for i in range(8000)))
            player = Player(music.Mci())
            player.volume = 0
            outcome = {}
            def opener():
                try:
                    player.play(tone)
                    outcome['mode'] = player.mode()
                except MusicError as exc:
                    outcome['error'] = str(exc)
            t = threading.Thread(target=opener); t.start(); t.join()
            try:
                if 'error' in outcome:
                    if 'device' in outcome['error'].lower() or 'driver' in outcome['error'].lower():
                        self.skipTest('no media device on this machine: ' + outcome['error'])
                    self.fail('the real media interface refused the open: ' + outcome['error'])
                self.assertEqual(outcome['mode'], 'playing')
                self.assertEqual(player.mode(), 'playing')   # from this thread, after the opening thread ended
                self.assertEqual(player.status()['title'], 'tone')
                stopped = player.stop()
                self.assertEqual(stopped['title'], 'tone')
                self.assertEqual(player.mode(), 'nothing')
            finally:
                player.stop()


if __name__ == '__main__':
    unittest.main()
