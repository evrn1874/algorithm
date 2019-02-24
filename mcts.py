
import copy
import time
from random import choice, shuffle
from math import log, sqrt


class Board(object):
    """
    游戏的棋盘类
    """

    def __init__(self, **kwargs):
        self.width = int(kwargs.get('width', 8))
        self.height = int(kwargs.get('height', 8))
        self.states = {}  # board states, key:move, value: piece type
        self.n_in_row = int(kwargs.get('n_in_row', 5))  # need how many pieces in a row to win

    def init_board(self):
        if self.width < self.n_in_row or self.height < self.n_in_row:
            raise Exception('board width and height can not less than %d' % self.n_in_row)
        self.availables = list(range(self.width * self.height))  # 初始化棋盘数组
        for m in self.availables:
            self.states[m] = -1

    # 数组指定值的索引对应棋盘上坐标
    def move_to_location(self, move):
        """
        3*3 board's moves like:
        6 7 8
        3 4 5
        0 1 2
        and move 5's location is (1,2)
        """
        h = move // self.width
        w = move % self.width
        return [h, w]

    # 棋盘上的坐标对应数组指定索引的值的
    def location_to_move(self, location):
        if len(location) != 2:
            return -1
        h = location[0]
        w = location[1]
        move = h * self.width + w
        if move not in range(self.width * self.height):
            return -1
        return move

    def update(self, player, move):
        self.states[move] = player
        self.availables.remove(move)  # 移除指定位置，不能再下


class MCTS(object):
    """
     AI 引擎, 用 基于 UCB 的蒙特卡洛树搜索
    """

    def __init__(self, board, play_turn, n_in_row=5, calc_time=5.0, max_actions=1000):
        self.board = board
        self.play_turn = play_turn
        self.calculation_time = float(calc_time)
        self.max_actions = max_actions
        self.n_in_row = n_in_row

        self.player = play_turn[0]  # AI is first at now
        self.confident = 1.96
        self.max_depth = 1

    def get_action(self):
        if len(self.board.availables) == 1:
            return self.board.availables[0]

        self.plays = {}  # key:(player, move), value:visited times  访问次数
        self.wins = {}  # key:(player, move), value:win times  获胜次数
        simulations = 0
        begin = time.time()
        while time.time() - begin < self.calculation_time:  # 限制计算时间，
            board_copy = copy.deepcopy(self.board)
            play_turn_copy = copy.deepcopy(self.play_turn)
            self.run_simulation(board_copy, play_turn_copy)
            simulations += 1

        print("total simulations=", simulations)

        move = self.select_one_move()
        location = self.board.move_to_location(move)
        print('Maximum depth searched:', self.max_depth)

        print("AI move: %d,%d\n" % (location[0], location[1]))

        return move

    def run_simulation(self, board, play_turn):
        """
        MCTS 算法主要操作类
        """

        plays = self.plays
        wins = self.wins
        availables = board.availables

        player = self.get_player(play_turn)
        visited_states = set()
        winner = -1
        expand = True
        # Simulation
        for t in range(1, self.max_actions + 1):
            # Selection
            # 如果所有步数都有走过（没走过的不在plays里面）
            if all(plays.get((player, move)) for move in availables):
                log_total = log(
                        sum(plays[(player, move)] for move in availables))  # 总的移棋次数
                value, move = max(
                        ((wins[(player, move)] / plays[(player, move)]) +
                         sqrt(self.confident * log_total / plays[(player, move)]), move)
                        for move in availables)  # 获取下一步UCB值最高的步数来走
            else:
                adjacents = []
                if len(availables) > self.n_in_row:
                    adjacents = self.adjacent_moves(board, player, plays)  # 获取已下子的区域附近没下过的所有位置

                if len(adjacents):
                    move = choice(adjacents)  # 随机选个位置下
                else:
                    peripherals = []
                    for move in availables:
                        if not plays.get((player, move)):
                            peripherals.append(move)
                    move = choice(peripherals)

            board.update(player, move)

            # Expand
            if expand and (player, move) not in plays:
                expand = False
                plays[(player, move)] = 0
                wins[(player, move)] = 0
                if t > self.max_depth:
                    self.max_depth = t

            visited_states.add((player, move))

            is_full = not len(availables)
            win, winner = self.has_a_winner(board)
            if is_full or win:  # 产生胜局或者无路可走
                break
            # 轮到下一个人
            player = self.get_player(play_turn)

        # Back-propagation 将
        for player, move in visited_states:
            if (player, move) not in plays:
                continue
            plays[(player, move)] += 1  # all visited moves
            if player == winner:
                wins[(player, move)] += 1  # only winner's moves

    def get_player(self, players):
        p = players.pop(0)
        players.append(p)
        return p

    # 获取剩余可走所有步数胜率最高的点
    def select_one_move(self):
        percent_wins, move = max(
                (self.wins.get((self.player, move), 0) /
                 self.plays.get((self.player, move), 1),
                 move)
                for move in self.board.availables)

        return move


    def adjacent_moves(self, board, player, plays):
        """
        获取所有走过的点附近能走的点的集合
        """
        moved = list(set(range(board.width * board.height)) - set(board.availables))
        adjacents = set()
        width = board.width
        height = board.height

        for m in moved:
            h = m // width
            w = m % width
            if w < width - 1:
                adjacents.add(m + 1)  # 右
            if w > 0:
                adjacents.add(m - 1)  # 左
            if h < height - 1:
                adjacents.add(m + width)  # 上
            if h > 0:
                adjacents.add(m - width)  # 下
            if w < width - 1 and h < height - 1:
                adjacents.add(m + width + 1)  # 右上
            if w > 0 and h < height - 1:
                adjacents.add(m + width - 1)  # 左上
            if w < width - 1 and h > 0:
                adjacents.add(m - width + 1)  # 右下
            if w > 0 and h > 0:
                adjacents.add(m - width - 1)  # 左下

        adjacents = list(set(adjacents) - set(moved))
        for move in adjacents:
            if plays.get((player, move)):
                adjacents.remove(move)
        return adjacents

    # 判断是否有胜者
    def has_a_winner(self, board):
        moved = list(set(range(board.width * board.height)) - set(board.availables))
        if len(moved) < self.n_in_row + 2:
            return False, -1

        width = board.width
        height = board.height
        states = board.states
        n = self.n_in_row
        for m in moved:  # 循环所有走过的位置
            h = m // width
            w = m % width
            player = states[m]

            if (w in range(width - n + 1) and  # 先判断横向从左到右起码能有n_in_row个位置
                        len(set(states[i] for i in range(m, m + n))) == 1):  # 判断横向从左到右是否同一个
                return True, player

            if (h in range(height - n + 1) and  # 判断从下往上起码能有n_in_row个位置
                        len(set(states[i] for i in range(m, m + n * width, width))) == 1):
                return True, player

            if (w in range(width - n + 1) and h in range(height - n + 1) and  # 判断从下往上，横向从左到右起码能有n_in_row个位置
                        len(set(states[i] for i in range(m, m + n * (width + 1), width + 1))) == 1):
                return True, player

            if (w in range(n - 1, width) and h in range(height - n + 1) and  # 判断右上方向的连子个数
                        len(set(states[i] for i in range(m, m + n * (width - 1), width - 1))) == 1):
                return True, player

        return False, -1

    def __str__(self):
        return "AI"


