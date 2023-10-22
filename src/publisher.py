from utils import json_serializer, wrap_data
# from faker import Faker
from game_events import Gameplay
import random
import time
import os

import asyncio

# pub sub section
from google.cloud import pubsub_v1

credential_path = "/Users/ayokunle/Documents/mylab/terraform/telemetry-demo-gcp/credentials.json"
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credential_path

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path("idyllic-web-401116", "demo-valid-data")

# creata a fuctino to create a player, and generate some events and progression 
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
    for i in range(num_sessions):
        game_session = player.create_game_session()
        # print(game_session)
        publish(table_name="sessions", event=game_session)
        # print(game_play.xp)
        game_progression = player.log_player_progession()
        # print(game_progression)
        publish(table_name="progression", event=game_progression)

async def main():
    tel_task1 = asyncio.create_task(generate_data())
    tel_task2 = asyncio.create_task(generate_data())
    tel_task3 = asyncio.create_task(generate_data())
    tel_task4 = asyncio.create_task(generate_data())
    tel_task5 = asyncio.create_task(generate_data())

if __name__ == "__main__":

    while True:
        asyncio.run(main())

# TO DO
# move project id and topic name to env file
# move credentials path to env file
# move code above "pub sub section to its own python file"