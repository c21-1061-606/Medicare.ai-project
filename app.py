from dotenv import load_dotenv
load_dotenv()
from flask import Flask, request, render_template
import sqlite3
from datetime import datetime
import openai
import os

app = Flask(__name__)

# ✅ Set your OpenAI API key from environment variable
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Rule-based training data ---
diagnosis_data = {
    "fever,cough": "Flu",
    "cough,headache,fatigue": "Cold",
    "headache,nausea,fatigue": "Migraine",
    "fever,headache,fatigue": "COVID-19",
    "cough,sore throat,fatigue": "Common Cold",
    "nausea,vomiting,abdominal pain": "Food Poisoning",
    "fever,chills,muscle aches": "Influenza",
    "sore throat,swollen glands": "Strep Throat",
    "fatigue,low energy,weight gain": "Hypothyroidism",
    "shortness of breath,chest pain": "Pneumonia",
    "abdominal cramps,diarrhea": "Gastroenteritis",
    "joint pain,swelling,stiffness": "Arthritis",
    "itching,rash,redness": "Allergic Reaction",
    "sneezing,runny nose,watery eyes": "Allergic Rhinitis",
    "dry skin,itchiness,red patches": "Eczema",
    "chest pain,sweating,nausea": "Heart Attack",
    "frequent urination,thirst,fatigue": "Diabetes",
    "weight loss,night sweats,cough": "Tuberculosis",
    "confusion,memory loss,difficulty concentrating": "Dementia",
    "persistent sadness,loss of interest,fatigue": "Depression"
}

# Optional links for results
diagnosis_links = {
    "Flu": "https://www.cdc.gov/flu/",
    "Cold": "https://www.healthline.com/health/common-cold",
    "Migraine": "https://www.webmd.com/migraines-headaches/default.htm",
    "COVID-19": "https://www.cdc.gov/coronavirus/2019-ncov/index.html",
    "Common Cold": "https://www.mayoclinic.org/diseases-conditions/common-cold",
    "Food Poisoning": "https://www.cdc.gov/foodsafety/symptoms.html",
    "Influenza": "https://www.cdc.gov/flu/about/index.html",
    "Strep Throat": "https://www.cdc.gov/groupastrep/diseases-public/strep-throat.html",
    "Hypothyroidism": "https://www.thyroid.org/hypothyroidism/",
    "Pneumonia": "https://www.lung.org/lung-health-diseases/lung-disease-lookup/pneumonia",
    "Gastroenteritis": "https://www.healthline.com/health/viral-gastroenteritis",
    "Arthritis": "https://www.arthritis.org/",
    "Allergic Reaction": "https://www.webmd.com/allergies/guide/allergy-symptoms-types",
    "Allergic Rhinitis": "https://www.mayoclinic.org/diseases-conditions/hay-fever",
    "Eczema": "https://nationaleczema.org/eczema/",
    "Heart Attack": "https://www.heart.org/en/health-topics/heart-attack",
    "Diabetes": "https://www.diabetes.org/diabetes",
    "Tuberculosis": "https://www.cdc.gov/tb/default.htm",
    "Dementia": "https://www.alz.org/alzheimers-dementia/what-is-dementia",
    "Depression": "https://www.nimh.nih.gov/health/topics/depression"
}

# Extract known symptoms
known_symptoms = set()
for symptoms in diagnosis_data:
    known_symptoms.update(s.strip().lower() for s in symptoms.split(','))

def process_input(symptoms_str):
    input_symptoms = [s.strip().lower() for s in symptoms_str.split(',')]
    recognized = [s for s in input_symptoms if s in known_symptoms]
    unrecognized = [s for s in input_symptoms if s not in known_symptoms]
    return recognized, unrecognized

def get_ai_diagnosis(symptoms):
    prompt = f"Given these symptoms: {symptoms}, what is the most likely medical diagnosis? Answer with a concise condition name only."
    response = openai.ChatCompletion.create(
        model="gpt-4",  # or "gpt-3.5-turbo"
        messages=[
            {"role": "system", "content": "You are a helpful and concise medical assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=50,
        temperature=0.4
    )
    return response.choices[0].message.content.strip()

def init_db():
    conn = sqlite3.connect('diagnosis.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS diagnoses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symptoms TEXT,
            diagnosis TEXT,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        symptoms = request.form['symptoms']
        recognized, unrecognized = process_input(symptoms)

        note = None
        if unrecognized:
            note = "Note: Some symptoms were not recognized in our system."

        # Rule-based matching
        possible_diagnoses = []
        for key, value in diagnosis_data.items():
            key_symptoms = set(key.split(','))
            match_score = len(set(recognized).intersection(key_symptoms))
            if match_score > 0:
                possible_diagnoses.append((value, match_score))

        possible_diagnoses.sort(key=lambda x: x[1], reverse=True)

        # Use rule-based or fallback to GPT or show unknown
        if possible_diagnoses:
            top_diagnosis = possible_diagnoses[0][0]
        elif recognized:
            top_diagnosis = get_ai_diagnosis(symptoms)
        else:
            top_diagnosis = "Unknown – your symptoms did not match any condition in our diagnosis data library."

        # Store result
        conn = sqlite3.connect('diagnosis.db')
        c = conn.cursor()
        c.execute("INSERT INTO diagnoses (symptoms, diagnosis, date) VALUES (?, ?, ?)",
                  (symptoms, top_diagnosis, datetime.now()))
        conn.commit()
        conn.close()

        return render_template('result.html',
                               symptoms=symptoms,
                               diagnosis=top_diagnosis,
                               recognized=recognized,
                               unrecognized=unrecognized,
                               possible_diagnoses=possible_diagnoses,
                               diagnosis_link=diagnosis_links.get(top_diagnosis),
                               diagnosis_links=diagnosis_links,
                               note=note)

    return render_template('index.html')

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
