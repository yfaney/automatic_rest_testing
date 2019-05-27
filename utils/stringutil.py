#!/usr/bin/python

import logging as logger
import operator
import re
import sys
from difflib import SequenceMatcher

"""
This script handles useful string manipulations.
Author Younghwan Jang (YJ048444)
at: https://github.cerner.com/curo/splunk_jira_tagger
"""

#if(DEBUG is not None):
#    logger.basicConfig(format='%(asctime)s:%(levelname)s:%(message)s', level=logger.DEBUG)


def cut_msg(msg, limit=50):
    # type: (str, int) -> str
    """
    Cuts the text and put three dots at the end of the string.

    :param msg: The text message to be cut
    :param limit: The number of limit to be cut.

    :return: The cut text.
    """
    if len(msg) > limit:
        return "%s..." % msg[:limit - 3]
    else:
        return msg


def is_similar_between(a, b, ratio):
    # type: (str, str, float) -> bool
    """
    Determines if the two string are similar with the provided probability.

    :param a: The first string.
    :param b: The second string.
    :param ratio: The ratio or probability if two strings are similar.

    :return: True if two are similar with the probability, False otherwise.
    """
    return True if (SequenceMatcher(None, a, b).ratio() > ratio) else False


def find_first_common_char(left, right):
    # type: (str, str) -> (int, int)
    """
    Finds the first common characters between two strings.

    :param left: The left string
    :param right: The right string

    :returns: The indexes of two strings which occurs first.
    """
    first_a = a_occur = sys.maxint
    first_b = b_occur = sys.maxint
    for i in range(len(left)):
        if left[i] == "*":
            continue
        if a_occur > right.find(left[i]) >= 0:
            a_occur = right.find(left[i])
            first_a = i
            if a_occur == 0:
                break
    for i in range(len(right)):
        if right[i] == "*":
            continue
        if b_occur > left.find(right[i]) >= 0:
            b_occur = left.find(right[i])
            first_b = i
            if b_occur == 0:
                break
    return first_a, first_b


def common_string(left, right):
    # type: (str, str) -> str
    """
    Retrieves common query string for two similar strings.
    For example, you will get "*bcdefg*abcdefg*k**m" from "abcdefghijklmnabcdefghijklmn" and "bcdefgabcdefgkkkkkmk"
    This uses heuristic algorithm so it might not give you the most efficient common string.

    :param left: first string
    :param right: right string

    :return: The generated common string
    """
    logger.debug("Comparing %s and %s" % (left, right))
    c = []
    count_a, count_b = find_first_common_char(left, right)
    if count_a > len(left) - 1 or count_b > len(right) - 1:
        return ""
    if count_a > count_b > 0:
        count_a = 0
    elif count_b > count_a > 0:
        count_b = 0
    elif count_a == count_b:
        if left[count_a] != right[count_b]:
            if len(left) > len(right):
                count_b = 0
            else:
                count_a = 0
    if count_a > 0 or count_b > 0:
        c.append("*")
    logger.debug("Starting from index %d and %d" % (count_a, count_b))
    while count_a < len(left) and count_b < len(right) and left[count_a] == right[count_b]:
        c.append(left[count_a])
        count_a += 1
        count_b += 1
    logger.debug("Appended: %s" % "".join(c))
    next_left = left[count_a:]
    next_right = right[count_b:]
    c.append(common_string(next_left, next_right))
    return "".join(c)


def is_all_characters_same(string_list, index):
    # type: (list, int) -> bool
    """
    Determines if all characters of the strings at the specified index are same.

    :param string_list: The list of string.
    :param index: The index for the characters to be compared

    :return: True if all characters are same, False otherwise.
    """
    char_compared = string_list[0][index]
    for string_item in string_list:
        if char_compared != string_item[index]:
            return False
    return True


def squash_asterisks(word):
    # type: (str) -> str
    """
    Squashes multiple asterisks into one

    :param word: Word that needs to be squashed

    :return: The squashed word
    """
    asterisk = False
    result = []
    for character in word:
        if character == '*':
            if asterisk:
                continue
            else:
                result.append('*')
                asterisk = True
        else:
            result.append(character)
            asterisk = False
    return ''.join(result)


def closest_match_words(string_list):
    # type: (list) -> str
    """
    Retrieves the closest match words. All string values should start with the same characters,
    or return all asterisks otherwise.
    e.g. "abcdefg" and "aacceee" gives "a*c*e**".

    :param string_list: The list of string values

    :return: The string match patterns with asterisks
    """
    if len(string_list) == 0:
        return ''
    elif len(string_list) == 1:
        return string_list[0]
    closest = []
    try:
        for index in range(len(string_list[0])):
            if is_all_characters_same(string_list, index):
                closest.append(string_list[0][index])
            else:
                closest.append('*')
    except IndexError:
        closest.append('*')
        return ''.join(closest)
    if len(string_list[0]) < len(string_list[1]):
        closest.append('*')
    return ''.join(closest)


