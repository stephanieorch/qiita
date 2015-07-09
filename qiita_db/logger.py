r"""
Logging objects (:mod: `qiita_db.logger`)
====================================

..currentmodule:: qiita_db.logger

This module provides objects for recording log information

Classes
-------

..autosummary::
    :toctree: generated/

    LogEntry
"""

# -----------------------------------------------------------------------------
# Copyright (c) 2014--, The Qiita Development Team.
#
# Distributed under the terms of the BSD 3-clause License.
#
# The full license is in the file LICENSE, distributed with this software.
# -----------------------------------------------------------------------------

from __future__ import division

from json import loads, dumps

from qiita_db.util import convert_to_id
from .sql_connection import TRN
from .base import QiitaObject


class LogEntry(QiitaObject):
    """
    Attributes
    ----------
    severity
    time
    info
    msg

    Methods
    -------
    clear_info
    add_info
    """

    _table = 'logging'

    @classmethod
    def newest_records(cls, numrecords=100):
        """Return a list of the newest records in the logging table

        Parameters
        ----------
        numrecords : int, optional
            The number of records to return. Default 100

        Returns
        -------
        list of LogEntry objects
            list of the log entries
        """
        with TRN:
            sql = """SELECT logging_id
                     FROM qiita.{0}
                     ORDER BY logging_id DESC LIMIT %s""".format(cls._table)
            TRN.add(sql, [numrecords])

            return [cls(i) for i in TRN.execute_fetchflatten()]

    @classmethod
    def create(cls, severity, msg, info=None):
        """Creates a new LogEntry object

        Parameters
        ----------
        severity : str  {Warning, Runtime, Fatal}
            The level of severity to use for the LogEntry. Refers to an entry
            in the SEVERITY table.
        msg : str
            The message text
        info : dict, optional
            Defaults to ``None``. If supplied, the information will be added
            as the first entry in a list of information dicts. If ``None``,
            an empty dict will be added.

        Notes
        -----
        - When `info` is added, keys can be of any type, but upon retrieval,
          they will be of type str
        """
        if info is None:
            info = {}

        info = dumps([info])

        with TRN:
            sql = """INSERT INTO qiita.{} (time, severity_id, msg, information)
                     VALUES (NOW(), %s, %s, %s)
                     RETURNING logging_id""".format(cls._table)
            severity_id = convert_to_id(severity, "severity")
            TRN.add(sql, [severity_id, msg, info])

            return cls(TRN.execute_fetchlast())

    @property
    def severity(self):
        """Returns the severity_id associated with this LogEntry

        Returns
        -------
        int
            This is a key to the SEVERITY table
        """
        with TRN:
            sql = """SELECT severity_id FROM qiita.{}
                     WHERE logging_id = %s""".format(self._table)
            TRN.add(sql, [self.id])
            return TRN.execute_fetchlast()

    @property
    def time(self):
        """Returns the time that this LogEntry was created

        Returns
        -------
        datetime
        """
        with TRN:
            sql = "SELECT time FROM qiita.{} WHERE logging_id = %s".format(
                self._table)
            TRN.add(sql, [self.id])

            return TRN.execute_fetchlast()

    @property
    def info(self):
        """Returns the info associated with this LogEntry

        Returns
        -------
        list of dict
            Each entry in the list is information that was added (the info
            added upon creation will be index 0, and if additional info
            was supplied subsequently, those entries will occupy subsequent
            indices)

        Notes
        -----
        - When `info` is added, keys can be of any type, but upon retrieval,
          they will be of type str
        """
        with TRN:
            sql = """SELECT information FROM qiita.{} WHERE
                     logging_id = %s""".format(self._table)
            TRN.add(sql, [self.id])

            return loads(TRN.execute_fetchlast())

    @property
    def msg(self):
        """Gets the message text for this LogEntry

        Returns
        -------
        str
        """
        with TRN:
            sql = "SELECT msg FROM qiita.{0} WHERE logging_id = %s".format(
                self._table)
            TRN.add(sql, [self.id])

            return TRN.execute_fetchlast()

    def clear_info(self):
        """Resets the list of info dicts to be an empty list
        """
        with TRN:
            sql = """UPDATE qiita.{} SET information = %s
                     WHERE logging_id = %s""".format(self._table)
            TRN.add(sql, [dumps([]), self.id])

            TRN.execute()

    def add_info(self, info):
        """Adds new information to the info associated with this LogEntry

        Parameters
        ----------
        info : dict
            The information to add.

        Notes
        -----
        - When `info` is added, keys can be of any type, but upon retrieval,
          they will be of type str
        """
        with TRN:
            current_info = self.info
            current_info.append(info)
            new_info = dumps(current_info)

            sql = """UPDATE qiita.{} SET information = %s
                     WHERE logging_id = %s""".format(self._table)
            TRN.add(sql, [new_info, self.id])
            TRN.execute()
