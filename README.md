# EPDquery
[![DOI](https://zenodo.org/badge/225420303.svg)](https://zenodo.org/badge/latestdoi/225420303)

The European Pollen Database ([EPD](http://europeanpollendatabase.net)) is a
valuable source of data accumulated throughout the last century by thousands of
researchers. As of 2019, the EPD is in the process of being [transferred][EPD
getdata] to [Neotoma][Neotoma]. Neotoma can be queried using the `neotoma` [R
package][Neotoma package]. However, while the transfer of the EPD to Neotoma is
ongoing, there are data which can only be accessed by querying the EPD
directly. This project aims to make this process as transparent, reproducible,
and easy to document as possible.

## Motivation

At the time of writing (Autumn 2019), the only file format in which the EPD is
distributed which does not require proprietary software to read is a dump from
a [Postgres database][Postgres]. To access this data, users need to:

1. Set up a Postgres database on their system
2. Consult the EPD's published [documentation][EPD documentation] to learn how
   the data they need is organised in the database
3. Construct a SQL query to relate the database tables containing the required
   data in the appropriate way, possibly making use of a schema diagram such as
   that shown in Fig. 1

Even for simple use cases, such as extracting pollen abundance time series for
a list of study sites, users are required to know how to administer a database
(and have the access rights on their system to do so), as well as how to write
SQL. This limits the accessibility of the data, in the sense of the [FAIR
guiding principles][FAIR] for data management, to people with specific
technical skills. In other words there is a data engineering problem which
needs to be solved before a reacher can begin to use the EPD to address their
research problem.

<div style="text-align:center">
<img src="img/epd-abundance-pollen.png"
     alt="Example of schema diagram used to construct SQL query on the EPD"
     width="600"/>
</div>

Fig. 1: A schema diagram used to construct the SQL query corresponding to the
`site_pollen_abundance_ts` dataset (see [Supported
datasets](#supported-datasets)). Underlined words are the names of tables in
the database, beneath which are shown fields relevant to the query. Arrows
indicate relations between the tables which were inferred by consulting the
database documentation available on the [EPD
website](http://europeanpollendatabase.net/data/downloads/).

EPDquery is a framework for providing specific, parameterised datasets we
might extract from the EPD with names we can refer to subsequently in our
analyses. See the [Supported datasets](#supported-datasets) section of this
page for a complete list of datasets which EPDquery can extract from the
EPD at present.

## Installation

### Install Docker Engine and Docker Compose

See the excellent [documentation][Docker install] on the Docker website to
install the Docker Engine and Docker Compose on your system if they are not
installed already. Docker makes it possible to construct and run a local
instance of the EPD from the database dump distributed on the EPD website
without requiring users to manually install and manage a Postgres instance.

### Clone this repository

```bash
git clone https://github.com/lanecodes/epd-query.git epd-query
```

### Download dependencies and build application

```bash
cd epd-query
docker-compose build
```

## How to use

After following the [installation](#installation) steps, EPDquery can be used as follows:

### 1. Download EPD database dump

First download the EPD Postgres distribution `.zip` file downloaded from the
[EPD website][EPD downloads]. This archive contains a file called
`dumpall_epd_db.sql.gz`. Put this file in the EPDquery application's `./data`
directory.

### 2. Specify which data to extract from the database

In this step we specify which pre-configured queries we want to run against the
EPD. Configuration is done using the file `./config/config.yml`.

The values in the `queries` list in `config.yml` correspond to the 'Dataset
name' column of the table in [Supported datasets](#supported-datasets).

`sites` in the configuration file is a list of maps each of which contain the
name and number of an EPD study site. See `./config/config.yml` in this
repository for an example.

### 3. Run the application

```bash
docker-compose up --abort-on-container-exit
```

The option `--abort-on-container-exit`
[tells](https://stackoverflow.com/questions/33799885) `docker-compose` to shut
down the database when our application has finished running.

Run the following to remove the temporary files created by the database while
running the application:

```bash
docker-compose down -v
```

Following this step, the application should have created a new `outputs`
directory containing `.csv` files holding datasets extracted from the EPD.


### 4. Change file permissions on output files [optional]

The final step which we have found necessary on Linux is to [change the
owner](https://unix.stackexchange.com/questions/101073) of the `outputs`
directory from `root` to our own user account. This is because Docker runs as
root, so files made under its process (including our outputs) are owned by the
super user.

```bash
sudo chown -R <my_user_name>:<my_user_name> outputs/
```

## Supported datasets

The following tables lists the currently implemented pre-configured datasets,
as well as the parameters which they require to be configured in `config.yml`.

| Dataset name               | Description                                                          | Parameters           |
| :---                       | :---                                                                 | :---                 |
| `site_location_info`       | Geographic coordinates of study sites                                | List of site numbers |
| `site_pollen_abundance_ts` | Sediment core-derived pollen abundance time series with chronologies | List of site numbers |


## Contributing

### Adding a new dataset

It is expected that contributions are most likely to come in the form of
additional named datasets which the application will extract from the EPD. Such
a change will include, as a minimum:

1. The addition of a new function to the file `src/queries.py`
2. A new entry in the table in the [Supported datasets](#supported-datasets)
   section of this page.

If your suggested dataset needs to extract data from the EPD on some basis
other than study site, we will need to think about how to best implement this,
especially in relation to configuration options. In that case, open an issue so
we can discuss it.

### Other changes

For any other ideas or suggestions, [open an issue][GH create issue] so we can
discuss the best way forward.

## Versioning

We use [semantic versioning][SemVer].

## Authors

- [Andrew Lane][ALane GitHub]

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file
for details.

## How to cite

Please visit the [Zenodo page](https://doi.org/10.5281/zenodo.3560683) for this
project to generate and export bibliographic information in the citation style
of your choice.

## Acknowledgements

This tool was developed by Andrew Lane during the course of his PhD in the
Department of Geography at King's College London. During this time Andrew was
supported by an Engineering and Physical Sciences Research Council (EPSRC) PhD
research studentship (EPSRC reference: EP/L015854/1).

[EPD getdata]: http://europeanpollendatabase.net/getdata/
[EPD downloads]: http://europeanpollendatabase.net/data/downloads/
[Neotoma]: https://www.neotomadb.org/
[Neotoma package]: https://www.rdocumentation.org/packages/neotoma
[Postgres]: https://www.postgresql.org/
[EPD documentation]: http://europeanpollendatabase.net/data/downloads/image/pollen-database-manual-20071011.doc
[FAIR]: https://www.nature.com/articles/sdata201618
[Docker install]: https://docs.docker.com/compose/install/
[GH create issue]: https://help.github.com/en/github/managing-your-work-on-github/creating-an-issue
[SemVer]: https://semver.org/
[ALane GitHub]: https://github.com/lanecodes
