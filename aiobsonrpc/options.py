# -*- coding: utf-8 -*-

"""
Option definitions and default options.
"""

from .misc import default_id_generator


class NoArgumentsPresentation(object):

    OMIT = 'omit'

    EMPTY_ARRAY = 'empty-array'

    EMPTY_OBJECT = 'empty-object'


class DefaultOptionsMixin(object):

    connection_id = ''

    id_generator = default_id_generator()

    concurrent_notification_handling = None

    no_arguments_presentation = NoArgumentsPresentation.OMIT

    custom_codec_implementation = None
