# Extension that adds mountainsort cluster metrics to PHY for curation
#
# Installation:
# Add this file to ~/.phy/plugins/
#
# Then open ~/.phy/phy_config.py and add this line:
# c.TemplateGUI.plugins = ['MSCurationTagsPlugin']

import numpy as np
from phy import IPlugin
import json
import os
import pandas as pd

class MSCurationTagsPlugin(IPlugin):
    '''
    Adds mountainsort curation tags statically to phy
    table at the beginning of execution.

    TODO
    ----
    Dynamically recompute metrics when clusters merge or split
    '''

    def __init__(self, remove_redundant_labels=True, ryan_preferred=True):
        self.remove_redundant_labels = remove_redundant_labels
        self.ryan_preferred = ryan_preferred

    def attach_to_controller(self, controller):
        """Note that this function is called at initialization time, *before*
        the supervisor is created. The `controller.cluster_metrics` items are
        then passed to the supervisor when constructing it."""

        self.get_metric_table(controller=controller)
        metrics = self.list_metric_names(remove_redundant_labels=self.remove_redundant_labels, ryan_preferred=self.ryan_preferred)
        metrics = self.order_metric_names(metrics)
        # Use this dictionary to define custom cluster metrics.  We memcache
        # the function so that cluster metrics are only computed once and saved
        # within the session, and also between sessions (the memcached values
        # are also saved on disk).
        for metric in metrics:
            #controller.cluster_metrics[metric] = \
            #    controller.context.memcache(get_cluster_lambda(metric, obj=self.df))
            controller.cluster_metrics[('ms\n' + metric).replace('_','\n')] = \
                self.get_cluster_lambda(metric)

    def get_metric_table(self, json_filename=None, controller=None,
                         adjust_index_by_order=True):
        '''
        Parse a json to obtain cluster metric table
        '''

        if json_filename is None:
            # If no json, look a folder above for the metrics_tagged file
            directory = os.path.expanduser(controller.dir_path)
            directory = os.path.split(directory)[:-1]
            directory = os.path.join(*directory)
            json_filename =  os.path.join(directory, "metrics_tagged.json")
        if not os.path.exists(json_filename):
            raise FileExistsError(f"{json_filename} does not exist!")

        with open(json_filename,'r') as F:
            J = json.load(F)

        clusters = J['clusters']

        df = pd.DataFrame()
        for i, elem in enumerate(clusters):

            label = elem['label']
            metrics = pd.DataFrame.from_dict(elem['metrics'], orient='index').T
            metrics.index = pd.Index([label], name='id')
            if len(elem['tags']) == 0:
                tags = ''
            else:
                tags = str(elem['tags'] if len(elem['tags'])!=1 else elem['tags'][0])
            metrics = metrics.assign(tags=tags)

            if i > 0:
                df = df.append(metrics)
            else:
                df = metrics

        if adjust_index_by_order:

            df.sort_index(inplace=True)
            old_index = df.index
            new_index = tuple(pd.Index(range(df.shape[0]),
                              name="label"))
            lookup = pd.Series(index=old_index, data=new_index)
            lookup.loc[0] = -1
            df.loc[:, 'overlap_cluster'] = lookup.loc[df.overlap_cluster.astype('int')].values
            df.loc[:, 'bursting_parent'] = lookup.loc[df.bursting_parent.astype('int')].values
            df.index = new_index

        self.df = df

    def get_cluster_metric(self, cluster_id:int, metric:str, obj=None):
        '''
        Obtain a metric at a cluster id
        '''

        if cluster_id in self.df.index:
            return self.df.loc[cluster_id][metric]
        else:
            return np.nan


    def get_cluster_lambda(self, metric:str):
        '''
        reeturna  lambda function that reports the value of a metric for a cluster id
        '''

        df = self.df[metric]

        def func(cluster_id, df=df):
            if cluster_id in df.index:
                return df.loc[cluster_id]
            else:
                # TODO, if not found, then reccompute cluster metrics; user may
                # have merged or split a cluster
                return np.nan
        return func

    def list_metric_names(self, remove_redundant_labels=False, ryan_preferred=False):
        metric_list = list(self.df.columns)
        if remove_redundant_labels:
            rlabels = ["num_events", "peak_amp", "firing_rate"]
            metric_list = [metric for metric in metric_list
                           if metric not in rlabels]
        if remove_redundant_labels:
            rlabels = ["num_events","peak_amp","firing_rate", "t1_sec", "t2_sec", "dur_sec"]
            metric_list = [metric for metric in metric_list
                           if metric not in rlabels]
        return metric_list

    def order_metric_names(self, metric_list):
        """
        This function merely imbues an order to the list of metrics
        based on which I find most important to my clustering.
        """

        order = ["isolation", "peak_snr", "noise_overlap",
                 "overalap_cluster", "bursting_parent", "tags"]
        order = np.array(order)
        mapnames = {name:np.where(order == name)[0] if name in order else np.nan
                   for name in metric_list}
        metric_list = sorted(metric_list, 
                             key=lambda x: mapnames[x])
        return metric_list

class TetrodeMetrics(IPlugin):
    '''
    Remove metrics from phy that I find useless for tetrodes
    '''
    from phy import IPlugin
    pass

class MSCurationSave(IPlugin):
    '''
    Whenever a save event is emitted, save the state of the cluster
    tags to mountainsort files
    '''
    from phy import IPlugin
    pass
