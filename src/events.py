# https://github.com/awslabs/game-analytics-pipeline/blob/master/source/demo/publish_data.py
# this code is modified and refactored from the AWS LABS Game Analytics code to fit the rest of the code that was frankly written before I saw this
import json
import random
import time
import uuid
import numpy
import requests

# import os
# import argparse
# from datetime import datetime
# from random import choice

# Event Payload defaults
DEFAULT_EVENT_VERSION = '1.0.0'
DEFAULT_BATCH_SIZE = 100

# api url
url = "http://localhost:8080/publish"


# Returns array of UUIDS. Used for generating sets of random event data
def getUUIDs(dataType, count):
    uuids = []
    for i in range(0, count):
        uuids.append(str(uuid.uuid4()))
    return uuids


# Randomly choose an event type from preconfigured options
def getEventType():
    event_types = {
        1: 'user_registration',
        2: 'user_knockout',
        3: 'item_viewed',
        4: 'iap_transaction',
        5: 'login',
        6: 'logout',
        7: 'tutorial_progression',
        8: 'user_rank_up',
        9: 'matchmaking_start',
        10: 'matchmaking_complete',
        11: 'matchmaking_failed',
        12: 'match_start',
        13: 'match_end',
        14: 'level_started',
        15: 'level_completed',
        16: 'level_failed',
        17: 'lootbox_opened',
        18: 'user_report',
        19: 'user_sentiment'
    }
    return event_types[numpy.random.choice([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19], 1,
                                           p=[0.04, 0.05, 0.18, 0.02, 0.1, 0.06, 0.04, 0.03, 0.025, 0.025, 0.01, 0.03,
                                              0.03, 0.08, 0.08, 0.08, 0.04, 0.04, 0.04])[0]]


