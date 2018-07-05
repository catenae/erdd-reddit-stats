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
        self.current_minute = Stats._get_current_minute()
        self.start_timestamp = Stats._get_current_timestamp()
        self.messages_left = 5

        # Ensure stats index
        self.stats.create_index('timestamp', unique=True, background=True)

    @staticmethod
    def _get_current_timestamp():
        return int(round(time.time()))

    @staticmethod
    def _get_current_minute():
        return datetime.datetime.fromtimestamp(Stats._get_current_timestamp()).strftime('%M')

    def transform(self, electron):
        current_timestamp = Stats._get_current_timestamp()

        if Stats._get_current_minute() > self.current_minute:
            # Reset counters
            self.users_counter = set()
            self.texts_counter = 0
            self.start_timestamp = current_timestamp

        self.current_minute = Stats._get_current_minute()

        if electron.previous_topic == 'processed_texts':
            self.texts_counter += 1
        elif electron.previous_topic == 'processed_users':
            self.users_counter.add(electron.key)

        # Update values
        seconds = current_timestamp - self.start_timestamp
        if seconds > 5 and self.messages_left == 0: # Avoid division by 0 and wait a bit
            self.messages_left = 5
            values = {}
            if self.texts_counter > 0:
                values['texts_second'] = self.texts_counter / seconds * 1.
            if len(self.users_counter) > 0:
                values['users_second'] = len(self.users_counter) / seconds * 1.
            self.stats.update_one(
                { 'group': 'real_time' },
                { '$set': values },
                upsert=True)
        elif seconds > 5:
            self.messages_left -= 1

if __name__ == "__main__":
    Stats().start(link_mode=Link.MULTIPLE_KAFKA_INPUTS_CUSTOM_OUPUT, mki_mode='parity')
