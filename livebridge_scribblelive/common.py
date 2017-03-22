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
import aiohttp
import asyncio
import json
import time
import logging
from os.path import join as path_join
from urllib.parse import urlencode, urljoin

logger = logging.getLogger(__name__)

class ScribbleLiveException(Exception):
    pass

class ScribbleLiveClient(object):

    type = "scribble"

    def __init__(self, *, config={}, **kwargs):
        self.auth_token = None
        self.auth_time = None

        # config data
        auth_creds = config.get("auth", {})
        self.api_key = auth_creds.get("api_key")
        self.user = auth_creds.get("user")
        self.password = auth_creds.get("password")
        self.event_id = config.get("event_id")
        self.endpoint =  config.get("endpoint", "https://apiv1.scribblelive.com")
        self.endpoint_v1 = config.get("endpoint_v1", "https://api.scribblelive.com/v1")
        self.target_id = "{}-{}-{}".format(self.type, self.user, self.event_id)

    async def _login(self):
        # reset login data
        self.auth_token = None
        self.auth_time = None
        auth = aiohttp.BasicAuth(self.user, password=self.password, encoding="UTF-8")
        login_url = "{}/user?".format(self.endpoint)
        resp = await self._get(login_url, auth=auth)
        if resp.get("Auth"):
            self.auth_token = resp["Auth"]
            self.auth_time = time.time()
            logger.debug("Login successfull for {}/{}".format(self.user, self.event_id))
            return self.auth_token
        return False

    async def _check_login(self):
        diff = (time.time()-self.auth_time) if self.auth_token else 0
        if self.auth_token and diff < 3600:
            return self.auth_token
        return await self._login()

    def _add_url_params(self, url):
        params = [
            ("Token", self.api_key),
            ("format", "json")
        ]
        if self.auth_token:
            params.append(("Auth", self.auth_token))
        return url+("" if url[-1] == "?" else "&")+urlencode(params)

    async def _get(self, url, *, auth=None, status=200):
        url = self._add_url_params(url)
        with aiohttp.ClientSession(auth=auth) as session:
            async with session.get(url) as resp:
                if resp.status == status:
                    return await resp.json()
                else:
                    logger.error(await resp.text())
                    raise ScribbleLiveException("Scribblelive GET request [{}] failed with status {}".format(url, resp.status))

    async def _post(self, url, images=[], content="", *, auth=None, status=200):
        url = self._add_url_params(url)
        data = {}
        if images:
            data = aiohttp.FormData()
            data.add_field("file",
                open(images[0], "rb"),
                content_type='multipart/form-data')
            data.add_field("content", content)
        elif content:
            data["content"] = content
        with aiohttp.ClientSession(auth=auth) as session:
            async with session.post(url, data=data) as resp:
                if resp.status == status:
                    return await resp.json()
                else:
                    logger.error(await resp.text())
                    raise ScribbleLiveException("Scribblelive POST request [{}] failed with status {}".format(url, resp.status))

    async def _put(self, url, content="", images=[], *, auth=None, status=200):
        url = self._add_url_params(url)
        data = json.dumps({"ThreadId": int(self.event_id), "Content": content})
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        with aiohttp.ClientSession(auth=auth, headers=headers) as session:
            async with session.put(url, data=data) as resp:
                if resp.status == status:
                    return await resp.json()
                else:
                    logger.error(await resp.text())
                    raise ScribbleLiveException("Scribblelive PUT request [{}] failed with status {}".format(url, resp.status))
