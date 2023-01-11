import networkx as nx
import random

# print(nx.dijkstra_path(G, source="s0", target="t"))

# TODO change
def path_lists_equal(path_list_1, path_list_2):
    return False

# # TODO change
def decompose(supply_chain_graph):
    return supply_chain_graph

# TODO return a weight proportional to the size of the raw sensing data
def get_job_weight(job_id):
    return 10

# each edge is defined as a tuple of two vertices
# d(l), where l is an edge
# output: [job-ids]
def get_jobs_with_edge(edge):
    pass

# N(l), where l is an edge
def get_weighted_congestion_rate(edge):
    pass

def utility(path, job_id):
    for
        get_job_weight(job_id) -

def scsr(supply_chain_graph, epsilon, job_list):
    decomposed_graph = decompose(supply_chain_graph)
    converge = False

    all_paths = []
    for i, job in enumerate(job_list):
        curr_job_paths = list(nx.all_simple_paths(decomposed_graph, source=f's{i}', target='t'))
        if len(all_paths) == 0:
            all_paths = curr_job_paths
        else:
            all_paths.append(curr_job_paths)

    print(all_paths)

    supply_chain_paths = [] * len(job_list)
    supply_chain_paths_dash = [] * len(job_list)

    for i, job in enumerate(job_list):
        # assign a random path
        supply_chain_paths[i] = random.choice(all_paths)
        supply_chain_paths_dash[i] = supply_chain_paths[i]

    while not converge:
        for i, job in enumerate(job_list):
            shortest_path = nx.dijkstra_path(decomposed_graph, source=f"s{i}", target="t")
            if utility(shortest_path) - utility(supply_chain_paths[i]) > epsilon:
                supply_chain_paths_dash[i] = shortest_path

        if path_lists_equal(supply_chain_paths, supply_chain_paths_dash):
            return supply_chain_paths

        supply_chain_paths = supply_chain_paths_dash

graph = nx.DiGraph()
# TODO set lambda param
lambda_param = 2
# we're considering only 2 jobs (s0, s1), two executors (e0, e1) and two tasks (t9 and t19)
# edge weight = energy cost + lambda_param * delay cost
# s0 => source location that supply the raw sensing data decided by the social sensing applications
edge_list = [('s0', 't9-e0', 0 + lambda_param * 0),
             ('s0', 't9-e1', 0 + lambda_param * 0),

             ('s1', 't9-e0', 0 + lambda_param * 0),
             ('s1', 't9-e1', 0 + lambda_param * 0),

             ('t9-e0', 't19-e0', 2.11 + lambda_param * 1895.67),  # energy for executing t9 on executor 0, delay for executing t9
             ('t9-e0', 't19-e1', 2.11 + lambda_param * 1895.67),

             ('t9-e1', 't19-e0', 4.19 + lambda_param * 4211.45),
             ('t9-e1', 't19-e1', 4.19 + lambda_param * 4211.45),

             ('t19-e0', 't', 4.20 + lambda_param * 18106.84),
             ('t19-e0', 't', 4.20 + lambda_param * 18106.84),

             ('t19-e1', 't', 112.43 + lambda_param * 114523.86),
             ('t19-e1', 't', 112.43 + lambda_param * 114523.86)]
graph.add_weighted_edges_from(edge_list)
# result -> [s0, ]
scsr(graph, 0, [0,1])

