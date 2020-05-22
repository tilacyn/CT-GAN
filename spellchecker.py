import codecs
import collections
import Levenshtein
import re
from operator import itemgetter
import os

russian_regex = re.compile('^[а-яА-Я]+$')


def is_russian(word):
    return russian_regex.match(word)


REPLACE = 'replace'
DELETE = 'delete'
INSERT = 'insert'


class ErrorModel:
    def __init__(self, a, b, c):
        self.operation_probability = collections.defaultdict(int)
        self.action_probability = collections.defaultdict(int)
        self.dependent_probability = collections.defaultdict(int)
        self.a = a
        self.b = b
        self.c = c

    def calculate_word_mutations(self, word, expected_word):
        def get_mutation(i):
            if i not in edit_indexes:
                return (REPLACE, word[i], word[i])
            else:
                cur_edit = edit_ops[0]
                if cur_edit[0] == REPLACE:
                    return (REPLACE, word[cur_edit[1]], expected_word[cur_edit[2]])
                elif cur_edit[0] == DELETE:
                    return (DELETE, word[cur_edit[1]])
                else:
                    return (INSERT, expected_word[cur_edit[2]])

        edit_ops = Levenshtein.editops(word, expected_word)
        edit_indexes = set(map(lambda op: op[1], edit_ops))
        return [get_mutation(i) for i in range(len(word))]

    def calculate_probabilities(self, word_mutation):
        prev_op = None
        for mut in word_mutation:
            self.operation_probability[mut[0]] += 1
            self.action_probability[mut] += 1
            self.dependent_probability[(prev_op, mut)] += 1
            prev_op = mut

    def build(self):
        with codecs.open("train.csv", 'r', 'utf8') as train:
            train.readline()
            i = 0
            for line in train:
                word, expected_word = line.split(',')
                word, expected_word = word.strip(), expected_word.strip()
                if (is_russian(word)):
                    word_mutations = self.calculate_word_mutations(word, expected_word)
                    self.calculate_probabilities(word_mutations)

    def compute_correction_probability(self, correction, prev_op):
        return self.a * self.operation_probability[correction[0]] + \
               self.b * self.action_probability[correction] + \
               self.c * self.dependent_probability[(prev_op, correction)]


class TrieModel:
    def __init__(self):
        self.frequencies = collections.defaultdict(int)
        self.trie = self.build_trie()

    def add(self, root, word, freq):
        node = root
        for symbol in word:
            found_in_child = False
            for child in node.children:
                if child.symbol == symbol:
                    node = child
                    found_in_child = True
                    break
            if not found_in_child:
                new_node = TrieNode(symbol)
                node.children.append(new_node)
                node = new_node
        node.terminal = True
        node.set_f(freq)
        node.set_w(word)

    def build_trie(self):
        root = TrieNode("*")
        with codecs.open('words.csv', 'r', 'utf8') as words:
            words.readline()
            for line in words:
                processed_line = line.split(',')
                word, freq = processed_line[0].strip(), int(processed_line[1].strip())
                if is_russian(word):
                    self.add(root, word, freq)
                    self.frequencies[word] = freq
        return root

    def correct_ratio(self, fix, word):
        return self.frequencies[fix] / self.frequencies[word]

    def best_ratio(self, fix1, fix2):
        return self.frequencies[fix1] / self.frequencies[fix2]


class TrieNode:
    def __init__(self, symbol):
        self.symbol = symbol
        self.children = []
        self.terminal = False
        self.w = None
        self.f = None

    def set_f(self, f):
        self.f = f

    def set_w(self, w):
        self.w = w

    def go(self, path):
        path += self.symbol
        print(path)
        if self.terminal:
            print(self.f)
            return
        for c in self.children:
            c.go(path)


class SpellChecker:
    def __init__(self):
        a = 0
        b = 0.9
        c = 0.1
        self.top = 3
        self.correct_ratio_threshold = 5.0
        self.best_ratio_threshold = 3.0
        self.trie_model = TrieModel()
        self.error_model = ErrorModel(a, b, c)
        self.error_model.build()

    def _stop_recursion(self, node, word, correction_predicts, corrections_num):
        if corrections_num > 1:
            return True
        if not node.terminal and not word:
            return True
        if node.terminal and not word:
            correction_predicts.append((node.word, node.freq))
            return True

    def _do_correct(self, node, word, correction_predicts, prev_op=None, corrections_num=0):
        if self._stop_recursion(node, word, correction_predicts, corrections_num):
            return
        corrections = []
        cur_symbol = word[0]
        for idx in range(len(node.children)):
            child = node.children[idx]
            if (len(word) >= 4) or (cur_symbol == child.symbol):
                corrections.append((REPLACE, cur_symbol, child.symbol, idx))
        corrections_probs = list(
            map(lambda cor: self.error_model.compute_correction_probability(cor[0:3], prev_op), corrections))
        corrections_statistic = sorted(list(zip(corrections, corrections_probs)), key=itemgetter(1), reverse=True)
        top_corrections = corrections_statistic[0:self.top]
        for correction, _ in top_corrections:
            cur_char, fixed_char, idx = correction[1:4]
            next_node = node.children[idx]
            self._do_correct(next_node, word[1:], correction_predicts, correction[0:3],
                             corrections_num if cur_char == fixed_char else corrections_num + 1)

    def correct(self, word):
        if is_russian(word) and len(word) < 100:
            correction_predicts = []
            # print('correct word ' + word)
            self._do_correct(self.trie_model.trie, word, correction_predicts)
            best_corrections = sorted(correction_predicts, key=itemgetter(1), reverse=True)
            result = best_corrections[0] if self.trie_model.correct_ratio(best_corrections[0][0],
                                                                          word) >= self.correct_ratio_threshold else word
            if len(best_corrections) > 1:
                result = best_corrections[0][0] if self.trie_model.best_ratio(best_corrections[0][0],
                                                                              best_corrections[1][
                                                                                  0]) >= self.best_ratio_threshold else word
            return result
        else:
            return word


def create_submission(no_fix_file, submission_file):
    spellchecker = SpellChecker()

    with codecs.open(no_fix_file, 'r', 'utf8') as file:
        with codecs.open(submission_file, 'w', 'utf8') as submission:
            header = file.readline()
            submission.write(header)
            for line in file:
                processed_line = line.split(',')
                word = processed_line[0]
                if is_russian(word):
                    corrected = spellchecker.correct(word)
                    submission.write('{},{}\n'.format(word, corrected))
                else:
                    submission.write(line)
