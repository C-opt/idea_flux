import networkx as nx
import pandas as pd
import yaml
import logging
from utils import create_directory
import os
import argparse
from pyvis.network import Network

class GraphsAnalysis():
    def __init__(self, **kwargs):
        self.setup_logging()
        self.h5_dir = kwargs.get("h5_dir")
        self.res_dir = kwargs.get("res_dir")
        self.topics_df_fp = kwargs.get("topics_df_fp")

        topics_df = pd.read_hdf(self.topics_df_fp, key="df")
        self.topics_df = topics_df.reset_index(drop=True)
        self.graph_analysis_list = list()

    def batch_summarization(self):

        dataframes_fn = os.listdir(self.h5_dir)
        if "topics_df.h5" in dataframes_fn: dataframes_fn.remove("topics_df.h5")

        for dataframe_fn in dataframes_fn:
            filename, ext = os.path.splitext(dataframe_fn)
            topic_id = filename #  string
            if ext == ".h5":
                txt_filename = self.res_dir + filename + ".txt"
                txt_file_stream = open(txt_filename, "w+")
                self.logger.info(filename)
                body_txt = str(self.topics_df.loc[self.topics_df["id"]==filename]["body"].values[0])
                title_txt = str(self.topics_df.loc[self.topics_df["id"]==filename]["title"].values[0])
                url_txt = str(self.topics_df.loc[self.topics_df["id"]==filename]["url"].values[0])

                try: 
                    txt_file_stream.write("Title:" + title_txt)
                    txt_file_stream.write("\n" + "URL: " + url_txt)
                    txt_file_stream.write("\n" + body_txt)
                except Exception as err:
                    self.logger.error(err)

                txt_file_stream.close()
                # dataframe = pd.read_hdf(self.h5_dir+dataframe_fn, key="df")
                graph_analysis = GraphAnalysis(topic_id=topic_id, dataframe_fp=self.h5_dir+dataframe_fn)
                graph_analysis.render_graph(self.res_dir+filename+".html")
                graph_analysis.summarize_comms(txt_filename)
                
                self.graph_analysis_list.append(graph_analysis)
        self.update_topics_df()
        return

    def save_df(self, filepath, df):
        self.logger.info("saving dataframe to ... {filepath}".format(filepath=filepath))
        return df.to_hdf(filepath, key="df")
    
    def update_topics_df(self):
        for graph_analysis in self.graph_analysis_list:

            topic_id = str(graph_analysis.topic_id)
            self.logger.info("updating topics_df at: {topic_id}".format(topic_id=topic_id))
            try: 
                topic_df_loc = self.topics_df.loc[self.topics_df["id"] == topic_id]
                topic_df_idx = topic_df_loc.index
                # self.logger.info(self.topics_df[topic_df_idx]["user_engagement"].values[0])
                self.topics_df.at[topic_df_idx, "user_engagement"] = graph_analysis.comm_engagement_score
            except Exception as err:
                    self.logger.error("Response error occurred: {err}".format(err=err))
        
        self.topics_df = self.topics_df.sort_values(by="user_engagement", ascending=False)
        self.topics_df.to_excel(self.h5_dir+"topics_df.xlsx", engine='xlsxwriter')
        return self.save_df(self.h5_dir+"topics_df.h5", self.topics_df)

    def setup_logging(self, log_level=logging.DEBUG):
        FORMAT = "%(asctime)s %(levelname)7s %(filename)20s:%(lineno)4s - %(name)15s.%(funcName)16s() %(message)s"

        log_dir = "logs/"
        log_file = log_dir + "{name}.log".format(name=type(self).__name__)
        create_directory(log_dir)
        if not os.path.exists(log_file):
            with open(log_file, "w+") as f:
                f.write("-------------- LOG FILE FOR {name} --------------\n".format(name=type(self).__name__))

        self.logger = logging.getLogger(type(self).__name__)
        if not self.logger.hasHandlers():
            self.logger.setLevel(log_level)

            file_handler = logging.FileHandler(log_file, encoding=None, delay=False)
            stream_handler = logging.StreamHandler()

            file_handler.setLevel(logging.INFO)
            stream_handler.setLevel(logging.DEBUG)

            file_format = logging.Formatter(FORMAT)
            stream_format = logging.Formatter(FORMAT)

            file_handler.setFormatter(file_format)
            stream_handler.setFormatter(stream_format)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)
        
        return 

