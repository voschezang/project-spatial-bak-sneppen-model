    
    def area_curve(self, sampling_scheme='quadrats'):
        # sampling_scheme = ['nested'|'quadrats']
        fig, ax = plt.subplots()

        if sampling_scheme == 'nested':
            area_curve = np.empty((self.dimensions[0],2))
            for s in range(1, self.dimensions[0]+1):
                species = set()
                for i in range(0, s):
                    for j in range(0, s):
                        species = species.union(self[(i,j)].species())

                nr = len(species)
                print(np.sum(self.nr_species()[range(0,s)][:,range(0,s)]), nr)
                #selection = nr[range(0,s)][:,range(0,s)]
                area_curve[s-1] = (s**2, nr)
                print(area_curve)
                ax.plot(*area_curve.T, "o")

        elif sampling_scheme == 'quadrats':
            area_curve = collections.OrderedDict()
            for grain_size in range(1, max(self.dimensions)+1):
                assert self.dimensions[0] == self.dimensions[1]
                means = []
                for interval_i in range(0, self.dimensions[0], grain_size):
                    for interval_j in range(0, self.dimensions[1], grain_size):
                        species = set()
                        for i,j in np.ndindex((grain_size,grain_size)):
                            ii = interval_i * grain_size + i
                            jj = interval_j * grain_size + j
                            species = species.union(self[(i,j)].species())

                        means.append(len(species))

                area_curve[grain_size] = np.mean(means)
                print('grain size: %i, mean: %0.3f', (grain_size, np.mean(means)))
            ax.scatter(list(area_curve.keys()), list(area_curve.values()))
