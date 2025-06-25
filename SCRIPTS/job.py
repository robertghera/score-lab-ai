import time
import requests
import json
import datetime
import os
from pymongo import MongoClient

print("STARTING DATA COLLECTION JOB...")

# Access an environment variable
api_key = os.environ.get('API_KEY')
database_username = os.environ.get('DATABASE_USERNAME')
database_password = os.environ.get('DATABASE_PASSWORD')


mongoClient = MongoClient(f"mongodb+srv://{database_username}:{database_password}@cluster.ywrlr.mongodb.net/score-lab?retryWrites=true&w=majority&appName=Cluster")
collectionPredictions = mongoClient["score-lab"]["predictions"]
collectionPredictionsTesting = mongoClient["score-lab"]["predictions-testing"]
collectionPredictionsTesting18 = mongoClient["score-lab"]["predictions-testing-18"]

date = datetime.datetime.now().strftime("%Y-%m-%d")
dataMongo = collectionPredictions.find({date: date}).to_list()

if len(dataMongo) == 0:
    LEAGUES = [
        2, # UCL, just because I CAN
	      3, # UEL, :)
        39, # EPL
        61, # Ligue 1   
        78, # Bundesliga
        88, # Eredivisie
        94, # Primeira Liga
        140, # La Liga
        135, # Serie A
    ]
    apiData = {"response": []}
    apiData = requests.get("https://v3.football.api-sports.io/fixtures?date=" + date, headers={"x-rapidapi-key": f"{api_key}"}).json()
    dbData = []
    dbData = collectionPredictionsTesting18.find({"hasStats": {"$exists": False}}).to_list()

    for fixture in apiData["response"]:
        if (fixture["league"]["id"] in LEAGUES):
            prediction = {
                "date": date,
                "fixture": fixture["fixture"],
                "league": fixture["league"],
                "teams": fixture["teams"],
            }
            collectionPredictions.insert_one(prediction)
            collectionPredictionsTesting.insert_one(prediction)
    
    print("Finished inserting fixtures for date: " + date)

    if len(dbData) == 0:
        print("No games with missing stats found in the database.")
    else:                
        print("Games with no stats: " + str(len(dbData)))

    for fixture in dbData:
        stats = requests.get("https://v3.football.api-sports.io/fixtures?id=" + str(fixture["fixture"]["id"]), headers={"x-rapidapi-key": f"{api_key}"}).json()
        print(fixture["fixture"]["id"])
        print(stats["response"][0]["fixture"]["id"])
        if stats["response"]:
            collectionPredictions.update_one({"_id": fixture["_id"]}, {"$set": {
                "goals": stats["response"][0]["goals"],
                "score": stats["response"][0]["score"],
                "events": stats["response"][0]["events"],
                "lineups": stats["response"][0]["lineups"],
                "statistics": stats["response"][0]["statistics"],
                "players": stats["response"][0]["players"],
                "hasStats": True
            }})
            collectionPredictionsTesting.update_one({"_id": fixture["_id"]}, {"$set": {
                "goals": stats["response"][0]["goals"],
                "score": stats["response"][0]["score"],
                "events": stats["response"][0]["events"],
                "lineups": stats["response"][0]["lineups"],
                "statistics": stats["response"][0]["statistics"],
                "players": stats["response"][0]["players"],
                "hasStats": True
            }})
            collectionPredictionsTesting18.update_one({"_id": fixture["_id"]}, {"$set": {
                "goals": stats["response"][0]["goals"],
                "score": stats["response"][0]["score"],
                "events": stats["response"][0]["events"],
                "lineups": stats["response"][0]["lineups"],
                "statistics": stats["response"][0]["statistics"],
                "players": stats["response"][0]["players"],
                "hasStats": True
            }})
        time.sleep(6.9) # API rate limit
else:
    print(json.dumps(dataMongo, indent=3))