class GraphAnalysis():
    def __init__(self, **kwargs):
        self.setup_logging()
        self.dataframe_fp = kwargs.get("dataframe_fp")
        self.topic_id = kwargs.get("topic_id")
        
        self.dataframe = pd.read_hdf(self.dataframe_fp, key="df")
        self.graph = None
        self.sorted_nodes_scores_dict = None
        self.comm_engagement_score = None

        self.gen_graph()
    
    def setup_logging(self, log_level=logging.DEBUG):

        # 
        FORMAT = "%(asctime)s %(levelname)7s %(filename)20s:%(lineno)4s - %(name)15s.%(funcName)16s() %(message)s"

        log_dir = "logs/"
        log_file = log_dir + "{name}.log".format(name=type(self).__name__)
        create_directory(log_dir)
        if not os.path.exists(log_file):
            with open(log_file, "w+") as f:
                f.write("-------------- LOG FILE FOR {name} --------------\n".format(name=type(self).__name__))

        self.logger = logging.getLogger(type(self).__name__)
        if not self.logger.hasHandlers():
            self.logger.setLevel(log_level)

            file_handler = logging.FileHandler(log_file, encoding=None, delay=False)
            stream_handler = logging.StreamHandler()

            file_handler.setLevel(logging.INFO)
            stream_handler.setLevel(logging.DEBUG)

            file_format = logging.Formatter(FORMAT)
            stream_format = logging.Formatter(FORMAT)

            file_handler.setFormatter(file_format)
            stream_handler.setFormatter(stream_format)

            self.logger.addHandler(file_handler)
            self.logger.addHandler(stream_handler)
        
        return 

    def gen_graph(self):
        self.logger.info("generating graph")
        graph = nx.from_pandas_edgelist(self.dataframe, source="parent_id", target="comm_id",edge_attr=["weight"], create_using=nx.DiGraph())
        self.graph = graph
        return graph
    
    def render_graph(self, save_fp):
        self.logger.info("rendering graph to {fp}".format(fp=save_fp))
        net = Network('1000px', '1000px', notebook=True)
        net.show_buttons(filter_=['physics'])
        net.from_nx(self.graph)
        return net.show(save_fp)

    def node_score(self, comm_id):
        return len(list(nx.descendants(self.graph, comm_id)))
    
    def nodes_scores(self):
        if self.graph == None: return 
        nodes_scores_dict = dict()
        for n in list(self.graph.nodes):
            n_pt = self.node_score(n)
            nodes_scores_dict.update({n:n_pt})
        sorted_nodes_scores_dict = dict(sorted(nodes_scores_dict.items(), key= lambda x:x[1], reverse=True))
        self.sorted_nodes_scores_dict = sorted_nodes_scores_dict 
        return sorted_nodes_scores_dict
    
    def calculate_comm_engagement_score(self):
        tmp_sum = 0
        for key in self.sorted_nodes_scores_dict.keys():
            score = self.sorted_nodes_scores_dict.get(key)
            tmp_sum += score
        score = tmp_sum/len(self.sorted_nodes_scores_dict)
        self.logger.debug("score = {score}".format(score=score))
        self.comm_engagement_score = score
        return score

    def summarize_comms(self, save_fp):

        def best_neighbor(neighbors, sorted_scores_nodes):
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

        # generate txt file for saving the prunning results
        # filename, ext = os.path.splitext(self.dataframe_fp)
        # txt_filename = filename + ".txt"
        txt_file_stream = open(save_fp, "a")
        self.logger.info("saving summary at {save_fp}".format(save_fp=save_fp))

        dict_sorted_scores_nodes = self.nodes_scores()
        list_sorted_scores_nodes = list(dict_sorted_scores_nodes)
        node = list_sorted_scores_nodes[0]
        if node: 
            # title_str = self.dataframe[self.dataframe["comm_id"] == node]["title"].values[0]
            # body_str = self.dataframe[self.dataframe["comm_id"] == node]["body"].values[0]
            txt_file_stream.write("\n"+"-"*10+"TITLE" + "-"*10)
            txt_file_stream.write("\nTopic engagement score: "+str(self.calculate_comm_engagement_score()))
            # self.logger.info(self.dataframe[self.dataframe["comm_id"] == node]["body"])
            
            
        while node != None:
            best_scores, best_nodes = best_neighbor(list(self.graph.successors(node)), dict_sorted_scores_nodes)
            
            if len(best_nodes) > 0: 
                node = best_nodes[len(best_nodes)-1]
                score = best_scores[len(best_nodes)-1]
            else:
                node = None
                score = None
            
                
            if node:
                txt_file_stream.write("\n"+"-"*40)
                txt_file_stream.write("\nComment ID: "+str(node))
                txt_file_stream.write("\nComment score: "+str(score))
                try: 
                    txt_file_stream.write("\nComment body: "+str(self.dataframe[self.dataframe["comm_id"] == node]["body"].values[0]))
                except Exception as err:
                    self.logger.error("Response error occurred: {err}".format(err=err))
                    self.logger.error(str(self.dataframe[self.dataframe["comm_id"] == node]["body"].values[0]))

                # print("-"*40)
                # print(node, score)
                # print(self.dataframe[self.dataframe["comm_id"] == node]["body"].values[0])
        
        txt_file_stream.close()
        return 

def parser():
    parser = argparse.ArgumentParser(description="Data scraper using praw")

    parser.add_argument("--h5_dir", type=str, default="data/",
                        help="h5 dir")

    parser.add_argument("--res_dir", type=str, default="data/",
                        help="results dir")
    
    parser.add_argument("--topics_df_fp", type=str, default="data/topics_df.h5",
                        help="filepath to master h5 (dataframe when accessed)")

    return parser.parse_args()

def main():
    args = parser()
    h5_dir = args.h5_dir
    res_dir = args.res_dir
    topics_df_fp = args.topics_df_fp

    graphs_analysis = GraphsAnalysis(h5_dir=h5_dir, res_dir=res_dir, topics_df_fp=topics_df_fp)
    graphs_analysis.batch_summarization()
    return

if __name__=="__main__":
    main()
