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
import os.path
from livebridge_scribblelive import LiveblogScribbleliveConverter
from livebridge.base import ConversionResult
from tests import load_json

class LiveblogScribbleliveConverterTest(asynctest.TestCase):

    def setUp(self):
        self.converter = LiveblogScribbleliveConverter()

    async def test_simple_conversion(self):
        post = load_json('post_to_convert.json')
        conversion = await self.converter.convert(post)
        assert len(conversion.content) >= 1
        assert conversion.content == """<p><b>Text</b> mit ein parr <i>Formatierungen</i>. Und einem <a href="http://dpa.de">Link</a>. Und weiterer <s>Text</s>.<br></p><div><img src="http://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/aa7c892f1b1b7df17f635106e27c55d86a5c5b6144bebe2490f4ce14be671dd7" /><br>Gähn <i>(Mich)</i></div><p>Listen:<br><br><br> • Eins<br> • Zwei<br> • Drei<br><br><br> • u1<br> • u2<br> • u3<br></p><blockquote>Mit dem Wissen wächst der Zweifel.<br><br> • <i>Johann Wolfgang von Goethe</i></blockquote><p>Nochmal <i><b>abschließender</b></i> Text.</p><div id="_nnc0gyzwv">\n     <blockquote class="twitter-tweet">\n         <p>\nNeue Trendsportart? Der Kick auf dem Brett - Drohnen-Surfen! https://t.co/DjyYgHkYJ3 @dpa-NewsBlog | @noz_de\n         </p>&mdash; \n         dpa·live on Twitter (@dpa_live)\n         <a href="https://twitter.com/dpa_live/status/775991579676909568">https://twitter.com/dpa_live/status/775991579676909568</a>\n     </blockquote>\n</div>"""
        await self.converter.remove_images(conversion.images)

    async def test_simple_conversion_failing(self):
        post = load_json('post_to_convert.json')
        # unknown embed
        post["groups"][1]["refs"] = [{"item": {"item_type" : "testtype"}, "type": "test"}]
        conversion = await self.converter.convert(post)
        assert conversion.content == ""
        assert conversion.images == []

        # let it fail with catched exception
        del post["groups"][1]["refs"]
        conversion = await self.converter.convert(post)
        assert conversion.content == ""
        assert conversion.images == []

    async def test_convert_image(self):
        post = load_json('post_to_convert.json')
        self.converter._download_image = asynctest.CoroutineMock(return_value="/tmp/foobaz")
        img_item = post["groups"][1]["refs"][1]
        content, tmp_path = await self.converter._convert_image(img_item)
        assert tmp_path == "/tmp/foobaz"
        assert content == "<br>Gähn <i>(Mich)</i><br> "
        self.converter._download_image.assert_called_once_with({
            'height': 1080,
            'media': '7966946203766696aed8d067b04972b3a8f695aac885b51675d4117b388c1454',
            'href': 'http://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/7966946203766696aed8d067'+\
                    'b04972b3a8f695aac885b51675d4117b388c1454',
            'width': 1621,
            'mimetype': 'image/jpeg'})

    async def test_convert_image_empty_desc_credit(self):
        post = load_json('post_to_convert.json')
        self.converter._download_image = asynctest.CoroutineMock(return_value="/tmp/foobaz")
        img_item = post["groups"][1]["refs"][1]
        img_item["item"]["meta"]["caption"] = ""
        img_item["item"]["meta"]["credit"] = ""
        content, tmp_path = await self.converter._convert_image(img_item)
        assert content == " "

    async def test_convert_image_failing(self):
        post = load_json('post_to_convert.json')
        self.converter._download_image = asynctest.CoroutineMock(side_effect=Exception)
        img_item = post["groups"][1]["refs"][1]
        content, tmp_path = await self.converter._convert_image(img_item)
        assert tmp_path == None
        assert content == ""

    async def test_convert_image_inline(self):
        post = load_json('post_to_convert.json')
        img_item = post["groups"][1]["refs"][1]
        content, tmp_path = await self.converter._convert_image_inline(img_item)
        assert tmp_path == None
        assert content == '<div><img src="http://newslab-liveblog-demo.s3-eu-central-1.amazonaws.com/aa7c892f1b1b7df17f635106e27c55d86a5c5b6144bebe2490f4ce14be671dd7" /><br>Gähn <i>(Mich)</i></div>'

        img_item["item"]["meta"]["media"]["renditions"]["viewImage"] = {}
        img_item["item"]["meta"]["caption"] = ""
        img_item["item"]["meta"]["credit"] = ""
        content, tmp_path = await self.converter._convert_image_inline(img_item)
        assert tmp_path == None
        assert content == " "

    async def test_convert_image_inline_failing(self):
        content, tmp_path = await self.converter._convert_image_inline({})
        assert tmp_path == None
        assert content == ''

    async def test_embed_text(self):
        item = {"item": {"meta": {
                    "title": "Titel",
                    "description": "Beschreibung",
                    "credit": "Credit",
                }}}
        content = await self.converter._convert_embed(item)
        assert content == "<br><div><strong>Titel</strong></div><p>Beschreibung</p><div><i>Credit</i></div>"

        item = {"item": {"meta": {
                    "title": "Titel",
                    "description": "Beschreibung",
                }}}
        content = await self.converter._convert_embed(item)
        assert content == "<br><div><strong>Titel</strong></div><p>Beschreibung</p>"

        item = {"item": {"meta": {
                    "description": "Beschreibung",
                    "credit": "Credit",
                }}}
        content = await self.converter._convert_embed(item)
        assert content == "<p>Beschreibung</p><div><i>Credit</i></div>"

        item = {"item": {"meta": {
                    "description": "Beschreibung",
                }}}
        content = await self.converter._convert_embed(item)
        assert content == "<p>Beschreibung</p>"

        item = {"item": {"meta": {
                    "credit": "Credit",
                }}}
        content = await self.converter._convert_embed(item)
        assert content == "<div><i>Credit</i></div>"

    async def test_convert_fb_embed(self):
        embed = '<script type="text/javascript" src="https://connect.facebook.net/en_US/all.js#xfbml=1&status=0&appId=">'
        embed += '</script><div id="_8dyj37s33"><div class="fb-post" data-width="350" data-href="https://www.facebook.com/'
        embed += 'DeutschePresseAgenturGmbH/posts/764149090389333"><div class="fb-xfbml-parse-ignore"><a href="https://www'
        embed += '.facebook.com/DeutschePresseAgenturGmbH/posts/764149090389333">Post</a> by <a href="https://www.facebook'
        embed += '.com/DeutschePresseAgenturGmbH">DeutschePresseAgenturGmbH</a>.</div></div></div>'
        embed2 = '<script>  if(window.FB !== undefined) {    window.FB.XFBML.parse(document.getElementById("_8dyj37s33"));  }</script>'
        item = {"item": {
            "meta": {
                "provider_name": "Facebook",
                "html": embed+embed2
            }
        }}
        res = await self.converter._convert_embed(item)
        assert res == embed

    async def test_convert_twitter_embed(self):
        embed = """<div id="_4f1cm9ovf">
     <blockquote class="twitter-tweet">
         <p>
Bundesliga-Relegation live! Nürnberg vs Frankfurt - die Partie jetzt im LiveTicker http://live.fussball.com/fbcom_fb_mbl/html_php/index_fbcom.html#/live-e852618 ... | @fbcompic.twitter.com/via9YxUG2d
         </p>&mdash; 
         dpa·live on Twitter (@dpa_live)
         <a href="https://twitter.com/dpa_live/status/734812416584744960">https://twitter.com/dpa_live/status/734812416584744960</a>
     </blockquote>
</div>"""
        embed2 = """<script>
    window.twttr = (function(d, s, id) {
        var js, fjs = d.getElementsByTagName(s)[0],t = window.twttr || {};
        if (d.getElementById(id)) return t; js = d.createElement(s);js.id = id;
        js.src = "https://platform.twitter.com/widgets.js";
        fjs.parentNode.insertBefore(js, fjs); t._e = [];
        t.ready = function(f) {t._e.push(f);}; return t;}(document, "script", "twitter-wjs"));
    window.twttr.ready(function(){
        window.twttr.widgets.load(document.getElementById("_4f1cm9ovf"));
    });
</script>"""
        item = {"item": {
            "meta": {
                "html": embed+embed2
            }
        }}
        content = await self.converter._convert_embed(item)
        assert content == embed

    async def test_convert_youtube(self):
        embed = '<iframe width="560" height="315" src="https://www.youtube.com/embed/86jugQW9Y9Y" '
        embed += 'frameborder="0" allowfullscreen></iframe>'
        item = {"item": {"meta": {"html": embed}}}
        res = await self.converter._convert_embed(item)
        assert res == embed

    async def test_convert_youtube_embedly(self):
        embed = '<iframe class="embedly-embed" src="//cdn.embedly.com/widgets/media.html?src=https%3A%'
        embed += '2F%2Fwww.youtube.com%2Fembed%2FxiE5AQHKj_Y%3Ffeature%3Doembed%26rel%3D0&url=http%3A%2F%2'
        embed += 'Fwww.youtube.com%2Fwatch%3Fv%3DxiE5AQHKj_Y&image=https%3A%2F%2Fi.ytimg.com%2Fvi%2FxiE5AQH'
        embed += 'Kj_Y%2Fhqdefault.jpg&key=979cf63d19e24e8cbcfcc7c5063867e2&type=text%2Fhtml&schema=youtube"'
        embed += ' width="350" height="263" scrolling="no" frameborder="0" allowfullscreen></iframe>'
        item = {"item": {"meta": {"html": embed}}}
        res = await self.converter._convert_embed(item)
        assert res == embed

    #@asynctest.skip("Skipped.")
    async def test_convert_instagram(self):
        embed = '<blockquote class="instagram-media" data-instgrm-captioned data-instgrm-version="7" style="width:100%;"> <div style="">'
        embed += '</div></div> <p style=" margin:8px 0 0 0; padding:0 4px;"> <a href="https://www.instagram.com/p/BE5F7Jgxwe4/" style="'
        embed += 'word-wrap:break-word;" target="_blank">This little &#34;beach&#34; at Brooklyn Bridge park offers gorgeous views, or '
        embed += 'for this little tyke, a place to practice riding a bike. Reported by @travelogged, your #BBCLocalite for #NYC</a></p>'
        embed += ' <p style="white-space:nowrap;">Ein von BBC Travel (@bbc_travel) gepostetes Foto am <time style="line-height:17px;" '
        embed += 'datetime="2016-05-02T04:50:18+00:00">1. Mai 2016 um 21:50 Uhr</time></p></div></blockquote>'
        embed2 = '<script async defer src="//platform.instagram.com/en_US/embeds.js"></script>'
        item = {"item": {
            "meta": {
                "html": embed+embed2
            }
        }}
        content = await self.converter._convert_embed(item)
        assert content == embed


    @asynctest.skip("Skipped.")
    async def test_convert_meta_html(self):
        item = {"item": {"meta": {"html": "<div>foo</div>"}}}
        res = await self.converter._convert_embed(item)
        assert res == "<div>foo</div>"

    @asynctest.skip("Skipped.")
    async def test_convert_embed_text(self):
        item = {"item": {"text": "Foobaz\nFoo", "meta": {}}}
        res = await self.converter._convert_embed(item)
        assert res == "Foobaz\nFoo"

    async def test_convert_quote(self):
        item = {"item": {"meta": {"quote": "Zitat", "credit": "Urheber"}}}
        res = await self.converter._convert_quote(item)
        assert res == "<blockquote>Zitat<br><br> • <i>Urheber</i></blockquote>"

    async def test_convert_quote_without_credit(self):
        item = {"item": {"meta": {"quote": "Zitat"}}}
        res = await self.converter._convert_quote(item)
        assert res == "<blockquote>Zitat<br></blockquote>"

    async def test_convert_text(self):
        text = """
            <p><ul><li>eins</li><li>zwei</li></ul>
            <ol><li>drei</li><li>vier</li></ol><p><br></p>
            <strike>STRIKE</strike>
            <div><b>bold</b><i>italic</i></div></p>
        """
        res = await self.converter._convert_text({"item":{"text": text}})
        assert res == """<p><br> • eins<br> • zwei<br>
            <br> • drei<br> • vier<br>
            <s>STRIKE</s>
            <div><b>bold</b><i>italic</i></div></p>"""
