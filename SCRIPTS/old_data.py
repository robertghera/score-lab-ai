import time
import requests
import json
import datetime
from pymongo import MongoClient

mongoClient = MongoClient("mongodb+srv://u:p@cluster.ywrlr.mongodb.net/score-lab?retryWrites=true&w=majority&appName=Cluster")
collectionPredictions = mongoClient["score-lab"]["predictions"]
mongoClientLocal = MongoClient("mongodb://localhost:27017/")
collectionPredictionsLocal = mongoClientLocal["score-lab"]["test"]

LEAGUE = 61
START_ID = 1213836

while True:
    dbPredData = collectionPredictions.find_one({"league.id": LEAGUE, "fixture.id": START_ID})
    if (dbPredData is None):
        print("New data found")
        apiData = requests.get("https://v3.football.api-sports.io/fixtures?id=" + str(START_ID), headers={"x-rapidapi-key": "k"}).json()
        if apiData["response"][0]["league"]["id"] != LEAGUE:
            print(START_ID, "is not in the league")
            break
        if apiData["response"][0]["league"]["season"] != 2024:
            print(START_ID, "is not in current season")
            break

        collectionPredictionsLocal.insert_one({
            "date": apiData["response"][0]["fixture"]["date"].split("T")[0],
            "fixture": apiData["response"][0]["fixture"],
            "league": apiData["response"][0]["league"],
            "teams": apiData["response"][0]["teams"],
            "goals": apiData["response"][0]["goals"],
            "score": apiData["response"][0]["score"],
            "events": apiData["response"][0]["events"],
            "lineups": apiData["response"][0]["lineups"],
            "statistics": apiData["response"][0]["statistics"],
            "players": apiData["response"][0]["players"],
            "hasStats": True
        })

        START_ID -= 1
        
        time.sleep(6.9) # API rate limit
    else:
        START_ID -= 1
        print("Data already exists")