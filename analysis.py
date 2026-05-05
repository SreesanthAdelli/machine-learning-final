import time
import matplotlib.pyplot as plt
import kuhn_poker as kp


NUM_ITERATIONS = 500_000
PRINT_EVERY = 100_000
SOLVED_VALUE = -1 / 18

ALL_DEALS = [
    ("J", "Q"), ("J", "K"),
    ("Q", "J"), ("Q", "K"),
    ("K", "J"), ("K", "Q"),
]


def train(n):
    kp.node_map = {}

    values = []
    regrets = []
    total = 0.0
    start = time.time()

    for i in range(1, n + 1):
        for cards in ALL_DEALS:
            total += kp.cfr(cards, "", 1.0, 1.0)

        avg_value = total / (i * len(ALL_DEALS))
        regret = kp.average_regret(i)

        values.append(avg_value)
        regrets.append(regret)

        if i % PRINT_EVERY == 0:
            elapsed = time.time() - start
            print(
                f"Iteration {i:,} | "
                f"avg: {avg_value:.6f} | "
                f"avg regret: {regret:.6f} | "
                f"time: {elapsed:.2f}s"
            )

    return values, regrets


def save_plot(name):
    plt.savefig(f"{name}.svg")
    plt.savefig(f"{name}.jpg", dpi=300)


def plot(values, ylabel, title, filename, log_y=False):
    x = range(1, len(values) + 1)

    plt.figure()
    plt.plot(x, values, 'o', markersize=1)
    plt.xscale("log")

    if log_y:
        plt.yscale("log")

    plt.xlabel("Iterations")
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.tight_layout()

    save_plot(filename)

    plt.show()


values, regrets = train(NUM_ITERATIONS)

x = range(1, NUM_ITERATIONS + 1)

# Convergence plot
plt.figure()
plt.plot(x, values, 'o', markersize=1, label="CFR average value")
plt.axhline(SOLVED_VALUE, linestyle="--", label=f"Solved value = {SOLVED_VALUE:.4f}")
plt.xscale("log")
plt.xlabel("Iterations")
plt.ylabel("Average game value")
plt.title("Kuhn Poker CFR Convergence")
plt.grid(True)
plt.legend()
plt.tight_layout()

save_plot("cfr_convergence")

plt.show()

# Regret plot
plot(
    regrets,
    "Average regret",
    "Average Regret Over Time",
    "cfr_regret",
    log_y=True
)

print(f"\nIterations: {NUM_ITERATIONS}")
print(f"Final average game value: {values[-1]:.6f}")
print(f"Solved game value:        {SOLVED_VALUE:.6f}")
print(f"Average regret:           {regrets[-1]:.6f}")

print("\nAverage strategy:")
for info_set in sorted(kp.node_map):
    strat = kp.node_map[info_set].get_average_strategy()
    print(f"{info_set:>3}: p={strat['p']:.8f}, b={strat['b']:.8f}")