# DataBase.py -- contains wrapper for a SQL database

import sqlite3
import logging
import datetime
import re
import Blacklist


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
                    self.db.create_function("domain_eq", 2, self.domain_eq)
                except sqlite3.Error, e:
                    logging.debug(str(e))
                    logging.critical("Cannot open database file " + databasefile)
                    raise e

            def __create_table(self):
                """Creates the post table if it does not exist already"""
                try:
                    self.cursor.execute('''create table if not exists channel_record
                    (channel_id text,
                    domain text,
                    channel_url text,
                    blacklist integer default 0,
                    strike_count integer default 0,
                    primary key(channel_id, domain))''')
                    try:
                        self.cursor.execute('create index blist on channel_record(blacklist)')
                    except sqlite3.OperationalError, e:
                        if str(e) == "index blist already exists":
                            pass
                        else:
                            logging.critical("Could not create index blist on table channel_record")
                            logging.debug(str(e))
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.critical("Could not create table channel_record")
                    logging.debug(str(e))
                    return False

                try:
                    self.cursor.execute('''create table if not exists reddit_record
                    (short_url text primary key,
                    channel_id text,
                    domain text,
                    date_added timestamp)''')
                    try:
                        self.cursor.execute('create index channel on reddit_record(channel_id, domain)')
                    except sqlite3.OperationalError, e:
                        if str(e) == "index channel already exists":
                            pass
                        else:
                            logging.critical("Could not create index channel on table reddit_record")
                            logging.debug(str(e))
                    try:
                        self.cursor.execute('create index mydate on reddit_record(date_added)')
                    except sqlite3.OperationalError, e:
                        if str(e) == "index mydate already exists":
                            pass
                        else:
                            logging.critical("Could not create index mydate on table reddit_record")
                            logging.debug(str(e))

                    self.db.commit()
                except sqlite3.Error, e:
                    logging.debug(str(e))
                    logging.critical("Could not create table reddit_record")
                    return False
                return True

            def newest_reddit_entries(self, limit=1):
                try:
                    return self.cursor.execute("select short_url from reddit_record order by date_added desc limit ?", (limit,))
                except Exception, e:
                    logging.error("Could not select newest reddit entries")
                    logging.debug(str(e))

            def check_channel_empty(self):
                """Checks wheter the reddit_record is empty or not"""
                try:
                    self.cursor.execute("select count(*) from channel_record")
                    list = self.cursor.fetchone()
                    return list is None
                except Exception, e:
                    logging.error("Could not check if channel_record was empty")
                    logging.debug(str(e))

            def check_reddit_empty(self):
                """Checks wheter the reddit_record is empty or not"""
                try:
                    self.cursor.execute("select count(*) from reddit_record")
                    list = self.cursor.fetchone()
                    return list is None
                except Exception, e:
                    logging.error("Could not check if reddit_record was empty")
                    logging.debug(str(e))

            def regexp(self, expr, item):
                reg = re.compile(expr)
                return reg.search(item) is not None

            def domain_eq(self, domain, item):
                return domain == item or domain.startswith(item)

            def add_reddit(self, reddit_entries):
                """adds the supplied reddit entries to the reddit_record

                :param reddit_entries: a list of tuples consisting of (short_url, channel_id, domain, date_added)
                :return:
                """
                try:
                    if not isinstance(reddit_entries, list):
                        reddit_entries = list(reddit_entries)
                    reddit_entries = [(e,) if not isinstance(e, tuple) else e for e in reddit_entries]
                    self.cursor.executemany('''insert into reddit_record values (?,?,?,?)''', reddit_entries)
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.error("Could not add reddit entries to database")
                    logging.debug(str(e))

            def get_reddit(self, channel_id=None, domain=None, date_added=None, return_channel_id=True, return_domain=True, return_dateadded=False):
                """returns a list of reddit entries matching the provided search modifiers (i.e. channel_id, domain, date_added)

                :returns: a list of tuples of the form (short_url, channel_id*, domain*, date_added* (*if specified))
                """
                query = 'select short_url'
                arglist = []
                if return_channel_id:
                    query += ', channel_id'
                if return_domain:
                    query += ', domain'
                if return_dateadded:
                    query += ', date_added'
                query += ' from reddit_record where '
                if channel_id:
                    query += 'channel_id = ?'
                    arglist.append(channel_id)
                if domain:
                    if len(arglist):
                        query += ' and '
                    query += 'domain_eq(domain, ?)'
                    arglist.append(domain)
                if date_added != None:
                    if len(arglist):
                        query += ' and '
                    query += ' date_added > ?'
                    arglist.append(date_added)
                if not len(arglist):
                    return None
                try:
                    self.cursor.execute(query, tuple(arglist))
                    return self.cursor.fetchall()
                except sqlite3.Error, e:
                    logging.error("Could not remove short_url from database")
                    logging.debug(str(e))

            def remove_reddit_older_than(self, days):
                """removes all entries from the reddit_record older than a certain date

                :param days: how many days ago
                """
                try:
                    the_time = datetime.datetime.now() - datetime.timedelta(days=days)
                    self.cursor.execute("delete from reddit_record where date_added < ?", (the_time,))
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.error("Could not remove reddit records older than " + str(days) + " days")
                    logging.debug(str(e))

            def remove_reddit(self, reddit_entries):
                """removes the entries from the reddit_record

                :param reddit_entries: a list of the short_url's to delete
                """
                try:
                    if not isinstance(reddit_entries, list):
                        reddit_entries = list(reddit_entries)
                    tupled = [(entry,) if not isinstance(entry, tuple) else entry for entry in reddit_entries]
                    self.cursor.executemany('delete from reddit_record where short_url = ?', tupled)
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.error("Could not remove short_url from database")
                    logging.debug(str(e))

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


            def channel_exists(self, channel_list):
                """checks whether the specified channels exist

                :param channel_list: a list of tuples of the form (channel_id, domain)
                :return: a list of booleans indicating whether the channel exists or not
                """

                try:
                    return [self.cursor.execute("""select channel_id from channel_record where channel_id = ?
                            and domain_eq(domain, ?)""", channel).fetchone() is not None for channel in channel_list]
                except sqlite3.Error, e:
                    logging.error("Error on channel exists check")
                    logging.debug(str(e))

            def get_channels(self, blacklist=None, blacklist_not_equal=None, domain=None, strike_count=None, id_filter=None, return_url=False, return_blacklist=False, return_strikes=False):
                """returns the channels matching the supplied query

                :param blacklist: the black/whitelist to match
                :param domain: the domain to match
                :param strike_count: the strike count to be less than or equal to
                :param id_filter: regex filter
                :return: (channel_id, domain, channel_url (if return_url), blacklist (if return_blacklist), strike_count (if return_strikes))
                         or None if empty query
                """

                #setup returns
                query = "select channel_id, domain"
                if return_url:
                    query += ", channel_url"
                if return_blacklist:
                    query += ", blacklist"
                if return_strikes:
                    query += ", strike_count"
                query += " from channel_record where"

                #set up filtering criteria
                arglist = []
                if blacklist:
                    if len(arglist):
                        query += " and"
                    query += " blacklist = ?"
                    arglist.append(blacklist)
                elif blacklist_not_equal:
                    if len(arglist):
                        query += " and"
                    query += " blacklist != ?"
                    arglist.append(blacklist_not_equal)
                if domain:
                    if len(arglist):
                        query += " and"
                    query += " domain_eq(domain, ?)"
                    arglist.append(domain)
                if strike_count:
                    if len(arglist):
                        query += " and"
                    query += " strike_count >= ?"
                    arglist.append(strike_count)
                if id_filter:
                    if len(arglist):
                        query += " and"
                    query += " channel_id regexp ?"
                    arglist.append(id_filter)
                #empty filter
                if not len(arglist):
                    return None

                #query
                try:
                    self.cursor.execute(query, tuple(arglist))
                    return self.cursor.fetchall()
                except sqlite3.Error, e:
                    logging.error("Error on get_channels fetch.")
                    logging.debug("domain, blacklist, id_filter:" + str(domain) + ", " + str(blacklist) + ", " + str(id_filter))

            def set_blacklist(self, channel_entries, value):
                """Updates the black/whitelist for the given channel entries

                :param channel_entries: a list of tuples of the form (channel_id, domain)
                :param value: the new blacklist enum value
                """
                try:
                    self.cursor.executemany('update channel_record set blacklist = ? where channel_id = ? and domain_eq(domain, ?)', [(value, channel[0], channel[1]) for channel in channel_entries])
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.error("Error on set_blacklist.")
                    logging.debug(str(e))

            def get_blacklist(self, channel_entries):
                """Gets the blacklist for the specified channels

                :param channel_entries: a list of tuples of the form (channel_id, domain)
                """
                try:
                    list = []
                    for channel in channel_entries:
                        list.append(self.cursor.execute('select blacklist from channel_record where channel_id = ? and domain_eq(domain, ?)', channel).fetchone())
                    list = [entry[0] if entry else Blacklist.BlacklistEnums.NotFound for entry in list]
                    return list
                except sqlite3.Error, e:
                    logging.error("Error on get_blacklist.")
                    logging.debug(str(e))

            def set_strikes(self, channel_entries):
                """Updates the strike count for the given channels

                :param channel_entries: a list of tuples of the form (channel_id, domain, new_strike_count)
                """
                try:
                    reordered = [(entry[2], entry[0], entry[1]) for entry in channel_entries]
                    self.cursor.executemany('update channel_record set strike_count = ? where channel_id = ? and domain_eq(domain, ?)', reordered)
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.error("Error on set_strikes.")
                    logging.debug(str(e))

            def add_strike(self, channel_entries):
                """Adds one to the strike count for the given channels

                :param channel_entries: a list of tuples of the form (channel_id, domain)
                """
                try:
                    self.cursor.executemany('update channel_record set strike_count = strike_count + 1 where channel_id = ? and domain_eq(domain, ?)', channel_entries)
                    self.db.commit()
                except sqlite3.Error, e:
                    logging.error("Error on set_strikes.")
                    logging.debug(str(e))



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