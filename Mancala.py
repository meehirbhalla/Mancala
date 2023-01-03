"""An implementation of the game mancala."""

from argparse import ArgumentParser
from cmath import pi
from multiprocessing.managers import ValueProxy
from blessed import Terminal
import sys
from time import sleep

#####
# Board setup
#####

TERM = Terminal()

NEUT = TERM.gray33      # 33% gray
P0DK = TERM.cyan4       # dark color for player 0
P0LT = TERM.cyan3       # light color for player 0
P1DK = TERM.violetred4  # dark color for player 1
P1LT = TERM.violetred1  # light color for player 1

# this template gets populated in Mancala.print_board
SLOT = "{:>2}"
TEMPLATE = f"""{TERM.home+TERM.clear}\
<SP>  {P0DK}\u2193  f  e  d  c  b  a  \u2190  <NAME0>
<SP> {P0LT}{SLOT} {SLOT} {SLOT} {SLOT} {SLOT} {SLOT} {SLOT}
<SP> {NEUT}------------------------
<SP> {P1LT}   {SLOT} {SLOT} {SLOT} {SLOT} {SLOT} {SLOT} {SLOT}
{P1DK}<NAME1>  \u2192  g  h  i  j  k  l  \u2191{TERM.normal}"""

PAUSE = 0.3             # used to help animate moves

PITS = "abcdef.ghijkl"  # helps convert between pit indexes and letters in UI
STORES = [6, 13]        # indexes of the stores

#####
# Helper function
#####

def get_move(game, player):
    """Get player's selection of a pit to play from.
    
    The player will select a letter corresponding to one of their pits. This
    function will translate their selection into an index of game.board. The
    function will ask repeatedly until the user provides valid input.
    
    Args:
        game (Mancala): the current game.
        player (int): index of the player (0 or 1).
    
    Returns:
        int: the pit selected by the user, expressed as an index of game.board.
    
    Side effects:
        Displays information in the terminal.
        May cause the program to exit.
    """
    while True:
        print()
        selection = (input(f"{game.names[player]}, select one of your pits that"
                          " is not empty (or enter q to quit): ")
                     .lower()
                     .strip())
        if selection == "q":
            sys.exit(0)
        try:
            if len(selection) != 1 or not selection.isalpha():
                raise ValueError("Please enter a single letter.")
            pit = PITS.find(selection)
            if pit == -1:
                raise ValueError("Please enter a letter corresponding to one of"
                                 " your non-empty pits.")
            game.validate_move(pit, player)
        except ValueError as e:
            print(e)
        else:
            return pit

#####
# Mancala class
#####

