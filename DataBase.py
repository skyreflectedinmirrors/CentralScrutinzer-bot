# DataBase.py -- contains wrapper for a SQL database

import sqlite3
import logging
import datetime
import re


class DataBaseWrapper(object):
    def __init__(self, databasefile, create_on_enter=True):
        self.databasefile = databasefile
        self.create_on_enter = create_on_enter

    """A wrapper to the SQL Database, designed be used in conjunction with a 'with'"""

    def __enter__(self):
        class DataBase:
            """
            :type db: sqlite3.Connection
            :type cursor: sqlite3.Cursor
            """

            def __init__(self, databasefile, create_on_enter):
                # open the database and create cursor
                try:
                    self.db = sqlite3.connect(databasefile)
                    self.cursor = self.db.cursor()
                    if create_on_enter:
                        self.__create_table()
                    self.db.create_function("regexp", 2, self.regexp)
                except sqlite3.Error, e:
                    logging.debug(str(e))
                    logging.critical("Cannot open database file " + databasefile)
                    raise e

            def __create_table(self):
                """Creates the post table if it does not exist already"""
                try:
                    self.cursor.execute('''create table if not exists channel_record
                    (channel_id text primary key,
                    domain text,
                    channel_url text,
                    blacklist integer,
                    strike_count integer default 0,
                    unique (channel_id, domain))''')
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.debug(str(e))
                    logging.critical("Could not create table channel_record")
                    return False

                try:
                    self.cursor.execute('''create table if not exists reddit_record
                    (short_url text primary key unique,
                    channel_id text,
                    domain text,
                    date_added timestamp)''')
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.debug(str(e))
                    logging.critical("Could not create table reddit_record")
                    return False
                return True

            def add_channels(self, channel_entries):
                """Adds channels to the channel_record

                :param channel_entries: a list of tuples consisting of (channel_id, domain, channel_url, blacklist, strike_count)
                """
                try:
                    self.cursor.executemany('''insert into channel_record values (?,?,?,?,?)''', channel_entries)
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.error("Could not add channels to database")
                    logging.debug(str(e))

            def add_reddit(self, reddit_entries):
                """adds the supplied reddit entries to the reddit_record

                :param reddit_entries: a list of tuples consisting of (short_url, channel_id, domain, date_added)
                :return:
                """
                try:
                    self.cursor.executemany('''insert into reddit_record values (?,?,?,?)''', reddit_entries)
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.error("Could not add reddit entries to database")
                    logging.debug(str(e))

            def regexp(self, expr, item):
                reg = re.compile(expr)
                return reg.search(item) is not None

            def channel_exists(self, channel_list):
                """checks whether the specified channels exist

                :param channel_list: a list of tuples of the form (channel_id, domain)
                :return: a list of booleans indicating whether the channel exists or not
                """

                try:
                    return [self.cursor.execute("""select channel_id from channel_record where channel_id = ?
                            and domain = ?""", channel).fetchone() is not None for channel in channel_list]
                except sqlite3.Error, e:
                    logging.error("Error on channel exists check")
                    logging.debug(str(e))

            def get_channels(self, blacklist, domain=None, strike_count=None, id_filter=None):
                """returns the channels matching the supplied query

                :param blacklist: the black/whitelist to match, not optional
                :param domain: the domain to match, can be None
                :param strike_count: the (optional strike count to match)
                :param id_filter: optional regex filter
                :return:
                """
                arglist = [blacklist]
                query = "select channel_id, channel_url from channel_record where blacklist = ?"
                if domain:
                    query += " and domain = ?"
                    arglist.append(domain)
                if strike_count:
                    query += " and strike_count = ?"
                    arglist.append(strike_count)
                if id_filter:
                    query += " and channel_id regexp ?"
                    arglist.append(id_filter)
                try:
                    self.cursor.execute(query, tuple(arglist))
                    return self.cursor.fetchall()
                except sqlite3.Error, e:
                    logging.error("Error on get_channels fetch.")
                    logging.debug("domain, blacklist, id_filter:" + str(domain) + ", " + str(blacklist) + ", " + str(id_filter))




        self.db = DataBase(self.databasefile, self.create_on_enter)
        return self.db

    def __exit__(self, exc_type, exc_val, exc_tb):
        """ Closes the database and commits any changes"""
        try:
            self.db.db.commit()
            self.db.db.close()
        except Exception, e:
            logging.critical("Error on database close/commit")
            logging.debug(str(e))