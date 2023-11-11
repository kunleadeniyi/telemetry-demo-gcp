import uuid
import random
from faker import Faker
import datetime

import math

fake = Faker()


class Gameplay():

    def __init__(self) -> None:
        player = self._create_player()
        self.player_id = player["player_id"]
        self.username = player["username"]
        self.first_name = player["first_name"]
        self.last_name = player["last_name"]
        self.email = player["email"]
        self.level = player["level"]
        self.points = player["points"]
        self.coins = player["coins"]
        self.xp = player["xp"]
        self.created_at = player["created_at"]
        self.last_login_date = player["last_login_date"]
        self.platform = player["platform"]
        self.region = player["region"]

        # internal properties
        # progression
        self._previous_points = player["points"]
        self._previous_xp = player["xp"]
        self._previous_coins = player["coins"]
        self._previous_level = player["level"]

        # session
        self._current_session = None

        # player data
        self.player_data = player

    @staticmethod
    def _create_player(level=1, points=500, coins=10, xp=1, platform="PC", region="Europe"):
        return {
            "player_id": str(uuid.uuid4()),
            "username": fake.name().split(' ')[0],
            "first_name": fake.name().split(' ')[0],
            "last_name": fake.name().split(' ')[1],
            "email": fake.email(),
            "level": level,
            "points": points,
            "coins": coins,
            "xp": xp,
            "created_at": datetime.datetime.now().timestamp(),
            "last_login_date": datetime.date.today().strftime("%d-%m-%Y"),
            "platform": platform,
            "region": region
        }

    @staticmethod
    def _random_game_mode():
        game_mode_list = ['single-player', 'co-op', 'multiplayer']
        game_mode = game_mode_list[random.randint(0, len(game_mode_list) - 1)]
        return game_mode

    def _random_game_map(self):
        game_map_list = ['Gulag', 'Rust', 'MarioCamp', 'ShipWreck']
        game_map = game_map_list[random.randint(0, len(game_map_list) - 1)]
        return game_map


    def _compute_level(self):
        return math.floor(math.log(self.xp, 2))

    def create_game_session(self):
        # creates a session that has a beginning time, end time, player id, game mode, session id
        start_time = datetime.datetime.now()
        end_time = start_time + datetime.timedelta(minutes=(random.randint(3, 15)))
        session_id = str(uuid.uuid1())

        # set current session internal property
        self._current_session = session_id

        return {
            "session_id": session_id,
            "player_id": self.player_id,
            "start_time": start_time.timestamp(),
            "end_time": end_time.timestamp(),
            "game_mode": self._random_game_mode(),
            "game_map": self._random_game_map() # adding this might break the etl to bigquery  due to schema issues
        }

    def log_player_progression(self):
        # modify player level, coins, xp, points and return new and previous values and session id when changes happened
        new_points = self._previous_points + random.randint(50, 100)
        new_xp = self._previous_xp + random.randint(3, 100)
        new_coins = self._previous_coins + random.randint(1, 5)
        new_level = self._compute_level()

        # update previous values
        self._previous_points = self.points
        self._previous_xp = self.xp
        self._previous_coins = self.coins
        self._previous_level = self.level

        # assign new xp to compute player level
        self.points = new_points
        self.xp = new_xp
        self.coins = new_coins
        self.level = new_level

        return {
            "session_id": self._current_session,
            "player_id": self.player_id,
            "previous_points": self._previous_points,
            "current_points": self.points,
            "previous_xp": self._previous_xp,
            "current_xp": self.xp,
            "previous_coins": self._previous_coins,
            "current_coins": self.coins,
            "previous_level": self._previous_level,
            "current_level": self.level,
            "timestamp": datetime.datetime.now().timestamp()  # adding this might break the etl to bigquery  due to schema issues
        }

    @staticmethod
    def _create_game_event(self, event_name: str, data: dict):
        # event name, event id, event type, player id, session id, timestamp of event
        game_event = data
        game_event["event_name"] = event_name
        return game_event

    def track_location(self):
        # event id, event type, player id, session id, timestamp of event
        session_id = self._current_session
        player_id = self.player_id
        event_id = str(uuid.uuid1())
        timestamp = datetime.datetime.now().timestamp()
        location = {
            "x_coord": random.randint(0, 1000),
            "y_coord": random.randint(0, 1000),
            "z_coord": random.randint(0, 400)
        }
        game_mode = self._random_game_mode()
        game_map = self._random_game_map()

        return {
            "session_id": session_id,
            "player_id": player_id,
            "event_id": event_id,
            "game_mode": game_mode,
            "game_map": game_map,
            "location": location,
            "timestamp": timestamp
        }

    def update_leaderboard(self):
        # return current player points and level
        pass

    def create_game_assets(self):
        skin_list = ["Ghost", "Spongebob", "SpookyFest", "Unknown Gunman", "21 Savage", "Siege"]
        operator_skills_list = ["Machine Gun", "War Head", "Captain America", "Helicopter", "Drone", "Goliath"]
        data = {
            "player_id": self.player_id,
            "assets": {
                "skins": random.sample(skin_list, 3),
                "operator_skills": random.sample(operator_skills_list, 3)
            },
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        return data

# def create_game_assets():
#     pass


# assumptions
"""
Every activity (session, progression, event etc) is done by a player
Every session is tied to a game mode and definitely a player
Every session leads to player progression
the session happens and then progression is computed

within a session there can be X many events 
"""

"""
demo workflow
create player
create multiple player sessions
    for each session, create progression


"""

"""
I want to generate data and publish it for a user so that i can call it numerous times asynchronously to simulate telemetry for different players
or write a wrapper for publishing data
"""


def generate_telemetry_per_user():
    i = 0
    while i < 5:
        print(i)
        i += 1


if __name__ == "__main__":
    game_play = Gameplay()
    print(game_play.player_data)
    # print(game_play.player_id)
    # print(game_play._random_game_mode())

    game_asset = game_play.create_game_assets()
    print(game_asset)

    num_sessions = 40
    for i in range(num_sessions):
        game_session = game_play.create_game_session()
        print(game_session)
        # print(game_play.xp)
        game_progression = game_play.log_player_progression()
        print(game_progression)


    # print(math.floor(compute_level(15)))
