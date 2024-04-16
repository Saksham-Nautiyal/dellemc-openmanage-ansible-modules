# -*- coding: utf-8 -*-

#
# Dell OpenManage Ansible Modules
# Version 9.2.0
# Copyright (C) 2024 Dell Inc. or its subsidiaries. All Rights Reserved.

# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
#

from __future__ import absolute_import, division, print_function


import pytest
from ansible_collections.dellemc.openmanage.plugins.modules import idrac_session
from ansible_collections.dellemc.openmanage.tests.unit.plugins.modules.common import FakeAnsibleModule
from mock import MagicMock
from ansible_collections.dellemc.openmanage.plugins.modules.idrac_session import main


MODULE_PATH = 'ansible_collections.dellemc.openmanage.plugins.modules.idrac_session.'
MODULE_UTILS_PATH = 'ansible_collections.dellemc.openmanage.plugins.module_utils.utils.'

REDFISH = "/redfish/v1"
SESSIONS = "Sessions"
ODATA = "@odata.id"
ODATA_REGEX = "(.*?)@odata"

SESSION_URL = "/redfish/v1/SessionService/Sessions"
GET_SESSION_URL = "Session.get_session_url"

CREATE_SUCCESS_MSG = "The session has been created successfully."
DELETE_SUCCESS_MSG = "The session has been deleted successfully."
FAILURE_MSG = "Unable to '{operation}' a session."
CHANGES_FOUND_MSG = "Changes found to be applied."
NO_CHANGES_FOUND_MSG = "No changes found to be applied."


class TestSession(FakeAnsibleModule):
    module = idrac_session

    @pytest.fixture
    def idrac_session_mock(self):
        idrac_obj = MagicMock()
        return idrac_obj

    @pytest.fixture
    def idrac_connection_session_mock(self, mocker, idrac_session_mock):
        idrac_conn_mock = mocker.patch(MODULE_PATH + 'SessionAPI',
                                       return_value=idrac_session_mock)
        idrac_conn_mock.return_value.__enter__.return_value = idrac_session_mock
        return idrac_conn_mock

    def test_get_session_url(self, idrac_default_args, idrac_connection_session_mock, mocker):
        v1_resp = {'Links': {'Sessions': {'@odata.id': SESSION_URL}}}
        mocker.patch(MODULE_PATH + "get_dynamic_uri",
                     return_value=v1_resp)
        f_module = self.get_module_mock(
            params=idrac_default_args, check_mode=False)
        session_obj = self.module.Session(
            idrac_connection_session_mock, f_module)
        sessions_url = session_obj.get_session_url()
        assert sessions_url == SESSION_URL


class TestCreateSession(FakeAnsibleModule):
    module = idrac_session

    @pytest.fixture
    def create_session_mock(self):
        idrac_obj = MagicMock()
        return idrac_obj

    @pytest.fixture
    def idrac_connection_session_mock(self, mocker, create_session_mock):
        idrac_conn_mock = mocker.patch(MODULE_PATH + 'SessionAPI',
                                       return_value=create_session_mock)
        idrac_conn_mock.return_value.__enter__.return_value = create_session_mock
        return idrac_conn_mock

    def test_session_operation(self, idrac_default_args, idrac_connection_session_mock):
        idrac_default_args.update({"state": "present"})
        f_module = self.get_module_mock(params=idrac_default_args, check_mode=False)
        session_class = self.module.CreateSession(idrac_connection_session_mock, f_module)
        assert isinstance(session_class, self.module.CreateSession)

        idrac_default_args.update({"state": "absent"})
        f_module = self.get_module_mock(params=idrac_default_args, check_mode=False)
        session_class = self.module.DeleteSession(idrac_connection_session_mock, f_module)
        assert isinstance(session_class, self.module.DeleteSession)

    def test_create_session_failure(self, idrac_connection_session_mock, mocker):
        f_module = MagicMock()
        session_obj = idrac_session.CreateSession(
            idrac_connection_session_mock, f_module)
        session_obj.get_session_url = MagicMock(return_value=SESSION_URL)
        f_module.check_mode = False
        f_module.params = {
            "username": "admin",
            "password": "password"
        }
        response_mock = MagicMock()
        response_mock.status_code = 201
        mocker.patch.object(idrac_connection_session_mock.return_value, 'invoke_request',
                            return_value=response_mock)

        session_obj.execute()
        f_module.exit_json.assert_called_once_with(
            msg="Unable to 'create' a session.",
            failed=True
        )

    def test_create_session_success(self, idrac_connection_session_mock):
        f_module = self.get_module_mock(
            params={"username": "admin", "password": "password"}, check_mode=False)
        session_obj = idrac_session.CreateSession(idrac_connection_session_mock, f_module)
        session_obj.get_session_url = MagicMock(return_value=SESSION_URL)
        session_obj.idrac.invoke_request.return_value.status_code = 201
        session_obj.idrac.invoke_request.return_value.json_data = {"SessionID": "123456"}
        session_obj.idrac.invoke_request.return_value.headers.get.return_value = "token123"
        f_module.exit_json = MagicMock()

        session_obj.execute()
        f_module.exit_json.assert_called_once_with(
            msg=CREATE_SUCCESS_MSG,
            changed=True,
            session_data={"SessionID": "123456"},
            x_auth_token="token123"
        )

    def test_main(self, mocker):
        module_mock = mocker.MagicMock()
        idrac_mock = mocker.MagicMock()

        # Mock the necessary functions and objects
        mocker.patch(MODULE_PATH + 'get_argument_spec', return_value={})
        mocker.patch(MODULE_PATH + 'AnsibleModule', return_value=module_mock)
        mocker.patch(MODULE_PATH + 'SessionAPI', return_value=idrac_mock)
        main()


