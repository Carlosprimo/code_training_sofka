import copy
import json
import requests
import time
import psycopg2
from decouple import config

class Database:
    def __init__(self, conn) -> None:
        self.conn = conn

class WordleGame:
    def __init__(self, list_of_words: list) -> None:
        """WordleGame class constructor

        Args:
            list_of_words (list): List of words
        """
        self.__list_of_words = list_of_words
        self.auxiliary_functions = AuxiliaryFunctions()

    def words_filter_initial_requirements(
            self, length: int, number_of_vowels: int, 
            number_of_consonants: int) -> list:
        """Filter out words that do not meet the initial requirements

        Args:
            length (int): Length that the words must have
            number_of_vowels (int): Number of vowels that words must have
            number_of_consonants (int): Number of consonants that words must have
        Returns:
            list: List of words that have the same length, number of vowels and
            consonants as the target word
        """
        # Filtering of words that do not match the length of the target word
        wordlist_with_single_length = (self.auxiliary_functions.
                                        filter_words_by_length(
            self.__list_of_words, length
        ))
        # Filtering of words that do not match the number of vowels in the
        # target word
        set_of_vowels = 'aeiou'
        wordlist_specified_number_vowels = (self.auxiliary_functions.
                                            filter_words_containing_certain_letters(
            wordlist_with_single_length, set_of_vowels, number_of_vowels
        ))
        # Filtering of words that do not match the number of consonants of the
        # target word
        set_of_consonants = 'bcdfghjklmnñpqrstvwxyz'
        wordlist_specified_number_consonants = (self.auxiliary_functions.
                                                filter_words_containing_certain_letters(
            wordlist_specified_number_vowels, set_of_consonants, 
            number_of_consonants
        ))
        return wordlist_specified_number_consonants

    def filter_words(
            self, wordlist: list, last_attempt: str,
            right_letters_in_right_positions: list,
            right_letters_in_wrong_positions: list) -> list:
        """Filter out words that do not satisfy the requirements.

        Args:
            wordlist (list): List of words
            last_attempt (str): Word used in the last attempt
            right_letters_in_right_positions (list): Boolean list containing the 
            correct letter positions
            right_letters_in_wrong_positions (list): List containing the correct 
            letters in the wrong positions

        Returns:
            list: List of filtered words 
        """
        # Filtering of words with letters in the correct position
        first_filter = self.__filter_words_with_right_letters_right_positions(
            wordlist, last_attempt, right_letters_in_right_positions
        )
        # Filter out words containing wrong letters
        second_filter = self.__filtering_words_with_bad_letters(
            first_filter,
            last_attempt,
            right_letters_in_wrong_positions,
            right_letters_in_right_positions,
        )
        # Filtering of words that have correct letters but with a wrong position
        third_filter = self.__filter_words_with_right_letters_bad_positions(
            last_attempt,
            second_filter,
            right_letters_in_wrong_positions,
            right_letters_in_right_positions,
        )
        return third_filter

    def __filter_words_with_right_letters_right_positions(
            self, wordlist: list, last_attempt: str, 
            right_letters_in_right_positions: list) -> list:
        """Filters out words containing letters in wrong positions

        Args:
            wordlist (list): List of words
            last_attempt (str): Word used in the last attempt
            right_letters_in_right_positions (list): Boolean list containing the 
            correct letter positions

        Returns:
            list: List of words with the letters in the correct position
        """
        return list(
            filter(
                lambda word: word
                if (self.auxiliary_functions.
                        comparison_position_letter_with_array_booleans(
                    last_attempt, word, right_letters_in_right_positions
                ))
                else None,
                wordlist,
            )
        )

    def __filter_words_with_right_letters_bad_positions(
            self, last_attempt: str, list_of_words: list,
            right_letters_in_bad_positions: list,
            right_letters_in_right_positions: list,) -> list:
        """Filtering of words that have correct letters but with a wrong 
        position

        Args:
            last_attempt (str): Word used in the last attempt
            list_of_words (list): List of words
            right_letters_in_bad_positions (list): List containing the correct 
            letters in the wrong positions
            right_letters_in_right_positions (list): Boolean list containing the
            correct letter positions

        Returns:
            list: List of words containing the correct letters, but in the wrong 
            position
        """
        # All words containing the letters known to belong to the target word 
        # are selected
        wordlist_contain_right_letter = []
        for word in list_of_words:
            sw = True
            for right_letter in right_letters_in_bad_positions:
                if not right_letter in word:
                    sw = False
                    break
            if sw:
                wordlist_contain_right_letter.append(word)
        if len(wordlist_contain_right_letter) == 0:
            return list_of_words
        # Eliminate words that have correct letters, but are known not to be in a
        # certain position
        wordslist_with_letters_wrong_positions = []
        # Creating a list of words that have correct letters, but are known not 
        # to be in a certain position
        for word in wordlist_contain_right_letter:
            for index in range(len(right_letters_in_right_positions)):
                if (
                    not right_letters_in_right_positions[index]
                    and word[index] == last_attempt[index]
                ):
                    wordslist_with_letters_wrong_positions.append(word)
        # Eliminating the words with an erroneous position with the list that 
        # was generated previously
        for word in list(set(wordslist_with_letters_wrong_positions)):
            wordlist_contain_right_letter.remove(word)
        return wordlist_contain_right_letter

    def __filtering_words_with_bad_letters(
            self, list_of_words: list, last_attempt: str,
            right_letters_in_bad_positions: list,
            right_letters_in_right_positions: list,) -> list:
        """Filter out words containing wrong letters

        Args:
            list_of_words (list): List of words
            last_attempt (str): Word used in the last attempt
            right_letters_in_bad_positions (list): List containing the correct 
            letters in the wrong positions
            right_letters_in_right_positions (list): Boolean list containing the 
            correct letter positions

        Returns:
            list: List of words that do not contain letters that the target word
            is known not to possess
        """
        # The letters that the target word does not have and that are found in 
        # the last attempt are found
        letters_not_located_in_wordtarget = []
        right_letter = [
            last_attempt[index]
            for index in range(len(right_letters_in_right_positions))
            if right_letters_in_right_positions[index]
        ]
        for i in range(len(last_attempt)):
            if (
                not last_attempt[i] in right_letters_in_bad_positions
                and not right_letters_in_right_positions[i]
                and not last_attempt[i] in right_letter
            ):
                letters_not_located_in_wordtarget.append(last_attempt[i])
        return list(
            filter(
                lambda word: word
                if self.auxiliary_functions.verify_word_no_wrong_letter(
                    letters_not_located_in_wordtarget, word
                )
                else None,
                list_of_words,
            )
        )

    def __Selection_word_with_highest_number_different_letters(
            self, list_of_word: list) -> list:
        """Select the set of words with the highest number of different letters

        Args:
            list_of_word (list): List of words

        Returns:
            list: List of words with the highest number of different letters
        """
        large = -1
        wordlist_with_highest_number_different_letters = []
        for word in list_of_word:
            tam = len(set(list(word)))
            if large < tam:
                large = tam
                wordlist_with_highest_number_different_letters = []
            if large == tam:
                wordlist_with_highest_number_different_letters.append(word)

        return wordlist_with_highest_number_different_letters

    def select_word(
            self, possible_words: list, length_target_word: int) -> str:
        """Select the word most likely to be correct

        Args:
            possible_words (list): List of words
            length_target_word (int): Length of the word target

        Returns:
            str: Selected word
        """
        wordlist_highest_number_different_letters = self.__Selection_word_with_highest_number_different_letters(
            possible_words
        )
        alpabhet = 'aeioubcdfghjklmnñpqrstvwxyz'
        alpabhet_list = list(alpabhet)
        # The word is selected by comparing the frequency of the letters in the 
        # word list, from left to right
        for index in range(length_target_word):
            large = -1
            letter_word = []
            letter_select = ""
            for word in wordlist_highest_number_different_letters:
                letter_word.append(word[index])
            for letter in alpabhet_list:
                amount = self.auxiliary_functions.letter_counter(letter_word, letter)
                if large < amount:
                    large = amount
                    letter_select = letter
            words_to_remove = []
            for word in wordlist_highest_number_different_letters:
                if word[index] != letter_select:
                    words_to_remove.append(word)
            for word in words_to_remove:
                wordlist_highest_number_different_letters.remove(word)
        return wordlist_highest_number_different_letters[0]


