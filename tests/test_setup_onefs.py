# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in setup_onefs.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_onefs_api.lib.worker import setup_onefs


class TestvSphereConsole(unittest.TestCase):
    """A suite of test cases for vSphereConsole object"""

    @patch.object(setup_onefs, 'webdriver')
    def test_init(self, fake_webdriver):
        """``__init__`` works for vSphereConsole"""
        console = setup_onefs.vSphereConsole(url='https://someHTMLconsole.com')

        self.assertTrue(isinstance(console, setup_onefs.vSphereConsole))

    @patch.object(setup_onefs.vSphereConsole, '_login')
    @patch.object(setup_onefs, 'webdriver')
    def test_auto_login(self, fake_webdriver, fake_login):
        """Creating the vSphereConsole object automatically logs a user into the HTML console"""
        console = setup_onefs.vSphereConsole(url='https://someHTMLconsole.com')

        self.assertEqual(fake_login.call_count, 1)

    @patch.object(setup_onefs.vSphereConsole, '_get_console')
    @patch.object(setup_onefs, 'webdriver')
    def test_finds_console(self, fake_webdriver, fake_get_console):
        """Creating the vSphereConsole object binds to the console HTML object"""
        console = setup_onefs.vSphereConsole(url='https://someHTMLconsole.com')

        self.assertEqual(fake_get_console.call_count, 1)

    @patch.object(setup_onefs, 'webdriver')
    def test_with(self, fake_webdriver):
        """vSphereConsole auto-closes the session upon exiting ``with`` statement"""
        fake_driver = MagicMock()
        fake_webdriver.Chrome.return_value = fake_driver
        with setup_onefs.vSphereConsole(url='https://someHTMLconsole.com') as console:
            pass

        self.assertEqual(fake_driver.quit.call_count, 1)

    @patch.object(setup_onefs.vSphereConsole, '_get_console')
    @patch.object(setup_onefs.time, 'sleep')
    @patch.object(setup_onefs, 'webdriver')
    def test_send_keys(self, fake_webdriver, fake_sleep, fake_get_console):
        """``send_keys`` Sends the supplied intput to the HTML console"""
        fake_console = MagicMock()
        fake_get_console.return_value = fake_console
        with setup_onefs.vSphereConsole(url='https://someHTMLconsole.com') as console:
            console.send_keys('woot', auto_enter=False)

        the_args, _ = fake_console.send_keys.call_args
        expected = ('woot',)

        self.assertEqual(the_args, expected)

    @patch.object(setup_onefs.vSphereConsole, '_get_console')
    @patch.object(setup_onefs.time, 'sleep')
    @patch.object(setup_onefs, 'webdriver')
    def test_send_keys_pauses(self, fake_webdriver, fake_sleep, fake_get_console):
        """``send_keys`` pauses to let the HTML console 'catch up'"""
        fake_console = MagicMock()
        fake_get_console.return_value = fake_console
        with setup_onefs.vSphereConsole(url='https://someHTMLconsole.com') as console:
            console.send_keys('woot', auto_enter=False)

        self.assertEqual(fake_sleep.call_count, 1)

    @patch.object(setup_onefs.vSphereConsole, '_get_console')
    @patch.object(setup_onefs.time, 'sleep')
    @patch.object(setup_onefs, 'webdriver')
    def test_send_keys_auto_enters(self, fake_webdriver, fake_sleep, fake_get_console):
        """``send_keys`` automatically sends the ENTER key by default"""
        fake_console = MagicMock()
        fake_get_console.return_value = fake_console
        with setup_onefs.vSphereConsole(url='https://someHTMLconsole.com') as console:
            console.send_keys('woot')

        the_args, _ = fake_console.send_keys.call_args
        expected = (setup_onefs.Keys.ENTER,)

        self.assertEqual(the_args, expected)

