import re
import json

from word_list_source.common_words import COMMON_WORDS
from word_list_source.dictionary import DICTIONARY
from word_list_source.scrabble_dict import SCRABBLE_DICT


GREY = '\33[90m'
ENDC = '\033[0m'

print(f'{GREY}Gathering and storing word list...{ENDC}')


all_words = [w for w in DICTIONARY.keys() if len(w) == 5 and w.isalpha()]

word_list = []


def get_word_list():
    with open('word_list.json') as json_file:
        word_list = json.load(json_file)
        return word_list


for w in COMMON_WORDS:
    if w in all_words and w in SCRABBLE_DICT:
        word_list.append(w)
        all_words.remove(w)

word_list.extend(all_words)

if __name__ == '__main__':
    with open('word_list.json', 'w') as outfile:
        json.dump(word_list, outfile)
