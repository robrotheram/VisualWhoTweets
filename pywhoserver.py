#!/usr/bin/env python
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
# under the License.from __future__ import division

from __future__ import division
import json
import os
from collections import defaultdict


import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import twitter
from tornado import web

from tornado.options import define, options
define("port", default=8888, help="run on the given port", type=int)
public_root = os.path.join(os.path.dirname(__file__), 'static')

class MainHandler(tornado.web.RequestHandler):
    def get(self):
        self.render('static/index.html')

class POSTHandler(tornado.web.RequestHandler):
    TWEET_COUNT = 200
    BAR_SIZE = 50

    def build_api(self, consumer_key, consumer_secret, access_token, access_token_secret):
        return twitter.Api(consumer_key=consumer_key,
                           consumer_secret=consumer_secret,
                           access_token_key=access_token,
                           access_token_secret=access_token_secret)

    def fetch_tweets(self, twitter_api, start=None):
        return twitter_api.GetHomeTimeline(count=self.TWEET_COUNT, max_id=start)


    def post(self):
        data = json.loads(self.request.body)
        api = self.build_api(data['consumer_key'], data['consumer_secret'], data['access_token'], data['access_token_secret'])
        try:
            new_tweets = self.fetch_tweets(api)
        except:
            new_tweets = None
        tweets = new_tweets
        i = 0
        if new_tweets is not None :
            while new_tweets and i < 5:
                oldest_tweet_id = new_tweets[-1].id
                try:
                    new_tweets = self.fetch_tweets(api, oldest_tweet_id)
                except:
                    pass
                tweets += new_tweets
                i = i + 1

            print(len(tweets))
            authors = defaultdict(int)
            for tweet in tweets:
                authors[tweet.user.screen_name] += 1
            sorted_authors = sorted(authors.items(), key=lambda x: x[1], reverse=True)
            max_count = sorted_authors[0][1]
            # scale = BAR_SIZE * 1.0 / max_count

            dict = []
            for author in sorted_authors:
                dict.append({
                    "name":'@{}'.format(author[0]),
                    "author_tweets":author[1],
                    "author_bar_size": int(round((author[1] / max_count) * self.BAR_SIZE))

                })
            self.write(json.dumps(dict))
        else:
            self.write(json.dumps({"error": "API Keys are wrong or rate Limit Exceeded try again later "}))

def main():
    tornado.options.parse_command_line()
    application = tornado.web.Application([

        (r'/', MainHandler),
        (r"/twitter", POSTHandler),
        (r'/(.*)', web.StaticFileHandler, {'path': public_root}),

    ])
    http_server = tornado.httpserver.HTTPServer(application)
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    main()
