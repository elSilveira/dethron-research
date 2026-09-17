import shlex
import unittest

from g4_contract import (PROFILE, bridge_command, config_text, expected_delivery,
                         interface_types, isolated, pipe_bridge, tcp_contact, tcp_listener)


class ContractTests(unittest.TestCase):
    def test_an_isolated_configuration_admits_only_the_pipe_bridge(self):
        self.assertTrue(isolated(config_text([pipe_bridge('python bridge.py')])))
        self.assertTrue(isolated(config_text([pipe_bridge('a', 'One'), pipe_bridge('b', 'Two')])))
        self.assertTrue(isolated(config_text([])))
        for interface in (tcp_listener(4000), tcp_contact(0, 4000)):
            with self.subTest(interface=interface):
                self.assertFalse(isolated(config_text([interface])))
        self.assertFalse(isolated(config_text([pipe_bridge('x'), tcp_listener(4000)])))

    def test_a_shared_instance_would_reopen_an_ip_path(self):
        text = config_text([pipe_bridge('python bridge.py')]).replace('share_instance = No',
                                                                     'share_instance = Yes')
        self.assertFalse(isolated(text))

    def test_interface_types_are_read_from_the_configuration_itself(self):
        text = config_text([tcp_listener(4000), tcp_contact(0, 4001), pipe_bridge('x')])
        self.assertEqual(interface_types(text),
                         ['TCPServerInterface', 'TCPClientInterface', 'PipeInterface'])

    def test_the_bridge_command_survives_configobj_and_shlex(self):
        # configobj drops surrounding quotes, so a quoted command would arrive as one argument.
        command = bridge_command('C:/py/python.exe', 'C:/w/g4_bridge.py', 'C:/w/ch', 'a', 'C:/w/a.ledger')
        self.assertEqual(shlex.split(command),
                         ['C:/py/python.exe', 'C:/w/g4_bridge.py', 'C:/w/ch', 'a', 'C:/w/a.ledger'])
        self.assertNotIn('"', command)

    def test_a_path_that_would_break_the_command_is_refused(self):
        for bad in ('C:/Program Files/python.exe', 'C:/w/"odd".py', ''):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                bridge_command(bad, 'C:/w/g4_bridge.py', 'C:/w/ch', 'a', 'C:/w/a.ledger')

    def test_windows_paths_become_posix_shaped(self):
        command = bridge_command(chr(92).join(['C:', 'py', 'python.exe']), 'b.py', 'ch', 'a', 'l')
        self.assertEqual(shlex.split(command)[0], 'C:/py/python.exe')

    def test_only_the_dark_scenario_is_expected_to_fail(self):
        self.assertEqual([s for s in PROFILE['scenarios'] if not expected_delivery(s)], ['dark'])


if __name__ == '__main__':
    unittest.main()
