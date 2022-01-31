import json
import string
from collections import defaultdict

from word_list_source.word_list_generator import get_word_list


COMMON_WORDS = common_words = get_word_list()

BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
GREY    = '\33[90m'
RED = '\033[91m'
ENDC = '\033[0m'
BOLD = '\033[1m'


class WordleGuesser:
    def __init__(self):
        self.current_turn = 0
        self.results_tally = []

        self.correct_letters = []
        self.exact_matches = {pos: None for pos in range(5)}
        self.partial_matches = {pos: [] for pos in range(5)}
        
        self.word_pool = COMMON_WORDS
        self.available_letters = self.get_letter_list()
        self.position_uses_per_letter = {l: [0 for i in range(5)] for l in list(string.ascii_lowercase)}
        self.likely_letters_by_position = [[] for pos in range(5)]
        
        self.calculate_position_uses_per_letter()
        self.calculate_likely_letters_by_position()
        self.words_by_usefulness = []
        self.words_by_commonness = []
        self.usefulness_weight = 0
        self.commonness_weight = 0


    def play_game(self):
        input("Press Enter to start.")
        done = False
        while not done and self.current_turn < 6:
            self.current_turn += 1
            guess = self.next_guess()
            if not guess:
                print('No more words to guess.')
                done = True
                continue
            print(f"{BLUE}Your next guess is {ENDC}{BOLD}{guess}{ENDC}")
            result = input(
                f"{GREEN}Enter result (_ = wrong, a = partial, A = exact){GREEN}:{ENDC} ")
            result = self.validate_result(guess, result)
            self.handle_display(guess, result)
            done = self.process_result(guess, result)
        print(f"{ENDC}Thanks for playing.")


    def validate_result(self, guess, result):
        msg = None
        if len(result) != 5:
            msg = 'Improper amount of characters in result.'
        elif not all([l in result.lower() for l in self.correct_letters]):
            msg = "Expected letters not in result."
        else:
            for i, l in enumerate(result):
                if self.exact_matches[i]:
                    if l.islower() or l.lower() != self.exact_matches[i]:
                        msg = "Earlier exact match not reflected in result."
                if l not in ['-', '_'] and l.lower() != guess[i]:
                    msg = "Letter in result does not reflect guess."
        if not msg:
            return result
        new_result = input(f'{RED}{msg}\n{ENDC}Please re-enter result: ')
        return self.validate_result(guess, new_result)


    def next_guess(self):
        self.calculate_weights()
        self.sort_word_pool()
        confirmed = False
        guess = ''
        i = 0
        while not confirmed:
            if i + 1 > len(self.word_pool):
                return None
            guess = self.word_pool[i]
            confirm = input(f'{ENDC}\nGuess #{self.current_turn}:\n{GREEN}Would you like to guess {BOLD}{guess}{ENDC}{GREEN}? (Y/n) {ENDC}')
            if confirm not in ['n', 'N']:
                confirmed = True
            i += 1
        return guess
    
    
    def process_result(self, guess, result):
        if result == result.upper() and all([x not in result for x in ['_', '-']]):
            print(f"{ENDC}{BOLD}Got it in {self.current_turn}!{ENDC}")
            return True
        self.word_pool.remove(guess)
        for i, l in enumerate(result):
            if l in ['_', '-']:
                if guess[i].upper() not in result:
                    try:
                        self.available_letters.remove(guess[i])
                    except:
                        continue
                self.partial_matches[i].append(guess[i])
            elif l.islower():
                if l not in self.correct_letters:
                    self.correct_letters.append(l)
                self.partial_matches[i].append(l)
            elif l.isupper():
                if l.lower() not in self.correct_letters:
                    self.correct_letters.append(l.lower())
                self.exact_matches[i] = l.lower()
            else:
                raise Exception('Incorrect character given')
        self.prune_word_pool()
        return False

    
    def sort_word_pool(self):
        self.calculate_position_uses_per_letter()
        self.calculate_likely_letters_by_position()
        self.words_by_usefulness = sorted(self.word_pool, key=self.get_usefulness, reverse=True)
        self.words_by_commonness = sorted(self.word_pool, key=self.get_commonness, reverse=True)
        sorted_words = sorted(self.word_pool, key=self.score_word, reverse=True)
        self.word_pool = sorted_words
        

    def calculate_position_uses_per_letter(self):
        for word in self.word_pool:
            for i, l in enumerate(word):
                self.position_uses_per_letter[l][i] += 1


    def calculate_likely_letters_by_position(self):
        for p in range(5):
            likely_letters = sorted([l for l, i in self.position_uses_per_letter.items(
            )], key=lambda l: self.position_uses_per_letter[l][p], reverse=True)
            self.likely_letters_by_position[p] = likely_letters
            
    
    def calculate_weights(self):
        known_letters_in_position = [l for l in self.exact_matches.values() if l]
        usefulness_weight = (5 - len(self.correct_letters)) + (5 - self.current_turn) - len(known_letters_in_position)
        commonness_weight = len(self.correct_letters) + len(known_letters_in_position) + self.current_turn
        self.usefulness_weight = max(usefulness_weight, 0)
        self.commonness_weight = max(commonness_weight, 0)
    
    
    def get_usefulness(self, word):
        usefulness = 0
        for i, l in enumerate(word):
            usefulness += self.position_uses_per_letter[l][i] / word.count(l)
        variety_of_letters = len(set(word)) * (1/5)
        usefulness = usefulness * variety_of_letters
        return usefulness


    def get_commonness(self, word):
        commonness = (len(COMMON_WORDS) / (COMMON_WORDS.index(word) + 1)) / len(COMMON_WORDS)
        return commonness

    
    def score_word(self, word):
        usefulness = (len(self.words_by_usefulness) - self.words_by_usefulness.index(word) + 1) / len(self.words_by_usefulness)
        commonness = (len(self.words_by_commonness) - self.words_by_commonness.index(word)) / len(self.words_by_commonness)
        
        usefulness = usefulness * self.usefulness_weight
        commonness = commonness * self.commonness_weight
        score = usefulness + commonness
        return score


    def get_letter_list(self):
        all_letters = defaultdict(int)
        for word in COMMON_WORDS:
            for letter in word:
                if letter.isalpha():
                    all_letters[letter] = all_letters[letter] + 1
        return sorted(all_letters.keys(), key=lambda w: all_letters[w], reverse=True)


    def is_possible_word(self, word):
        has_no_unavailable_letters = all([l in self.available_letters for l in word])
        right_letters_in_all_known_positions = all([word[p] in l for p, l in self.exact_matches.items() if l])
        no_letters_in_wrong_positions = all([word[p] not in self.partial_matches[p] for p in range(5)])
        contains_known_letters = all([l in word for l in self.correct_letters])
        is_possible = all([has_no_unavailable_letters, right_letters_in_all_known_positions,
                           no_letters_in_wrong_positions, contains_known_letters])
        return is_possible


    def prune_word_pool(self):
        available_words = filter(self.is_possible_word, self.word_pool)
        self.word_pool = list(available_words)


    def printable_result(self, guess, result):
        printable = f'{ENDC}  '
        for i, l in enumerate(result):
            if l in ['_', '-']:
                printable += GREY + guess[i].upper()
            elif l.islower():
                printable += YELLOW + l.upper()
            elif l.isupper():
                printable += BOLD + GREEN + l + ENDC
        return printable + ENDC
    

    def handle_display(self, guess, result):
        turn = self.printable_result(guess, result)
        self.results_tally.append(turn)
        for t in self.results_tally:
            print(t)


if __name__ == '__main__':
    w = WordleGuesser()
    w.play_game()
