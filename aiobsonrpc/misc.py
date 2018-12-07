# -*- coding: utf-8 -*-

"""
Miscellaneous helper functions.
"""


def default_id_generator():
    msg_id = 0
    while True:
        msg_id += 1
        yield msg_id
