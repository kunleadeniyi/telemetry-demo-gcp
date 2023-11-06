from utils import json_serializer, wrap_data
from game_events import Gameplay
from dotenv import load_dotenv
import random
# import time
from datetime import datetime
import os
import asyncio

# pub/sub import
from google.cloud import pubsub_v1

load_dotenv()

credential_path = os.getenv("CREDENTIAL_PATH")
project_id = os.getenv("PROJECT_ID")
pubsub_topic = os.getenv("VALID_PUBSUB_TOPIC")

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, pubsub_topic)


# create a function to create a player, and generate some events and progression
# run it concurrently multiple times
def publish(table_name, event):
    message = wrap_data(table_name=table_name, data=event)
    data = json_serializer(message)
    pubsub_response = publisher.publish(topic_path, data)
    print(pubsub_response.result())
    # time.sleep(1)
    # print(data)


async def generate_data():
    player = Gameplay()
    publish(table_name="player", event=player.player_data)
    num_sessions = random.randint(30, 75)
    for session in range(num_sessions):
        game_session = player.create_game_session()
        publish(table_name="sessions", event=game_session)

        for j in range(random.randint(200, 450)):
            publish(table_name="events", event=player.track_location())

        game_progression = player.log_player_progression()
        publish(table_name="progression", event=game_progression)


############## delete till async def main()


def generate_array_data(player_id):
    skin_list = ["Ghost", "Spongebob", "SpookyFest", "Unknown Gunman", "21 Savage", "Siege"]
    operator_skills_list = ["Machine Gun", "War Head", "Captain America", "Helicopter", "Drone", "Goliath"]
    data = {
        "player_id": player_id,
        "assets": {
            "skins": random.sample(skin_list, 3),
            "operator_skills": random.sample(operator_skills_list, 3)
        },
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    return data


async def generate_data():
    player = Gameplay()
    publish(table_name="test_players", event=player.player_data)

    player_id = player.player_id
    publish(table_name="test_assets", event=generate_array_data(player_id))


async def main():
    tel_task1 = asyncio.create_task(generate_data())
    tel_task2 = asyncio.create_task(generate_data())
    # tel_task3 = asyncio.create_task(generate_data())
    # tel_task4 = asyncio.create_task(generate_data())
    # tel_task5 = asyncio.create_task(generate_data())


if __name__ == "__main__":

    # print(project_id, pubsub_topic, credential_path)
    i = 0
    # while True:
    while i < 10:
        asyncio.run(main())
        i += 1

# TO DO
# move project id and topic name to env file
# move credentials path to env file
# move code above "pub sub section to its own python file"
