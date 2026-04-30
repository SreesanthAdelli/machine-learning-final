#!/usr/bin/env python3

import curses
import random



CARDS = ["J", "Q", "K"]

# Full Nash average strategy covering all info sets including re-raise (pbX)
POLICY = {
    "J":   {"p": 0.780, "b": 0.220},
    "Jb":  {"p": 1.000, "b": 0.000},
    "Jp":  {"p": 0.668, "b": 0.332},
    "Jpb": {"p": 1.000, "b": 0.000},
    "K":   {"p": 0.337, "b": 0.663},
    "Kb":  {"p": 0.000, "b": 1.000},
    "Kp":  {"p": 0.000, "b": 1.000},
    "Kpb": {"p": 0.000, "b": 1.000},
    "Q":   {"p": 1.000, "b": 0.000},
    "Qb":  {"p": 0.664, "b": 0.336},
    "Qp":  {"p": 1.000, "b": 0.000},
    "Qpb": {"p": 0.445, "b": 0.555},
}

CARD_SUIT = "♠"



def deal():
    deck = CARDS[:]
    random.shuffle(deck)
    return deck[0], deck[1]


def rank(card):
    return {"J": 0, "Q": 1, "K": 2}[card]


def terminal(history):
    return history in ["pp", "bp", "bb", "pbp", "pbb"]


def player_turn(history, first_to_act):
    """Return 0 (human) or 1 (agent) based on whose turn it is."""
    # In Kuhn poker the player who acts is determined by position + history length.
    # first_to_act=0 means human goes first on an empty history.
    return (len(history) + first_to_act) % 2


def action_label(action, history):
    """Human-readable name for an action given the history so far."""
    # A bet is on the table if the last character in history is 'b'
    bet_on_table = history.endswith("b")
    if not bet_on_table:
        return "Check" if action == "p" else "Bet"
    else:
        return "Fold" if action == "p" else "Call"


def history_label(history):
    """Build a readable action sequence string from a full history."""
    parts = []
    for i, a in enumerate(history):
        parts.append(action_label(a, history[:i]))
    return " → ".join(parts)


def sample(strategy):
    return "p" if random.random() < strategy["p"] else "b"


def payoff(history, human_card, agent_card, first_to_act):
    """
    Return net chips for the human player.
    In Kuhn poker the pot starts at 1 chip each (antes).
    'p' = pass/check/fold, 'b' = bet/call
    Player indices in history depend on first_to_act.
    """
    human_wins = rank(human_card) > rank(agent_card)

    if history == "pp":
        return 1 if human_wins else -1

    if history == "bb":
        return 2 if human_wins else -2

    if history == "bp":
        # First actor bet, second folded → first actor wins the pot (1 chip ante)
        if first_to_act == 0:
            # Human bet first, agent folded → human wins
            return 1
        else:
            # Agent bet first, human folded → agent wins
            return -1

    if history == "pbp":
        # First actor passed, second bet, first folded
        if first_to_act == 0:
            # Human passed, agent bet, human folded → agent wins
            return -1
        else:
            # Agent passed, human bet, agent folded → human wins
            return 1

    if history == "pbb":
        return 2 if human_wins else -2

    raise ValueError(f"Unknown terminal history: {history!r}")




def _safe_addstr(win, y, x, text, attr=0):
    """addstr that silently clips at window boundary."""
    h, w = win.getmaxyx()
    if y < 0 or y >= h or x >= w:
        return
    if x < 0:
        text = text[-x:]
        x = 0
    available = w - x
    if available <= 0:
        return
    try:
        win.addstr(y, x, text[:available], attr)
    except curses.error:
        pass


def draw_card(win, y, x, card, face_down=False, color_pair=0):
    """Draw a mini playing card (5×4 chars)."""
    attr = curses.color_pair(color_pair)
    lines = [
        "┌───┐",
        f"│{card if not face_down else '?'}  │",
        f"│ {CARD_SUIT} │",
        "└───┘",
    ]
    for i, line in enumerate(lines):
        _safe_addstr(win, y + i, x, line, attr)




