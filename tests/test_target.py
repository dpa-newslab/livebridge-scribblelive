# -*- coding: utf-8 -*-
#
# Copyright 2016 dpa-infocom GmbH
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import asynctest
import aiohttp
import time
from livebridge.base import BaseTarget, BasePost, TargetResponse
from livebridge_scribblelive import ScribbleLiveTarget
from livebridge_scribblelive.common import ScribbleLiveClient, ScribbleLiveException
from tests import load_json


class TestResponse:

    def __init__(self, url, data={}, status=200):
        self.status = status
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        pass

    async def json(self):
        return self.data

    async def text(self):
        return repr(self.data)


class TestPost(BasePost):
    pass


class ScribbleLiveTargetTests(asynctest.TestCase):

    def setUp(self):
        self.api_key = "baz"
        self.user = "foo"
        self.password = "bla"
        self.event_id = 12345
        self.endpoint= "https://example.com/api"
        self.endpoint_v1= "https://example2.com/api"
        self.client= ScribbleLiveTarget(config={
                        "auth": {"api_key": self.api_key, "user": self.user, "password": self.password},
                        "event_id": self.event_id, "endpoint": self.endpoint, "endpoint_v1": self.endpoint_v1})

    @asynctest.ignore_loop
    def test_init(self):
        assert self.client.type == "scribble"
        assert self.client.api_key == self.api_key
        assert self.client.user == self.user
        assert self.client.password == self.password
        assert self.client.event_id == self.event_id
        assert self.client.endpoint == self.endpoint
        assert self.client.endpoint_v1 == self.endpoint_v1
        assert issubclass(ScribbleLiveTarget, BaseTarget) == True
        assert issubclass(ScribbleLiveTarget, ScribbleLiveClient) == True
        assert isinstance(self.client, BaseTarget) == True

    @asynctest.ignore_loop
    def test_url_params(self):
        url = self.client._add_url_params("http://test.com/foo?")
        assert url == "http://test.com/foo?Token=baz&format=json"

        url = self.client._add_url_params("http://test.com/foo?baz=bla")
        assert url == "http://test.com/foo?baz=bla&Token=baz&format=json"

        self.client.auth_token = "foo"
        url = self.client._add_url_params("http://test.com/foo?baz=bla")
        assert url == "http://test.com/foo?baz=bla&Token=baz&format=json&Auth=foo"

    @asynctest.ignore_loop
    def test_get_id_target(self):
        post_data = load_json('post_to_convert.json')

        post = TestPost(post_data)
        post.target_doc = {"Id": 456}
        assert self.client.get_id_at_target(post) == 456
        
        post.target_doc = {}
        assert self.client.get_id_at_target(post) == None

    async def test_login_ok(self):
        api_res = {
            'Name': 'Martin Borho',
            'Id': 53620032,
            'Avatar': '',
            'Auth': 'YjJmNGpqajBFS05KOGdZQU5kSTFLaHlqR1A0UzlRZm10Z0I3bThXdTl6SmVLNm5PVkl5VTVMQmhhSjZXY0M2NA'
        }
        self.client._get =  asynctest.CoroutineMock(return_value=api_res)
        res = await self.client._login()
        assert res == api_res["Auth"]
        assert self.client._get.call_args_list[0][0][0] == 'https://example.com/api/user?'
        assert type(self.client._get.call_args_list[0][1]["auth"]) == aiohttp.BasicAuth

    async def test_login_not_ok(self):
        self.client._get =  asynctest.CoroutineMock(return_value={})
        res = await self.client._login()
        assert res == False

    async def test_check_login(self):
        self.client.auth_token = "authed_1"
        self.client.auth_time = time.time()
        self.client._login = asynctest.CoroutineMock(return_value="authed_2")
        res = await self.client._check_login()
        assert res == "authed_1"
        assert self.client._login.call_count == 0

        self.client.auth_time = time.time()-3610
        self.client._login =  asynctest.CoroutineMock(return_value="authed_2")
        res = await self.client._check_login()
        assert res == "authed_2"
        assert self.client._login.call_count == 1

    async def test_post_item(self):
        api_res = {'Id': 252657529, 'IsStuck': 0, 'PostMeta': {'CreationDate': '1460467186'},
                   'EventId': 220029, 'LastModified': '/Date(1460467186700+0000)/',
                   'Created': '/Date(1460467186700+0000)/',
                   'Creator': {'Id': 53620032, 'Name': 'Martin Borho', 'Avatar': ''},
                    'IsComment': 0, 'Content': 'Test, mit Ü.', 'Type': 'TEXT', 'IsApproved': 1,
                    'Source': '', 'IsDeleted': 0}
        self.client._post =  asynctest.CoroutineMock(return_value=api_res)
        self.client.auth_time = time.time()-10
        self.client.auth_token = "foobaz"

        post = asynctest.MagicMock()
        post.images = []
        post.content = "Test, mit Ü."
        resp = await self.client.post_item(post)
        assert type(resp) == TargetResponse
        assert resp == api_res
        self.client._post.assert_called_once_with('https://example.com/api/event/12345?', [], u'Test, mit Ü.')

    async def test_update_item(self):
        api_res = {'IsComment': 0, 'Source': '',
                   'Creator': {'Id': 53620032, 'Avatar': '', 'Name': 'Martin Borho'},
                   'Created': '/Date(1460471421403+0000)/', 'EventId': 220029, 'IsApproved': 1,
                   'IsDeleted': 0, 'PostMeta': {'ShowEditedBy': 'true', 'CreationDate': '1460471421'},
                   'Content': 'Test, mit Äh.', 'LastModified': '/Date(1460471759447+0000)/',
                    'IsStuck': 0, 'Id': 252686461, 'Type': 'TEXT'}
        self.client._put =  asynctest.CoroutineMock(return_value=api_res)
        self.client.auth_time = time.time()-10
        self.client.auth_token = "foobaz"

        post = asynctest.MagicMock()
        post.target_doc = {"Id": "252686461"}
        post.images = []
        post.content = "Test, mit Äh."
        resp = await self.client.update_item(post)
        assert type(resp) == TargetResponse
        assert resp == api_res
        self.client._put.assert_called_once_with('https://example2.com/api/post/252686461?', u'Test, mit Äh.', [])

    async def test_update_item_failing(self):
        post = asynctest.MagicMock()
        self.client.get_id_at_target = lambda x: None
        self.client._check_login = asynctest.CoroutineMock(return_value=None)
        res = await self.client.update_item(post)
        assert res == False
        assert self.client._check_login.call_count == 0

    async def test_handle_extras(self):
        post = asynctest.MagicMock()
        post.target_doc = {"Id": "12345"}
        post.is_deleted = False
        self.client._handle_sticky = asynctest.CoroutineMock(side_effect=Exception)
        # throws Exception when handle_sticky is called, which is right
        with self.assertRaises(Exception):
            await self.client.handle_extras(post)
        self.client._handle_sticky.assert_called_once_with(post)

    async def test_handle_none_extras(self):
        post = asynctest.MagicMock()
        post.target_doc = None
        assert None == await self.client.handle_extras(post)

    async def test_handle_sticky_failing(self):
        post = asynctest.MagicMock()
        post.is_known = False
        post.target_doc = {"Id": "12345"}
        post.is_sticky = True
        post.get_existing = lambda: {"sticky": "0"}
        self.client._stick_item = asynctest.CoroutineMock(side_effect=Exception)
        res = await self.client._handle_sticky(post)
        assert res == None
        self.client._stick_item.assert_called_once_with('12345')

    async def test_handle_stick_item(self):
        post = asynctest.MagicMock()
        post.is_known = False
        post.target_doc = {"Id": "12345"}
        post.is_sticky = True
        post.get_existing = lambda: {"sticky": "0"}
        self.client._stick_item = asynctest.CoroutineMock(return_value={"foo":"baz"})
        self.client._unstick_item = asynctest.CoroutineMock(side_effect=Exception)
        res = await self.client._handle_sticky(post)
        assert res == {"foo":"baz"}
        self.client._stick_item.assert_called_once_with("12345")
        assert self.client._unstick_item.call_count == 0

        post.is_sticky = False
        res = await self.client._handle_sticky(post)
        assert res == None
        self.client._stick_item.assert_called_once_with("12345")
        assert self.client._unstick_item.call_count == 0

    async def test_handle_unstick_item(self):
        post = asynctest.MagicMock()
        post.is_known = True
        post.target_doc = {"Id": "12345"}
        post.is_sticky = False
        post.get_existing = lambda: {"sticky": "1"}
        self.client._unstick_item = asynctest.CoroutineMock(return_value={"foo":"baz"})
        self.client._stick_item = asynctest.CoroutineMock(side_effect=Exception)
        res = await self.client._handle_sticky(post)
        assert res == {"foo":"baz"}
        self.client._unstick_item.assert_called_once_with("12345")
        assert self.client._stick_item.call_count == 0

        post.get_existing = lambda: {"sticky": "0"}
        res = await self.client._handle_sticky(post)
        assert res == None

    async def test_stick_post(self):
        api_res = {'IsComment': 0, 'Source': '',
                   'Creator': {'Id': 53620032, 'Avatar': '', 'Name': 'Martin Borho'},
                   'Created': '/Date(1460471421403+0000)/', 'EventId': 220029, 'IsApproved': 1,
                   'IsDeleted': 0, 'PostMeta': {'ShowEditedBy': 'true', 'CreationDate': '1460471421'},
                   'Content': 'Test, mit Äh.', 'LastModified': '/Date(1460471759447+0000)/',
                    'IsStuck': 1, 'Id': 252686461, 'Type': 'TEXT'}
        self.client._get =  asynctest.CoroutineMock(return_value=api_res)

        post_id = 252686461
        resp = await self.client._stick_item(post_id)
        assert resp["Id"] == post_id
        assert resp["IsStuck"] == 1
        assert self.client._get.call_count == 2
        self.client._get.assert_called_with('https://example.com/api/post/252686461/stick?')

    async def test_unstick_post(self):
        api_res = {'IsComment': 0, 'Source': '',
                   'Creator': {'Id': 53620032, 'Avatar': '', 'Name': 'Martin Borho'},
                   'Created': '/Date(1460471421403+0000)/', 'EventId': 220029, 'IsApproved': 1,
                   'IsDeleted': 0, 'PostMeta': {'ShowEditedBy': 'true', 'CreationDate': '1460471421'},
                   'Content': 'Test, mit Äh.', 'LastModified': '/Date(1460471759447+0000)/',
                    'IsStuck': 0, 'Id': 252686461, 'Type': 'TEXT'}
        self.client._get =  asynctest.CoroutineMock(return_value=api_res)

        post_id = 252686461
        resp = await self.client._unstick_item(post_id)
        assert resp["Id"] == post_id
        assert resp["IsStuck"] == 0
        assert self.client._get.call_count == 2
        self.client._get.assert_called_with('https://example.com/api/post/252686461/unstick?')

    async def test_delete_item(self):
        api_res = {'IsStuck': 0, 'Content': 'Test, mit Äh.', 'IsComment': 0, 'EventId': 220029,
                   'Type': 'TEXT', 'IsApproved': 1, 'LastModified': '/Date(1460472667143+0000)/',
                   'Source': '', 'Id': 252686461, 'IsDeleted': 1,
                   'Editor': {'Avatar': '', 'Id': 53620032, 'Name': 'Martin Borho'},
                   'Creator': {'Avatar': '', 'Id': 53620032, 'Name': 'Martin Borho'},
                   'Created': '/Date(1460471421403+0000)/',
                    'PostMeta': {'ShowEditedBy': 'true', 'CreationDate': '1460471421'}}
        self.client._get =  asynctest.CoroutineMock(return_value=api_res)

        post = asynctest.MagicMock()
        post.id = 252686461
        post.target_doc = api_res
        resp = await self.client.delete_item(post)
        assert type(resp) == TargetResponse
        assert resp["Id"] == post.id
        assert resp["IsDeleted"] == 1
        assert self.client._get.call_count == 2
        self.client._get.assert_called_with('https://example.com/api/post/252686461/delete?')

    async def test_delete_item_failing(self):
        post = asynctest.MagicMock()
        self.client.get_id_at_target = lambda x: None
        self.client._check_login = asynctest.CoroutineMock(return_value=None)
        res = await self.client.delete_item(post)
        assert res == False
        assert self.client._check_login.call_count == 0

    async def test_common_put(self):
        data = {"foo": "bla"}
        with asynctest.patch("aiohttp.client.ClientSession.put") as patched:
            patched.return_value = TestResponse(url="http://foo.com", data=data)
            res = await self.client._put("https://dpa.com/resource", data, 201)
            assert type(res) == dict
            assert res == data

            # failing
            with self.assertRaises(ScribbleLiveException):
                await self.client._put("https://dpa.com/resource", data, status=404)

    async def test_common_post(self):
        images = ["tests/test.jpg"]
        content = "<b>Test</b>"
        with asynctest.patch("aiohttp.client.ClientSession.post") as patched:
            patched.return_value = TestResponse(url="http://foo.com",status=201,  data={"content": "data"})
            # with image
            res = await self.client._post("https://dpa.com/resource", images=images, status=201)
            assert type(res) == dict
            assert res == {"content": "data"}
            # with content
            res = await self.client._post("https://dpa.com/resource", content=content, status=201)
            assert type(res) == dict
            assert res == {"content": "data"}

            # failing
            with self.assertRaises(ScribbleLiveException):
                await self.client._post("https://dpa.com/resource", images=images, content=content, status=404)

    async def test_common_get(self):
        data = {"foo": "bla"}
        with asynctest.patch("aiohttp.client.ClientSession.get") as patched:
            patched.return_value = TestResponse(url="http://foo.com", data=data)
            res = await self.client._get("https://dpa.com/resource")#, data, 201)
            assert type(res) == dict
            assert res == data

            # failing
            with self.assertRaises(ScribbleLiveException):
                await self.client._get("https://dpa.com/resource", status=404)
