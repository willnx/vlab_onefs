# -*- coding: UTF-8 -*-
"""This module encapsulates configuring a OneFS node"""
import time

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from vlab_onefs_api.lib import const


BOOT_WAIT = 60   # dumb sleep while waiting for the node to fully boot
FORMAT_WAIT = 90 # dumb sleep waiting for the new VMDKs for format
BUILD_WAIT = 150  # dumb sleep while OneFS applies the new config
SECTION_PROCESS_PAUSE = 2 # allow the wizard to process a section, before moving onto the next one

# Compliance mode license: http://licensing.west.isilon.com/internal-license.php?modules=0xfffff


class vSphereConsole(object):
    """Login and return an interactive session with the HTML console for a VM"""
    def __init__(self, url, username=const.INF_VCENTER_READONLY_USER, headless=True,
                 password=const.INF_VCENTER_READONLY_PASSWORD):
        options = Options()
        options.add_argument("--headless")
        options.add_argument("--no-sandbox")
        self._driver = webdriver.Chrome(chrome_options=options, service_log_path='/var/log/webdriver.log')
        login_page = 'https://{}/ui'.format(const.INF_VCENTER_SERVER)
        self._username = username
        self._password = password
        self._driver.get(login_page)
        self._login()
        self._console = self._get_console(url)
        self.keys = Keys

    def _login(self):
        # Waits upwards of 30 seconds for the page to load
        username_field = WebDriverWait(self._driver, 30).until(
            EC.presence_of_element_located((By.ID, "username")))
        username_field.send_keys(self._username)
        password_field = self._driver.find_element_by_id('password')
        password_field.send_keys(self._password)
        login_button = self._driver.find_element_by_id('submit')
        login_button.click()
        # Waits for the login to complete; avoids race between getting auth cookie
        # and attempting to access the HTML console
        WebDriverWait(self._driver, 30).until(
            EC.presence_of_element_located((By.ID, "MainTemplateController"))
        )

    def _get_console(self, url):
        self._driver.get(url)
        # Waits upwards of 30 seconds for the page to load
        console = WebDriverWait(self._driver, 30).until(
            EC.presence_of_element_located((By.ID, "mainCanvas")))
        return console

    def __enter__(self):
        """Enables use of the ``with`` statement"""
        return self

    def __exit__(self, exc_type, exc_value, the_traceback):
        self._driver.quit()

    def send_keys(self, *args, auto_enter=True):
        """Like, if you were to type with your keyboard.

        For non-standard keys (like ENTER, SHIFT, etc), look at the
        vSphereConsole.keys object.

        :Returns: None

        :param *args: The series of keys you want to input to the console
        :type *args: List

        :param auto_enter: Presses the ENTER key for you when set to True.
        :type auto_enter: Boolean
        """
        self._console.send_keys(*args)
        time.sleep(1) # Give the HTML console time to react to input
        if auto_enter:
            self._console.send_keys(Keys.ENTER)
            time.sleep(1)


def join_existing_cluster(console_url, cluster_name, logger):
    """Adds a new node to an existing cluster"""
    logger.info('Setting up Selenium')
    with vSphereConsole(console_url) as console:
        logger.info('Waiting {} seconds for node to fully boot'.format(BOOT_WAIT))
        time.sleep(BOOT_WAIT) # Wait for the node to finish booting
        logger.info('Formatting disks')
        format_disks(console)
        logger.info('Joining cluster {}'.format(cluster_name))
        console.send_keys('2')
        console.send_keys(cluster_name)
        logger.info('Waiting {} seconds for the node to join'.format(BUILD_WAIT))
        time.sleep(BUILD_WAIT)


