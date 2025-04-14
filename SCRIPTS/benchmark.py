from pymongo import MongoClient

# mongoClientLocal = MongoClient("mongodb://localhost:27017/")
# collectionPredictionsResult = mongoClientLocal["score-lab"]["test-best-win"]

mongoClientLocal = MongoClient("mongodb+srv://u:p@cluster.ywrlr.mongodb.net/score-lab?retryWrites=true&w=majority&appName=Cluster")
collectionPredictionsResult = mongoClientLocal["score-lab"]["test"]

# Get all the predictions
predictions = collectionPredictionsResult.find({}).to_list()

total = {}
corect = {}
odds_name = {
    "W": "B365H",
    "D": "B365D",
    "L": "B365A"
}
odds = {}

for prediction in predictions:
    if prediction.get("final_prediction", None) is not None:
        if total.get(prediction["final_prediction"], None) is None:
            total[prediction["final_prediction"]] = 1
        else:
            total[prediction["final_prediction"]] += 1
        if prediction["final_prediction"] == prediction["result"]:
            if corect.get(prediction["final_prediction"], None) is None:
                corect[prediction["final_prediction"]] = 1
            else:
                corect[prediction["final_prediction"]] += 1
            if odds.get(prediction["final_prediction"], None) is None:
                odds[prediction["final_prediction"]] = prediction["odds"][odds_name[prediction["final_prediction"]]]
            else:
                odds[prediction["final_prediction"]] += prediction["odds"][odds_name[prediction["final_prediction"]]]

for key in total.keys():
    print(f"Total: {key} - {total[key]}")
    print(f"Prediction: {key} - Accuracy: {round(corect.get(key, 0) / total[key] * 100, 2)}%")
    print(f"Total odds: {key} - {round(odds.get(key, 0) - total[key], 2)}")
    print(f"Average odds: {key} - {round((odds.get(key, 0) - total[key]) / total[key], 4)}")
    print("===============================================")