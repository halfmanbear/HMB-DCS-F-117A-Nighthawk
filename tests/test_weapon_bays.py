"""Each weapon bay has its own command, door light state and (with the EFM and model) its own draw argument."""
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools/cockpit'))
from check_display_calibration import runtime  # noqa: E402

SCRIPTS = ROOT / 'Cockpit/Scripts'
EFM_ROOT = Path(r'C:\Users\Fraser\Git\HMB-DCS-F-117A-EFM\EFM Source Code')
COMMANDS = {'BOMB_BAY_TOGGLE': 10100, 'BOMB_BAY_SELECTED_TOGGLE': 10130,
            'BOMB_BAY_LEFT_TOGGLE': 10131, 'BOMB_BAY_RIGHT_TOGGLE': 10132}


def lua_commands():
    text = (SCRIPTS / 'command_defs.lua').read_text(encoding='utf-8')
    block = text[text.index('f117_commands'):]
    block = block[:block.index('\n}')]
    return {name: int(value) for name, value in re.findall(r'(\w+)\s*=\s*(\d+)', block)}


class WeaponBayTests(unittest.TestCase):
    def test_commands_are_unique_and_as_expected(self):
        commands = lua_commands()
        for name, value in COMMANDS.items():
            self.assertEqual(commands[name], value, name)
        self.assertEqual(len(set(commands.values())), len(commands), 'a command ID is used twice')

    def test_every_bay_command_is_bound_for_keyboard_and_joystick(self):
        for device in ('keyboard', 'joystick'):
            text = (ROOT / 'Input/F-117-NightHawk' / device / 'default.lua').read_text(encoding='utf-8')
            for name in COMMANDS:
                self.assertEqual(text.count(f'f117_commands.{name},'), 1, f'{device} {name}')

    def test_keyboard_combos_do_not_collide(self):
        text = (ROOT / 'Input/F-117-NightHawk/keyboard/default.lua').read_text(encoding='utf-8')
        combos = []
        for line in text.splitlines():
            match = re.search(r"combos = \{\{key = '(\w+)', reformers = \{([^}]*)\}\}\}", line)
            if match:
                combos.append((match.group(1), tuple(sorted(re.findall(r"'(\w+)'", match.group(2))))))
        self.assertEqual(len(combos), len(set(combos)), 'two keyboard commands share a key combination')

    def light_states(self, position):
        lua, load = runtime()
        lua.execute('function make_default_activity() end')
        load(SCRIPTS / 'Systems/bomb_bay.lua')
        params = lua.globals()._parameters
        params.F117_BAY_L = position[0]
        params.F117_BAY_R = position[1]
        lua.globals().update()
        return [params[name] for name in ('F117_BAY_L_DOOR', 'F117_BAY_L_TRAP', 'F117_BAY_R_DOOR', 'F117_BAY_R_TRAP')]

    def test_door_and_trapeze_lights_follow_each_bay(self):
        self.assertEqual(self.light_states((0, 0)), [0, 0, 0, 0])
        self.assertEqual(self.light_states((0.4, 0)), [1, 0, 0, 0])      # left door travelling
        self.assertEqual(self.light_states((0.7, 0.7)), [2, 1, 2, 1])    # doors open; trapezes start at 0.6
        self.assertEqual(self.light_states((0.9, 1)), [2, 1, 2, 2])      # left trapeze lowering, right down
        self.assertEqual(self.light_states((1, 0.2)), [2, 2, 1, 0])

    def test_bay_device_never_falls_back_to_a_default_aim_point(self):
        self.assertNotIn('dispatch_action', (SCRIPTS / 'Systems/bomb_bay.lua').read_text(encoding='utf-8'))

    @unittest.skipUnless(EFM_ROOT.is_dir(), 'EFM source not checked out')
    def test_efm_has_the_same_commands_and_draw_arguments(self):
        inputs = (EFM_ROOT / 'Inputs.h').read_text(encoding='utf-8-sig')
        for name, efm_name in (('BOMB_BAY_TOGGLE', 'bombay'), ('BOMB_BAY_SELECTED_TOGGLE', 'bombaySelected'),
                               ('BOMB_BAY_LEFT_TOGGLE', 'bombayLeft'), ('BOMB_BAY_RIGHT_TOGGLE', 'bombayRight')):
            self.assertRegex(inputs, rf'constexpr int {efm_name} = {COMMANDS[name]};')
        source = (EFM_ROOT / 'F_117_NightHawk.cpp').read_text(encoding='utf-8-sig')
        self.assertIn('kWeaponBayArgs[kWeaponBayCount] = {27, 28}', source)
        self.assertIn('kWeaponBayAnyArg = 26', source)
        self.assertIn('"F117_BAY_L","F117_BAY_R"', source)


if __name__ == '__main__':
    unittest.main()
