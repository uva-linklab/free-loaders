import networkx as nx
import random
import copy

def get_edge_list(jobs,
                  executors,
                  tasks,
                  task_executor_energy,
                  task_executor_time,
                  lambda_param,
                  executor_thread_count,
                  energy_split_base_percent):
    edge_list = []
    for index, task in enumerate(tasks):
        for executor_id in executors:
            # create 3 nodes: t9-e0-base, t9-e0-thread, t9-e0-end
            base_node = f'{task}-e{executor_id}-base'
            thread_node = f'{task}-e{executor_id}-thread'
            end_node = f'{task}-e{executor_id}-end'

            # connect start and base
            if index == 0:
                for job_id in range(jobs):
                    # create a new start node
                    job_start_node = f"s{job_id}"
                    edge_list.append((job_start_node, base_node, 0))

            # connect base and thread
            base_to_thread_cost = task_executor_energy[(task, executor_id)] * energy_split_base_percent
            edge_list.append(
                (base_node,
                 thread_node,
                 base_to_thread_cost)
            )

            thread_count = executor_thread_count[executor_id]
            # connect thread to end
            thread_to_end_cost = task_executor_energy[(task, executor_id)] * (1 - energy_split_base_percent)
            thread_to_end_cost += lambda_param * task_executor_time[(task, executor_id)] # add the exec time

            for i in range(thread_count):
                edge_list.append(
                    (thread_node,
                     end_node,
                     thread_to_end_cost))

            # if last task, connect to t
            if index == len(tasks) - 1:
                edge_list.append((end_node, 't', 0))
            # if not, connect to the base of next task
            else:
                for next_exec_id in executors:
                    next_task = tasks[index+1]
                    next_base_node = f'{next_task}-e{next_exec_id}-base'
                    edge_list.append((end_node, next_base_node, 0))

    return edge_list

def get_edge_weight(g, edge):
    return g.edges[edge]['weight']

# # TODO change
def decompose(supply_chain_graph):
    return supply_chain_graph

def get_link_capacity(edge):
    if edge[0].startswith("s"):
        return 1
    else:
        node_type = edge[0].split("-")[2]
        if node_type == "base":
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
        else:
            return 1

# TODO return a weight proportional to the size of the raw sensing data
def get_job_weight(job_id):
    return 10

# each edge is defined as a tuple of two vertices
# d(l), where l is an edge
# output: [job-ids]
def get_jobs_with_edge(supply_chain_paths, edge):
    jobs_with_edge = set()
    for job_id, supply_chain_path in enumerate(supply_chain_paths):
        if edge in supply_chain_path:
            jobs_with_edge.add(job_id)
    return list(sorted(jobs_with_edge))

def get_shortest_path(graph, job_id, source, target, supply_chain_paths):
    all_paths_from_source = list(nx.all_simple_edge_paths(graph, source=source, target=target))

    shortest_path = all_paths_from_source[0]
    utility_shortest_path = utility(shortest_path, supply_chain_paths)
    for path in all_paths_from_source:
        utility_path = utility(path, supply_chain_paths)
        if utility_path < utility_shortest_path:
            shortest_path = path
            utility_shortest_path = utility_path

    return shortest_path

