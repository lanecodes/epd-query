import logging

from sqlalchemy import create_engine

from db import PGDatabaseCreds, restore_sql_dump, restore_epd
from queries import site_loc_info, site_pollen_abundance

logging.basicConfig(filename='epd_restore.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')

SITE_DICT = {
    # original selection presented in checkpoint report
    'Sanabria Marsh' : 44,
    'Albufera Alcudia' : 759,
    'Laguna Guallar' : 761,
    'San Rafael' : 486,
    'Navarrés' : 396,
    'Monte Areo mire' : 1252,
    # additional sites Carrion2010 called outstanding
    # examples of sites with anthropogenic disturbance
    'Atxuri' : 76, # neolithic
    'Puerto de Los Tornos' : 560, # neolithic
    'Charco da Candieira' : 762, # neolithic
    'Bajondillo' : 1260, # neolithic
    'Algendar' : 55 # Bronze age, Minorca
}


if __name__ == '__main__':
    db = PGDatabaseCreds('localhost', 5442, 'postgres', 'postgres')

    logging.info('Creating epd and wwwadm database users...')
    # These users are assumed to exist in the EPD SQL dump
    db_setup_res = restore_sql_dump('db_setup.sql', db)
    epd_res = restore_epd('dumpall_epd_db.sql.gz', db)

    logging.info('Extracting csv data...')
    epd_engine = create_engine(db.conn_str)

    site_loc_info(epd_engine,
                  SITE_DICT.values()).to_csv('site_loc_info.csv')

    site_pollen_abundance(epd_engine,
                          SITE_DICT.values()).to_csv('pol_abundance.csv')

    logging.info('Finished extracting csv data')
