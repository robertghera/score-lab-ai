import time
import requests
import json
import datetime
from pymongo import MongoClient

mongoClient = MongoClient("mongodb+srv://u:p@cluster.ywrlr.mongodb.net/score-lab?retryWrites=true&w=majority&appName=Cluster")
collectionPredictions = mongoClient["score-lab"]["predictions"]
collectionPredictionsTesting = mongoClient["score-lab"]["predictions-testing"]

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
    apiData = requests.get("https://v3.football.api-sports.io/fixtures?date=" + date, headers={"x-rapidapi-key": "k"}).json()
    dbData = collectionPredictions.find({"hasStats": {"$exists": False}}).to_list()
    print("Games with no stats: " + str(len(dbData)))

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
    
    for fixture in dbData:
        stats = requests.get("https://v3.football.api-sports.io/fixtures?id=" + str(fixture["fixture"]["id"]), headers={"x-rapidapi-key": "k"}).json()
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
        time.sleep(6.9) # API rate limit
else:
    print(json.dumps(dataMongo, indent=3))