def configure_new_cluster(version, logger, **kwargs):
    """Because for some reason, the order of the Wizard changes with OneFS releases...

    :param version: The version of OneFS to configure
    :type version: String
    """
    if version >= '8.1.2.0':
        logger.info('Config OneFS >= 8.1.2.0')
        return configure_new_8_1_2_cluster(logger=logger, **kwargs)
    elif version >= '8.1.0.0':
        logger.info('Config OneFS 8.1.0 -> 8.1.1')
        return configure_new_8_1_cluster(logger=logger, **kwargs)
    else:
        logger.info('Config OneFS 8.0.0')
        return configure_new_8_0_cluster(logger=logger, **kwargs)


def configure_new_8_0_cluster(console_url, cluster_name, int_netmask, int_ip_low, int_ip_high,
                              ext_netmask, ext_ip_low, ext_ip_high, gateway, dns_servers,
                              encoding, sc_zonename, smartconnect_ip, logger):
    """Walk through the config Wizard to create a functional one-node cluster

    :Returns: None

    :param console_url: The URL to the vSphere HTML console for the OneFS node
    :type console_url: String

    :param cluster_name: The name to give the new cluster
    :type cluster_name: String

    :param int_netmask: The subnet mask for the internal OneFS network
    :type int_netmask: String

    :param int_ip_low: The smallest IP to assign to an internal NIC
    :type int_ip_low: String (IPv4 address)

    :param int_ip_high: The largest IP to assign to an internal NIC
    :type int_ip_high: String (IPv4 address)

    :param ext_ip_low: The smallest IP to assign to an external/public NIC
    :type ext_ip_low: String (IPv4 address)

    :param ext_ip_high: The largest IP to assign to an external/public NIC
    :type ext_ip_high: String (IPv4 address)

    :param gateway: The IP address for the default gateway
    :type gateway: String (IPv4 address)

    :param dns_servers: A common separated list of IPs of the DNS servers to use
    :type dns_servers: String

    :param encoding: The filesystem encoding to use.
    :type encoding: String

    :param sc_zonename: The SmartConnect Zone name to use. Skipped if None.
    :type sc_zonename: String

    :param smartconnect_ip: The IPv4 address to use as the SIP
    :type smartconnect_ip: String (IPv4 address)

    :param logger: A object for logging information/errors
    :type logger: logging.Logger
    """
    logger.info('Setting up Selenium')
    with vSphereConsole(console_url) as console:
        logger.info('Waiting {} seconds for node to fully boot'.format(BOOT_WAIT))
        time.sleep(BOOT_WAIT) # Wait for the node to finish booting
        logger.info('Formatting disks')
        format_disks(console)
        logger.info('Accepting EULA')
        make_new_and_accept_eual(console)
        logger.info('Setting root and admin passwords')
        set_passwords(console)
        logger.info('Skipping ESRS config')
        set_esrs(console) # 8.0.0.x; ESRS comes before everything else...
        logger.info("Naming cluster {}".format(cluster_name))
        set_name(console, cluster_name)
        logger.info("Settings encoding to {}".format(encoding))
        set_encoding(console, encoding)
        # setup int network
        logger.info('Setting up internal network - Mask: {} Low: {} High: {}'.format(int_netmask, int_ip_low, int_ip_high))
        config_network(console, netmask=int_netmask, ip_low=int_ip_low, ip_high=int_ip_high)
        # setup ext network
        logger.info('Settings up external network - Mask: {} Low: {} High: {}'.format(ext_netmask, ext_ip_low, ext_ip_high))
        config_network(console, netmask=ext_netmask, ip_low=ext_ip_low, ip_high=ext_ip_high, ext_network=True)
        logger.info('Setting up default gateway for ext network to {}'.format(gateway))
        set_default_gateway(console, gateway)
        logger.info('Configuring SmartConnect - Zone: {} IP: {}'.format(sc_zonename, smartconnect_ip))
        set_smartconnect(console, sc_zonename, smartconnect_ip)
        logger.info('Setting DNS servers to {}'.format(dns_servers))
        set_dns(console, dns_servers)
        logger.info('Skipping timezone config')
        set_timezone(console)
        logger.info('Skipping join mode config')
        set_join_mode(console)
        logger.info('Commiting changes and waiting {} seconds'.format(BUILD_WAIT))
        commit_config(console)
        time.sleep(BUILD_WAIT)


