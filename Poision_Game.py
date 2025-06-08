import random
import getpass

def get_unique_poison(existing_poison):
    while True:
        p = random.randint(1, 20)
        if p not in existing_poison:
            return p

def pick_your_poison_multiplayer():
    print("🎮 Pick Your Poison - Multiplayer Mode (1 to 6 players)\n")

    # Ask for number of players
    while True:
        try:
            num_players = int(input("Enter number of players (1-6): "))
            if 1 <= num_players <= 6:
                break
            else:
                print("❗ Please enter a number between 1 and 6.")
        except ValueError:
            print("❗ Invalid input. Enter a number.")

    players = []
    poison_dict = {}
    alive_players = []

    # Player setup
    for i in range(num_players):
        is_computer = input(f"Is Player {i+1} a computer? (y/n): ").strip().lower()
        if is_computer == 'y':
            name = f"Computer{i+1}"
            poison = get_unique_poison(poison_dict.values())
            print(f"🤖 {name} has chosen its poison (secret).")
        else:
            name = input(f"Enter name for Player {i+1}: ")
            while True:
                try:
                    poison = int(getpass.getpass(f"{name}, enter your poison number (1-20): "))
                    if 1 <= poison <= 50 and poison not in poison_dict.values():
                        break
                    else:
                        print("❗ Invalid or duplicate poison number. Try again.")
                except ValueError:
                    print("❗ Enter a valid number.")
        players.append(name)
        poison_dict[name] = poison
        alive_players.append(name)

    round_num = 1

    # Game loop
    while len(alive_players) > 1:
        print(f"\n--- ROUND {round_num} ---")
        new_alive = []

        for name in alive_players:
            if name.startswith("Computer"):
                pick = random.randint(1, 50)
                print(f"🤖 {name} chooses: {pick}")
            else:
                while True:
                    try:
                        pick = int(input(f"{name}, choose a number (1-20): "))
                        if 1 <= pick <= 50:
                            break
                        else:
                            print("❗ Choose a number between 1 and 20.")
                    except ValueError:
                        print("❗ Enter a valid number.")

            # Check if the pick is someone else's poison
            poisoned = False
            for other in alive_players:
                if other != name and pick == poison_dict[other]:
                    print(f"💀 {name} picked {other}'s poison ({poison_dict[other]})!")
                    poisoned = True
                    break

            if not poisoned:
                print(f"✅ {name} is safe.")
                new_alive.append(name)

        alive_players = new_alive
        round_num += 1

    # Final result
    if len(alive_players) == 1:
        print(f"\n🏆 {alive_players[0]} is the LAST PLAYER STANDING!  WON!")
    else:
        print("\n💥 No one survived. Game Over.")

# Start the game
pick_your_poison_multiplayer()


