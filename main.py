from games import Ugolki

"""
-- Reinforcement Learning --

an AGENT interacts with its ENVIRONMENT by taking an ACTION according to a POLICY and observing a change in the environment. 
The agent has a REWARD that it tries to maximize.

environment = env.init()
policy = policy.init()
actions = [action1, action2, ...] # set of actions to take
for tick in time: 
    action = policy(environment, actions) # finds the next best action according to policy
    agent.take_action(action) # updates the environment
    if environment is some_state: 
        agent.receive_reward()

"""

if __name__ == "__main__":
    # Standard game
    ugolki = Ugolki.create_game()
    ugolki.print_board()
    actions = ugolki.get_legal_actions()
    print(f"White has {len(actions)} legal moves\n")

    # Random position (20 moves in)
    print("=" * 40)
    print("Random position after 20 moves:")
    print("=" * 40)
    random_game = Ugolki.create_random_game(num_moves=20)
    random_game.print_board()
    actions = ugolki.get_legal_actions()
    print(f"White has {len(actions)} legal moves\n")
