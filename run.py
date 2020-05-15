#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
from typing import List, Union

import click
from kg_covid_19 import download as kg_download
from kg_covid_19 import transform as kg_transform
from kg_covid_19.edges import make_edges
from kg_covid_19.load_utils.merge_kg import load_and_merge
from kg_covid_19.query import QUERIES, run_query
from kg_covid_19.transform import DATA_SOURCES


@click.group()
def cli():
    pass


@cli.command()
@click.option("yaml_file", "-y", required=True, default="download.yaml",
              type=click.Path(exists=True))
@click.option("output_dir", "-o", required=True, default="data/raw")
@click.option("ignore_cache", "-i", is_flag=True, default=False,
              help='ignore cache and download files even if they exist [false]')
def download(*args, **kwargs) -> None:
    """Downloads data files from list of URLs (default: download.yaml) into data
    directory (default: data/raw).

    Args:
        yaml_file: Specify the YAML file containing a list of datasets to download.
        output_dir: A string pointing to the directory to download data to.
        ignore_cache: If specified, will ignore existing files and download again.

    Returns:
        None.

    """

    kg_download(*args, **kwargs)

    return None


@cli.command()
@click.option("input_dir", "-i", default="data/raw", type=click.Path(exists=True))
@click.option("output_dir", "-o", default="data/transformed")
@click.option("sources", "-s", default=None, multiple=True,
              type=click.Choice(DATA_SOURCES.keys()))
def transform(*args, **kwargs) -> None:
    """Calls scripts in kg_covid_19/transform/[source name]/ to transform each source
    into nodes and edges.

    Args:
        input_dir: A string pointing to the directory to import data from.
        output_dir: A string pointing to the directory to output data to.
        sources: A list of sources to transform.

    Returns:
        None.

    """

    # call transform script for each source
    kg_transform(*args, **kwargs)

    return None


@cli.command()
@click.option('yaml', '-y', default="merge.yaml", type=click.Path(exists=True))
def load(yaml: str) -> None:
    """Use KGX to load subgraphs to create a merged graph.

    Args:
        yaml: A string pointing to a KGX compatible config YAML.

    Returns:
        None.

    """

    load_and_merge(yaml)


@click.option("query", "-q", required=True, default=None, multiple=False,
              type=click.Choice(QUERIES.keys()))
@click.option("input_dir", "-i", default="data/")
@click.option("output_dir", "-o", default="data/queries/")
def query(query: str, input_dir: str, output_dir: str) -> None:
    """Perform a query of knowledge graph using a class contained in query_utils

    Args:
        query: A query class containing instructions for performing a query
        input_dir: Directory where any input files required to execute query are
            located (typically 'data', where transformed and merged graph files are)
        output_dir: Directory to output results of query

    Returns:
        None.

    """
    run_query(query=query, input_dir=input_dir, output_dir=output_dir)


@cli.command()
@click.option("num_edges", required=True, type=int)
@click.option("nodes", default="data/merged/nodes.tsv", type=click.Path(exists=True))
@click.option("edges", default="data/merged/edges.tsv", type=click.Path(exists=True))
@click.option("output_dir", default="data/edges/", type=click.Path(exists=True))
@click.option("train_fraction", default=0.8)
@click.option("validation", is_flag=True, default=False)
@click.option("node_src_dst_types", default=[None, None], type=List[Union[str, None]])
@click.option("min_degree", default=2)
def edges(*args, **kwargs) -> None:
    """Make sets of edges for ML training

    Given a graph (in KGX formatted node and edge TSVs), output positive and negative
    edges for use in machine learning.

    Positive edges are randomly selected from the edges in the graph, IFF both nodes
    participating in the edge have a degree greater than min_degree (to avoid creating
    disconnected components). This edge is then removed in the output graph. Negative
    edges are selected by randomly selecting pairs of nodes that are not connected by an
    edge. Optionally, if edge_type is specified, only edges between nodes of
    node_src_dst_types[0] and node_src_dst_types[1] are selected.

    For both positive and negative edge sets, edges are assigned to training set
    according to train_fraction (0.8 by default). The remaining are assigned to test set
    or split evenly between test and validation set, if [validation==True].

    Outputs these files in [output_dir]:
        edges.tsv + edges.tsv - new graph with positive edges removed
        pos_train.tsv
        pos_test.tsv
        pos_valid.tsv (optional)
        neg_train.tsv
        neg_test.tsv
        neg_valid.tsv (optional)

    Args:
        num_edges:      number of positive and negative edges to emit
        nodes:          nodes of input graph, in KGX TSV format [data/merged/nodes.tsv]
        edges:          edges for input graph, in KGX TSV format [data/merged/edges.tsv]
        output_dir:     directory to output edges and new graph [data/edges/]
        train_fraction: fraction of edges to emit as training [0.8]
        validation:     should we make validation edges? [False]
        min_degree      when choosing edges, what is the minimum degree of nodes involved
                        in the edge
        node_src_dst_types: what node types should we make edges from? by default, any
                       [None, None]
    """
    make_edges(*args, **kwargs)


if __name__ == "__main__":
    cli()
