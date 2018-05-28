#!/usr/bin/env python
# -*- coding: utf-8 -*-

from catenae import Link, Electron, util
from pymongo import MongoClient
from conf import conf_loader as conf
import time
import datetime


class Stats(Link):

    def setup(self):
        self.mongo_client = MongoClient(conf.mongo['address'], conf.mongo['port'])
        self.db = self.mongo_client.reddit_early_risk
        self.stats = self.db.stats

        self.users_counter = set()
        self.texts_counter = 0

        # Ensure stats index
        self.stats.create_index('timestamp', unique=True, background=True)

    def transform(self, electron):
        try:
            if electron.previous_topic == 'processed_texts':
                self.texts_counter += 1
            elif electron.previous_topic == 'processed_users':
                self.users_counter.add(electron.key)

            values = {}
            values['texts_second'] = self.texts_counter
            values['users_second'] = len(self.users_counter)

            self.stats.update_one(
                { 'group': 'real_time' },
                { '$set': values },
                upsert=True)
        except Exception as e:
            print(e)

if __name__ == "__main__":
    Stats().start(link_mode=Link.MULTIPLE_KAFKA_INPUTS_CUSTOM_OUPUT, mki_mode='parity')