def closest_match_sentence(sentence_list, delimiter):
    # type: (list, str) -> str
    """
    Finds the closest match sentence with the given list of string values. It replaces all number values
    into asterisks.
    e.g. "abcdefg123 abcde" and "aacceeg23 bcdef" gives "a*c*e*g* *".

    :param sentence_list: The list of string values.
    :param delimiter: Delimiter of the sentence. Generally space.

    :return: The generated closest match sentence with asterisks.
    """
    matrix = []
    result = []
    for sentence_item in sentence_list:
        matrix.append(sentence_item.split(' '))
    try:
        for index in range(len(matrix[0])):
            closest_matched_word = closest_match_words([row[index] for row in matrix])
            closest_matched_word = re.sub(r'[0-9]', '*', closest_matched_word)
            result.append(squash_asterisks(closest_matched_word))
    except IndexError:
        pass
    return delimiter.join(result)


def group_by_similar_strings(string_list, ratio):
    # type: (list, float) -> list
    """
    Group string values by similar strings.

    :param string_list: The list of string values
    :param ratio: The ratio of similarity

    :return: The list of groupped string list
    """

    if len(string_list) == 0:
        return []
    elif len(string_list) == 1:
        return string_list
    string_list = filter(lambda a: (a != "") or (a != " "), string_list)
    string_list.sort()
    result = []
    group = []
    for index in range(len(string_list) - 1):
        first_item = string_list[index]
        second_item = string_list[index + 1]
        if index == 0:
            group.append(first_item)
        if first_item[0] != second_item[0]:
            result.append(group)
            group = [second_item]
        elif is_similar_between(first_item, second_item, ratio):
            group.append(second_item)
        else:
            result.append(group)
            group = [second_item]
        if index == len(string_list) - 2:
            result.append(group)
    return result


def group_by_similar_values(string_list, key, ratio):
    # type: (list, Any, float) -> list
    """
    Group string values by similar strings.
    For example, if the list have those string values:
    ["ABCDE", "ABDEE", "ZZZZZ", "ZZZAA"]
    Then this function will return the following value:
    [["ABCDE", "ABDEE"], ["ZZZZZ", "ZZZAA"]]

    :param string_list: The list of string values
    :param key:
    :param ratio: The ratio of similarity

    :return: The list of grouped string list
    """
    if len(string_list) == 0:
        return []
    elif len(string_list) == 1:
        return string_list
    string_list = filter(lambda a: (a[key] != "") or (a[key] != " "), string_list)
    string_list.sort(key=operator.itemgetter(key))
    result = []
    group = []
    for index in range(len(string_list) - 1):
        first_item = string_list[index]
        second_item = string_list[index + 1]
        if index == 0:
            group.append(first_item)
        if first_item[key][0] != second_item[key][0]:
            result.append(group)
            group = [second_item]
        elif is_similar_between(first_item[key], second_item[key], ratio):
            group.append(second_item)
        else:
            result.append(group)
            group = [second_item]
        if index == len(string_list) - 2:
            result.append(group)
    return result


def squash_list_by_similarity(ungrouped_list, key, ratio):
    # type: (list, str, float) -> list
    """
    This function groups similar exception messages and extracts the common string value (squashes)
    and replaces different string values as asterisks(*) so that the query of eventtypes can easily contain
    similar messages by "*".
    The format of returned value will be "<Some values>*<Some values>"

    For example, if the result contains those two similar messages:
    "There is an error with user ABC001 with ID 4011234."
    "There is an error with user AEF005 with ID 1032483."
    "Unable to start MainActivity for User A."
    "Unable to start MainActivity for User B."

    Then this function will make a list of those common string
    "There is an error with user A* with ID *."
    "Unable to start MainActivity for User *."

    The intensity of squashing depends on how high the similar ratio you set here.
    If you set this value too low, the query in the created JIRA issue might include less related events as well.
    In contrast, if you set this value too high, some of JIRA issues might be duplicated with the same query.

    :param ungrouped_list: The log list
    :param key: The key that you want to squash by
    :param ratio: The similar ratio to group by. Higher gets stricter grouping

    :return: The squashed list
    """
    # Groups similar strings by the ratio, and put into each list
    groups = group_by_similar_values(ungrouped_list, key, ratio)
    result_list = []
    for group in groups:
        squashed_item = {}
        for g_key in group[0]:
            squashed_item[g_key] = group[0][g_key]
        grouped_values = [row[key] for row in group]
        squashed_item[key] = closest_match_sentence(grouped_values, " ")
        result_list.append(squashed_item)
    return result_list