def configure_new_8_1_cluster(console_url, cluster_name, int_netmask, int_ip_low, int_ip_high,
                              ext_netmask, ext_ip_low, ext_ip_high, gateway, dns_servers,
                              encoding, sc_zonename, smartconnect_ip, logger):
    """Walk through the config Wizard to create a functional one-node cluster

    :Returns: None

    :param console_url: The URL to the vSphere HTML console for the OneFS node
    :type console_url: String

    :param cluster_name: The name to give the new cluster
    :type cluster_name: String

    :param int_netmask: The subnet mask for the internal OneFS network
    :type int_netmask: String

    :param int_ip_low: The smallest IP to assign to an internal NIC
    :type int_ip_low: String (IPv4 address)

    :param int_ip_high: The largest IP to assign to an internal NIC
    :type int_ip_high: String (IPv4 address)

    :param ext_ip_low: The smallest IP to assign to an external/public NIC
    :type ext_ip_low: String (IPv4 address)

    :param ext_ip_high: The largest IP to assign to an external/public NIC
    :type ext_ip_high: String (IPv4 address)

    :param gateway: The IP address for the default gateway
    :type gateway: String (IPv4 address)

    :param dns_servers: A common separated list of IPs of the DNS servers to use
    :type dns_servers: String

    :param encoding: The filesystem encoding to use.
    :type encoding: String

    :param sc_zonename: The SmartConnect Zone name to use. Skipped if None.
    :type sc_zonename: String

    :param smartconnect_ip: The IPv4 address to use as the SIP
    :type smartconnect_ip: String (IPv4 address)

    :param logger: A object for logging information/errors
    :type logger: logging.Logger
    """
    logger.info('Setting up Selenium')
    with vSphereConsole(console_url) as console:
        logger.info('Waiting {} seconds for node to fully boot'.format(BOOT_WAIT))
        time.sleep(BOOT_WAIT)
        logger.info('Formatting disks')
        format_disks(console)
        logger.info('Accepting EULA')
        make_new_and_accept_eual(console)
        logger.info('Setting root and admin passwords')
        set_passwords(console)
        logger.info("Naming cluster {}".format(cluster_name))
        set_name(console, cluster_name) # 8.1.0.4 name comes before ESRS
        logger.info("Settings encoding to {}".format(encoding))
        set_encoding(console, encoding)
        logger.info('Skipping ESRS config')
        set_esrs(console)
        # setup int network
        logger.info('Setting up internal network - Mask: {} Low: {} High: {}'.format(int_netmask, int_ip_low, int_ip_high))
        config_network(console, netmask=int_netmask, ip_low=int_ip_low, ip_high=int_ip_high)
        # setup ext network
        logger.info('Settings up external network - Mask: {} Low: {} High: {}'.format(ext_netmask, ext_ip_low, ext_ip_high))
        config_network(console, netmask=ext_netmask, ip_low=ext_ip_low, ip_high=ext_ip_high, ext_network=True)
        logger.info('Setting up default gateway for ext network to {}'.format(gateway))
        set_default_gateway(console, gateway)
        logger.info('Configuring SmartConnect - Zone: {} IP: {}'.format(sc_zonename, smartconnect_ip))
        set_smartconnect(console, sc_zonename, smartconnect_ip)
        logger.info('Setting DNS servers to {}'.format(dns_servers))
        set_dns(console, dns_servers)
        logger.info('Skipping timezone config')
        set_timezone(console)
        logger.info('Skipping join mode config')
        set_join_mode(console)
        logger.info('Commiting changes and waiting {} seconds'.format(BUILD_WAIT))
        commit_config(console)
        time.sleep(BUILD_WAIT)


