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
import logging
from livebridge.base import BaseTarget, TargetResponse
from livebridge_scribblelive.common import ScribbleLiveClient, ScribbleLiveException


logger = logging.getLogger(__name__)


class ScribbleLiveTarget(ScribbleLiveClient, BaseTarget):

    type = "scribble"

    def get_id_at_target(self, post):
        """Extracts from the given **post** the id of the target resource.
        
        :param post: post  being processed
        :type post: livebridge.posts.base.BasePost
        :returns: string"""  
        id_at_target = None
        if post.target_doc:
            id_at_target = post.target_doc.get("Id")
        else:
            logger.warning("No id at target found.")
        return id_at_target

    async def post_item(self, post):
        await self._check_login()
        post_url = "{}/event/{}?".format(self.endpoint, self.event_id)
        return TargetResponse(await self._post(post_url, post.images, post.content))

    async def update_item(self, post):
        id_at_target = self.get_id_at_target(post)
        if not id_at_target:
            logger.warning("Handling updated item without TARGET-ID: [{}] on {}".format(post.id, self.target_id))
            return False
        await self._check_login()
        update_url = "{}/post/{}?".format(self.endpoint_v1, self.get_id_at_target(post))
        return TargetResponse(await self._put(update_url, post.content, post.images))

    async def delete_item(self, post):
        id_at_target = self.get_id_at_target(post)
        if not id_at_target:
            logger.warning("Handling deleted item without TARGET-ID: [{}] on {}".format(post.id, self.target_id))
            return False
        await self._check_login()
        delete_url = "{}/post/{}/delete?".format(self.endpoint, id_at_target)
        return TargetResponse(await self._get(delete_url))

    async def handle_extras(self, post):
        if self.get_id_at_target(post) and not post.is_deleted:
            return TargetResponse(await self._handle_sticky(post))
        return None

    async def _handle_sticky(self, post):
        res = None
        id_at_target = self.get_id_at_target(post)
        try:
            old_sticky = bool(int("0" if not post.is_known else post.get_existing().get("sticky")))
            logger.debug("HANDLING STICKY new: {} old:{}".format(post.is_sticky, old_sticky))
            if old_sticky == False and post.is_sticky:
                res = await self._stick_item(id_at_target)
            elif old_sticky == True and not post.is_sticky:
                res = await self._unstick_item(id_at_target)
        except Exception as e:
            logger.error("Error when sticking/unsticking {} {}".format(id_at_target, post.is_sticky))
            logger.exception(e)
        return res

    async def _stick_item(self, post_id):
        await self._check_login()
        stick_url = "{}/post/{}/stick?".format(self.endpoint, post_id)
        return await self._get(stick_url)

    async def _unstick_item(self, post_id):
        await self._check_login()
        unstick_url = "{}/post/{}/unstick?".format(self.endpoint, post_id)
        return await self._get(unstick_url)
