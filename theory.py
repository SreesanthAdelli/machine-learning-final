import numpy as np
import matplotlib.pyplot as plt

np.random.seed(42)

NUM_ITERATIONS = 100_000
ACTIONS = ["Rock", "Paper", "Scissors"]

# Payoff matrix for Player 0
# rows = P0 action, cols = P1 action
PAYOFF = np.array([
    [0, -1,  1],   # Rock
    [1,  0, -1],   # Paper
    [-1, 1,  0],   # Scissors
])


def get_strategy(regret_sum):
    positive_regret = np.maximum(regret_sum, 0)

    if positive_regret.sum() > 0:
        return positive_regret / positive_regret.sum()

    return np.ones(3) / 3


# small random initialization so neither player starts exactly uniform
p0_regret_sum = np.random.uniform(-0.1, 0.1, 3)
p1_regret_sum = np.random.uniform(-0.1, 0.1, 3)

p0_strategy_sum = np.zeros(3)
p1_strategy_sum = np.zeros(3)

p0_strategies = []
p1_strategies = []
p0_avg_strategies = []
p1_avg_strategies = []
game_values = []
p0_regrets = []
p1_regrets = []

for t in range(1, NUM_ITERATIONS + 1):
    p0_strategy = get_strategy(p0_regret_sum)
    p1_strategy = get_strategy(p1_regret_sum)

    # Expected value of each pure action against opponent strategy
    p0_action_values = PAYOFF @ p1_strategy
    p1_action_values = (-PAYOFF.T) @ p0_strategy

    # Expected value of current mixed strategy
    p0_value = p0_strategy @ p0_action_values
    p1_value = p1_strategy @ p1_action_values

    # Regret updates
    p0_regret_sum += p0_action_values - p0_value
    p1_regret_sum += p1_action_values - p1_value

    # Average strategy tracking
    p0_strategy_sum += p0_strategy
    p1_strategy_sum += p1_strategy

    p0_avg = p0_strategy_sum / p0_strategy_sum.sum()
    p1_avg = p1_strategy_sum / p1_strategy_sum.sum()

    p0_strategies.append(p0_strategy.copy())
    p1_strategies.append(p1_strategy.copy())
    p0_avg_strategies.append(p0_avg.copy())
    p1_avg_strategies.append(p1_avg.copy())
    game_values.append(p0_value)

    p0_regrets.append(np.sum(np.maximum(p0_regret_sum, 0)) / t)
    p1_regrets.append(np.sum(np.maximum(p1_regret_sum, 0)) / t)

p0_strategies = np.array(p0_strategies)
p1_strategies = np.array(p1_strategies)
p0_avg_strategies = np.array(p0_avg_strategies)
p1_avg_strategies = np.array(p1_avg_strategies)

print("Player 0 average strategy:", p0_avg_strategies[-1])
print("Player 1 average strategy:", p1_avg_strategies[-1])
print("Equilibrium strategy:      ", np.ones(3) / 3)

# ---- Average strategy plot ----
plt.figure()

for i, action in enumerate(ACTIONS):
    plt.plot(p0_avg_strategies[:, i], "o", markersize=1, label=f"P0 {action}")

plt.axhline(1/3, linestyle="--", label="Equilibrium 1/3")
plt.xscale("log")
plt.xlabel("Iteration")
plt.ylabel("Average strategy probability")
plt.title("Player 0 Average Strategy")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig("rps_avg_strategy.svg")
plt.savefig("rps_avg_strategy.jpg", dpi=300)

plt.show()

# ---- Regret plot ----
plt.figure()

plt.plot(p0_regrets, "o", markersize=1, label="Player 0")
plt.plot(p1_regrets, "o", markersize=1, label="Player 1")

plt.xscale("log")
plt.yscale("log")

plt.xlabel("Iteration")
plt.ylabel("Average positive regret")
plt.title("Average Regret Over Time")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig("rps_avg_regret.svg")
plt.savefig("rps_avg_regret.jpg", dpi=300)

plt.show()