class TestDeleteSession(FakeAnsibleModule):
    module = idrac_session

    @pytest.fixture
    def idrac_session_mock(self):
        idrac_obj = MagicMock()
        return idrac_obj

    @pytest.fixture
    def idrac_connection_session_mock(self, mocker, idrac_session_mock):
        idrac_conn_mock = mocker.patch(MODULE_PATH + 'SessionAPI',
                                       return_value=idrac_session_mock)
        idrac_conn_mock.return_value.__enter__.return_value = idrac_session_mock
        return idrac_conn_mock

    def test_delete_session_success_check_mode_changes(self, idrac_connection_session_mock):
        f_module = MagicMock()
        delete_session_obj = idrac_session.DeleteSession(idrac_connection_session_mock, f_module)
        delete_session_obj.idrac.invoke_request.return_value.status_code = 200
        delete_session_obj.execute()
        f_module.exit_json.assert_called_once_with(msg=CHANGES_FOUND_MSG, changed=True)

    def test_delete_session_success_check_mode_no_changes(self, idrac_connection_session_mock):
        f_module = MagicMock()
        delete_session_obj = idrac_session.DeleteSession(idrac_connection_session_mock, f_module)
        delete_session_obj.idrac.invoke_request.return_value.status_code = 201
        delete_session_obj.execute()
        f_module.exit_json.assert_called_once_with(msg=NO_CHANGES_FOUND_MSG)

    def test_delete_session_success(self, idrac_connection_session_mock):
        f_module = self.get_module_mock(
            params={"session_id": "1234", "hostname": "X.X.X.X"}, check_mode=False)
        session_obj = idrac_session.DeleteSession(idrac_connection_session_mock, f_module)
        session_obj.get_session_url = MagicMock(return_value=SESSION_URL)
        session_obj.idrac.invoke_request.return_value.status_code = 200

        # Patch the exit_json method of the module
        f_module.exit_json = MagicMock()

        session_obj.execute()
        f_module.exit_json.assert_called_once_with(msg=DELETE_SUCCESS_MSG, changed=True)

    def test_delete_session_check_mode_false_no_changes(self, idrac_connection_session_mock):
        f_module = self.get_module_mock(
            params={"session_id": "1234", "hostname": "X.X.X.X"}, check_mode=False)
        session_obj = idrac_session.DeleteSession(idrac_connection_session_mock, f_module)
        session_obj.get_session_url = MagicMock(return_value=SESSION_URL)
        session_obj.idrac.invoke_request.return_value.status_code = 201

        # Patch the exit_json method of the module
        f_module.exit_json = MagicMock()

        session_obj.execute()
        f_module.exit_json.assert_called_once_with(msg=NO_CHANGES_FOUND_MSG)
