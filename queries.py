"""
queries.py
~~~~~~~~~~

Functions used to run canned SQL queries against the EPD.

The functions in this module follow a policy of leaving column names as they
are in the EPD to assist in understanding subsequent analysis. See
documentation on the `EPD website`_ for more information about the dataset.

.. _EPD website: http://europeanpollendatabase.net/data/downloads/
"""
from collections import namedtuple
import logging
from pathlib import Path
import sys
from typing import Iterable

from sqlalchemy import exc, select, Table, MetaData, and_
from sqlalchemy.engine.base import Engine
from sqlalchemy.sql.selectable import Select

import numpy as np
import pandas as pd

SiteList = Iterable[int]
AbundanceTables = namedtuple(
    'AbundanceTables',
    ['entity', 'p_counts', 'p_vars', 'p_agedpt', 'chron', 'siteloc']
)  


def _check_EPD_con(con: Engine) -> None:
    """Check EPD connection object works.

    Use simple example query which should be achievable with any instance of
    the EPD.
    """
    try:
        pd.read_sql_query('select * from entity limit10;', con=con)
    except exc.SQLAlchemyError as e:
        logging.error('Could not connect to the EPD with the supplied engine.')
        raise exc.SQLAlchemyError(e)
    logging.info('Test query successfully run against EPD.')


def site_loc_info(con: Engine, sites: SiteList) -> pd.DataFrame:
    """Return DataFrame providing location information for study sites.
    
    Parameters
    ----------
    con:
        SQLAlchemy database connection engine pointing at an instance of the
        EPD.
    sites:
        List of integer site numbers corresponding to the field 'site_' in the
        siteloc and entity tables in the EPD.
        
    Returns
    -------
    DataFrame with the following row index and fields:
        - sitename (index): Name of site where core was collected
        - latdd: Decimal latitude
        - londd: Decimal longitude
        - elevation: Elevation of site above sea level
        - site_: Site number, primary key of siteloc table
    """
    siteloc = Table('siteloc', MetaData(), autoload_with=con)
    sites_select = (
        select([siteloc.c.sitename, siteloc.c.latdd, siteloc.c.londd,
                siteloc.c.elevation, siteloc.c.site_])
        .where(siteloc.c.site_.in_(sites))
    )
    return pd.read_sql_query(sites_select, con=con).set_index('sitename')


def site_pollen_abundance(con: Engine, sites: SiteList) -> pd.DataFrame:
    """Return DataFrame of pollen abundance time series for study sites.
    
    Parameters
    ----------
    con:
        SQLAlchemy database connection engine pointing at an instance of the
        EPD.
    sites:
        List of integer site numbers corresponding to the field 'site_' in the
        siteloc and entity tables in the EPD.
        
    Returns
    -------
    DataFrame with the following row (multi)index and fields:
        - sitename (index): Name of site where core was collected
        - sigle (index): Code uniquely identifying a sediment core
        - sample_ (index): Identifies sample extracted from sediment core
        - varcode (index): Species identifier
        - agebp: Age BP of sample according to default chronology
        - count: Number of `varcode` pollen grains found in sample
        - varname: Name of species corresponding to `varcode`
        - site_: Site number, primary key of siteloc table
        - e_: Entity (sediment core) numner, primary key of entities table
        - chron_: Chronology numner, primary key of chrons table
        - var_: Variable number, primary key of p_vars table    
    """
    # Create Python objects representing database tables
    metadata = MetaData()  
    tables = AbundanceTables(*[
        Table(t_name, metadata, autoload_with=con)
        for t_name in AbundanceTables._fields
    ])
    
    df = (
        pd.read_sql_query(_pollen_abundance_select(tables, sites), con=con)
        .set_index(['sitename', 'sigle', 'sample_', 'varcode'])
        .fillna(np.nan)
    )
    
    assert (((df.index.value_counts() > 1).sum() == 0)
            and (df.index.is_unique)), (
        'site/ entity (sediment core)/ sample (date)/ species combinations '
        'should be unique.'
    )
    
    return df


def _pollen_abundance_select(at: AbundanceTables, sites: SiteList) -> Select:
    """Construct SQL query needed to obtain pollen abundance data.
    
    Only data for the site codes given in `sites` will be selected.
    
    Note that we extract only the default chronology for each sample.
    """
    return (
        select([at.p_agedpt.c.agebp, at.p_counts.c.count, at.p_vars.c.varcode,
                at.p_vars.c.varname, at.siteloc.c.sitename, at.entity.c.site_,
                at.entity.c.e_, at.entity.c.sigle, at.p_counts.c.sample_,
                at.chron.c.chron_, at.p_counts.c.var_])
        .select_from(
            at.p_counts
            .join(at.entity, at.p_counts.c.e_ == at.entity.c.e_)
            .join(at.p_agedpt, and_(at.p_counts.c.e_ == at.p_agedpt.c.e_,
                                 at.p_counts.c.sample_ == at.p_agedpt.c.sample_))
            .join(at.chron, and_(at.p_agedpt.c.e_ == at.chron.c.e_,
                              at.p_agedpt.c.chron_ == at.chron.c.chron_))
            .join(at.p_vars, at.p_counts.c.var_ == at.p_vars.c.var_)
            .join(at.siteloc, at.entity.c.site_ == at.siteloc.c.site_)
        )
        .where(and_(at.entity.c.site_.in_(sites),
                    at.chron.c.defaultchron == 'Y'))
    )