def utility(supply_chain_path, supply_chain_paths):
    utility = 0
    for edge in supply_chain_path:
        for job_id in get_jobs_with_edge(supply_chain_paths, edge):
            l_cap = get_link_capacity(edge)
            update_to_utility = (get_job_weight(job_id) - l_cap + 1) * get_edge_weight(graph, edge)
            utility += update_to_utility
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
        all_paths_from_si = list(nx.all_simple_edge_paths(decomposed_graph, source=f's{i}', target='t'))
        supply_chain_paths.append(random.choice(all_paths_from_si))
        supply_chain_paths_dash = copy.deepcopy(supply_chain_paths)

    while not converge:
        for i, job in enumerate(job_list):
            # shortest_path = nx.dijkstra_path(decomposed_graph, source=f"s{i}", target="t")
            # shortest_path_edges = [(shortest_path[i], shortest_path[i+1], 0) for i in range(len(shortest_path)-1)]
            supply_chain_paths_current_removed = copy.deepcopy(supply_chain_paths_dash)
            del supply_chain_paths_current_removed[i]

            shortest_path_edges = get_shortest_path(decomposed_graph,
                                                    i,
                                                    f"s{i}",
                                                    "t",
                                                    supply_chain_paths_current_removed)

            supply_chain_paths_current_removed.insert(i, shortest_path_edges)

            utility_shortest_path = utility(shortest_path_edges, supply_chain_paths_current_removed)
            utility_current_path = utility(supply_chain_paths[i], supply_chain_paths)
            if utility_current_path - utility_shortest_path > epsilon:
                supply_chain_paths_dash[i] = copy.deepcopy(shortest_path_edges)
            else:
                print(f"found a case: {utility_current_path - utility_shortest_path}")

        if supply_chain_paths_dash == supply_chain_paths:
            return supply_chain_paths

        supply_chain_paths = copy.deepcopy(supply_chain_paths_dash)

def our_scsr(supply_chain_graph, epsilon, job_list):
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
    for i in job_list:
        shortest_path = nx.dijkstra_path(supply_chain_graph, source=f"s{i}", target="t")
        shortest_path_edges = [(shortest_path[i], shortest_path[i+1], 0) for i in range(len(shortest_path)-1)]

        print(f'{shortest_path}')
        for edge in shortest_path_edges:
            if "thread" in edge[0]:
                if supply_chain_graph.number_of_edges(edge[0], edge[1]) == 1:
                    # put back the link capacity no. of edges
                    executor=edge[0].split('-')[1]
                    l_cap=executor_lcap[executor]
                    edge_weight=get_edge_weight(supply_chain_graph, edge)

                    # remove edge
                    supply_chain_graph.remove_edge(edge[0], edge[1])
                    for j in range(l_cap):
                        supply_chain_graph.add_edge(edge[0], edge[1], weight=2*edge_weight)

                    # double the edge weight of base
                    base_node_weight = get_edge_weight(supply_chain_graph, prev_edge)
                    supply_chain_graph[prev_edge[0]][prev_edge[1]][prev_edge[2]]['weight']=2*base_node_weight
                else:
                    # remove the edge from the graph
                    supply_chain_graph.remove_edge(edge[0], edge[1])
            prev_edge = copy.deepcopy(edge)

