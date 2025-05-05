from pymongo import MongoClient
import time
import datetime
import pandas as pd
import joblib
from tensorflow.keras.models import load_model
import numpy as np

MODEL_NAME = "test"

collectionPredictions = mongoClient["score-lab"]["predictions"]
mongoClientLocal = MongoClient("mongodb+srv://u:p@cluster.ywrlr.mongodb.net/score-lab?retryWrites=true&w=majority&appName=Cluster")
collectionPredictionsResult = mongoClientLocal["score-lab"]["predictions-test"]
mongoClientLocal = MongoClient("mongodb://localhost:27017/")
collectionData = mongoClientLocal["sports-miner"]["fbref"]

TEAM_MAPPINGS = {
    "Borussia Dortmund": "Dortmund",
    "SC Freiburg": "Freiburg",
    "VfL Wolfsburg": "Wolfsburg",
    "VfL Bochum": "Bochum",
    "FSV Mainz 05": "Mainz 05",
    "FC St. Pauli": "St. Pauli",
    "Borussia Mönchengladbach": "Mönchengladbach",
    "FC Koln": "Köln",
    "FC Augsburg": "Augsburg",
    "1. FC Heidenheim": "Heidenheim",
    "Bayern München": "Bayern Munich",
    "1899 Hoffenheim": "Hoffenheim",
    "VfB Stuttgart": "Stuttgart",
    "VfL Wolfsburg": "Wolfsburg",
    "Alaves": "Alavés",
    "Atletico Madrid": "Atlético Madrid",
    "Leganes": "Leganés",
    "AC Milan": "Milan",
    "Inter": "Internazionale",
    "Verona": "Hellas Verona",
    "AS Roma": "Roma",
    "Saint Etienne": "Saint-Étienne",
    "LE Havre": "Le Havre",
    "Stade Brestois 29": "Brest",
    "Paris Saint Germain": "Paris Saint-Germain",
    "Leicester": "Leicester City",
    "Wolves": "Wolverhampton Wanderers",
    "West Ham": "West Ham United",
    "Ipswich": "Ipswich Town",
    "Tottenham": "Tottenham Hotspur",
    "Almere City FC": "Almere City",
    "Waalwijk": "RKC Waalwijk",
    "Heracles": "Heracles Almelo",
    "GO Ahead Eagles": "Go Ahead Eagles",
    "PEC Zwolle": "Zwolle",
    "SC Braga": "Braga",
    "GIL Vicente": "Gil Vicente FC",
    "AVS": "AVS Futebol",
    "Famalicao": "Famalicão",
    "FC Porto": "Porto",
    "Guimaraes": "Vitória Guimarães"
};

feature_columns = ['goals_for_home', 'goals_against_home',
                           'shots_home', 'shots_on_target_home',
                           'shots_against_home' ,'shots_on_target_against_home',
                           # "shots_rate_home", "shots_rate_against_home",
                           # 'passes_home', 
                           # "passes_against_home",
                           'passes_completed_home',
                           "passes_completed_against_home",
                           # "passes_rate_home", "passes_rate_against_home",
                           'possesion_home',
                           # 'corners_home', 'fouls_home',
                           # "cards_home",
                           "past_games_losses_home", "past_games_draws_home", "past_games_wins_home",
                           # 'result_home',
                           'goals_for_away', 'goals_against_away',
                           'shots_away', 'shots_on_target_away',
                           'shots_against_away', 'shots_on_target_against_away', 
                           # "shots_rate_away", "shots_rate_against_away",
                           # 'passes_away',
                           # "passes_against_away",
                           'passes_completed_away',
                           "passes_completed_against_away", 
                           # "passes_rate_away", "passes_rate_against_away",
                           'possesion_away',
                           # 'corners_away', 'fouls_away',
                           # "cards_away",
                           "past_games_losses_away", "past_games_draws_away", "past_games_wins_away"
                           # 'result_away'
                  ]

def notGameType(gameType):
    if gameType == "_home":
        return "_away"
    return "_home"

model = load_model("D:\Repos\Personal\score-lab-ai\checkpoints\\best_model_24.keras")
scaler = joblib.load("D:\Repos\Personal\score-lab-ai\checkpoints\saved_scaler.pkl")

TIMESTAMP_LIMIT = 40 * 24 * 60 * 60 * 1000 # 40 days
step = 0