class KuhnPokerUI:
    START_CHIPS = 20
    LOG_MAX = 14

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.human_chips = self.START_CHIPS
        self.agent_chips = self.START_CHIPS
        self.log: list[tuple[str, int]] = []   # (message, color_pair)
        self.hand_count = 0
        self.first_to_act = 0   # 0 = human goes first, alternates each hand

        curses.curs_set(0)
        curses.start_color()
        curses.use_default_colors()

        # Palette
        curses.init_pair(1, curses.COLOR_WHITE,   -1)
        curses.init_pair(2, curses.COLOR_GREEN,   -1)
        curses.init_pair(3, curses.COLOR_RED,     -1)
        curses.init_pair(4, curses.COLOR_YELLOW,  -1)
        curses.init_pair(5, curses.COLOR_CYAN,    -1)
        curses.init_pair(6, curses.COLOR_WHITE,   curses.COLOR_BLUE)
        curses.init_pair(7, curses.COLOR_BLACK,   curses.COLOR_WHITE)
        curses.init_pair(8, curses.COLOR_MAGENTA, -1)

        self.run()



    def layout(self):
        H, W = self.stdscr.getmaxyx()
        self.title_h   = 3
        self.chips_h   = 3
        self.arena_h   = 10
        self.action_h  = 5
        self.log_h     = H - self.title_h - self.chips_h - self.arena_h - self.action_h
        self.W = W
        self.H = H



    def redraw(self, human_card=None, agent_card=None, history="",
               reveal=False, message="", waiting=False, first_to_act=0):
        self.layout()
        s = self.stdscr
        s.erase()

        H, W = self.H, self.W
        y = 0

        self._draw_title(y, W)
        y += self.title_h

        self._draw_chips(y, W, first_to_act)
        y += self.chips_h

        self._draw_arena(y, W, human_card, agent_card, history, reveal, first_to_act)
        y += self.arena_h

        self._draw_actions(y, W, history, waiting, message)
        y += self.action_h

        self._draw_log(y, W)

        s.refresh()

    def _draw_title(self, y, W):
        s = self.stdscr
        banner = "  ♠  KUHN POKER  ♠  "
        _safe_addstr(s, y + 1, (W - len(banner)) // 2, banner,
                     curses.color_pair(8) | curses.A_BOLD)
        _safe_addstr(s, y, 0, "─" * W, curses.color_pair(5))
        _safe_addstr(s, y + 2, 0, "─" * W, curses.color_pair(5))

    def _draw_chips(self, y, W, first_to_act):
        s = self.stdscr
        you_tag  = " ◄ FIRST" if first_to_act == 0 else ""
        them_tag = " FIRST ► " if first_to_act == 1 else ""
        you_str  = f"  YOU  {self.human_chips:>3} chips{you_tag}"
        them_str = f"{them_tag}AGENT  {self.agent_chips:>3} chips  "
        _safe_addstr(s, y + 1, 2, you_str,  curses.color_pair(4) | curses.A_BOLD)
        _safe_addstr(s, y + 1, W - len(them_str) - 2, them_str,
                     curses.color_pair(5) | curses.A_BOLD)
        _safe_addstr(s, y + 2, 0, "─" * W, curses.color_pair(5))

    def _draw_arena(self, y, W, human_card, agent_card, history, reveal, first_to_act):
        s = self.stdscr

        # Your card (left)
        if human_card:
            draw_card(s, y + 2, 6, human_card, face_down=False, color_pair=4)
            _safe_addstr(s, y + 1, 5, "  YOUR CARD  ", curses.color_pair(1))

        # Agent card (right)
        if agent_card:
            draw_card(s, y + 2, W - 12, agent_card,
                      face_down=not reveal, color_pair=5 if reveal else 1)
            _safe_addstr(s, y + 1, W - 14, "  AGENT CARD  ", curses.color_pair(1))

        # Action history in the centre
        if history:
            label = f"Actions: {history_label(history)}"
            _safe_addstr(s, y + 4, (W - len(label)) // 2, label, curses.color_pair(1))

        # Hand count + position info
        pos = "You act first" if first_to_act == 0 else "Agent acts first"
        hc = f"Hand #{self.hand_count}  |  {pos}"
        _safe_addstr(s, y + 6, (W - len(hc)) // 2, hc, curses.color_pair(1) | curses.A_DIM)

        _safe_addstr(s, y + self.arena_h - 1, 0, "─" * W, curses.color_pair(5))

    def _draw_actions(self, y, W, history, waiting, message):
        s = self.stdscr

        if message:
            _safe_addstr(s, y + 1, (W - len(message)) // 2, message,
                         curses.color_pair(4) | curses.A_BOLD)

        if waiting:
            left_label  = f"  [C] {action_label('p', history)}  "
            right_label = f"  [B] {action_label('b', history)}  "
            lx = W // 2 - len(left_label) - 3
            rx = W // 2 + 3
            _safe_addstr(s, y + 3, lx, left_label, curses.color_pair(7) | curses.A_BOLD)
            _safe_addstr(s, y + 3, rx, right_label, curses.color_pair(6) | curses.A_BOLD)
            hint = f"C = {action_label('p', history)}   B = {action_label('b', history)}"
            _safe_addstr(s, y + 4, (W - len(hint)) // 2, hint, curses.color_pair(1) | curses.A_DIM)
        else:
            prompt = "Press any key for next hand…"
            _safe_addstr(s, y + 3, (W - len(prompt)) // 2, prompt, curses.color_pair(1) | curses.A_DIM)

        _safe_addstr(s, y + self.action_h - 1, 0, "─" * W, curses.color_pair(5))

    def _draw_log(self, y, W):
        s = self.stdscr
        _safe_addstr(s, y, 2, " LOG ", curses.color_pair(1) | curses.A_BOLD)
        visible = self.log[-(self.log_h - 2):]
        for i, (msg, cp) in enumerate(visible):
            _safe_addstr(s, y + 1 + i, 2, msg[:W - 4], curses.color_pair(cp))



    def log_msg(self, msg, color_pair=1):
        self.log.append((msg, color_pair))

    def run(self):
        while True:
            self.play_hand()
            if self.human_chips <= 0 or self.agent_chips <= 0:
                winner = "YOU" if self.agent_chips <= 0 else "AGENT"
                self.log_msg(f"── GAME OVER ── {winner} wins! ──", 4)
                self.redraw(message=f"Game over! {winner} wins! Press Q to quit.",
                            waiting=False, first_to_act=self.first_to_act)
                while True:
                    k = self.stdscr.getch()
                    if k in (ord('q'), ord('Q')):
                        return

    def play_hand(self):
        self.hand_count += 1
        fta = self.first_to_act          # snapshot for this hand
        human_card, agent_card = deal()
        history = ""

        self.log_msg(f"── Hand #{self.hand_count}  ({'You' if fta==0 else 'Agent'} acts first) ──", 5)
        self.log_msg(f"Your card: {human_card}{CARD_SUIT}", 4)

        # If agent goes first, let it act immediately (no human key needed)
        if fta == 1:
            self.redraw(human_card=human_card, agent_card=agent_card,
                        history=history, message=f"Your card: {human_card}{CARD_SUIT}  — Agent acts first",
                        first_to_act=fta)
            curses.napms(900)

            # Agent's first action
            info_set = agent_card + history
            action = sample(POLICY[info_set])
            self.log_msg(f"Agent: {action_label(action, history)}", 5)
            history += action
            self.redraw(human_card=human_card, agent_card=agent_card,
                        history=history, message=f"Agent: {action_label(action, history[:-1])}",
                        first_to_act=fta)
            curses.napms(600)
        else:
            self.redraw(human_card=human_card, agent_card=agent_card,
                        history=history, message=f"Your card: {human_card}{CARD_SUIT}",
                        first_to_act=fta)
            self.stdscr.getch()

        # Main action loop
        while not terminal(history):
            turn = player_turn(history, fta)

            if turn == 0:
                # Human's turn
                self.redraw(human_card=human_card, agent_card=agent_card,
                            history=history, waiting=True, first_to_act=fta)
                action = self._get_human_action(history)
                self.log_msg(f"You: {action_label(action, history)}", 4)
                history += action
                self.redraw(human_card=human_card, agent_card=agent_card,
                            history=history, first_to_act=fta)
            else:
                # Agent's turn
                info_set = agent_card + history
                action = sample(POLICY[info_set])
                lbl = action_label(action, history)
                self.log_msg(f"Agent: {lbl}", 5)
                history += action
                self.redraw(human_card=human_card, agent_card=agent_card,
                            history=history, message=f"Agent: {lbl}",
                            first_to_act=fta)
                curses.napms(800)

        # Showdown
        net = payoff(history, human_card, agent_card, fta)
        self.human_chips += net
        self.agent_chips -= net

        if net > 0:
            result_msg = f"You win {net:+d} chip{'s' if abs(net) > 1 else ''}!"
            cp = 2
        elif net < 0:
            result_msg = f"Agent wins {abs(net)} chip{'s' if abs(net) > 1 else ''}."
            cp = 3
        else:
            result_msg = "Tie."
            cp = 1

        self.log_msg(f"Agent had: {agent_card}{CARD_SUIT}  →  {result_msg}", cp)

        self.redraw(human_card=human_card, agent_card=agent_card,
                    history=history, reveal=True, message=result_msg,
                    waiting=False, first_to_act=fta)
        self.stdscr.getch()

        # Rotate who acts first
        self.first_to_act = 1 - self.first_to_act

    def _get_human_action(self, history):
        """Wait for C (check/fold) or B (bet/call)."""
        while True:
            k = self.stdscr.getch()
            if k in (ord('c'), ord('C'), ord('p'), ord('P')):
                return 'p'
            if k in (ord('b'), ord('B')):
                return 'b'



def main():
    curses.wrapper(KuhnPokerUI)


if __name__ == "__main__":
    main()