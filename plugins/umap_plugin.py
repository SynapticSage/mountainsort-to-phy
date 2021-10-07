# import from plugins/umap_view.py
"""Show how to write a custom dimension reduction view."""

from phy import IPlugin, Bunch
from phy.cluster.views import ScatterView


def umapfunc(x, doGPU=True, **kws):
    """Perform the dimension reduction of the array x."""
    import sys

    # Attempt to grab the GPU version
    if doGPU:
        try:
            print("Trying GPU", file=sys.stderr)
            from cuml.manifold.umap import UMAP
        except ImportError:
            print("Using CPU", file=sys.stderr)
            from umap import UMAP
    else:
        from umap import UMAP

    return UMAP(**kws).fit_transform(x)

class WaveformUMAPView(ScatterView):
    """Every view corresponds to a unique view class, so we need to subclass ScatterView."""
    pass

class WaveformUMAPPlugin(IPlugin):
    def attach_to_controller(self, controller):
        def coords(cluster_ids):
            """Must return a Bunch object with pos, spike_ids, spike_clusters."""
            # We select 200 spikes from the selected clusters, using a batch size of 50 spikes.
            # WARNING: lasso and split will work but will *only split the shown subselection* of
            # spikes. You should use the `load_all` keyword argument to `coords()` to load all
            # spikes before computing the spikes inside the lasso, however (1) this could be
            # prohibitely long with UMAP, and (2) the coordinates will change when reperforming
            # the dimension reduction on all spikes, so the splitting would be meaningless anyway.
            # A warning is displayed when trying to split on a view that does not accept the
            # `load_all` keyword argument, because it means that all relevant spikes (even not
            # shown ones) are not going to be split.
            spike_ids = controller.selector(200, cluster_ids, 50)
            # We get the cluster ids corresponding to the chosen spikes.
            spike_clusters = controller.supervisor.clustering.spike_clusters[spike_ids]
            # We get the waveforms of the spikes, across all channels so that we use the
            # same dimensions for every cluster.
            data = controller.model.get_waveforms(spike_ids, None)
            # We reshape the array as a 2D array so that we can pass it to the t-SNE algorithm.
            (n_spikes, n_samples, n_channels) = data.shape
            data = data.transpose((0, 2, 1))  # get an (n_spikes, n_channels, n_samples) array
            data = data.reshape((n_spikes, n_samples * n_channels))
            # We perform the dimension reduction.
            pos = umapfunc(data, n_neighbors=20)
            return Bunch(pos=pos, spike_ids=spike_ids, spike_clusters=spike_clusters)

        def create_view():
            """Create and return a histogram view."""
            return WaveformUMAPView(coords=controller.context.cache(coords))

        # Maps a view name to a function that returns a view
        # when called with no argument.
        controller.view_creator['WaveformUMAPView'] = create_view


class WaveformUMAPPluginComplete(IPlugin):
    '''
    This version of umap cluster plugin takes longer to run (exectues on all
    spikes) execpt that its extremely helpful for drawing a lasso to split a
    cluster. More helpful than the quicker view.
    '''
    def attach_to_controller(self, controller):
        def coordscomplete(cluster_ids):
            """Must return a Bunch object with pos, spike_ids, spike_clusters."""
            # We select 200 spikes from the selected clusters, using a batch size of 50 spikes.
            # WARNING: lasso and split will work but will *only split the shown subselection* of
            # spikes. You should use the `load_all` keyword argument to `coords()` to load all
            # spikes before computing the spikes inside the lasso, however (1) this could be
            # prohibitely long with UMAP, and (2) the coordinates will change when reperforming
            # the dimension reduction on all spikes, so the splitting would be meaningless anyway.
            # A warning is displayed when trying to split on a view that does not accept the
            # `load_all` keyword argument, because it means that all relevant spikes (even not
            # shown ones) are not going to be split.    
            spike_ids = controller.selector(None, cluster_ids, 50)
            # We get the cluster ids corresponding to the chosen spikes.
            spike_clusters = controller.supervisor.clustering.spike_clusters[spike_ids]
            # We get the waveforms of the spikes, across all channels so that we use the
            # same dimensions for every cluster.
            data = controller.model.get_waveforms(spike_ids, None)
            # We reshape the array as a 2D array so that we can pass it to the t-SNE algorithm.
            (n_spikes, n_samples, n_channels) = data.shape
            data = data.transpose((0, 2, 1))  # get an (n_spikes, n_channels, n_samples) array
            data = data.reshape((n_spikes, n_samples * n_channels))
            # We perform the dimension reduction.
            pos = umapfunc(data, n_neighbors=15)
            return Bunch(pos=pos, spike_ids=spike_ids, spike_clusters=spike_clusters)

        def create_view():
            """Create and return a histogram view."""
            return WaveformUMAPView(coords=controller.context.cache(coordscomplete))

        # Maps a view name to a function that returns a view
        # when called with no argument.
        controller.view_creator['WaveformUMAPCompleteView'] = create_view

    def cache_all_clusters():
        ''' Function that caches all clusters '''
        pass