@patch.object(setup_onefs.time, 'sleep')
@patch.object(setup_onefs, 'vSphereConsole')
class TestSetupFunctions(unittest.TestCase):
    """A suite of test cases for the functions within setup_onefs.py"""

    def test_join_existing_cluster(self, fake_vSphereConsole, fake_sleep):
        """``join_existing_cluster`` returns None"""
        fake_logger = MagicMock()
        output = setup_onefs.join_existing_cluster('https://someHTMLconsole.com', 'mycluster', fake_logger)
        expected = None

        self.assertEqual(output, expected)


    def test_join_existing_cluster_with(self, fake_vSphereConsole, fake_sleep):
        """``join_existing_cluster`` uses context manager of vSphereConsole"""
        fake_logger = MagicMock()
        setup_onefs.join_existing_cluster('https://someHTMLconsole.com', 'mycluster', fake_logger)

        call_count = fake_vSphereConsole.return_value.__enter__.call_count
        expected = 1

        self.assertEqual(call_count, expected)

    def test_join_existing_cluster_pause(self, fake_vSphereConsole, fake_sleep):
        """``join_existing_cluster`` waits for the disks to format"""
        fake_logger = MagicMock()
        setup_onefs.join_existing_cluster('https://someHTMLconsole.com', 'mycluster', fake_logger)

        paused = fake_sleep.called

        self.assertTrue(paused)

    @patch.object(setup_onefs, 'format_disks')
    def test_join_existing_cluster_formats(self, fake_vSphereConsole, fake_sleep, fake_format_disks):
        """``join_existing_cluster`` formats the disks"""
        fake_logger = MagicMock()
        setup_onefs.join_existing_cluster('https://someHTMLconsole.com', 'mycluster', fake_logger)

        formatted_disks = fake_format_disks.called

        self.assertTrue(formatted_disks)

    def test_configure_new_cluster(self, fake_vSphereConsole, fake_sleep):
        """``configure_new_cluster`` returns None"""
        fake_logger = MagicMock()
        output = setup_onefs.configure_new_cluster(version='8.1.1.1',
                                                   logger=fake_logger,
                                                   console_url='https://someHTMLconsole.com',
                                                   cluster_name='mycluster',
                                                   int_netmask='255.255.255.0',
                                                   int_ip_low='8.6.7.5',
                                                   int_ip_high='8.6.7.50',
                                                   ext_netmask='255.255.255.0',
                                                   ext_ip_low='3.0.9.2',
                                                   ext_ip_high='3.0.9.20',
                                                   gateway='3.0.9.1',
                                                   dns_servers='1.1.1.1',
                                                   encoding='utf-8',
                                                   sc_zonename='myzone.foo.org',
                                                   smartconnect_ip='3.0.9.21')
        expected = None

        self.assertEqual(output, expected)

    @patch.object(setup_onefs, 'configure_new_8_0_cluster')
    def test_configure_new_cluster_8_0(self, fake_configure_new_8_0_cluster, fake_vSphereConsole, fake_sleep):
        """``configure_new_cluster`` executes the correct function for OneFS 8.0.0.x"""
        fake_logger = MagicMock()
        setup_onefs.configure_new_cluster(version='8.0.0.1', logger=fake_logger)

        called = fake_configure_new_8_0_cluster.call_count
        expected = 1

        self.assertEqual(called, expected)

    @patch.object(setup_onefs, 'configure_new_8_1_cluster')
    def test_configure_new_cluster_8_1_0(self, fake_configure_new_8_1_cluster, fake_vSphereConsole, fake_sleep):
        """``configure_new_cluster`` executes the correct function for OneFS 8.1.0.x"""
        fake_logger = MagicMock()
        setup_onefs.configure_new_cluster(version='8.1.0.3', logger=fake_logger)

        called = fake_configure_new_8_1_cluster.call_count
        expected = 1

        self.assertEqual(called, expected)

    @patch.object(setup_onefs, 'configure_new_8_1_cluster')
    def test_configure_new_cluster_8_1_1(self, fake_configure_new_8_1_cluster, fake_vSphereConsole, fake_sleep):
        """``configure_new_cluster`` executes the correct function for OneFS 8.1.1.x"""
        fake_logger = MagicMock()
        setup_onefs.configure_new_cluster(version='8.1.1.2', logger=fake_logger)

        called = fake_configure_new_8_1_cluster.call_count
        expected = 1

        self.assertEqual(called, expected)

    @patch.object(setup_onefs, 'configure_new_8_1_2_cluster')
    def test_configure_new_cluster_8_1_2(self, fake_configure_new_8_1_2_cluster, fake_vSphereConsole, fake_sleep):
        """``configure_new_cluster`` executes the correct function for OneFS 8.1.2.x"""
        fake_logger = MagicMock()
        setup_onefs.configure_new_cluster(version='8.1.2.0', logger=fake_logger)

        called = fake_configure_new_8_1_2_cluster.call_count
        expected = 1

        self.assertEqual(called, expected)

    @patch.object(setup_onefs, 'configure_new_8_2_0_cluster')
    def test_configure_new_cluster_8_2_0(self, fake_configure_new_8_2_0_cluster, fake_vSphereConsole, fake_sleep):
        """``configure_new_cluster`` executes the correct function for OneFS 8.2.0.x"""
        fake_logger = MagicMock()
        setup_onefs.configure_new_cluster(version='8.2.0.0', logger=fake_logger)

        called = fake_configure_new_8_2_0_cluster.call_count
        expected = 1

        self.assertEqual(called, expected)

    def test_configure_new_8_0_cluster(self, fake_vSphereConsole, fake_sleep):
        """``configure_new_8_0_cluster`` returns None"""
        fake_logger = MagicMock()
        output = setup_onefs.configure_new_8_0_cluster(logger=fake_logger,
                                                       console_url='https://someHTMLconsole.com',
                                                       cluster_name='mycluster',
                                                       int_netmask='255.255.255.0',
                                                       int_ip_low='8.6.7.5',
                                                       int_ip_high='8.6.7.50',
                                                       ext_netmask='255.255.255.0',
                                                       ext_ip_low='3.0.9.2',
                                                       ext_ip_high='3.0.9.20',
                                                       gateway='3.0.9.1',
                                                       dns_servers='1.1.1.1',
                                                       encoding='utf-8',
                                                       sc_zonename='myzone.foo.org',
                                                       smartconnect_ip='3.0.9.21')
        expected = None

        self.assertEqual(output, expected)

    def test_configure_new_8_1_cluster(self, fake_vSphereConsole, fake_sleep):
        """``configure_new_8_1_cluster`` returns None"""
        fake_logger = MagicMock()
        output = setup_onefs.configure_new_8_1_cluster(logger=fake_logger,
                                                       console_url='https://someHTMLconsole.com',
                                                       cluster_name='mycluster',
                                                       int_netmask='255.255.255.0',
                                                       int_ip_low='8.6.7.5',
                                                       int_ip_high='8.6.7.50',
                                                       ext_netmask='255.255.255.0',
                                                       ext_ip_low='3.0.9.2',
                                                       ext_ip_high='3.0.9.20',
                                                       gateway='3.0.9.1',
                                                       dns_servers='1.1.1.1',
                                                       encoding='utf-8',
                                                       sc_zonename='myzone.foo.org',
                                                       smartconnect_ip='3.0.9.21')
        expected = None

        self.assertEqual(output, expected)

    def test_configure_new_8_2_0_cluster(self, fake_vSphereConsole, fake_sleep):
        """``configure_new_8_2_0_cluster`` returns None"""
        fake_logger = MagicMock()
        output = setup_onefs.configure_new_8_2_0_cluster(logger=fake_logger,
                                                       console_url='https://someHTMLconsole.com',
                                                       cluster_name='mycluster',
                                                       int_netmask='255.255.255.0',
                                                       int_ip_low='8.6.7.5',
                                                       int_ip_high='8.6.7.50',
                                                       ext_netmask='255.255.255.0',
                                                       ext_ip_low='3.0.9.2',
                                                       ext_ip_high='3.0.9.20',
                                                       gateway='3.0.9.1',
                                                       dns_servers='1.1.1.1',
                                                       encoding='utf-8',
                                                       sc_zonename='myzone.foo.org',
                                                       smartconnect_ip='3.0.9.21')
        expected = None

        self.assertEqual(output, expected)

    @patch.object(setup_onefs, 'make_new_and_accept_eual')
    def test_configure_new_8_2_0_cluster_eula(self, fake_make_new_and_accept_eual, fake_vSphereConsole, fake_sleep):
        """``configure_new_8_2_0_cluster`` presses enter before trying to accept the EULA"""
        fake_logger = MagicMock()
        setup_onefs.configure_new_8_2_0_cluster(logger=fake_logger,
                                                console_url='https://someHTMLconsole.com',
                                                cluster_name='mycluster',
                                                int_netmask='255.255.255.0',
                                                int_ip_low='8.6.7.5',
                                                int_ip_high='8.6.7.50',
                                                ext_netmask='255.255.255.0',
                                                ext_ip_low='3.0.9.2',
                                                ext_ip_high='3.0.9.20',
                                                gateway='3.0.9.1',
                                                dns_servers='1.1.1.1',
                                                encoding='utf-8',
                                                sc_zonename='myzone.foo.org',
                                                smartconnect_ip='3.0.9.21')

        _, the_kwargs = fake_make_new_and_accept_eual.call_args
        pressed_enter = the_kwargs['auto_enter']

        self.assertTrue(pressed_enter)

    def test_configure_new_8_1_2_cluster(self, fake_vSphereConsole, fake_sleep):
        """``configure_new_8_1_2_cluster`` returns None"""
        fake_logger = MagicMock()
        output = setup_onefs.configure_new_8_1_2_cluster(logger=fake_logger,
                                                       console_url='https://someHTMLconsole.com',
                                                       cluster_name='mycluster',
                                                       int_netmask='255.255.255.0',
                                                       int_ip_low='8.6.7.5',
                                                       int_ip_high='8.6.7.50',
                                                       ext_netmask='255.255.255.0',
                                                       ext_ip_low='3.0.9.2',
                                                       ext_ip_high='3.0.9.20',
                                                       gateway='3.0.9.1',
                                                       dns_servers='1.1.1.1',
                                                       encoding='utf-8',
                                                       sc_zonename='myzone.foo.org',
                                                       smartconnect_ip='3.0.9.21')
        expected = None

        self.assertEqual(output, expected)

    @patch.object(setup_onefs, 'set_esrs')
    def test_configure_new_8_1_2_cluster_esrs(self, fake_set_esrs, fake_vSphereConsole, fake_sleep):
        """``configure_new_8_1_2_cluster`` does not config ESRS"""
        fake_logger = MagicMock()
        setup_onefs.configure_new_8_1_2_cluster(logger=fake_logger,
                                                console_url='https://someHTMLconsole.com',
                                                cluster_name='mycluster',
                                                int_netmask='255.255.255.0',
                                                int_ip_low='8.6.7.5',
                                                int_ip_high='8.6.7.50',
                                                ext_netmask='255.255.255.0',
                                                ext_ip_low='3.0.9.2',
                                                ext_ip_high='3.0.9.20',
                                                gateway='3.0.9.1',
                                                dns_servers='1.1.1.1',
                                                encoding='utf-8',
                                                sc_zonename='myzone.foo.org',
                                                smartconnect_ip='3.0.9.21')
        called = fake_set_esrs.call_count
        expected = 0

        self.assertEqual(called, expected)


