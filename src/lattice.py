import numpy as np
import matplotlib.pyplot as plt
import networkx as nx
import collections
from src.bs import Avalanches, BS


def interpolate(a=[], b=[], amt=0.5):
    """ Linear interpolation for each dimension i in a,b
    a,b: array-like or float
    """
    return (1 - amt) * a + amt * b


class Iterator:
    # Generate species identifiers (index values/keys)
    def __init__(self, start=0):
        self._next = start

    def get_next(self):
        # Return next identifier value and update internal state
        self._next += 1
        return self._next - 1


class Lattice:
    def __init__(self, dimensions, N, network, P, fitness_correlation=1, migration_bias=1):
        """
        dimension: shape of lattice, e.g. N x N
        P: probability of mutation (Bernoulli trial)
            success -> mutation (replacement by new species)
            fail -> migration (replacement by a species originating from neighbourhood)
        fitness_correlation: float in [0,1]
            Parameter that controls fitness after migration.
            Low values randomize the fitness and high values maintain the previous fitness.
        migration_bias: float in [-1,1]
            Parameter to control the influence of fitness on migration.
             0: fitness has no influence on migration.
            -1: least fit have priority.
            +1: fittest species have priority.
        """
        self.data = None
        self.N_species = N
        self.dimensions = dimensions
        self.P = P
        self.identifier_iter = Iterator(start=np.prod(dimensions) * N)
        self.fitness_correlation = fitness_correlation
        self.migration_bias = migration_bias
        # create lattice
        self.lattice = nx.grid_graph(list(dimensions), periodic=True)
        self.avalanches = Avalanches()
        # create BS network in each point of the lattice
        for (i, point) in enumerate(self.lattice):
            self.lattice.node[point]["BS"] = BS(
                N, network, species_ids=range(N * i, N * (i + 1)), fitnesses=None)

    def __getitem__(self, i):
        return self.lattice.node[i]["BS"]

    @property
    def N(self):
        return self.lattice.number_of_nodes()

    def run(self, t_max: int, collect_data=False):
        if collect_data:
            self.data = np.empty((t_max + 1,) + self.dimensions, dtype=object)
            for i, j in np.ndindex(self.dimensions):
                self.data[0, i, j] = set(self[i, j].species_list)

        for t in range(1, t_max + 1):
            self.run_step(t, collect_data)

    def run_step(self, t, collect_data):
        # Randomize update order to reduce iteration-order side effects
        global_fitness = 1
        for i, j in np.random.permutation(self.lattice):
            # select node with lowest fitness
            bs = self[i, j]
            lattice_neighbours = list(self.lattice[i, j])
            idx, fitness = bs.min_fitness()
            node_indices = [idx] + list(bs.g[idx])

            bs.avalanches.update(fitness)

            # apply mutation-migration step for each node
            for node_id in node_indices:
                if np.random.random() < self.P:
                    self.mutate(bs, node_id)
                else:
                    self.migrate(bs, node_id, lattice_neighbours)

            if collect_data:
                self.data[t, i, j] = set(bs.species_list)

            global_fitness = min(fitness, global_fitness)
        if t > 2:
            self.avalanches.update(fitness)

    def mutate(self, bs, node_id):
        bs.update(node_id, self.identifier_iter.get_next())

    def migrate(self, bs, node_id, lattice_neighbours=[]):
        # select a random neighbour as migration source
        bs_source = self[lattice_neighbours[np.random.randint(
            0, len(lattice_neighbours))]]
        source_nodes = bs_source.g
        if self.migration_bias != 0:
            nodes = bs_source.g.nodes
            # sort based on fitness
            reverse = self.migration_bias > 0
            nodes = bs_source.g.nodes
            source_nodes = sorted(source_nodes,
                                  key=lambda node_i: nodes[node_i]['fitness'],
                                  reverse=reverse)
        else:
            # select all source species
            source_nodes = np.random.permutation(source_nodes)

        target_species_ids = set(bs.species_list)
        # iterate randomly over selection
        for source_node_id in source_nodes:
            species_id = bs_source[source_node_id]["id"]
            # let the species migrate from source to target bs
            if species_id not in target_species_ids:
                # migrate and stop searching
                fitness_new = interpolate(bs_source[source_node_id]["fitness"],
                                          np.random.random(),
                                          amt=1 - self.fitness_correlation)
                bs.update(node_id, species_id, fitness=fitness_new)
                return

        print("Migration failed from {} to {}".format(
            bs_source.species, bs.species))
        self.mutate(bs, node_id)

    def draw(self):
        nx.draw(self.lattice, with_labels=True)

    def mean_species(self):
        ids = set()
        for point in self.lattice:
            ids = ids.union(self[point].species_list)
        return len(ids) / np.prod(self.dimensions)

    def fitness_stats(self):
        fitness = self.avg_fitness_per_point()
        return np.mean(fitness), np.std(fitness)

    def avg_fitness(self):
        # avg of avg fitness per point
        fitness = self.avg_fitness_per_point()
        return np.mean(fitness)

    def avg_fitness_per_point(self):
        return [self[point].fitness_array().mean() for point in self.lattice]

    def area_curve(self, log=True, plot_bool=True, ax=None, v=0):
        """ Compute and plot the species-area curve
        """
        area_curve = collections.OrderedDict()
        sd = []
        for grain_size in range(1, max(self.dimensions) + 1):
            assert self.dimensions[0] == self.dimensions[1]
            means = []
            i = 0
            for interval_i in range(0, self.dimensions[0] - grain_size + 1):
                for interval_j in range(0, self.dimensions[1] - grain_size + 1):
                    species = set()
                    for i, j in np.ndindex((grain_size, grain_size)):
                        ii = interval_i + i
                        jj = interval_j + j
                        species = species.union(self[ii, jj].species_list)
                        i += 1

                    means.append(len(species))

            area_curve[grain_size**2] = np.mean(means)

            sd.append(np.std(means) * 1.96 / np.sqrt(i))
            if plot_bool and v > 0:
                print('grain size: %i, mean: %0.3f' %
                      (grain_size, np.mean(means)))

        X = np.log10(np.array([list(area_curve.keys())])).T[2:]
        y = (np.log10(
            np.array([list(area_curve.values())])).T - np.log10(self.N_species))[2:]
        power, res = np.linalg.lstsq(X, y)[0:2]
        res = np.mean(res)

        if plot_bool:
            if ax is None:
                fig, ax = plt.subplots()
            ax.errorbar(list(area_curve.keys()), list(
                area_curve.values()), yerr=sd, fmt="x", capsize=2)
            ax.plot()
            ax.plot(list(area_curve.keys()), (self.N_species * np.array(
                list(area_curve.keys()))**power)[0], color='red', linestyle='dashed')
            ax.set_xlabel("Area")
            ax.set_ylabel("Number of species")

            if log:
                ax.set_xscale("log")
                ax.set_yscale("log")
            plt.margins(0)

        print("power: {}, MSE: {}".format(round(power[0][0], 3), res))
        return power[0][0], res

    def avg_n_species(self, grain_size: int, species=None):
        # Compute mean, std number of species per area using "quadrats" sampling scheme
        means = []
        i = 0
        for interval_i in range(0, self.dimensions[0] - grain_size + 1):
            for interval_j in range(0, self.dimensions[1] - grain_size + 1):
                unique_species = set()
                for i, j in np.ndindex((grain_size, grain_size)):
                    ii = interval_i + i
                    jj = interval_j + j
                    if species is None:
                        unique_species = unique_species.union(
                            self[ii, jj].species_list)
                    else:
                        unique_species = unique_species.union(species[ii, jj])
                    i += 1

                means.append(len(unique_species))

        mean = np.mean(means)
        std = np.std(means) * 1.96 / np.sqrt(i)
        return mean, std