class Human(object):
    """
    玩家操作类
    """

    def __init__(self, board, player):
        self.board = board
        self.player = player

    def get_action(self):
        try:
            location = [int(n, 10) for n in input("Your move: ").split(",")]
            move = self.board.location_to_move(location)
        except Exception as e:
            move = -1
        if move == -1 or move not in self.board.availables:
            print("invalid move")
            move = self.get_action()
        return move

    def __str__(self):
        return "Human"


class Game(object):
    """
    游戏服务类
    """

    def __init__(self, board, **kwargs):
        self.board = board
        self.player = [1, 2]  # player1 and player2
        self.n_in_row = int(kwargs.get('n_in_row', 5))
        self.calc_time = float(kwargs.get('time', 5))
        self.max_actions = int(kwargs.get('max_actions', 1000))

    def start(self):
        p1, p2 = self.init_player()
        self.board.init_board()

        ai = MCTS(self.board, [p1, p2], self.n_in_row, self.calc_time, self.max_actions)
        human = Human(self.board, p2)
        players = {}
        players[p1] = ai
        players[p2] = human
        turn = [p1, p2]
        shuffle(turn)
        self.graphic(self.board, human, ai)
        while (1):
            p = turn.pop(0)
            turn.append(p)
            player_in_turn = players[p]
            move = player_in_turn.get_action()
            self.board.update(p, move)
            self.graphic(self.board, human, ai)
            end, winner = self.game_end(ai)
            if end:
                if winner != -1:
                    print("Game end. Winner is", players[winner])
                break

    def init_player(self):
        plist = list(range(len(self.player)))
        index1 = choice(plist)
        plist.remove(index1)
        index2 = choice(plist)

        return self.player[index1], self.player[index2]

    def game_end(self, ai):
        win, winner = ai.has_a_winner(self.board)
        if win:
            return True, winner
        elif not len(self.board.availables):
            print("Game end. Tie")
            return True, -1
        return False, -1

    def graphic(self, board, human, ai):
        """
        画棋盘和相关信息
        """
        width = board.width
        height = board.height

        print("Human Player", human.player, "with X".rjust(3))
        print("AI    Player", ai.player, "with O".rjust(3))
        print()
        for x in range(width):
            print("{0:8}".format(x), end='')
        print('\r\n')
        for i in range(height - 1, -1, -1):
            print("{0:4d}".format(i), end='')
            for j in range(width):
                loc = i * width + j
                if board.states[loc] == human.player:
                    print('X'.center(8), end='')
                elif board.states[loc] == ai.player:
                    print('O'.center(8), end='')
                else:
                    print('_'.center(8), end='')
            print('\r\n\r\n')


def run():
    n = 5
    try:
        #8*8的棋盘
        board = Board(width=8, height=8, n_in_row=n)
        #time值越大模拟次数越多，越智能，但影响下棋体验
        game = Game(board, n_in_row=n, time=5)
        game.start()
    except KeyboardInterrupt:
        print('\n\rquit')


if __name__ == '__main__':
    run()
