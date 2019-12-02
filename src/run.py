import argparse
from dataclasses import dataclass
from pathlib import Path
import logging
from typing import Callable, List

import yaml

from sqlalchemy import create_engine
from sqlalchemy.engine.base import Engine
from sqlalchemy.exc import NoSuchTableError

import pandas as pd

from db import PGDatabaseCreds, restore_sql_dump, restore_epd
import queries
from queries import SiteList

logging.basicConfig(
    filename='logs/epd_extract.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

DB_HOSTNAME = 'db'
DB_PORT = 5432  # Container port for the Postgres container's database.


@dataclass
class Site:
    name: str
    epd_number: int


@dataclass
class Config:
    queries: List[str]
    sites: List[Site]


def _read_config_file(config_file: str) -> Config:
    """Read application configuration file.

    TODO: Add error handling
    """
    with open(config_file) as f:
        config_dict = yaml.load(f, Loader=yaml.SafeLoader)

    return Config(
        queries=config_dict['queries'],
        sites=[Site(d['name'], d['epd_number']) for d in config_dict['sites']],
    )


def _get_command_line_args() -> argparse.Namespace:
    """Process command line arguments."""
    parser = argparse.ArgumentParser()
    parser.add_argument('--restore-epd', action='store_true')
    return parser.parse_args()


def _get_query_function(query_name: str) -> Callable[[Engine, SiteList],
                                                     pd.DataFrame]:
        try:
            query_func = getattr(queries, query_name)
        except AttributeError as e:
            logging.error(f"No function named '{query_name}' in queries.py")
            raise AttributeError(e)
        return query_func


def _get_query_data(query_func: Callable[[Engine, SiteList], pd.DataFrame],
                    epd_engine: Engine, site_numbers: SiteList) -> pd.DataFrame:
    """Run query spefified by `query_func` against the database."""
    try:
        query_data = query_func(epd_engine, site_numbers)
    except NoSuchTableError as e:
        logging.error('Query could not find table. Check EPD has been '
                      'restored')
        raise NoSuchTableError(e)

    return query_data


if __name__ == '__main__':
    args = _get_command_line_args()
    config = _read_config_file('config/config.yml')
    db = PGDatabaseCreds(DB_HOSTNAME, DB_PORT, 'postgres', 'postgres')

    if args.restore_epd:
        logging.info('Creating epd and wwwadm database users...')
        # These users are assumed to exist in the EPD SQL dump
        db_setup_res = restore_sql_dump('data/db_setup.sql', db)
        # Restore the EPD itself from the SQL dump
        epd_res = restore_epd('data/dumpall_epd_db.sql.gz', db)

    epd_engine = create_engine(db.conn_str)

    output_dir = Path('outputs')
    output_dir.mkdir(exist_ok=True)

    logging.info('Extracting csv data...')
    for query_name in config.queries:
        query_data = _get_query_data(
            _get_query_function(query_name),
            epd_engine,
            [s.epd_number for s in config.sites]
        )
        query_data.to_csv(output_dir / (query_name + '.csv'))

    logging.info('Finished extracting csv data')
