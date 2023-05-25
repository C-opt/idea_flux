import argparse
import logging
import os

import networkx as nx
import pandas as pd
import yaml
from pyvis.network import Network

from backend.miner import SQL
from backend.utils import create_directory, setup_logging


class SubmissionCommentAnalysis:
    def __init__(self, submission_id: str, sql_handle: SQL):
        self.logger = None
        setup_logging(self)

        self.sql_handle = sql_handle

        self.graph = None
        self.raw_df = None
        self.submission_id = submission_id
        self.db2graph()

        self.user_engagement_per_comment = None
        self.user_engagement_per_submission = None
        self.spine_body = None

        self.compute_user_engagement_per_comment()
        self.compute_user_engagement_for_submission()
        self.get_submission_comment_spine()

    def db2graph_df(
        self,
    ):
        table_name = "reddit_comments"
        cols = ["comment_id", "parent_id", "submission_id", "body"]
        add_query = " WHERE submission_id = '{q}';".format(q=self.submission_id)
        raw_df = self.sql_handle.sql_table2df(table_name, cols, add_query)

        # https://dataindependent.com/pandas/add-column-to-dataframe-pandas/
        raw_df["edge_weight"] = 1
        self.raw_df = raw_df
        return raw_df

    def graph_df2graph(self):
        self.graph = nx.from_pandas_edgelist(
            self.raw_df,
            source="parent_id",
            target="comment_id",
            edge_attr=["edge_weight"],
            create_using=nx.DiGraph(),
        )

    def db2graph(
        self,
    ):
        self.db2graph_df()
        self.graph_df2graph()

    def compute_user_engagement_per_comment(self) -> dict:
        if self.graph == None:
            return
        user_engagement_calc_dict = dict()
        for n in list(self.graph.nodes):
            n_pt = len(list(nx.descendants(self.graph, n)))
            user_engagement_calc_dict.update({n: n_pt})
        user_engagement_per_comment = dict(
            sorted(user_engagement_calc_dict.items(), key=lambda x: x[1], reverse=True)
        )
        self.user_engagement_per_comment = user_engagement_per_comment

    def compute_user_engagement_for_submission(self) -> int:
        tmp_sum = 0
        for key in self.user_engagement_per_comment.keys():
            score = self.user_engagement_per_comment.get(key)
            tmp_sum += score
        if len(self.user_engagement_per_comment) > 0:
            score = tmp_sum / len(self.user_engagement_per_comment)
        else:
            score = 0
        self.logger.debug("score = {score}".format(score=score))
        self.user_engagement_for_submission = score
        return score

    def get_submission_comment_spine_ids(self):
        def best_neighbor(neighbors: str, sorted_scores_nodes: list):
            best_score = 0
            best_node = None

            best_nodes = list()
            best_scores = list()
            for neighbor in neighbors:
                tmp_score = sorted_scores_nodes.get(neighbor)
                if tmp_score > best_score:
                    best_score = tmp_score
                    best_node = neighbor

                    best_scores.append(best_score)
                    best_nodes.append(best_node)
            return best_scores, best_nodes

        res = list()
        list_sorted_u_engagement_score = list(self.user_engagement_per_comment)
        if len(list_sorted_u_engagement_score) <= 0:
            return res
        curr_comm = list_sorted_u_engagement_score[0]

        while curr_comm is not None:
            best_scores, best_comms = best_neighbor(
                list(self.graph.successors(curr_comm)), self.user_engagement_per_comment
            )

            if len(best_comms) > 0:
                curr_comm = best_comms[len(best_comms) - 1]
                curr_u_engagement_score = best_scores[len(best_comms) - 1]
            else:
                curr_comm = None
                curr_u_engagement_score = None

            if curr_comm:
                res.append(curr_comm)
        return res

    def get_submission_comment_spine(
        self,
    ):
        submission_title = self.sql_handle.get_column_from_table(
            "submissions",
            "title",
            " WHERE submission_id = '{id}';".format(id=self.submission_id),
        )

        submission_body = self.sql_handle.get_column_from_table(
            "submissions",
            "body",
            " WHERE submission_id = '{id}';".format(id=self.submission_id),
        )

        add_query = " WHERE submission_id = '{id}' ".format(id=self.submission_id)
        ids = self.get_submission_comment_spine_ids()
        if len(ids) > 0:
            add_query += "AND ("
        for id, i in zip(ids, range(len(ids))):
            add_query += "comment_id = '{id}' ".format(id=id)
            if i < len(ids) - 1:
                add_query += "OR "
        if len(ids) > 0:
            add_query += ")"
        add_query += ";"

        comm_bodies = self.sql_handle.get_column_from_table(
            "reddit_comments", "body", add_query
        )

        res = "\n" + "-" * 10 + "TITLE" + "-" * 10
        res += "\n" + submission_title[0]
        res += "\n" + submission_body[0]

        for body, id in zip(comm_bodies, ids):
            res += "\n" + "-" * 40
            res += "\nComment ID: " + str(id)
            res += "\n" + body
        self.spine_body = res
        return res