def configure_new_8_1_2_cluster(console_url, cluster_name, int_netmask, int_ip_low, int_ip_high,
                              ext_netmask, ext_ip_low, ext_ip_high, gateway, dns_servers,
                              encoding, sc_zonename, smartconnect_ip, logger):
    """Walk through the config Wizard to create a functional one-node cluster

    :Returns: None

    :param console_url: The URL to the vSphere HTML console for the OneFS node
    :type console_url: String

    :param cluster_name: The name to give the new cluster
    :type cluster_name: String

    :param int_netmask: The subnet mask for the internal OneFS network
    :type int_netmask: String

    :param int_ip_low: The smallest IP to assign to an internal NIC
    :type int_ip_low: String (IPv4 address)

    :param int_ip_high: The largest IP to assign to an internal NIC
    :type int_ip_high: String (IPv4 address)

    :param ext_ip_low: The smallest IP to assign to an external/public NIC
    :type ext_ip_low: String (IPv4 address)

    :param ext_ip_high: The largest IP to assign to an external/public NIC
    :type ext_ip_high: String (IPv4 address)

    :param gateway: The IP address for the default gateway
    :type gateway: String (IPv4 address)

    :param dns_servers: A common separated list of IPs of the DNS servers to use
    :type dns_servers: String

    :param encoding: The filesystem encoding to use.
    :type encoding: String

    :param sc_zonename: The SmartConnect Zone name to use. Skipped if None.
    :type sc_zonename: String

    :param smartconnect_ip: The IPv4 address to use as the SIP
    :type smartconnect_ip: String (IPv4 address)

    :param logger: A object for logging information/errors
    :type logger: logging.Logger
    """
    logger.info('Setting up Selenium')
    with vSphereConsole(console_url) as console:
        logger.info('Waiting {} seconds for node to fully boot'.format(BOOT_WAIT))
        time.sleep(BOOT_WAIT)
        logger.info('Formatting disks')
        format_disks(console)
        logger.info('Accepting EULA')
        make_new_and_accept_eual(console)
        logger.info('Setting root and admin passwords')
        set_passwords(console)
        logger.info("Naming cluster {}".format(cluster_name))
        set_name(console, cluster_name) # 8.1.0.4 name comes before ESRS
        logger.info("Settings encoding to {}".format(encoding))
        set_encoding(console, encoding)
        logger.info('Skipping ESRS config')
        # ESRS not even set via Wizard...
        # setup int network
        logger.info('Setting up internal network - Mask: {} Low: {} High: {}'.format(int_netmask, int_ip_low, int_ip_high))
        config_network(console, netmask=int_netmask, ip_low=int_ip_low, ip_high=int_ip_high)
        # setup ext network
        logger.info('Settings up external network - Mask: {} Low: {} High: {}'.format(ext_netmask, ext_ip_low, ext_ip_high))
        config_network(console, netmask=ext_netmask, ip_low=ext_ip_low, ip_high=ext_ip_high, ext_network=True)
        logger.info('Setting up default gateway for ext network to {}'.format(gateway))
        set_default_gateway(console, gateway)
        logger.info('Configuring SmartConnect - Zone: {} IP: {}'.format(sc_zonename, smartconnect_ip))
        set_smartconnect(console, sc_zonename, smartconnect_ip)
        logger.info('Setting DNS servers to {}'.format(dns_servers))
        set_dns(console, dns_servers)
        logger.info('Skipping timezone config')
        set_timezone(console)
        logger.info('Skipping join mode config')
        set_join_mode(console)
        logger.info('Commiting changes and waiting {} seconds'.format(BUILD_WAIT))
        commit_config(console)
        time.sleep(BUILD_WAIT)


def format_disks(console):
    """vOneFS clusters require you to format the new VMDKs"""
    console.send_keys('yes')
    # sleep here while disks format...
    time.sleep(FORMAT_WAIT)


def make_new_and_accept_eual(console):
    """First prompt of the Wizard; choose to make a new cluster, and accept the EULA"""
    # 1 means "make a new cluster"
    console.send_keys('1')
    # Accept EULA
    # Skip to the yes/no prompt
    console.send_keys(console.keys.SHIFT, 'g', auto_enter=False)
    console.send_keys('yes')


