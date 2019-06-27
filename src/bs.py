import numpy as np
import networkx as nx


class Avalanches:
    # Data collector
    def __init__(self):
        self._trace = []
        self.time_trace = [0]
        self.min_fitness = 0
        self.size = -1

    def update(self, fitness):
        if fitness < self.min_fitness:
            self.size += 1
            self.time_trace[-1] += 1
        else:
            self._trace.append(self.size)
            self.time_trace.append(0)
            self.min_fitness = fitness
            self.size = 1

    @property
    def trace(self):
        # never return the first element
        return self._trace[1:]


class BS:
    def __init__(self, N, network, random_relations=False, species_ids=None, fitnesses=None):
        """ Bak-Sneppen Model
        g: graph of the co-evolution dependencies
        network: type of graph
        """
        self.network = network
        self.avalanches = Avalanches()
        # create graph
        if network[0] == "watts-strogatz":
            (_, k, p) = network
            self.g = nx.watts_strogatz_graph(N, k, p)
            if species_ids is None:
                species_ids = range(N)
            if fitnesses is None:
                fitnesses = np.random.random(N)
            if random_relations:
                random_indices = np.random.permutation(N)
                species_ids = species_ids[random_indices]
                fitnesses = fitnesses[random_indices]
            for node in self.g:
                self[node]["id"] = species_ids[node]
                self[node]["fitness"] = fitnesses[node]

        else:
            raise ValueError("Unknown network type")

    def update(self, node_id, new_species_id, fitness=None):
        if fitness is None:
            fitness = np.random.random()
        self[node_id]["fitness"] = fitness
        self[node_id]["id"] = new_species_id
        self.avalanches.update(fitness)

    @property
    def N(self):
        return self.g.number_of_nodes()

    def __getitem__(self, i):
        return self.g.node[i]

    @property
    def species(self):
        return self.g.nodes.data("id")

    @property
    def species_list(self):
        return [i for _, i in self.species]

    def fitness(self):
        return self.g.nodes.data("fitness")

    def fitness_array(self):
        return np.array([f for _, f in self.fitness()])

    def min_fitness(self):
        return min(self.fitness(), key=lambda x: x[1])

    def max_fitness(self):
        return max(self.fitness(), key=lambda x: x[1])

    def sorted_fitness(self):
        return sorted(self.fitness(), key=lambda x: x[1])

    def contains(self, species_id) -> bool:
        return species_id in self.species_list