class TestWizardRoutines(unittest.TestCase):
    """
    A set of test cases for the functions that handle a specific part of the
    OneFS configuration wizard.
    """
    @classmethod
    def setUp(cls):
        cls.fake_console = MagicMock()

    @patch.object(setup_onefs.time, 'sleep')
    def test_format_disks(self, fake_sleep):
        """``format_disks`` returns None"""
        output = setup_onefs.format_disks(self.fake_console)
        expected = None

        self.assertEqual(output, expected)

    @patch.object(setup_onefs.time, 'sleep')
    def test_format_disks(self, fake_sleep):
        """``format_disks`` blocks while the disks format"""
        setup_onefs.format_disks(self.fake_console)

        args, _ = fake_sleep.call_args
        expected = (setup_onefs.FORMAT_WAIT,)

        self.assertEqual(args, expected)

    def test_make_new_and_accept_eual(self):
        """``make_new_and_accept_eual`` returns None"""
        output = setup_onefs.make_new_and_accept_eual(self.fake_console)
        expected = None

        self.assertEqual(output, expected)

    @patch.object(setup_onefs.time, 'sleep')
    def test_set_passwords(self, fake_sleep):
        """``set_passwords`` returns None"""
        output = setup_onefs.set_passwords(self.fake_console)
        expected = None

        self.assertEqual(output, expected)

    def test_set_esrs(self):
        """``set_esrs`` returns None"""
        output = setup_onefs.set_esrs(self.fake_console)
        expected = None

        self.assertEqual(output, expected)

    def test_set_name(self):
        """``set_esrs`` returns None"""
        output = setup_onefs.set_name(self.fake_console, 'mycluster')
        expected = None

        self.assertEqual(output, expected)

    @patch.object(setup_onefs.time, 'sleep')
    def test_set_encoding(self, fake_sleep):
        """``set_encoding`` returns None"""
        output = setup_onefs.set_encoding(self.fake_console, 'utf-8')
        expected = None

        self.assertEqual(output, expected)

    @patch.object(setup_onefs.time, 'sleep')
    def test_config_network(self, fake_sleep):
        """``config_network`` returns None"""
        output = setup_onefs.config_network(self.fake_console,
                                            netmask='255.255.255.0',
                                            ip_low='2.2.2.2',
                                            ip_high='2.2.2.20')
        expected = None

        self.assertEqual(output, expected)

    def test_set_default_gateway(self):
        """``set_default_gateway`` returns None"""
        output = setup_onefs.set_default_gateway(self.fake_console, '2.2.2.1')
        expected = None

        self.assertEqual(output, expected)

    def test_set_smartconnect(self):
        """``set_smartconnect`` returns None"""
        output = setup_onefs.set_smartconnect(self.fake_console,
                                              sc_zonename='myzone.foo.com',
                                              smartconnect_ip='3.3.3.3')
        expected = None

        self.assertEqual(output, expected)

    def test_set_smartconnect_zone_name_optional(self):
        """``set_smartconnect`` setting the SmartConnect zone name is optional"""
        output = setup_onefs.set_smartconnect(self.fake_console,
                                              smartconnect_ip='3.3.3.3')
        expected = None

        self.assertEqual(output, expected)

    def test_set_smartconnect_sip_optional(self):
        """``set_smartconnect`` setting the SmartConnect IP is optional"""
        output = setup_onefs.set_smartconnect(self.fake_console,
                                              sc_zonename='myzone.foo.com')
        expected = None

        self.assertEqual(output, expected)

    def test_set_smartconnect_all_optional(self):
        """``set_smartconnect`` All smartconnect settings are skipped if not supplied"""
        setup_onefs.set_smartconnect(self.fake_console)

        call_count = self.fake_console.send_keys.call_count
        expected = 1

        self.assertEqual(call_count, expected)

    def test_set_dns(self):
        """``set_dns`` returns None"""
        output = setup_onefs.set_dns(self.fake_console, dns_servers='1.1.1.1')

        expected = None

        self.assertEqual(output, expected)

    def test_set_timezone(self):
        """``set_timezone`` returns None"""
        output = setup_onefs.set_timezone(self.fake_console)

        expected = None

        self.assertEqual(output, expected)

    def test_set_join_mode(self):
        """``set_join_mode`` returns None"""
        output = setup_onefs.set_join_mode(self.fake_console)

        expected = None

        self.assertEqual(output, expected)

    def test_commit_config(self):
        """``commit_config`` returns None"""
        output = setup_onefs.commit_config(self.fake_console)

        expected = None

        self.assertEqual(output, expected)


if __name__ == '__main__':
    unittest.main()
