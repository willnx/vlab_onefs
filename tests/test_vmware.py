# -*- coding: UTF-8 -*-
"""
A suite of tests for the functions in vmware.py
"""
import unittest
from unittest.mock import patch, MagicMock

from vlab_onefs_api.lib.worker import vmware


class TestVMware(unittest.TestCase):
    """A set of test cases for the vmware.py module"""
    @classmethod
    def setUpClass(cls):
        vmware.logger = MagicMock()

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'vCenter')
    def test_show_onefs(self, fake_vCenter, fake_get_info):
        """``show_onefs`` returns a dictionary when everything works as expected"""
        fake_vm = MagicMock()
        fake_vm.name = 'isi01'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value =  {'meta' :{'component': 'OneFS',
                                                'created': 1234,
                                                'version': '8.0.0.4',
                                                'configured': False,
                                                'generation': 1}}

        output = vmware.show_onefs(username='alice')
        expected = {'isi01': {'meta' :{'component': 'OneFS',
                                                'created': 1234,
                                                'version': '8.0.0.4',
                                                'configured': False,
                                                'generation': 1}}}

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'vCenter')
    def test_show_onefs_nothing(self, fake_vCenter, fake_get_info):
        """``show_onefs`` returns an empty dictionary no onefs is found"""
        fake_vm = MagicMock()
        fake_vm.name = 'isi01'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta' :{'component': 'otherThing',
                                                'created': 1234,
                                                'version': '8.0.0.4',
                                                'configured': False,
                                                'generation': 1}}

        output = vmware.show_onefs(username='alice')
        expected = {}

        self.assertEqual(output, expected)

    @patch.object(vmware.virtual_machine, 'consume_task')
    @patch.object(vmware, 'make_network_map')
    @patch.object(vmware, 'Ova')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, 'vCenter')
    def test_create_onefs(self, fake_vCenter, fake_deploy_from_ova, fake_get_info, fake_Ova, make_network_map, fake_consume_task):
        """``create_onefs`` returns the new onefs's info when everything works"""
        fake_logger = MagicMock()
        fake_Ova.return_value.networks = ['vLabNetwork']
        fake_get_info.return_value = {'worked' : True}
        fake_deploy_from_ova.return_value.name = 'isi01'

        output = vmware.create_onefs(username='alice',
                                     machine_name='isi01',
                                     image='8.0.0.4',
                                     front_end='externalNetwork',
                                     back_end='internalNetwork',
                                     logger=fake_logger)
        expected = {'isi01': {'worked': True}}

        self.assertEqual(output, expected)

    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'Ova')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, 'vCenter')
    def test_create_onefs_value_error(self, fake_vCenter, fake_deploy_from_ova, fake_get_info, fake_Ova, fake_consume_task):
        """``create_onefs`` raises ValueError if supplied with a non-existing front_end network"""
        fake_logger = MagicMock()
        fake_Ova.return_value.networks = ['vLabNetwork']
        fake_get_info.return_value = {'worked' : True}
        fake_vCenter.return_value.__enter__.return_value.networks = {'internalNetwork': vmware.vim.Network(moId='asdf')}

        with self.assertRaises(ValueError):
            vmware.create_onefs(username='alice',
                                    machine_name='isi01',
                                    image='8.0.0.4',
                                    front_end='not a thing',
                                    back_end='internalNetwork',
                                    logger=fake_logger)

    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'Ova')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, 'vCenter')
    def test_create_onefs_value_error_2(self, fake_vCenter, fake_deploy_from_ova, fake_get_info, fake_Ova, fake_consume_task):
        """``create_onefs`` raises ValueError if supplied with a non-existing back_end network"""
        fake_logger = MagicMock()
        fake_Ova.return_value.networks = ['vLabNetwork']
        fake_get_info.return_value = {'worked' : True}
        fake_vCenter.return_value.__enter__.return_value.networks = {'externallNetwork': vmware.vim.Network(moId='asdf')}

        with self.assertRaises(ValueError):
            vmware.create_onefs(username='alice',
                                    machine_name='isi01',
                                    image='8.0.0.4',
                                    front_end='externallNetwork',
                                    back_end='not a thing',
                                    logger=fake_logger)

    @patch.object(vmware, 'consume_task')
    @patch.object(vmware, 'Ova')
    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware.virtual_machine, 'deploy_from_ova')
    @patch.object(vmware, 'vCenter')
    def test_create_onefs_bad_image(self, fake_vCenter, fake_deploy_from_ova, fake_get_info, fake_Ova, fake_consume_task):
        """``create_onefs`` raises ValueError if supplied with a non-existing image of OneFS"""
        fake_logger = MagicMock()
        fake_Ova.side_effect = FileNotFoundError("testing")
        fake_get_info.return_value = {'worked' : True}
        fake_vCenter.return_value.__enter__.return_value.networks = {'externallNetwork': vmware.vim.Network(moId='asdf')}

        with self.assertRaises(ValueError):
            vmware.create_onefs(username='alice',
                                machine_name='isi01',
                                image='4.0.0.0',
                                front_end='externallNetwork',
                                back_end='internalNetwork',
                                logger=fake_logger)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware.virtual_machine, 'power')
    @patch.object(vmware, 'vCenter')
    def test_delete_onefs(self, fake_vCenter, fake_power, fake_consume_task, fake_get_info):
        """``delete_onefs`` powers off the VM then deletes it"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'isi01'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'meta' :{'component': 'OneFS',
                                                'created': 1234,
                                                'version': '8.0.0.4',
                                                'configured': False,
                                                'generation': 1}}
        vmware.delete_onefs(username='alice', machine_name='isi01', logger=fake_logger)

        self.assertTrue(fake_power.called)
        self.assertTrue(fake_vm.Destroy_Task.called)

    @patch.object(vmware.virtual_machine, 'get_info')
    @patch.object(vmware, 'consume_task')
    @patch.object(vmware.virtual_machine, 'power')
    @patch.object(vmware, 'vCenter')
    def test_delete_onefs_value_error(self, fake_vCenter, fake_power, fake_consume_task, fake_get_info):
        """``delete_onefs`` raises ValueError if no onefs machine has the supplied name"""
        fake_logger = MagicMock()
        fake_vm = MagicMock()
        fake_vm.name = 'isi01'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder
        fake_get_info.return_value = {'worked': True, 'note': "OneFS=8.0.0.4"}

        with self.assertRaises(ValueError):
            vmware.delete_onefs(username='alice', machine_name='not a thing', logger=fake_logger)

    @patch.object(vmware.os, 'listdir')
    def test_list_images(self, fake_listdir):
        """``list_images`` returns a list of images when everything works as expected"""
        fake_listdir.return_value = ['8.0.0.4.ova']

        output = vmware.list_images()
        expected = ['8.0.0.4']

        self.assertEqual(output, expected)

    def test_convert_name(self):
        """``convert_name`` defaults to converting versions to images"""
        output = vmware.convert_name('8.0.0.4')
        expected = '8.0.0.4.ova'

        self.assertEqual(output, expected)

    def test_convert_name_to_version(self):
        """``convert_name`` can convert from versions to image names"""
        output = vmware.convert_name('8.0.0.4.ova', to_version=True)
        expected = '8.0.0.4'

        self.assertEqual(output, expected)

    def test_make_network_map(self):
        """``make_network_map`` returns a list when everything works as expected"""
        fake_vcenter_networks = {'extNetwork': vmware.vim.Network(moId='asdf'),
                                 'intNetwork': vmware.vim.Network(moId='1234'),
                                }

        result = vmware.make_network_map(fake_vcenter_networks,
                                         front_end='extNetwork',
                                         back_end='intNetwork')

        self.assertTrue(isinstance(result, list))

    @patch.object(vmware.virtual_machine, 'set_meta')
    @patch.object(vmware, 'vCenter')
    def test_update_meta(self, fake_vCenter, fake_set_meta):
        """``update_meta`` connets to vSphere and sets the meta data on a supplied VM"""
        fake_vm = MagicMock()
        fake_vm.name = 'isi01'
        fake_folder = MagicMock()
        fake_folder.childEntity = [fake_vm]
        fake_vCenter.return_value.__enter__.return_value.get_by_name.return_value = fake_folder

        vmware.update_meta(username='jill', vm_name='isi01', new_meta={'worked': True})

        self.assertTrue(fake_set_meta.called)



if __name__ == '__main__':
    unittest.main()