predictions = collectionPredictions.find({"league.id": {"$nin": [2,3]} }).to_list() # The query should be something related to current date/ season etc. This is a first itteration for now every time
print("Total predictions to make: ", len(predictions))
for prediction in predictions:
    fixture = prediction["fixture"]
    timestamp = int(time.mktime(datetime.datetime.strptime(prediction["date"],
                                            "%Y-%m-%d").timetuple())) * 1000
    home_team_query = prediction['teams']['home']['name']
    away_team_query = prediction['teams']['away']['name']

    if (TEAM_MAPPINGS.get(prediction['teams']['home']['name'])):
        home_team_query = TEAM_MAPPINGS[prediction['teams']['home']['name']]
    if (TEAM_MAPPINGS.get(prediction['teams']['away']['name'])):
        away_team_query = TEAM_MAPPINGS[prediction['teams']['away']['name']]

    home_team = collectionData.find({"$or": [{"home_team": home_team_query}, {"away_team": home_team_query}], "date": { "$lt": timestamp, "$gt": timestamp - TIMESTAMP_LIMIT}}).sort("date", -1).limit(4).to_list()
    away_team = collectionData.find({"$or": [{"home_team": away_team_query}, {"away_team": away_team_query}], "date": { "$lt": timestamp, "$gt": timestamp - TIMESTAMP_LIMIT}}).sort("date", -1).limit(4).to_list()

    if len(home_team) < 4 or len(away_team) < 4:
        continue

    stats_to_consider = [
        "shots",
        "shots_on_target",
        "passes_completed",
        "possesion",
    ]

    stats_to_consider_against = [
        "shots_on_target",
        "shots",
        "passes_completed",
    ]

    home_team_stats = {}
    wins = 0
    draws = 0
    losses = 0
    for game in home_team:
        try:
            game_type = "_home"
            if game["home_team"] != home_team_query:
                game_type = "_away"

            if game["stats"]["score" + game_type] > game["stats"]["score" + notGameType(game_type)]:
                wins += 1
            elif game["stats"]["score" + game_type] == game["stats"]["score" + notGameType(game_type)]:
                draws += 1
            else:
                losses += 1
            
            if home_team_stats.get("goals_for" + "_home", None) == None:
                home_team_stats["goals_for" + "_home"] = 0
            if home_team_stats.get("goals_against" + "_home", None) == None:
                home_team_stats["goals_against" + "_home"] = 0

            home_team_stats["goals_for" + "_home"] += game["stats"]["score" + game_type]
            home_team_stats["goals_against" + "_home"] += game["stats"]["score" + notGameType(game_type)]

            for feature in stats_to_consider:
                currentFeature = feature + game_type
                if home_team_stats.get(feature + "_home", None) != None:
                    home_team_stats[feature + "_home"] += game["stats"].get(currentFeature)
                else:
                    home_team_stats[feature + "_home"] = game["stats"].get(currentFeature)
                
            for feature in stats_to_consider_against:
                currentFeature = feature + notGameType(game_type)
                if home_team_stats.get(feature + "_against_home", None) != None:
                    home_team_stats[feature + "_against_home"] += game["stats"].get(currentFeature)
                else:
                    home_team_stats[feature + "_against_home"] = game["stats"].get(currentFeature)
        except Exception as e:
            print(game)

    home_team_stats["past_games_wins_home"] = wins
    home_team_stats["past_games_draws_home"] = draws
    home_team_stats["past_games_losses_home"] = losses

    away_team_stats = {}
    wins = 0
    draws = 0
    losses = 0
    for game in away_team:
        try:
            game_type = "_home"
            if game["home_team"] != away_team_query:
                game_type = "_away"

            if game["stats"]["score" + game_type] > game["stats"]["score" + notGameType(game_type)]:
                wins += 1
            elif game["stats"]["score" + game_type] == game["stats"]["score" + notGameType(game_type)]:
                draws += 1
            else:
                losses += 1
            
            if away_team_stats.get("goals_for" + "_away", None) == None:
                away_team_stats["goals_for" + "_away"] = 0
            if away_team_stats.get("goals_against" + "_away", None) == None:
                away_team_stats["goals_against" + "_away"] = 0

            away_team_stats["goals_for" + "_away"] += game["stats"]["score" + game_type]
            away_team_stats["goals_against" + "_away"] += game["stats"]["score" + notGameType(game_type)]

            for feature in stats_to_consider:
                currentFeature = feature + game_type
                if away_team_stats.get(feature + "_away", None) != None:
                    away_team_stats[feature + "_away"] += game["stats"].get(currentFeature)
                else:
                    away_team_stats[feature + "_away"] = game["stats"].get(currentFeature)
                
            for feature in stats_to_consider_against:
                currentFeature = feature + notGameType(game_type)
                if away_team_stats.get(feature + "_against_away", None) != None:
                    away_team_stats[feature + "_against_away"] += game["stats"].get(currentFeature)
                else:
                    away_team_stats[feature + "_against_away"] = game["stats"].get(currentFeature)
        except Exception as e:
            print(game)
    
    away_team_stats["past_games_wins_away"] = wins
    away_team_stats["past_games_draws_away"] = draws
    away_team_stats["past_games_losses_away"] = losses

    for key, value in home_team_stats.items():
        if not key.startswith("past_games"):
            home_team_stats[key] = value / 4
    for key, value in away_team_stats.items():
        if not key.startswith("past_games"):
            away_team_stats[key] = value / 4

    df1 = pd.DataFrame([home_team_stats])
    df2 = pd.DataFrame([away_team_stats])
    df = pd.concat([df1, df2], axis=1)

    prediction_array = model.predict(scaler.transform(df[feature_columns]), verbose=0)
    prediction_value = int(np.argmax(prediction_array[0]))
    final_prediction = None
    if prediction_value == 0 and prediction_array[0][0] > 0.55:
        final_prediction = "L"
    elif prediction_value == 1 and prediction_array[0][1] > 0.38:
        final_prediction = "D"
    elif prediction_value == 2 and prediction_array[0][2] > 0.55:
        final_prediction = "W"
    
    current_game = collectionData.find_one({"home_team": home_team_query, "away_team": away_team_query, "season": "2024-2025"})

    if current_game == None: # TODO: This is big problem
        print(home_team_query, away_team_query)
        print(prediction.get("fixture").get("id"))
        continue
    if current_game.get("odds", None) == None:
        print(home_team_query, away_team_query)
        print(prediction.get("fixture").get("id"))

    result = current_game["stats"]["score_home"] - current_game["stats"]["score_away"]
    if result > 0:
        result = "W"
    elif result < 0:
        result = "L"
    else:
        result = "D"
    
    if prediction_value == 0:
        prediction_value = "L"
    elif prediction_value == 1:
        prediction_value = "D"
    else:
        prediction_value = "W"

    # if final_prediction == None:
    #     collectionPredictionsResult.insert_one({
    #         "prediction": np.array(prediction_array[0], dtype=float).tolist(),
    #         "fixture": fixture,
    #         "date": prediction["date"],
    #         "league": prediction["league"],
    #         "teams": prediction["teams"],
    #         "prediciton": prediction_value,
    #         "odds": current_game["odds"],
    #         "result": result
    #     })
    # else:
    #     collectionPredictionsResult.insert_one({
    #         "prediction": np.array(prediction_array[0], dtype=float).tolist(),
    #         "fixture": fixture,
    #         "date": prediction["date"],
    #         "league": prediction["league"],
    #         "teams": prediction["teams"],
    #         "final_prediction": final_prediction,
    #         "prediciton": prediction_value,
    #         "odds": current_game["odds"],
    #         "result": result
    #     })

    model_name = MODEL_NAME

    if final_prediction == None:
        collectionPredictionsResult.update_one({"fixture.id": prediction.get("fixture").get("id")}, {
            "$set": {
               f'prediction.{model_name}': np.array(prediction_array[0], dtype=float).tolist(),
                f'prediction_given.{model_name}': prediction_value,
                "odds": current_game.get("odds", None),
                "result": result
            }
        })
    else:
        collectionPredictionsResult.update_one({"fixture.id": prediction.get("fixture").get("id")},{
            "$set": {
                f'prediction.{model_name}': np.array(prediction_array[0], dtype=float).tolist(),
                f'prediction_given.{model_name}': prediction_value,
                f"final_prediction.{model_name}": final_prediction,
                "odds": current_game.get("odds", None),
                "result": result
            }
        })
    
    step += 1
    if step % 25 == 0:
        print("Step: ", step)
    