# we're considering only 2 jobs (s0, s1), two executors (e0, e1) and two tasks (t9 and t19)
# edge weight = energy cost + lambda_param * delay cost
# s0 => source location that supply the raw sensing data decided by the social sensing applications
# TODO: check what to do with GPU worker?
# READ THIS FIRST: for each job Ji, there is a supply chain graph starting at si (s0, s1, s2,..)
# the objective is to find P = P0, P1, ..., which are the supply chain paths (optimal paths)
# P0 -> optimal path for J0 that optimizes both delay and energy
random.seed(993123129)
jobs = 10
executors = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
tasks = ["t9","t19","t29"]
task_executor_energy = {
    ("t9",0): 2.11,
    ("t9",1): 4.19,
    ("t9",2): 4.19,
    ("t9",3): 3.82,
    ("t9",4): 3.82,
    ("t9",5): 3.82,
    ("t9",6): 3.82,
    ("t9",7): 3.82,
    ("t9",8): 4.92,
    ("t9",9): 24.97,

    ("t19",0): 4.20,
    ("t19",1): 112.43,
    ("t19",2): 112.43,
    ("t19",3): 98.28,
    ("t19",4): 98.28,
    ("t19",5): 98.28,
    ("t19",6): 98.28,
    ("t19",7): 98.28,
    ("t19",8): 10.01,
    ("t19",9): 166.54,

    ("t29",0): 0.29,
    ("t29",1): 1.02,
    ("t29",2): 1.02,
    ("t29",3): 2.28,
    ("t29",4): 2.28,
    ("t29",5): 2.28,
    ("t29",6): 2.28,
    ("t29",7): 2.28,
    ("t29",8): 0.76,
    ("t29",9): 6.68,
}
normalized_task_executor_energy = {
    ("t9",0): 0.01,
    ("t9",1): 0.03,
    ("t9",2): 0.03,
    ("t9",3): 0.02,
    ("t9",4): 0.02,
    ("t9",5): 0.02,
    ("t9",6): 0.02,
    ("t9",7): 0.02,
    ("t9",8): 0.03,
    ("t9",9): 0.15,

    ("t19",0): 0.03,
    ("t19",1): 0.68,
    ("t19",2): 0.68,
    ("t19",3): 0.59,
    ("t19",4): 0.59,
    ("t19",5): 0.59,
    ("t19",6): 0.59,
    ("t19",7): 0.59,
    ("t19",8): 0.06,
    ("t19",9): 1.00,

    ("t29",0): 0.00,
    ("t29",1): 0.01,
    ("t29",2): 0.01,
    ("t29",3): 0.01,
    ("t29",4): 0.01,
    ("t29",5): 0.01,
    ("t29",6): 0.01,
    ("t29",7): 0.01,
    ("t29",8): 0.00,
    ("t29",9): 0.04,
}
task_executor_time = {
    ("t9",0): 1895.67,
    ("t9",1): 4211.45,
    ("t9",2): 4211.45,
    ("t9",3): 2793.96,
    ("t9",4): 2793.96,
    ("t9",5): 2793.96,
    ("t9",6): 2793.96,
    ("t9",7): 2793.96,
    ("t9",8): 1812.70,
    ("t9",9): 655.23,

    ("t19",0): 18106.84,
    ("t19",1): 114523.86,
    ("t19",2): 114523.86,
    ("t19",3): 88838.08,
    ("t19",4): 88838.08,
    ("t19",5): 88838.08,
    ("t19",6): 88838.08,
    ("t19",7): 88838.08,
    ("t19",8): 4389.75,
    ("t19",9): 5141.28,

    ("t29",0): 8790.52,
    ("t29",1): 8849.62,
    ("t29",2): 8849.62,
    ("t29",3): 5213.41,
    ("t29",4): 5213.41,
    ("t29",5): 5213.41,
    ("t29",6): 5213.41,
    ("t29",7): 5213.41,
    ("t29",8): 2129.78,
    ("t29",9): 2846.57,
}
normalized_task_executor_time = {
    ("t9",0): 0.02,
    ("t9",1): 0.04,
    ("t9",2): 0.04,
    ("t9",3): 0.02,
    ("t9",4): 0.02,
    ("t9",5): 0.02,
    ("t9",6): 0.02,
    ("t9",7): 0.02,
    ("t9",8): 0.02,
    ("t9",9): 0.01,

    ("t19",0): 0.16,
    ("t19",1): 1.00,
    ("t19",2): 1.00,
    ("t19",3): 0.78,
    ("t19",4): 0.78,
    ("t19",5): 0.78,
    ("t19",6): 0.78,
    ("t19",7): 0.78,
    ("t19",8): 0.04,
    ("t19",9): 0.04,

    ("t29",0): 0.08,
    ("t29",1): 0.08,
    ("t29",2): 0.08,
    ("t29",3): 0.05,
    ("t29",4): 0.05,
    ("t29",5): 0.05,
    ("t29",6): 0.05,
    ("t29",7): 0.05,
    ("t29",8): 0.02,
    ("t29",9): 0.02,
}
executor_thread_count = {
    0: 4,
    1: 4,
    2: 4,
    3: 4,
    4: 4,
    5: 4,
    6: 4,
    7: 4,
    8: 6,
    9: 8
}
lambda_param = 1
energy_split_base_percent = 0
edge_list = get_edge_list(jobs,
                          executors,
                          tasks,
                          normalized_task_executor_energy,
                          normalized_task_executor_time,
                          lambda_param,
                          executor_thread_count,
                          energy_split_base_percent)

graph = nx.MultiDiGraph()
graph.add_weighted_edges_from(edge_list)
epsilon = 1

# print(scsr(graph, epsilon, range(jobs)))
our_scsr(graph, epsilon, range(jobs))