class Mancala:
    """A class for the turns and calculations in Mancala.
    
    Attributes: 
        names (list of str): A list containing the names of both players
        turn_funcs (list of function object): A list containing the turn functions
            for each respective player
        board(empty list): A list containing nothing, will be populated in the
            play_round() method
    """    
    def __init__(self, p0_name, p1_name, func0 = get_move, func1 = get_move):                
        """Creates attributes for player names, turn functions, and board.

        Args:
            p0_name (str): Name of the first player
            p1_name (str): Name of the second player
            func0 (func, optional): The turn function for the first player, used to call
                on first player's turn. Defaults to get_move
            func1 (func, optional): The turn function for the second player, used to call
                on second player's turn. Defaults to get_move
                
        Side effects: 
            Created attribute names of p0_name and p1_name objects, attribute turn_funcs of
            func0 and func1 objects, and attribute board as an empty list.
        """        
        self.names = [p0_name, p1_name]
        self.turn_funcs = [func0, func1]
        self.board = []
    
    def validate_move(self, pit_index, player_index):
        """Checks if player is allowed to play from the selected pit.

        Args:
            pit_index (int): The index (position) the player has chosen to play from
            player_index (int): Which player is currently playing with 0 representing
                the first player and 1 representing the second player

        Raises:
            ValueError: Player cannot select either store
            ValueError: Player cannot select opponent's pit
            ValueError: Player cannot select an empty pit
        """        
        if pit_index in STORES:
            raise ValueError("Sorry, you can't select the store.")
        if self.is_own_pit(pit_index, player_index) == False:
            raise ValueError("Sorry, you don’t control that pit.")
        if self.board[pit_index] == 0:
            raise ValueError("Sorry, that pit is empty.")
        
    def check_capture(self, last_seed_index, player_index):
        """Determines if player can capture seeds.

        Args:
            last_seed_index (int): The index in which the player has placed their last seed
            player_index (int): The current player
        
        Side effects: 
            Prints message to the terminal stating the player who has captured, the opponents pit
            captured, and their pit captured. This happens if player is eligible to capture seed.
            
            Prints board to screen after capture is complete.
            
            board (list of int): Updates value of selected index and opposite index and sets those
                indexes to 0
        """        
        if (self.is_own_pit(last_seed_index, player_index) == True) and (last_seed_index != STORES[player_index]) and (self.board[last_seed_index] == 1):
                # define the opposite pit
                opp_pit_index = 12 - last_seed_index
                # index of the player's store
                player_store_index = STORES[player_index]
                # add points of opposite pit and player pit to player's store
                self.board[player_store_index] += self.board[opp_pit_index]
                self.board[player_store_index] += self.board[last_seed_index]
                # set opposite pit and player pit to 0
                self.board[opp_pit_index] = 0
                self.board[last_seed_index] = 0
                self.print_board()
                print(f'{self.names[player_index]} captured the contents of pits {PITS[opp_pit_index]} and {PITS[last_seed_index]}')
            
    def distribute_seeds(self, selected_pit, player_index):
        """Distributes seeds to following pits and player's store if applicable.
        
        Args:
            selected_pit (int): The index of the pit the player has selected
            player_index (int): The current player

        Returns:
            int: The index of the last pit or store a seed was placed in
        
        Side effects: 
            Displays the current board setup to the terminal each time a seed is moved or distributed.
            
            board (list of int): The board attribute is modified/updated whenever a seed is
                distributed into a pit or store and the selected index is also changed to 0
        """        
        num_seeds = self.board[selected_pit]
        self.board[selected_pit] = 0
        self.print_board()
        count = 0
        count2 = 0
        while count < num_seeds:
            count+=1
            pit = (selected_pit + count + count2)%14
            OL = STORES[1-player_index]
            if pit != OL:
                self.board[pit] += 1
                self.print_board()
            else:
                count2+=1
                self.board[pit] += 0
                self.board[(pit+1)%14] += 1
                self.print_board()
        return pit
    
    def play_round(self):
        """Plays out one round of Mancala. This includes initializing and printing
        the board and managing player's turns until there is a winner.
        
        Side effects:
            Prints board to scrren after board is initialized.
            
            Prints to the terminal if a player gets an extra turn.
            
            board (list of int): Populates the board attribute/redefines board
        """        
        self.board = ([4]*6 + [0]) * 2
        self.print_board()
        player_tracker = 0
        while self.game_over() == False:
            selected_pit = self.turn_funcs[player_tracker](self, player_tracker)
            last_seed_index = self.distribute_seeds(selected_pit, player_tracker)
            self.check_capture(last_seed_index, player_tracker)
            if last_seed_index == STORES[player_tracker]:
                print(f"{self.names[player_tracker]} gets an extra turn!")
            else:
                player_tracker = 1 - player_tracker
        self.print_winner()
    
    def game_over(self):
        """Determine whether a round is over.
        
        A round is considered over when one player's pits are all empty.
        
        Returns:
            bool: True if the game is over, otherwise False.
        """
        return sum(self.board[0:6]) == 0 or sum(self.board[7:13]) == 0
    
    def score(self, player):
        """Calculate a player's score.
        
        Args:
            player (int): player's index (0 or 1).
        
        Returns:
            int: the requested player's score.
        """
        start = 0 if player == 0 else 7
        end = start + 7
        return sum(self.board[start:end])
    
    def is_own_pit(self, pit, player):
        """Determine if pit belongs to player.
        
        Args:
            pit (int): index into self.board.
            player (int): player's index (0 or 1).
        
        Returns:
            bool: True if pit belongs to player.
        """
        first_pit = 0 if player == 0 else 7
        store = first_pit + 6
        return first_pit <= pit <= store
    
    def play(self):
        """Manage game play.
        
        After each round, ask players if they would like to play again.
        
        Side effects:
            Displays information in the terminal.
            Calls methods that modify self.board.
        """
        with TERM.fullscreen():
            while True:
                try:
                    self.play_round()
                    if not self.play_again():
                        sys.exit(0)
                except SystemExit:
                    print("Thanks for playing!")
                    sleep(PAUSE*3)
                    raise
        
    def play_again(self):
        """Ask players if they would like to play another round.

        Returns:
            bool: True if players choose to keep playing, otherwise False.
        
        Side effects:
            Displays information in the terminal.
        """
        print()
        while True:
            response = (input("Would you like to play again (y/n)? ")
                        .strip()
                        .lower()[0])
            if response not in "ny":
                print("Please type 'y' or 'n'.")
                continue
            return response == "y"
    
    def print_board(self, pause=PAUSE):
        """Displays the board in the terminal and pauses momentarily.

        Args:
            pause (float, optional): duration to pause before allowing the
                program to continue. Expressed in seconds. Defaults to PAUSE.
        
        Side effects:
            Displays information in the terminal.
            Delays program execution for a brief amount of time.
        """
        template = (TEMPLATE
                    .replace("<NAME0>", self.names[0])
                    .replace("<NAME1>", self.names[1])
                    .replace("<SP>", " "*len(self.names[1])))
        print(template.format(*(self.board[6::-1]+self.board[7:])))
        sleep(pause)

    def print_winner(self):
        """Display information about the winner of a round.
        
        Side effects:
            Displays information in the terminal.
        """
        self.print_board()
        print()
        score0 = self.score(0)
        score1 = self.score(1)
        if score0 == score1:
            print("Tie game!")
        else:
            winner = 0 if score0 > score1 else 1
            winner_score = max(score0, score1)
            loser_score = min(score0, score1)
            print(f"{self.names[winner]} wins {winner_score} to {loser_score}.")


#####
# Code to run the program
#####

def parse_args(arglist):
    """Parse command-line arguments.
    
    Expect two required arguments (the names of two players).
    
    Returns:
        namespace: a namespace with two attributes: name0 and name1, both
        strings.
    """
    parser = ArgumentParser()
    parser.add_argument("name0", help="the first player's name")
    parser.add_argument("name1", help="the second player's name")
    return parser.parse_args(arglist)


if __name__ == "__main__":
    args = parse_args(sys.argv[1:])
    game = Mancala(args.name0, args.name1)
    game.play()
