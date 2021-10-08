# import from plugins/umap_view.py
"""Show how to write a custom dimension reduction view."""

from phy import IPlugin, Bunch, connect
from phy.cluster.views import ScatterView


class WaveformUMAPView(ScatterView):
    """Every view corresponds to a unique view class, so we need to subclass ScatterView."""
    pass

class WaveformUMAPPluginComplete(IPlugin):
    '''
    This version of umap cluster plugin takes longer to run (exectues on all
    spikes) execpt that its extremely helpful for drawing a lasso to split a
    cluster. More helpful than the quicker view.
    '''

    def __init__(self, n_neighbors=15, spike_count=None, batch_size=50):
        self.n_neighbors = n_neighbors
        self.spike_count = spike_count
        self.batch_size = 50

    @staticmethod
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

    def attach_to_controller(self, controller):
        #                                                                 
        #                        ,---.|                   o|    |         
        #                        |---||    ,---.,---.,---..|--- |---.,-.-.
        #                        |   ||    |   ||   ||    ||    |   || | |
        #                        `   '`---'`---|`---'`    ``---'`   '` ' '
        #                                  `---'                          
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
            spike_ids = controller.selector(self.spike_count, cluster_ids, self.batch_size)

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
            pos = WaveformUMAPPluginComplete.umapfunc(data, n_neighbors=self.n_neighbors)
            return Bunch(pos=pos, spike_ids=spike_ids, spike_clusters=spike_clusters)
        #                              o          
        #                        .    ,.,---.. . .
        #                         \  / ||---'| | |
        #                          `'  ``---'`-'-'
        #                                         
        def create_view():
            """Create and return a histogram view."""
            return WaveformUMAPView(coords=controller.context.cache(coordscomplete))

        # Maps a view name to a function that returns a view
        # when called with no argument.
        controller.view_creator['WaveformUMAPCompleteView'] = create_view

        #                                  |    o               
        #                        ,---.,---.|--- .,---.,---.,---.
        #                        ,---||    |    ||   ||   |`---.
        #                        `---^`---'`---'``---'`   '`---'
        #                                                       
        @connect(event='add_view')
        def on_gui_ready(sender, gui):
            import sys
            # Add a separator at the end of the File menu.
            # Note: currently, there is no way to add actions at another position in the menu.
            view = gui.views[-1]
            view_action = gui.actions[-1]


            print(f"View added {str(view)}", file=sys.stderr)
            if not isinstance(view, WaveformUMAPView):
                return

            @view_action.add(shortcut='ctrl+u',view=view, prompt=True)  # the keyboard shortcut is A
            def change_neighbors(n_neighbors):

                self.n_neighbors = n_neighbors

                gui.status_message = "UMAP: changed the number of neighbors"

            @view_action.add(shortcut='ctrl+U',view=view, prompt=True)  # the keyboard shortcut is A
            def change_spike_count(spike_count):

                if spike_count <= 0:
                    spike_count = None

                self.spike_count = spike_count
                gui.status_message = f"UMAP: changed the number of spikes to {spike_count}"

            @view_action.add(shortcut='ctrl+B',view=view, prompt=True)  # the keyboard shortcut is A
            def change_spike_count(batch_size):

                if batch_size <= 0:
                    batch_size = None

                self.batch_size = batch_size
                gui.status_message = f"UMAP: changed the batch size to {batch_size}"


    def cache_all_clusters():
        ''' Function that caches all clusters '''
        pass
