# SPDX-FileCopyrightText: 2024 University of Washington
#
# SPDX-License-Identifier: BSD-3-Clause

"""
This module sets the default logging level for NcCut and defines ways for the user to access and adjust the logging
level. NcCut itself does not implement logging messages but it's dependencies do.
"""


import logging

# Configure the root logger
logging.getLogger().setLevel(logging.WARNING)


def set_logging_level(level):
    """
    Set the logging level for the root logger and specific dependency loggers.
    This allows end users to change the logging level.

    Parameters:
        level (str): The logging level to set (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {level}')

    # Set the level for the root logger
    logging.getLogger().setLevel(numeric_level)


def get_logging_level():
    """
    Get the current logging level for the root logger.

    Returns:
        str: The current logging level (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')
    """
    level = logging.getLogger().level
    return logging.getLevelName(level)
