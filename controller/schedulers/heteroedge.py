import networkx as nx
import random

def get_edge_weight(g, edge):
    for u, v, w in g.edges.data('weight'):
        if u == edge[0] and v == edge[1]:
            return w

# TODO change
def path_lists_equal(path_list_1, path_list_2):
    return False

# # TODO change
def decompose(supply_chain_graph):
    return supply_chain_graph

# TODO return a weight proportional to the size of the raw sensing data
def get_job_weight(job_id):
    return 1

# each edge is defined as a tuple of two vertices
# d(l), where l is an edge
# output: [job-ids]
def get_jobs_with_edge(supply_chain_paths, edge):
    jobs_with_edge = set()
    for job_id, supply_chain_path in enumerate(supply_chain_paths):
        edges = [(supply_chain_path[i], supply_chain_path[i+1]) for i in range(len(supply_chain_path)-1)]
        if edge in edges:
            jobs_with_edge.add(job_id)
    return list(sorted(jobs_with_edge))

# N(l), where l is an edge
def get_weighted_congestion_rate(supply_chain_paths, edge):
    jobs_with_edge = get_jobs_with_edge(supply_chain_paths, edge)
    weighted_congestion_rate = 0
    for job_id in jobs_with_edge:
        # TODO check
        l_cap = 1
        weighted_congestion_rate += (get_job_weight(job_id) - l_cap + 1)
    return weighted_congestion_rate


def utility(supply_chain_path, supply_chain_paths):
    utility = 0
    edges = [(supply_chain_path[i], supply_chain_path[i+1]) for i in range(len(supply_chain_path)-1)]
    for edge in edges:
        for job_id in get_jobs_with_edge(supply_chain_paths, edge):
            l_cap = 1
            utility += (get_job_weight(job_id) - l_cap + 1) * get_edge_weight(graph, edge)
    return utility

def scsr(supply_chain_graph, epsilon, job_list):
    """
        epsilon: e-Nash equilibrium
    """
    decomposed_graph = decompose(supply_chain_graph)
    converge = False

    supply_chain_paths = [] # this is P
    supply_chain_paths_dash = [] # this is P'

    for i, job in enumerate(job_list):
        # assign a random path (strategy)
        all_paths_from_si = list(nx.all_simple_paths(decomposed_graph, source=f's{i}', target='t'))

        supply_chain_paths.append(random.choice(all_paths_from_si))
        supply_chain_paths_dash.append(supply_chain_paths[i])

    while not converge:
        for i, job in enumerate(job_list):
            shortest_path = nx.dijkstra_path(decomposed_graph, source=f"s{i}", target="t")
            if utility(supply_chain_paths[i], supply_chain_paths) - utility(shortest_path, supply_chain_paths) > epsilon:
                supply_chain_paths_dash[i] = shortest_path

        if supply_chain_paths == supply_chain_paths_dash:
            return supply_chain_paths

        supply_chain_paths = supply_chain_paths_dash


graph = nx.DiGraph()
# TODO set lambda param
lambda_param = 0
# we're considering only 2 jobs (s0, s1), two executors (e0, e1) and two tasks (t9 and t19)
# edge weight = energy cost + lambda_param * delay cost
# s0 => source location that supply the raw sensing data decided by the social sensing applications
# TODO: check what to do with GPU worker?
# READ THIS FIRST: for each job Ji, there is a supply chain graph starting at si (s0, s1, s2,..)
# the objective is to find P = P0, P1, ..., which are the supply chain paths (optimal paths)
# P0 -> optimal path for J0 that optimizes both delay and energy
edge_list = [('s0', 't9-e0', 0 + lambda_param * 0),
             ('s0', 't9-e1', 0 + lambda_param * 0),

             ('s1', 't9-e0', 0 + lambda_param * 0),
             ('s1', 't9-e1', 0 + lambda_param * 0),

             ('t9-e0', 't19-e0', 2.11 + lambda_param * 1895.67),  # energy for executing t9 on executor 0, delay for executing t9
             ('t9-e0', 't19-e1', 2.11 + lambda_param * 1895.67),

             ('t9-e1', 't19-e0', 4.19 + lambda_param * 4211.45),
             ('t9-e1', 't19-e1', 4.19 + lambda_param * 4211.45),

             ('t19-e0', 't', 4.20 + lambda_param * 18106.84),
             ('t19-e1', 't', 112.43 + lambda_param * 114523.86)]
graph.add_weighted_edges_from(edge_list)
# result -> [s0, ]
print(scsr(graph, 0, [0,1]))

# print(list(graph.edges.data('weight')))



# print(get_edge_weight(graph, ('t9-e0', 't19-e1')))