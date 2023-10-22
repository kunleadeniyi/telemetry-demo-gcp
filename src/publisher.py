from utils import json_serializer, wrap_data
from utils import create_player
# from faker import Faker
from game_events import Gameplay
import random
import time
import os



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



if __name__ == "__main__":

    # max = 200
    # i = 0
    # while i < max:
    #     player = Gameplay()
    #     # message = wrap_data("users", dummy_data)
    #     message = wrap_data(table_name="player", data=player.player_data)
    #     data = json_serializer(message)
    #     pubsub_response = publisher.publish(topic_path, data)
    #     print(pubsub_response)
    #     # print(data)
    #     time.sleep(1)
    #     i += 1

    player = Gameplay()
    publish(table_name="player", event=player.player_data)
    num_sessions = 40
    for i in range(num_sessions):
        game_session = player.create_game_session()
        # print(game_session)
        publish(table_name="sessions", event=game_session)
        # print(game_play.xp)
        game_progression = player.log_player_progession()
        # print(game_progression)
        publish(table_name="progression", event=game_progression)


# not working because of schema issues

# TO DO
# move project id and topic name to env file
# move credentials path to env file
# move code above "pub sub section to its own python file"