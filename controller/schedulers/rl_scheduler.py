import pandas as pd
import os

import csv
import time
import copy
import chainer
import chainer.functions as F
import chainer.links as L
import numpy as np
from chainer import serializers
import queue
import threading

rewards_csv_file='reward_loss.csv'

class RLScheduler:

    def __init__(self, executers):
        self.executers = executers
        self.alpha = 0.0
        self.threshold = 200
        self.q_lock = threading.Lock()
        self.needs_before_state = True
        self.needs_feedback = True

        class Q_Network(chainer.Chain):

            def __init__(self, input_size, hidden_size, output_size):
                super(Q_Network, self).__init__(
                    fc1=L.Linear(input_size, hidden_size),
                    fc2=L.Linear(hidden_size, hidden_size),
                    fc3=L.Linear(hidden_size, hidden_size),
                    fc4=L.Linear(hidden_size, hidden_size),
                    fc5=L.Linear(hidden_size, output_size)
                )

            def __call__(self, x):
                h = F.relu(self.fc1(x))
                h = F.relu(self.fc2(h))
                h = F.relu(self.fc3(h))
                h = F.relu(self.fc4(h))
                y = self.fc5(h)
                return y

            def reset(self):
                self.zerograds()

        self.total_executor = len(executers.keys())

        self.Q = Q_Network(input_size=43, hidden_size=400, output_size=self.total_executor)
        if os.path.exists('Q.model'):
            serializers.load_npz('Q.model', self.Q)
            print('[rl] loaded Q.model')

        self.Q_ast = copy.deepcopy(self.Q)
        self.optimizer = chainer.optimizers.Adam()
        self.optimizer.setup(self.Q)

        self.epoch_num = 5
        self.memory_size = 100
        self.batch_size = 10
        self.epsilon = 0.9
        self.epsilon_decrease = 1e-3
        self.epsilon_min = 0.0
        self.temperature = 0.5
        self.start_reduce_epsilon = 500
        self.train_freq = 5
        self.gamma = 0.1
        self.show_log_freq = 1

        # Energy consumption extremes per-task ID.
        # task ID -> (min energy, max_energy)
        self.energy_usage_per_task = {}

        self.memory = []
        self.total_step = 0
        self.total_reward = 0

        self.state_table = {}

        self.feedback_q = queue.Queue()

        # ensure we clear the csv file before we start
        if os.path.exists(rewards_csv_file):
            os.remove(rewards_csv_file)

        print(f'[rls] started rl scheduler with alpha={self.alpha},threshold={self.threshold},epoch_num={self.epoch_num},memory_size={self.memory_size},batch_size={self.batch_size},epsilon={self.epsilon},epsilon_decrease={self.epsilon_decrease},epsilon_min={self.epsilon_min},start_reduce_epsilon={self.start_reduce_epsilon},train_freq={self.train_freq},gamma={self.gamma},show_log_freq={self.show_log_freq}')

    def save_state(self, task, state, act):

        self.state_table[task.offload_id] = [task, state, act, task.deadline]

    def get_saved_state(self, offload_id):

        task, state, act, deadline = self.state_table[offload_id]
        del self.state_table[offload_id]

        return task, state, act, deadline

    def process_state(self, before_state, task):
        input_vec = []

        # Task ID input as a vector.
        import hashlib
        tid_hash = hashlib.md5(str(task.task_id).encode()).hexdigest()
        tid_hash_int = int(tid_hash[:8], 16)
        input_vec.extend([int(x) for x in list('{:032b}'.format(tid_hash_int))])

        # Deadline
        input_vec.extend([task.deadline])

        # Include only the stats named here.
        included_stats = ['cpu-load']
        for eid in before_state:
            executor_state = [v for (k, v) in before_state[eid].items() if k in included_stats]
            input_vec.extend(executor_state)
        # print('[rls] input state: {}'.format(input_vec))

        from joblib import load
        path_to_scaler = os.path.join(os.getcwd(), 'rl', 'std_scaler.bin')
        scaler = load(path_to_scaler)
        scaled_input_vec = scaler.transform(np.array(input_vec).reshape(1, -1))
        # print('[rls] scaled state: {}'.format(scaled_input_vec))

        return scaled_input_vec

    def generate_new_state(self, before_state, new_state_of_executor, exec_id):

        import copy
        new_state = copy.deepcopy(before_state)

        new_state[exec_id] = new_state_of_executor

        return new_state

    def generate_reward(self, task_id, deadline, exec_time, status, energy):

        if status != 0 or exec_time > deadline:
            return -1

        # Track energy usage of the task.
        # Just successful executions that meet the deadline.
        # We don't want to penalize the agent for being unable to do the impossible.
        # E.g., cannot get a high reward because it can't get a compute-intensive task to run on RPi3.
        (energy_min, energy_max,) = self.energy_usage_per_task.get(task_id, (energy, energy,))
        print('[rls] energy range for task_id={}: {:.2f} - {:.2f}'.format(task_id, energy_min, energy_max))
        energy_min = min(energy, energy_min)
        energy_max = max(energy, energy_max)
        self.energy_usage_per_task[task_id] = (energy_min, energy_max,)
        energy_range = energy_max - energy_min

        if energy_range == 0:
            return 1.0
        else:
            return (energy_max - energy) / energy_range

    # TODO: When to stop? Optional for now
    def done_with_learning(self, reward):

        #if reached plateau return 1, else return 0

        return 0

    def schedule(self, before_state, task):

        pobs = self.process_state(before_state, task)

        # select act
        pact = np.random.randint(self.total_executor)
        explore = True

        self.q_lock.acquire()
        pact_arr = self.Q(np.array(pobs, dtype=np.float32).reshape(1, -1))
        self.q_lock.release()

        exp_pact_arr = np.exp((pact_arr.data[0] - np.max(pact_arr.data[0])) / self.temperature)
        probabilities = exp_pact_arr / np.sum(exp_pact_arr)
        print('[rls] p_act_prb = {}'.format('[' + ', '.join(['{:.2f}'.format(x) for x in probabilities.data.tolist()]) + ']'))
        pact = np.random.choice(self.total_executor, p=probabilities)

        pact_l = [round(x, 2) for x in pact_arr.data[0].tolist()]
        print('[rls] p_act_arr = {}, p_act = {} (p = {:.2f})'.format(pact_l, pact, probabilities[pact].item()))

        print(f'[rls] scheduled task(offload_id={task.offload_id}, task_id={task.task_id}) on executer_id={pact}. (total_step={self.total_step})')
        self.save_state(task, before_state, pact)

        return pact


    def task_finished(self, offload_id, exec_id, task_id, status, exec_time, energy, new_state_of_executor):
        # status = 0 => successful task, status != 0 => failed task

        # Create a before and after state to train with.
        task, before_state, pact, deadline = self.get_saved_state(offload_id)
        new_state = self.generate_new_state(before_state, new_state_of_executor, exec_id)
        print('[rls] before state for offload_id={}, executer_id={}: {}'.format(
            offload_id, exec_id, before_state[exec_id]))
        print('[rls]  after state for offload_id={}, executer_id={}: {}'.format(
            offload_id, exec_id, new_state[exec_id]))

        pobs = self.process_state(before_state, task)
        obs =  self.process_state(new_state, task)

        reward = self.generate_reward(task_id, deadline, exec_time, status, energy)
        self.total_reward += reward

        done = self.done_with_learning(reward)

        print(f"[rls] reward={reward}, total_reward={self.total_reward} for task(offload_id={offload_id}, task_id={task.task_id}) on executer_id={exec_id}. exec_time={exec_time}, deadline={deadline}, status={status}, energy={energy}")

        # add memory
        self.memory.append((pobs, pact, reward, obs, done))
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)

        if self.total_step % self.train_freq == 0:
            # train or update q
            if len(self.memory) >= self.batch_size:
                self.q_lock.acquire()

                for epoch in range(self.epoch_num):
                    shuffled_memory = np.random.permutation(self.memory)
                    memory_idx = range(len(shuffled_memory))
                    for i in memory_idx[::self.batch_size]:
                        batch = np.array(shuffled_memory[i:i + self.batch_size])

                        b_pobs = np.array(batch[:, 0].tolist(), dtype=np.float32)
                        b_pact = np.array(batch[:, 1].tolist(), dtype=np.int32)
                        b_reward = np.array(batch[:, 2].tolist(), dtype=np.float32)
                        b_obs = np.array(batch[:, 3].tolist(), dtype=np.float32)
                        b_done = np.array(batch[:, 4].tolist(), dtype=np.bool)

                        # Calculate (rather, re-calculate) the Q-values for taking actions in the before-state.
                        # Output is a 2D array: (step x action's Q-value)
                        q = self.Q(b_pobs)

                        maxq = np.max(self.Q_ast(b_obs).data, axis=1)
                        target = copy.deepcopy(q.data)

                        # For each step we want to train on...
                        for j in range(target.shape[0]):
                            # Recall, target is 2D array of (step x Q-values).
                            # We fix j here as the first index because we only want to access that particular step.
                            # We use b_pact[j] because we only want to update the Q-value for the action we took
                            # (i.e., the executor we selected).
                            #
                            # We want to incorporate some measure of:
                            # "how well did the action set us up for future success?"
                            # So we find the maximum Q-value of the next state
                            # and use that in the calculation as well.
                            # The target puts the reward for the action taken in the before state
                            # together with some regard to the maximum Q-value attainable from the after state
                            # (it is scaled by gamma; lower gamma -> short-sighted agent).
                            target[j, b_pact[j]] = b_reward[j] + self.gamma * maxq[j] * (not b_done[j])

                        self.Q.reset()
                        loss = F.mean_squared_error(q, target)
                        loss.backward()
                        self.optimizer.update()

                self.Q_ast = copy.deepcopy(self.Q)

                self.q_lock.release()

        # next step
        self.total_step += 1

        # epsilon
        if self.epsilon > self.epsilon_min and self.total_step > self.start_reduce_epsilon:
            self.epsilon -= self.epsilon_decrease

        with open(rewards_csv_file, 'a', newline='') as f:
            # save Q, total_losses, total_rewards
            writer = csv.writer(f)
            writer.writerow([str(self.total_reward)])

        serializers.save_npz('Q.model', self.Q)

    def feedback_consumer(self):
        print("[rls] starting feedback consumer")
        while True:
            item = self.feedback_q.get()

            self.task_finished(item["offload_id"],
                               item["exec_id"],
                               item["task_id"],
                               item["status"],
                               item["exec_time"],
                               item["energy"],
                               item["new_state_of_executor"])

            self.feedback_q.task_done()
