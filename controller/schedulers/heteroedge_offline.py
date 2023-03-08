import networkx as nx
import random

# input: no. of jobs, no. of tasks, cost for each task on each executor
# output: edge_list
def get_edge_list(jobs, executors, tasks, task_executor_cost):
    edge_list = []
    for index, task in enumerate(tasks):
        for executor_id in executors:
            node = f'{task}-e{executor_id}'
            if index == 0:
                for job_id in range(jobs):
                    # create a new start node
                    job_start_node = f"s{job_id}"
                    edge_list.append((job_start_node, node, 0))
            if index == len(tasks) - 1:
                edge_list.append((node, 't', task_executor_cost[(task, executor_id)]))
            else:
                for next_exec_id in executors:
                    next_task = tasks[index+1]
                    next_node = f'{next_task}-e{next_exec_id}'
                    edge_list.append((node, next_node, task_executor_cost[(task, executor_id)]))

    return edge_list

def get_edge_weight(g, edge):
    for u, v, w in g.edges.data('weight'):
        if u == edge[0] and v == edge[1]:
            return w

# # TODO change
def decompose(supply_chain_graph):
    return supply_chain_graph

def get_link_capacity(edge):
    if edge[0].startswith("s"):
        return 1
    else:
        executor = edge[0].split("-")[1]
        # no. of cpu(s) from lscpu
        executor_lcap = {
            "e0": 4, # nano
            "e1": 4, # rpi3
            "e2": 4, # rpi3
            "e3": 4, # rpi4
            "e4": 4,
            "e5": 4,
            "e6": 4,
            "e7": 4,
            "e8": 6, # tx2
            "e9": 8, #server
        }
        return executor_lcap[executor]

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
# def get_weighted_congestion_rate(supply_chain_paths, edge):
#     jobs_with_edge = get_jobs_with_edge(supply_chain_paths, edge)
#     weighted_congestion_rate = 0
#     for job_id in jobs_with_edge:
#         # TODO check
#         l_cap = 1
#         weighted_congestion_rate += (get_job_weight(job_id) - l_cap + 1)
#     return weighted_congestion_rate


def utility(supply_chain_path, supply_chain_paths):
    utility = 0
    edges = [(supply_chain_path[i], supply_chain_path[i+1]) for i in range(len(supply_chain_path)-1)]
    for edge in edges:
        for job_id in get_jobs_with_edge(supply_chain_paths, edge):
            # l_cap = 1
            l_cap = get_link_capacity(edge)
            # print(f'lcap of edge {edge} = {l_cap}')
            utility += (get_job_weight(job_id) - l_cap + 1) * get_edge_weight(graph, edge)
    print(f'utility of {supply_chain_path} = {utility}')
    return utility

def scsr(supply_chain_graph, epsilon, job_list):
    """
        epsilon: e-Nash equilibrium
    """
    decomposed_graph = decompose(supply_chain_graph)
    converge = False

    supply_chain_paths = [] # this is P
    supply_chain_paths_dash = [] # this is P'

    # assign a random path (strategy)
    for i, job in enumerate(job_list):
        all_paths_from_si = list(nx.all_simple_paths(decomposed_graph, source=f's{i}', target='t'))

        supply_chain_paths.append(random.choice(all_paths_from_si))
        supply_chain_paths_dash.append(supply_chain_paths[i])

    # supply_chain_paths = [['s0', 't9-e0', 't19-e1', 't'], ['s1', 't9-e1', 't19-e1', 't']]
    # supply_chain_paths_dash = [['s0', 't9-e0', 't19-e1', 't'], ['s1', 't9-e1', 't19-e1', 't']]
    print(supply_chain_paths)
    while not converge:
        for i, job in enumerate(job_list):
            shortest_path = nx.dijkstra_path(decomposed_graph, source=f"s{i}", target="t")
            print(f'i={i}, shortest_path ={shortest_path}')
            if utility(shortest_path, supply_chain_paths) - utility(supply_chain_paths[i], supply_chain_paths) > epsilon:
                print("updated!")
                supply_chain_paths_dash[i] = shortest_path

        if supply_chain_paths_dash == supply_chain_paths:
            return supply_chain_paths

        supply_chain_paths = supply_chain_paths_dash


