# coding=utf-8
import random
import numpy as np


def gen_map_data(m_len, min_l=1, max_l=20):
    map_data = np.zeros((m_len, m_len), dtype='int16')
    for i in range(m_len):
        for j in range(m_len):
            if i != j:
                map_data[i][j] = random.randint(min_l, max_l)
    return map_data


def get_min_ship(data):
    N = len(data)
    b = 2 ** (N - 1)
    F = [[-1] * b for _ in range(N)]  # 保存最优子结构
    M = [[-1] * b for _ in range(N)]
    # 先初始化各点回到起点的距离
    for i in range(N):
        F[i][0] = data[i][0]
    # 遍历并填表 1，2，3，4=》000001，0000010，0000011，00000100
    for i in range(1, b):  # b表示所有经过点的集合,i表示当前将要走的点
        for j in range(1, N):  #
            # 判断结点j不在i表示的集合中,当前是j，接下来走的不能是自己，或者之前已经出现过的点
            if int(2 ** (j - 1) & i) == 0:
                min = 65535
                for k in range(1, N):
                    # k是i表示的点集合中包含的点
                    if int(2 ** (k - 1) & i):
                        temp = data[j][k] + F[k][i - int(2 ** (k - 1))]  # j到k的距离加上k到结束的距离
                        if temp < min:
                            min = temp
                            F[j][i] = min  # 保存阶段最优值，从j出发经过i包含的点然后回去的最小值
                            M[j][i] = k  # 保存最优决策
    # 最后一列，即总最优值的计算
    # 计算选择哪个点作为第二个点的总路程最短
    min = 65535
    for k in range(1, N):
        # b-1的二进制全1，表示集合{1,2,3,4,5}，11111
        # 从中去掉k结点即将k对应的二进制位置0，k结点前面的清0，后面的保留
        temp = data[0][k] + F[k][b - 1 - int(2 ** (k - 1))]
        if temp < min:
            min = temp
            F[0][b - 1] = min  # 总最优值
            M[0][b - 1] = k
    print("最短路径总长度" + str(F[0][b - 1]))
    # 回溯查表M输出最短路径(编号0~n - 1)
    print("最短路径(编号1—6)：", "v1", end='')
    i = b - 1
    j = 0
    while i > 0:
        j = M[j][i]  # 下一步去往哪个结点
        i -= int(2 ** (j - 1))  # 从i中去掉j结点
        print("->v" + str(j + 1), end=''),
    print("->v1")
    return 0

# 自定义距离数组
# map_data = gen_map_data(4)
# map_data = [[0, 17, 13, 14],
#             [5, 0, 17, 11],
#             [13, 20, 0, 12],
#             [18, 18, 19, 0]]

map_data = [[0, 10, 20, 30, 40, 50],
            [12, 0, 18, 30, 25, 21],
            [23, 19, 0, 5, 10, 15],
            [34, 32, 4, 0, 8, 16],
            [45, 27, 11, 10, 0, 18],
            [56, 22, 16, 20, 12, 0]]
get_min_ship(map_data)