# Generate a randomized event from preconfigured sample data
def getEvent(event_type):
    levels = [
        '1',
        '2',
        '3',
        '4',
        '5'
    ]

    countries = [

        'UNITED STATES',
        'UK',
        'JAPAN',
        'SINGAPORE',
        'AUSTRALIA',
        'BRAZIL',
        'SOUTH KOREA',
        'GERMANY',
        'CANADA',
        'FRANCE'
    ]

    items = getUUIDs('items', 10)

    currencies = [
        'USD',
        'EUR',
        'YEN',
        'RMB'
    ]

    platforms = [
        'nintendo_switch',
        'ps4',
        'xbox_360',
        'iOS',
        'android',
        'pc',
        'fb_messenger'
    ]

    tutorial_screens = [
        '1_INTRO',
        '2_MOVEMENT',
        '3_WEAPONS',
        '4_FINISH'
    ]

    match_types = [
        '1v1',
        'TEAM_DM_5v5',
        'CTF'
    ]

    matching_failed_msg = [
        'timeout',
        'user_quit',
        'too_few_users'
    ]

    maps = [
        'WAREHOUSE',
        'CASTLE',
        'AIRPORT'
    ]

    game_results = [
        'WIN',
        'LOSE',
        'KICKED',
        'DISCONNECTED',
        'QUIT'
    ]

    spells = [
        'WATER',
        'EARTH',
        'FIRE',
        'AIR'
    ]

    ranks = [
        '1_BRONZE',
        '2_SILVER',
        '3_GOLD',
        '4_PLATINUM',
        '5_DIAMOND',
        '6_MASTER'
    ]

    item_rarities = [
        'COMMON',
        'UNCOMMON',
        'RARE',
        'LEGENDARY'

    ]

    report_reasons = [
        'GRIEFING',
        'CHEATING',
        'AFK',
        'RACISM/HARASSMENT'

    ]

    switcher = {
        'login': {
            'event_data': {
                'platform': str(numpy.random.choice(platforms, 1, p=[0.2, 0.1, 0.3, 0.15, 0.1, 0.05, 0.1])[0]),
                'last_login_time': int(time.time()) - random.randint(40000, 4000000)
            }
        },

        'logout': {
            'event_data': {
                'last_screen_seen': 'the last screen'
            }
        },

        'client_latency': {
            'event_data': {
                'latency': numpy.random.choice((random.randint(40, 185), 1)),
                'connected_server_id': str(random.choice(SERVERS)),
                'region': str(random.choice(countries))
            }
        },

        'user_registration': {
            'event_data': {
                'country_id': str(
                    numpy.random.choice(countries, 1, p=[0.3, 0.1, 0.2, 0.05, 0.05, 0.02, 0.15, 0.05, 0.03, 0.05])[0]),
                'platform': str(numpy.random.choice(platforms, 1, p=[0.2, 0.1, 0.3, 0.15, 0.1, 0.05, 0.1])[0])
            }
        },

        'user_knockout': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'map_id': str(numpy.random.choice(maps, 1, p=[0.6, 0.3, 0.1])[0]),
                'spell_id': str(numpy.random.choice(spells, 1, p=[0.1, 0.4, 0.3, 0.2])[0]),
                'exp_gained': random.randint(1, 2)
            }
        },

        'item_viewed': {
            'event_data': {
                'item_id': str(
                    numpy.random.choice(items, 1, p=[0.125, 0.11, 0.35, 0.125, 0.04, 0.01, 0.07, 0.1, 0.05, 0.02])[0]),
                'item_version': random.randint(1, 2)
            }
        },

        'iap_transaction': {
            'event_data': {
                'item_id': str(
                    numpy.random.choice(items, 1, p=[0.125, 0.11, 0.35, 0.125, 0.04, 0.01, 0.07, 0.1, 0.05, 0.02])[0]),
                'item_version': random.randint(1, 2),
                'item_amount': random.randint(1, 4),
                'currency_type': str(numpy.random.choice(currencies, 1, p=[0.7, 0.15, 0.1, 0.05])[0]),
                'country_id': str(
                    numpy.random.choice(countries, 1, p=[0.3, 0.1, 0.2, 0.05, 0.05, 0.02, 0.15, 0.05, 0.03, 0.05])[0]),
                'currency_amount': random.randint(1, 10),
                'transaction_id': str(uuid.uuid4())
            }
        },

        'tutorial_progression': {
            'event_data': {
                'tutorial_screen_id': str(numpy.random.choice(tutorial_screens, 1, p=[0.3, 0.3, 0.2, 0.2])[0]),
                'tutorial_screen_version': random.randint(1, 2)
            }
        },

        'user_rank_up': {
            'event_data': {
                'user_rank_reached': str(numpy.random.choice(ranks, 1, p=[0.25, 0.35, 0.2, 0.15, 0.0499, 0.0001])[0])
            }
        },

        'matchmaking_start': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'match_type': str(numpy.random.choice(match_types, 1, p=[0.4, 0.3, 0.3])[0])
            }
        },

        'matchmaking_complete': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'match_type': str(numpy.random.choice(match_types, 1, p=[0.6, 0.2, 0.2])[0]),
                'matched_slots': random.randrange(start=6, stop=10)
            }
        },

        'matchmaking_failed': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'match_type': str(numpy.random.choice(match_types, 1, p=[0.35, 0.2, 0.45])[0]),
                'matched_slots': random.randrange(start=1, stop=10),
                'matching_failed_msg': str(numpy.random.choice(matching_failed_msg, 1, p=[0.35, 0.2, 0.45])[0])
            }
        },

        'match_start': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'map_id': str(numpy.random.choice(maps, 1, p=[0.3, 0.3, 0.4])[0])
            }
        },

        'match_end': {
            'event_data': {
                'match_id': str(random.choice(MATCHES)),
                'map_id': str(numpy.random.choice(maps, 1, p=[0.3, 0.3, 0.4])[0]),
                'match_result_type': str(numpy.random.choice(game_results, 1, p=[0.4, 0.4, 0.05, 0.05, 0.1])[0]),
                'exp_gained': random.randrange(start=100, stop=200),
                'most_used_spell': str(numpy.random.choice(spells, 1, p=[0.1, 0.4, 0.2, 0.3])[0])
            }
        },

        'level_started': {
            'event_data': {
                'level_id': str(numpy.random.choice(levels, 1, p=[0.2, 0.2, 0.2, 0.2, 0.2])[0]),
                'level_version': random.randint(1, 2)
            }
        },
        'level_completed': {
            'event_data': {
                'level_id': str(numpy.random.choice(levels, 1, p=[0.6, 0.2, 0.12, 0.05, 0.03])[0]),
                'level_version': random.randint(1, 2)
            }
        },
        'level_failed': {
            'event_data': {
                'level_id': str(numpy.random.choice(levels, 1, p=[0.001, 0.049, 0.05, 0.3, 0.6])[0]),
                'level_version': random.randint(1, 2)
            }
        },

        'lootbox_opened': {
            'event_data': {
                'lootbox_id': str(uuid.uuid4()),
                'lootbox_cost': random.randint(2, 5),
                'item_rarity': str(numpy.random.choice(item_rarities, 1, p=[0.5, 0.3, 0.17, .03])[0]),
                'item_id': str(
                    numpy.random.choice(items, 1, p=[0.125, 0.11, 0.35, 0.125, 0.04, 0.01, 0.07, 0.1, 0.05, 0.02])[0]),
                'item_version': random.randint(1, 2),
                'item_cost': random.randint(1, 5)
            }
        },

        'user_report': {
            'event_data': {
                'report_id': str(uuid.uuid4()),
                'report_reason': str(numpy.random.choice(report_reasons, 1, p=[0.2, 0.5, 0.1, 0.2])[0])
            }
        },

        'user_sentiment': {
            'event_data': {
                'user_rating': random.randint(1, 5)
            }
        }
    }

    return switcher[event_type]


def modify_key_names(event):  # to make it compatible with already built pipeline
    event['table_name'] = event['event_name']
    del event['event_name']
    event['data'] = event['event_data']
    del event['event_data']
    return event


# Take an event type, get event data for it and then merge that event-specific data with the default event fields to create a complete event
def generate_event():
    event_type = getEventType()
    # Within the demo script the event_name is set same as event_type for simplicity.
    # In many use cases multiple events could exist under a common event type which can enable you to build a richer data taxonomy.
    event_name = event_type
    event_data = getEvent(event_type)

    event_data['event_name'] = event_name
    event_data['event_data']['event_version'] = DEFAULT_EVENT_VERSION
    event_data['event_data']['event_id'] = str(uuid.uuid4())
    event_data['event_data']['event_type'] = event_type
    event_data['event_data']['event_timestamp'] = int(time.time())
    event_data['event_data']['app_version'] = str(numpy.random.choice(['1.0.0', '1.1.0', '1.2.0'], 1, p=[0.05, 0.80, 0.15])[0])

    return modify_key_names(event_data)


def send(event):
    payload = json.dumps(event)
    headers = {'Content-Type': 'application/json'}
    print(payload)
    response = requests.request("POST", url, headers=headers, data=payload)
    print(response.text)


if __name__ == '__main__':
    SERVERS = getUUIDs('servers', 3)
    MATCHES = getUUIDs('matches', 50)

    while True:
        generated_event = generate_event()
        send(generated_event)
        # time.sleep(1)
