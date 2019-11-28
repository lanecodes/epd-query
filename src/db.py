"""
db.py
~~~~~

Functions and classes related to setting up the European Pollen Database.
"""

from dataclasses import dataclass
import gzip
import logging
from pathlib import Path
from subprocess import CompletedProcess, run
import shlex
import tempfile


@dataclass
class PGDatabaseCreds:
    """Postgres database credentials.

    Parameters
    ----------
    host:
        IP address or name of database's host computer.
    port:
        Port at host via which database can be accessed.
    database:
        Name of database within the postgres instance.
    user:
        Name of user to log into the database under.

    Attributes
    ----------
    conn_str:
        Connection string to be passed to, e.g. `SQLAlchemy.create_engine`.
    """
    host: str
    port: int
    database: str
    user: str

    @property
    def conn_str(self) -> str:
        return f'postgresql://{self.user}@{self.host}:{self.port}/{self.database}'


def restore_epd(file: str, db_creds: PGDatabaseCreds) -> CompletedProcess:
    """Restore the EPD from compressed SQL dump to the given Postgres instance.

    Parameters
    ----------
    file:
        Path to the file dumpall_epd_db.sql.gz included in the EPD Postgres
        distribution downloaded from the `EPD website`_.
    db_creds:
        Postgres credentials to use to log into the database.

    Returns
    -------
    CompletedProcess

    .. _EPD website: http://europeanpollendatabase.net/data/downloads/
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        sql_file = Path(tmpdir) / 'tmp.sql'

        logging.info('Uncompressing EPD SQL dump...')
        with gzip.open(file, 'rb') as src_f:
            with open(sql_file, 'wb') as tgt_f:
                for line in src_f:
                    tgt_f.write(line)

        logging.info('Loading sql into database at '
                     f'{db_creds.host}:{db_creds.port}...')
        res = restore_sql_dump(str(sql_file), db_creds)
        logging.info('Restore stdout:\n' + res.stdout)

        if res.stderr:
            logging.info('Restore stderr:\n' + res.stderr)

        logging.info('Finished restoring database.')

        return res


def restore_sql_dump(file: str, db_creds: PGDatabaseCreds) -> CompletedProcess:
    """Restore a SQL dump to a Postgres database.

    Parameters
    ----------
    file:
        Path to SQL dump file to restore to the database.
    db_creds:
        Postgres credentials to use to log into the database.

    Notes
    -----
    Implementation takes example from the responses to `this SO question`_

    .. _this SO question: https://stackoverflow.com/questions/43380273

    Returns
    -------
    CompletedProcess
    """
    return run(shlex.split(
        f'psql -h {db_creds.host} -p {db_creds.port} -d {db_creds.database} '
        f'-U {db_creds.user} -f {file}'
    ), check=True, capture_output=True, text=True)