class AuxiliaryFunctions:
    def __init__(self):
        """AuxiliaryFunctions class constructor
        """
        self

    def filter_words_containing_certain_letters(
            self, list_of_words: list, string_of_letters: str,
            number_of_letters_allowed: int,) -> list:
        """Filters out words that do not contain a specified number of letters

        Args:
            list_of_words (list): List of words
            string_of_letters (str): String containing the letters to be checked
            number_of_letters_allowed (int): Number of the string of letters that must be in the word

        Returns:
            list: List of words that satisfy the specified number of letters.
        """
        return list(
            filter(
                lambda word: word
                if self.letter_counter(word, string_of_letters)
                == number_of_letters_allowed
                else None,
                list_of_words,
            )
        )

    def filter_words_by_length(
            self, list_of_words: list, length: int) -> list:
        """Filters out words that do not have the specified length

        Args:
            list_of_words (list): List of words
            length (int): Length that the words must have

        Returns:
            list: List of words with the same length
        """
        return list(
            filter(lambda word: word if (len(word) == length) else None, list_of_words)
        )

    def letter_counter(self, word: str, set_of_letters: str) -> int:
        """Count the number of times a letter appears

        Args:
            word (str): Word whose letters must be counted
            set_of_letters (str): Letters to be counted

        Returns:
            int: Number of letters found in the word
        """
        return sum(map(word.count, set_of_letters))

    def comparison_position_letter_with_array_booleans(
            self, last_attempt: str, word: str, boolean_list: list) -> bool:
        """Returns if the word to compare and the target match, plus which boolean list validates that they should be the same

        Args:
            last_attempt (str): Word used in the last attempt
            word (str): word to be compared with an array of booleans
            boolean_list (list): List of booleans

        Returns:
            bool: The comparison between a word and the target word is satisfactory
        """
        list_of_letters_in_the_correct_position = list(
            map(
                lambda index: True
                if last_attempt[index] == word[index] and boolean_list[index]
                else False,
                range(len(word)),
            )
        )
        return sum(list_of_letters_in_the_correct_position) == sum(boolean_list)

    def verify_word_no_wrong_letter(
            self, letters_not_located_in_the_target_word: list, word: str) -> bool:
        """Check that the word does not have any wrong letters

        Args:
            letters_not_located_in_the_target_word (list): list of letters not found 
            in the target word
            word (str): Word to be checked that does not contain letters not found 
            in the target word

        Returns:
            bool: Returns True if the word has letters not found in the target word
        """
        list_aux = list(
            map(
                lambda letter: True
                if letter in letters_not_located_in_the_target_word
                else False,
                list(word),
            )
        )
        return sum(list_aux) == 0