class SubmissionsAnalysis:
    def __init__(
        self,
        **kwargs,
    ):
        self.logger = None
        setup_logging(self)
        self.sql_handle = kwargs.get("sql_handle")

    def submissions_user_engagement_init(self):
        submissions_user_engagement_dict = dict()
        submissions_user_engagement_dict.update({"submission_id": list()})
        submissions_user_engagement_dict.update({"user_engagement": list()})
        submissions_user_engagement_dict.update({"spine_body": list()})

        return submissions_user_engagement_dict

    def routine(self):
        submission_ids = self.sql_handle.get_column_from_table(
            "submissions", "submission_id", " WHERE comments_num > 1;"
        )
        already_processed_submission_ids = self.sql_handle.get_column_from_table(
            "submissions_user_engagement", "submission_id"
        )

        tbproc_sub_ids = list(
            set(submission_ids) - set(already_processed_submission_ids)
        )

        sub_ue_dict = self.submissions_user_engagement_init()

        for submission_id in tbproc_sub_ids:
            sub_comms_handle = SubmissionCommentAnalysis(
                submission_id=submission_id,
                sql_handle=self.sql_handle,
            )

            self.logger.info(submission_id)
            id = submission_id
            body = sub_comms_handle.spine_body
            score = sub_comms_handle.user_engagement_for_submission

            sub_ue_dict.get("submission_id").append(id)
            sub_ue_dict.get("user_engagement").append(score)
            sub_ue_dict.get("spine_body").append(body)

        sub_ue_df = pd.DataFrame(sub_ue_dict)
        self.sql_handle.execute_values(sub_ue_df, "submissions_user_engagement")

        return


class GraphAnalysis:
    def __init__(self, **kwargs):
        self.logger = None
        setup_logging(self)

        self.dataframe_fp = kwargs.get("dataframe_fp")
        self.topic_id = kwargs.get("topic_id")

        self.dataframe = pd.read_hdf(self.dataframe_fp, key="df")
        self.graph = None
        self.sorted_nodes_scores_dict = None
        self.user_engagement_for_submission = None

        self.gen_graph()

    def gen_graph(self):
        self.logger.info("generating graph")
        graph = nx.from_pandas_edgelist(
            self.dataframe,
            source="parent_id",
            target="comm_id",
            edge_attr=["weight"],
            create_using=nx.DiGraph(),
        )
        self.graph = graph
        return graph

    def render_graph(self, save_fp):
        self.logger.info("rendering graph to {fp}".format(fp=save_fp))
        net = Network("1000px", "1000px", notebook=True)
        net.show_buttons(filter_=["physics"])
        net.from_nx(self.graph)
        return net.show(save_fp)


def parser():
    p = argparse.ArgumentParser(description="Data scraper using praw")

    p.add_argument(
        "--pg_host",
        type=str,
        default="localhost",
        help="Folder where h5 files are going to be saved",
    )

    p.add_argument(
        "--pg_database",
        type=str,
        default="ideaflux",
        help="Folder where h5 files are going to be saved",
    )

    p.add_argument(
        "--pg_user",
        type=str,
        default="postgres",
        help="Folder where h5 files are going to be saved",
    )

    p.add_argument(
        "--pg_password",
        type=str,
        default="postgres",
        help="Folder where h5 files are going to be saved",
    )

    return p.parse_args()


def main():
    args = parser()

    pg_host = args.pg_host
    pg_database = args.pg_database
    pg_user = args.pg_user
    pg_password = args.pg_password

    sql_handle = SQL(
        host=pg_host,
        database=pg_database,
        user=pg_user,
        password=pg_password,
    )

    sub_analysis = SubmissionsAnalysis(sql_handle=sql_handle)
    sub_analysis.routine()

    sql_handle.close_conn()
    return


if __name__ == "__main__":
    main()
