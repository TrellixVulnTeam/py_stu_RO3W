import os
import gym
import numpy as np
import paddle.fluid as fluid
import parl
from parl.utils import logger  # 日志打印工具
from model import Model
from algorithm import DQN  # from parl.algorithms import DQN # parl>=1.3.1
from agent import Agent

from replay_memory import ReplayMemory

LEARN_FREQ = 5  # 训练频率，不需要每一个step都learn,攒一些新增经验后再learn,提供效率
MEMORY_SIZE = 20000  # replay_memory 的大小，
MEMORY_WARMUP_SIZE = 200  # replay_momory 里需要预存一些经验数据，再从里面sample 一个batch 的经验，让agent 去learn
BATCH_SIZE = 32  # 每次给agent_learn 的数据数量，从replay memory随机里sample 一批数据出来
LEARN_RATE = 0.001  # 学习率
GAMMA = 0.99  # reward 的衰减因子，一般取0.9到0.999


# 训练一个episode
def run_episode(env, agent, rpm):
    total_reward = 0
    obs = env.reset()
    step = 0
    while True:
        step += 1
        action = agent.sample(obs)  # 采样动作，所有的动作都有概率被尝试到
        next_obs, reward, done, _ = env.step(action)
        rpm.append((obs, action, reward, next_obs, done))
        # train model
        if (len(rpm) > MEMORY_WARMUP_SIZE) and (step % LEARN_FREQ == 0):
            (batch_obs, batch_action, batch_reward, batch_next_obs, batch_done) = rpm.sample(BATCH_SIZE)
            train_loss = agent.learn(batch_obs, batch_action, batch_reward,
                                     batch_next_obs,
                                     batch_done)  # s ,a ,r ,s' , done
        total_reward += reward
        obs = next_obs
        if done:
            break
    return total_reward


# 评估agent, 跑5个episode ,总reward 求平均
def evaluate(env, agent, render=False):
    eval_reward = []
    for i in range(5):
        obs = env.reset()
        episode_reward = 0
        while True:
            action = agent.predict(obs)  # 预测动作,只选最优动作
            obs, reward, done, _ = env.step(action)
            episode_reward += reward
            if render:
                env.render()
            if done:
                break
        eval_reward.append(episode_reward)
    return np.mean(eval_reward)


def main():
    env = gym.make(
        # 'CartPole-V0'
        'CartPole-v0'

    )
    action_dim = env.action_space.n  # CartPole-v0:2
    obs_shape = env.observation_space.shape  # CartPole-v0:(4,)
    rpm = ReplayMemory(MEMORY_SIZE)  # DQN的经验回放池
    # 根据parl 框架构建agent
    model = Model(act_dim=action_dim)
    algorithm = DQN(model, act_dim=action_dim, gamma=GAMMA, lr=LEARN_RATE)
    agent = Agent(
        algorithm,
        obs_dim=obs_shape[0],
        act_dim=action_dim,
        e_greed=0.1,  # 有一定概率随机选取动作，探索
        e_greed_decrement=1e-6)  # 随着训练逐步收敛，探索的程度慢慢降低
    # 加载模型
    # save_path='./dqn_model.ckpt'
    # agent.restore(save_path)
    # 现在经验池里存一些数据，避免最开始训练的时候样本丰富度不够
    while len(rpm) < MEMORY_WARMUP_SIZE:
        run_episode(env, agent, rpm)
    max_episode = 2000
    # start train
    episode = 0
    while episode < max_episode:  # 训练max_episode 个回合 ，test 部分不计算入episode 数量
        # train part
        for i in range(0, 50):
            total_reward = run_episode(env, agent, rpm)
            episode += 1
        # test part
        eval_reward = evaluate(env, agent, render=True)
        logger.info('episode :{} , e_greed : {} test reward:{}'.
                    format(episode, agent.e_greed, eval_reward))
    # 训练结束，保存模型
    save_path = './dqn_model.ckpt'
    agent.save(save_path)


if __name__ == '__main__':
    main()