class Play:
    def __init__(
            self, user_name_api: str, password_api: str, hostname_db: str, 
            username_db: str, password_db: str, dbname: str, api_get_url :str,
            api_post_url: str) -> None:
        """Play class constructor

        Args:
            user_name (str): API account username
            password (str): API account password

        """
        session = requests.Session()
        session.auth = (user_name_api, password_api)
        connection = psycopg2.connect(
            host=hostname_db,
            user=username_db,
            password=password_db,
            dbname=dbname
        )
        self.wordle_game = None
        self.play(session, connection, api_get_url, api_post_url)

    def init_game(self, url: str, session) -> json:
        """Init the game by making the API request

        Args:
            url (str): API URL

        Returns:
            json: API response in json format
        """
        response = session.get(url)
        return response.json()

    def find_word(
            self, length_target_word: int, number_vowels: int, 
            number_consonants: int, api_post_url: str, session) -> None:
        """Find the target word

        Args:
            length_target_word (int): Length of the word target
            number_vowels (int): Number of vowels in the target word
            number_consonants (int): Number of consonants in the target word
        """
        possible_initial_words = self.wordle_game.words_filter_initial_requirements(
            length_target_word, number_vowels, number_consonants
        )
        # Select the first word
        first_attempt = self.wordle_game.select_word(
            possible_initial_words, length_target_word
        )
        attempt_data = self.send_word(first_attempt, api_post_url, session)
        attempt_word = attempt_data.get('word_sent')
        attempt_count = 0
        possible_words = copy.deepcopy(possible_initial_words)
        position_array = attempt_data.get('position_array')
        right_letters_in_wrong_positions = attempt_data.get(
            'right_letters_in_wrong_positions'
        )

        currrent_attempt = attempt_data.get('current_attemps')
        # Make the five attempts allowed by the game to find the word
        while attempt_count < 5:
            print(f'Attempt {currrent_attempt}: {attempt_word}')
            print(attempt_data)
            if attempt_data.get('score') == 1.0:
                print(f'Word found: {attempt_word}')
                break
            else:
                possible_words = copy.deepcopy(
                    self.wordle_game.filter_words(
                        possible_words,
                        attempt_word,
                        position_array,
                        right_letters_in_wrong_positions,
                    )
                )
                attempt_word = copy.deepcopy(
                    self.wordle_game.select_word(possible_words, length_target_word)
                )
                attempt_data = copy.deepcopy(self.send_word(attempt_word, api_post_url, session))
                position_array = copy.deepcopy(attempt_data.get('position_array'))
                right_letters_in_wrong_positions = copy.deepcopy(
                    attempt_data.get("right_letters_in_wrong_positions")
                )
                currrent_attempt = copy.deepcopy(attempt_data.get('current_attemps'))
            attempt_count += 1

    def send_word(self, word: str, api_post_url: str, session) -> json:
        """Sends the selected word to the API to verify if it is correct

        Args:
            word (str): Selected word

        Returns:
            json: API response when sending a word
        """
        data = {'result_word': word}
        response = session.post(api_post_url,json=data)
        return response.json()

    def play(
        self, session, connection, api_get_url: str, api_post_url: str) -> None:
        initial_application_time = time.time()
        word_bank_management = WordBankManagement()
        # Create a list of words
        word_bank_management.create_list_of_words(
            r'C:\Users\carlo\Documents\WordleGame\bancoPalabrasCarlos.txt'
        )
        wordlist = word_bank_management.get_list_of_words()
        # Create a wordle game
        wordle_game = WordleGame(wordlist)
        self.wordle_game = wordle_game
        # # Initialize the game
        initial_time_find_word = time.time()
        word_data = self.init_game(api_get_url, session)
        print(word_data)
        length_target_word = word_data.get('length_word')
        number_of_vowels = word_data.get('vowels')
        number_of_consonants = word_data.get('consonants')
        # Play the game and find the target word
        self.find_word(length_target_word, number_of_vowels, number_of_consonants, api_post_url, session)
        final_application_time = time.time()
        total_application_time = final_application_time - initial_application_time
        total_time_find_word = final_application_time - initial_time_find_word
        print('')
        print(
            f'The total time for the execution of the application is {total_application_time} seconds'
        )
        print(f'The total time to find the word is {total_time_find_word} seconds')
    
