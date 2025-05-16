from sklearn.tree import DecisionTreeClassifier
import joblib

X = [
    [1, 1, 0, 0, 0],  # fever, cough → Flu
    [0, 1, 1, 0, 1],  # cough, headache, fatigue → Cold
    [0, 0, 1, 1, 1],  # headache, nausea, fatigue → Migraine
    [1, 0, 1, 0, 1],  # fever, headache, fatigue → COVID-19
]
y = ["Flu", "Cold", "Migraine", "COVID-19"]

model = DecisionTreeClassifier()
model.fit(X, y)
joblib.dump(model, 'model.pkl')
