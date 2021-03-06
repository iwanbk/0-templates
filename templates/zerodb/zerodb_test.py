from unittest import TestCase
from unittest.mock import MagicMock, patch, call
import tempfile
import shutil
import os
import pytest

from zerodb import Zerodb, CONTAINER_TEMPLATE_UID, ZERODB_FLIST, NODE_CLIENT
from zerorobot import config
from zerorobot.template_uid import TemplateUID
from zerorobot.template.state import StateCheckError


class TestZerodbTemplate(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.valid_data = {
            'nodePort': 9900,
            'mode': 'user',
            'sync': False,
            'admin': '',
            'disk': '/dev/sda1',
        }
        config.DATA_DIR = tempfile.mkdtemp(prefix='0-templates_')
        Zerodb.template_uid = TemplateUID.parse(
            'github.com/zero-os/0-templates/%s/%s' % (Zerodb.template_name, Zerodb.version))

    @classmethod
    def tearDownClass(cls):
        if os.path.exists(config.DATA_DIR):
            shutil.rmtree(config.DATA_DIR)

    def setUp(self):
        patch('js9.j.clients.zero_os.sal', MagicMock()).start()

    def tearDown(self):
        patch.stopall()

    def test_create_valid_data(self):
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb.validate()
        assert zdb.data == self.valid_data

    def test_node_sal(self):
        """
        Test node_sal property
        """
        get_node = patch('js9.j.clients.zero_os.sal.get_node', MagicMock(return_value='node_sal')).start()
        zdb = Zerodb('zdb', data=self.valid_data)

        assert zdb._node_sal == 'node_sal'
        get_node.assert_called_once_with(NODE_CLIENT)

    def test_container_sal(self):
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb._node_sal.containers.get = MagicMock(return_value='container')

        assert zdb._container_sal == 'container'
        zdb._node_sal.containers.get.assert_called_once_with(zdb._container_name)

    def test_zerodb_sal(self):
        """
        Test node_sal property
        """
        zdb_sal = patch('js9.j.clients.zero_os.sal.get_zerodb', MagicMock(return_value='zdb_sal')).start()
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb.api.services.get = MagicMock()

        assert zdb._zerodb_sal == 'zdb_sal'
        assert zdb_sal.called

    def test_install(self):
        """
        Test install action
        """
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb.api.services.find_or_create = MagicMock()
        zdb._node_sal.freeports = MagicMock(return_value=[9900])

        zdb.install()

        zdb.api.services.find_or_create.assert_called_once_with(
            CONTAINER_TEMPLATE_UID, zdb._container_name, data=zdb._container_data)
        zdb.state.check('actions', 'install', 'ok')

    def test_start(self):
        """
        Test start action
        """
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb.state.set('actions', 'install', 'ok')
        zdb.api.services.get = MagicMock()
        zdb._node_sal.freeports = MagicMock(return_value=[9900])
        zdb.start()

        zdb.api.services.get.assert_called_once_with(
            template_uid=CONTAINER_TEMPLATE_UID, name=zdb._container_name)
        zdb._zerodb_sal.start.assert_called_once_with()
        zdb.state.check('actions', 'start', 'ok')

    def test_start_before_install(self):
        """
        Test start action without installing
        """
        with pytest.raises(StateCheckError,
                           message='start action should raise an error if zerodb is not installed'):
            zdb = Zerodb('zdb', data=self.valid_data)
            zdb.start()

    def test_stop(self):
        """
        Test stop action
        """
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb.state.set('actions', 'install', 'ok')
        zdb.api.services.get = MagicMock()
        zdb.stop()

        zdb._zerodb_sal.stop.assert_called_once_with()

    def test_stop_before_install(self):
        """
        Test stop action without install
        """
        with pytest.raises(StateCheckError,
                           message='stop action should raise an error if zerodb is not installed'):
            zdb = Zerodb('zdb', data=self.valid_data)
            zdb.stop()

    def test_namespace_list_before_start(self):
        """
        Test namespace_list action without start
        """
        with pytest.raises(StateCheckError,
                           message='namespace_list action should raise an error if zerodb is not started'):
            zdb = Zerodb('zdb', data=self.valid_data)
            zdb.namespace_list()

    def test_namespace_list(self):
        """
        Test namespace_list action
        """
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb.state.set('actions', 'start', 'ok')
        zdb.api.services.get = MagicMock()
        zdb.namespace_list()

        zdb._zerodb_sal.list_namespaces.assert_called_once_with()

    def test_namespace_info_before_start(self):
        """
        Test namespace_info action without start
        """
        with pytest.raises(StateCheckError,
                           message='namespace action should raise an error if zerodb is not started'):
            zdb = Zerodb('zdb', data=self.valid_data)
            zdb.namespace_info('namespace')

    def test_namespace_info(self):
        """
        Test namespace_info action
        """
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb.state.set('actions', 'start', 'ok')
        zdb.api.services.get = MagicMock()
        zdb.namespace_info('namespace')

        zdb._zerodb_sal.get_namespace_info.assert_called_once_with('namespace')

    def test_namespace_create_before_start(self):
        """
        Test namespace_create action without start
        """
        with pytest.raises(StateCheckError,
                           message='namespace_create action should raise an error if zerodb is not started'):
            zdb = Zerodb('zdb', data=self.valid_data)
            zdb.namespace_create('namespace')

    def test_namespace_create(self):
        """
        Test namespace_set action
        """
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb.state.set('actions', 'start', 'ok')
        zdb.api.services.get = MagicMock()
        zdb.namespace_create('namespace', 12, 'secret')

        zdb._zerodb_sal.create_namespace.assert_called_once_with('namespace')
        zdb._zerodb_sal.set_namespace_property.assert_has_calls(
            [call('namespace', 'maxsize', 12), call('namespace', 'password', 'secret')])

    def test_namespace_set_before_start(self):
        """
        Test namespace_set action without start
        """
        with pytest.raises(StateCheckError,
                           message='namespace_set action should raise an error if zerodb is not started'):
            zdb = Zerodb('zdb', data=self.valid_data)
            zdb.namespace_set('namespace', 'maxsize', 12)

    def test_namespace_set(self):
        """
        Test namespace_set action
        """
        zdb = Zerodb('zdb', data=self.valid_data)
        zdb.state.set('actions', 'start', 'ok')
        zdb.api.services.get = MagicMock()
        zdb.namespace_set('namespace', 'maxsize', 12)

        zdb._zerodb_sal.set_namespace_property.assert_called_once_with('namespace', 'maxsize', 12)
