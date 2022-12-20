import pandas as pd
import os
from sklearn.utils import shuffle
from sklearn.model_selection import train_test_split

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
        self.alpha = 1.0
        self.threshold = 200
        self.q_lock = threading.Lock()

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

        self.Q = Q_Network(input_size=102, hidden_size=400, output_size=self.total_executor)

        self.Q_ast = copy.deepcopy(self.Q)
        self.optimizer = chainer.optimizers.Adam()
        self.optimizer.setup(self.Q)

        self.epoch_num = 20
        self.memory_size = 1000
        self.batch_size = 15
        self.epsilon = 0.9
        self.epsilon_decrease = 1e-3
        self.epsilon_min = 0.1
        self.start_reduce_epsilon = 3000
        self.train_freq = 1
        self.gamma = 0.97
        self.show_log_freq = 1

        self.memory = []
        self.total_step = 0
        self.total_reward = 0

        self.state_table = {}

        self.feedback_q = queue.Queue()

        # ensure we clear the csv file before we start
        if os.path.exists(rewards_csv_file):
            os.remove(rewards_csv_file)

    def save_state(self, task, state, act):

        self.state_table[task.offload_id] = [task, state, act, task.deadline]

    def get_saved_state(self, offload_id):

        task, state, act, deadline = self.state_table[offload_id]
        del self.state_table[offload_id]

        return task, state, act, deadline

    def process_state(self, before_state, task):
        state = [int(task.task_id), task.deadline]
        # task_id_vec = [int(x) for x in list('{:032b}'.format(int(task.task_id)))]

        for key in before_state:
            state.extend(list(before_state[key].values()))

        return state

    def generate_new_state(self, before_state, new_state_of_executor, exec_id):

        new_state = before_state

        new_state[exec_id] = new_state_of_executor

        return new_state

    def generate_reward(self, deadline, exec_time, status, energy):

        if status !=0:
            return -10

        if exec_time > deadline:
            reward = self.alpha*(-np.tanh(exec_time/deadline)) + (1-self.alpha)*(-(energy/self.threshold))
        else:
            reward = self.alpha*(1-np.tanh(exec_time/(deadline+exec_time))) + (1-self.alpha)*(1-(energy/self.threshold))

        return reward

    # TODO: When to stop? Optional for now
    def done_with_learning(self, reward):

        #if reached plateau return 1, else return 0

        return 0

    def schedule(self, before_state, task):

        pobs = self.process_state(before_state, task)

        # select act
        pact = np.random.randint(self.total_executor)
        explore = True

        if np.random.rand() > self.epsilon:
            self.q_lock.acquire()

            pact = self.Q(np.array(pobs, dtype=np.float32).reshape(1, -1))
            pact = np.argmax(pact.data).item()
            explore = False

            self.q_lock.release()


        print(f'[rls] scheduled task(offload_id={task.offload_id}, task_id={task.task_id}) on executer_id={pact}. (epsilon={self.epsilon}, total_step={self.total_step}, mode={"exploration" if explore else "exploitation"})')
        self.save_state(task, before_state, pact)

        return pact


    def task_finished(self, offload_id, exec_id, status, exec_time, energy, new_state_of_executor):
        # status = 0 => successful task, status != 0 => failed task

        task, before_state, pact, deadline = self.get_saved_state(offload_id)
        new_state = self.generate_new_state(before_state, new_state_of_executor, exec_id)

        pobs = self.process_state(before_state, task)
        obs =  self.process_state(new_state, task)

        reward = self.generate_reward(deadline, exec_time, status, energy)
        self.total_reward += reward

        done = self.done_with_learning(reward)

        print(f"[rls] reward={reward}, total_reward={self.total_reward} for task(offload_id={offload_id}, task_id={task.task_id}) on executer_id={exec_id}. exec_time={exec_time}, deadline={deadline}, status={status}, energy={energy}")

        # add memory
        self.memory.append((pobs, pact, reward, obs, done))
        if len(self.memory) > self.memory_size:
            self.memory.pop(0)

        if self.total_step % self.train_freq == 0:
            # train or update q
            if len(self.memory) == self.memory_size:
                self.q_lock.acquire()

                for epoch in range(self.epoch_num):
                    shuffled_memory = np.random.permutation(self.memory)
                    memory_idx = range(len(shuffled_memory))
                    for i in memory_idx[::self.batch_size]:
                        batch = np.array(shuffled_memory[i:i + self.batch_size])

                        #b_pobs = np.array(batch[:, 0].tolist(), dtype=np.float32).reshape(self.batch_size, -1)
                        b_pobs = np.array(batch[:, 0].tolist(), dtype=np.float32)
                        b_pact = np.array(batch[:, 1].tolist(), dtype=np.int32)
                        b_reward = np.array(batch[:, 2].tolist(), dtype=np.int32)
                        #b_obs = np.array(batch[:, 3].tolist(), dtype=np.float32).reshape(self.batch_size, -1)
                        b_obs = np.array(batch[:, 3].tolist(), dtype=np.float32)
                        b_done = np.array(batch[:, 4].tolist(), dtype=np.bool)

                        q = self.Q(b_pobs)

                        maxq = np.max(self.Q_ast(b_obs).data, axis=1)
                        target = copy.deepcopy(q.data)

                        for j in range(target.shape[0]):
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
                               item["status"],
                               item["exec_time"],
                               item["energy"],
                               item["new_state_of_executor"])

            self.feedback_q.task_done()