graph = nx.DiGraph()
# TODO set lambda param
lambda_param = 1
# we're considering only 2 jobs (s0, s1), two executors (e0, e1) and two tasks (t9 and t19)
# edge weight = energy cost + lambda_param * delay cost
# s0 => source location that supply the raw sensing data decided by the social sensing applications
# TODO: check what to do with GPU worker?
# READ THIS FIRST: for each job Ji, there is a supply chain graph starting at si (s0, s1, s2,..)
# the objective is to find P = P0, P1, ..., which are the supply chain paths (optimal paths)
# P0 -> optimal path for J0 that optimizes both delay and energy
# edge_list = [('s0', 't9-e0', 0 + lambda_param * 0),
#              ('s0', 't9-e1', 0 + lambda_param * 0),
#
#              ('s1', 't9-e0', 0 + lambda_param * 0),
#              ('s1', 't9-e1', 0 + lambda_param * 0),
#
#              ('t9-e0', 't19-e0', 2.11 + lambda_param * 1895.67),  # energy for executing t9 on executor 0, delay for executing t9
#              ('t9-e0', 't19-e1', 2.11 + lambda_param * 1895.67),
#
#              ('t9-e1', 't19-e0', 4.19 + lambda_param * 4211.45),
#              ('t9-e1', 't19-e1', 4.19 + lambda_param * 4211.45),
#
#              ('t19-e0', 't', 4.20 + lambda_param * 18106.84),
#              ('t19-e1', 't', 112.43 + lambda_param * 114523.86)]
#
# edge_list_2 = [('s0', 't9-e0', 0 + lambda_param * 0),
#
#              ('s1', 't9-e1', 0 + lambda_param * 0),
#
#              ('t9-e0', 't19-e0', 5),  # energy for executing t9 on executor 0, delay for executing t9
#              ('t9-e0', 't19-e1', 200),
#
#              ('t9-e1', 't19-e0', 100),
#              ('t9-e1', 't19-e1', 5),
#
#              ('t19-e0', 't', 5),
#              ('t19-e1', 't', 5)]

jobs = 2
executors = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
# executors = [0, 1]
tasks = ["t9", "t19", "t29"]
# tasks = ["t9", "t19"]
task_executor_cost = {
    ("t9",0): 2.11 + lambda_param * 1895.67,
    ("t9",1): 4.19 + lambda_param * 4211.45,
    ("t9",2): 4.19 + lambda_param * 4211.45,
    ("t9",3): 3.82 + lambda_param * 2793.96,
    ("t9",4): 3.82 + lambda_param * 2793.96,
    ("t9",5): 3.82 + lambda_param * 2793.96,
    ("t9",6): 3.82 + lambda_param * 2793.96,
    ("t9",7): 3.82 + lambda_param * 2793.96,
    ("t9",8): 4.92 + lambda_param * 1812.70,
    ("t9",9): 24.97 + lambda_param * 655.23,

    ("t19",0): 4.20 + lambda_param * 18106.84,
    ("t19",1): 112.43 + lambda_param * 114523.86,
    ("t19",2): 112.43 + lambda_param * 114523.86,
    ("t19",3): 98.28 + lambda_param * 88838.08,
    ("t19",4): 98.28 + lambda_param * 88838.08,
    ("t19",5): 98.28 + lambda_param * 88838.08,
    ("t19",6): 98.28 + lambda_param * 88838.08,
    ("t19",7): 98.28 + lambda_param * 88838.08,
    ("t19",8): 10.01 + lambda_param * 4389.75,
    ("t19",9): 166.54 + lambda_param * 5141.28,

    ("t29",0): 0.29 + lambda_param * 8790.52,
    ("t29",1): 1.02 + lambda_param * 8849.62,
    ("t29",2): 1.02 + lambda_param * 8849.62,
    ("t29",3): 2.28 + lambda_param * 5213.41,
    ("t29",4): 2.28 + lambda_param * 5213.41,
    ("t29",5): 2.28 + lambda_param * 5213.41,
    ("t29",6): 2.28 + lambda_param * 5213.41,
    ("t29",7): 2.28 + lambda_param * 5213.41,
    ("t29",8): 0.76 + lambda_param * 2129.78,
    ("t29",9): 6.68 + lambda_param * 2846.57,
}

import pprint
pprint.pprint(task_executor_cost)

edge_list = get_edge_list(jobs, executors, tasks, task_executor_cost)
print(edge_list)
print(len(edge_list))
graph.add_weighted_edges_from(edge_list)

epsilon = 1
print(scsr(graph, epsilon, range(jobs)))