def set_passwords(console, root='a', admin='a'):
    """Set the root and admin user passwords"""
    # Set root password
    console.send_keys(root)
    # Confirm root password
    console.send_keys(root)
    # Set admin password
    console.send_keys(admin)
    # Confirm admin password
    console.send_keys(admin)
    time.sleep(SECTION_PROCESS_PAUSE)


def set_esrs(console, enabled='no'):
    """Configure ESRS"""
    console.send_keys(enabled)


def set_name(console, cluster_name):
    """Define the name of the new cluster"""
    # set cluster name
    console.send_keys(cluster_name)


def set_encoding(console, encoding):
    """Choose the filesystem encoding used"""
    # config for UTF8 encoding
    mapping = {
        'windows-sjis' : '1',
        'windows-949' : '2',
        'windows-1252' : '3',
        'euc-kr' : '4',
        'euc-jp' : '5',
        'euc-jp-ms' : '6',
        'utf-8-mac' : '7',
        'utf-8' : '8',
        'latin-1' : '9',
        'latin-2' : '10',
        'latin-3' : '11',
        'latin-4' : '12',
        'cyrillic' : '13',
        'arabic' : '14',
        'greek' : '15',
        'hebrew' : '16',
        'latin-5' : '17',
        'latin-6' : '18',
        'latin-7' : '19',
        'latin-8' : '20',
        'latin-9' : '21',
        'latin-10' : '22'
    }
    console.send_keys(mapping[encoding.lower()])
    time.sleep(SECTION_PROCESS_PAUSE)


def config_network(console, netmask, ip_low, ip_high, ext_network=False):
    """Setting external or internal network information is the same series of prmopts"""
    if ext_network:
        # choose to use the ext interface, instead of the IB network...
        console.send_keys('1')
    # set Netmask
    console.send_keys('1')
    console.send_keys(netmask)
    # config IP range
    console.send_keys('3')
    # Add IP range
    console.send_keys('1')
    console.send_keys(ip_low)
    # Clear out the low IP
    for char in ip_low:
        console.send_keys(console.keys.BACKSPACE, auto_enter=False)
    console.send_keys(ip_high, auto_enter=False)
    # Keep current config
    console.send_keys(console.keys.ENTER, auto_enter=False)
    # onto the next section
    console.send_keys(Keys.ENTER, auto_enter=False)
    console.send_keys(Keys.ENTER, auto_enter=False)
    console.send_keys(Keys.ENTER, auto_enter=False)
    time.sleep(SECTION_PROCESS_PAUSE)


def set_default_gateway(console, gateway):
    """Define the default gateway for the external network"""
    # set default gateway
    console.send_keys(gateway)


def set_smartconnect(console, sc_zonename=None, smartconnect_ip=None):
    """Configure SmartConnect"""
    if sc_zonename:
        console.send_keys('1')
        console.send_keys(sc_zonename)
    if smartconnect_ip:
        console.send_keys('2')
        console.send_keys(smartconnect_ip)
    console.send_keys(console.keys.ENTER, auto_enter=False)


def set_dns(console, dns_servers):
    """Configure the DNS servers the external network uses

    dsn_servers must be an IPv4 address or common delimited IPv4 addresses
    """
    # Set DNS server(s)
    console.send_keys('1')
    console.send_keys(dns_servers)
    # Exit DNS config
    console.send_keys(console.keys.ENTER, auto_enter=False)
    # Exit Ext network config
    console.send_keys(console.keys.ENTER, auto_enter=False)


def set_timezone(console, timezone=None):
    """Configure the timezone information"""
    # Skip timezone stuff
    console.send_keys(Keys.ENTER, auto_enter=False)


def set_join_mode(console):
    """Define the mode nodes need to join the cluster"""
    # Keep default join mode
    console.send_keys(Keys.ENTER, auto_enter=False)


def commit_config(console):
    """Submit the new config"""
    # Commit changes?
    console.send_keys('yes')
