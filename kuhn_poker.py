import random

random.seed(42)

CARDS = ["J", "Q", "K"]
ACTIONS = ["p", "b"]


def is_terminal(history):
    return history in ["pp", "bp", "bb", "pbp", "pbb"]


def next_player(history):
    return len(history) % 2


def deal_cards():
    deck = CARDS.copy()
    random.shuffle(deck)
    return deck[0], deck[1]


def card_rank(card):
    return {"J": 0, "Q": 1, "K": 2}[card]


def terminal_utility(history, cards):
    p0_card, p1_card = cards
    p0_wins = card_rank(p0_card) > card_rank(p1_card)

    if history == "pp":
        return 1 if p0_wins else -1

    if history == "bb":
        return 2 if p0_wins else -2

    if history == "bp":
        return 1

    if history == "pbp":
        return -1

    if history == "pbb":
        return 2 if p0_wins else -2

    raise ValueError(f"Unknown terminal history: {history}")


class Node:
    def __init__(self, info_set):
        self.info_set = info_set
        self.actions = ACTIONS
        self.regret_sum = {a: 0.0 for a in self.actions}
        self.strategy_sum = {a: 0.0 for a in self.actions}

    def get_strategy(self, realization_weight):
        strategy = {}
        total_positive_regret = 0.0

        for action in self.actions:
            strategy[action] = max(self.regret_sum[action], 0.0)
            total_positive_regret += strategy[action]

        if total_positive_regret > 0:
            for action in self.actions:
                strategy[action] /= total_positive_regret
        else:
            for action in self.actions:
                strategy[action] = 1.0 / len(self.actions)

        for action in self.actions:
            self.strategy_sum[action] += realization_weight * strategy[action]

        return strategy

    def get_average_strategy(self):
        total = sum(self.strategy_sum.values())

        if total > 0:
            return {
                action: self.strategy_sum[action] / total
                for action in self.actions
            }

        return {action: 1.0 / len(self.actions) for action in self.actions}

    def __str__(self):
        avg = self.get_average_strategy()
        return f"{self.info_set:>3}: p={avg['p']:.3f}, b={avg['b']:.3f}"


node_map = {}


def cfr(cards, history, p0, p1):
    if is_terminal(history):
        return terminal_utility(history, cards)

    player = next_player(history)
    info_set = cards[player] + history

    if info_set not in node_map:
        node_map[info_set] = Node(info_set)

    node = node_map[info_set]
    strategy = node.get_strategy(p0 if player == 0 else p1)

    action_utils = {}
    node_util = 0.0

    for action in ACTIONS:
        next_history = history + action

        if player == 0:
            action_utils[action] = cfr(
                cards,
                next_history,
                p0 * strategy[action],
                p1,
            )
        else:
            action_utils[action] = cfr(
                cards,
                next_history,
                p0,
                p1 * strategy[action],
            )

        node_util += strategy[action] * action_utils[action]

    for action in ACTIONS:
        regret = action_utils[action] - node_util

        if player == 0:
            node.regret_sum[action] += p1 * regret
        else:
            node.regret_sum[action] += p0 * (-regret)

    return node_util


def train_cfr_all_deals(num_iterations):
    global node_map
    node_map = {}

    all_deals = [
        ("J", "Q"), ("J", "K"),
        ("Q", "J"), ("Q", "K"),
        ("K", "J"), ("K", "Q"),
    ]

    total_utility = 0.0

    for _ in range(num_iterations):
        for cards in all_deals:
            total_utility += cfr(cards, "", 1.0, 1.0)

    return total_utility / (num_iterations * len(all_deals))


def print_average_strategy():
    print("\nAverage strategy:")
    for info_set in sorted(node_map):
        print(node_map[info_set])


def main():
    num_iterations = 10000

    avg_value = train_cfr_all_deals(num_iterations)

    print(f"Iterations: {num_iterations}")
    print(f"Average game value for Player 0: {avg_value:.4f}")
    print(f"Number of information sets: {len(node_map)}")

    print_average_strategy()


if __name__ == "__main__":
    main()