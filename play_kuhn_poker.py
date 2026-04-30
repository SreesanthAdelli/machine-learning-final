# play_kuhn_poker.py
import random

CARDS = ["J", "Q", "K"]

POLICY = {
    "Jp":  {"p": 0.668, "b": 0.332},
    "Qp":  {"p": 1.000, "b": 0.000},
    "Kp":  {"p": 0.000, "b": 1.000},

    "Jb":  {"p": 1.000, "b": 0.000},
    "Qb":  {"p": 0.664, "b": 0.336},
    "Kb":  {"p": 0.000, "b": 1.000},
}


def deal():
    deck = CARDS[:]
    random.shuffle(deck)
    return deck[0], deck[1]


def rank(card):
    return {"J": 0, "Q": 1, "K": 2}[card]


def terminal(history):
    return history in ["pp", "bp", "bb", "pbp", "pbb"]


def player_turn(history):
    return len(history) % 2


def action_name(action, history):
    if history in ["", "p"]:
        return {"p": "check", "b": "bet"}[action]
    return {"p": "fold", "b": "call"}[action]


def sample(strategy):
    r = random.random()
    return "p" if r < strategy["p"] else "b"


def human_action(history):
    while True:
        print(f"\np = {action_name('p', history)}")
        print(f"b = {action_name('b', history)}")
        a = input("> ").strip().lower()

        if a in ["p", "b"]:
            return a

        print("Invalid action.")


def payoff(history, human_card, agent_card):
    human_wins = rank(human_card) > rank(agent_card)

    if history == "pp":
        return 1 if human_wins else -1

    if history == "bb":
        return 2 if human_wins else -2

    if history == "bp":
        return 1

    if history == "pbp":
        return -1

    if history == "pbb":
        return 2 if human_wins else -2

    raise ValueError(history)


def play_hand(human_chips, agent_chips):
    human_card, agent_card = deal()
    history = ""

    print("\n--- New hand ---")
    print(f"Chips: you={human_chips}, agent={agent_chips}")
    print(f"Your card: {human_card}")

    while not terminal(history):
        if player_turn(history) == 0:
            action = human_action(history)
        else:
            info_set = agent_card + history
            action = sample(POLICY[info_set])
            print(f"\nAgent chooses: {action_name(action, history)}")

        history += action

    net = payoff(history, human_card, agent_card)

    human_chips += net
    agent_chips -= net

    print("\n--- Result ---")
    print(f"History: {history}")
    print(f"Agent card: {agent_card}")
    print(f"Hand result: {net:+d}")
    print(f"Chips: you={human_chips}, agent={agent_chips}")

    return human_chips, agent_chips


def main():
    human_chips = 20
    agent_chips = 20

    while True:
        human_chips, agent_chips = play_hand(human_chips, agent_chips)


if __name__ == "__main__":
    main()