class WordBankManagement:
    def __init__(self) -> None:
        """WordBankManagement class constructor
        """
        self.__list_of_words = []

    def create_list_of_words(self, url_words_bank: str) -> None:
        """Create a list of words
        Args:
            url_words_bank (str): Location of the txt file containing the words
        """
        try:
            with open(
                file=url_words_bank, mode="r", encoding="utf-8"
            ) as word_bank_file:
                self.__set_list_of_words(word_bank_file.readline().split())
        except:
            print('Error reading the file containing the words')

    def __set_list_of_words(self, list_of_words: list) -> None:
        """Assign word list

        Args:
            list_of_words (list): List of words 
        """
        self.__list_of_words = list_of_words

    def get_list_of_words(self) -> list:
        """Return the list of words

        Returns:
            list: List of words
        """
        return self.__list_of_words

if __name__ == '__main__':
    user_name_api = config('USERNAME_API')
    password_api = config('PASSWORD_API')
    api_get_url = config('URL_API_GET')
    api_post_url = config('URL_API_POST')
    hostname_db = config('POSTGRESQL_HOSTNAME')
    username_db = config('POSTGRESQL_USERNAME')
    password_db = config('POSTGRESQL_PASSWORD')
    dbname = config('POSTGRESQL_DBNAME')

    Play(
        user_name_api, password_api, 
        hostname_db, username_db, password_db, dbname,
        api_get_url, api_post_url)