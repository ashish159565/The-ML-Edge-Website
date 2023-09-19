from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
from sklearn.metrics import r2_score, accuracy_score
import firebase_admin
from firebase_admin import db
import os
import numpy as np

cred_obj = firebase_admin.credentials.Certificate('key.json')
default_app = firebase_admin.initialize_app(cred_obj, {
	'databaseURL':"https://themledge-default-rtdb.firebaseio.com/" 
	})

ref = db.reference("/")

app = Flask(__name__)

# Function to calculate the accuracy between two CSV DataFrames
def calculate_accuracy(uploaded_df, reference_df):
    try:
        # Calculate the accuracy using scikit-learn's accuracy_score
        accuracy = accuracy_score(reference_df, uploaded_df) * 100

        x =  f"{accuracy:.2f}"
        return float(x)
    except Exception as e:
        return str(e)

def calculate_accuracy_tcs1(uploaded_df, reference_df):
    accuracy = r2_score(uploaded_df, reference_df) * 100
    x = f"{accuracy: 2f}"
    return float(x)    

# ...
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        rollno = request.form["rollno"]
        uploaded_file = request.files["file"]
        tag = request.form["tag"]
        name = request.form["name"]
        # Specify the path to the reference CSV files
        reference_csv_path_1 = 'tcs1.csv'
        reference_csv_path_2 = 'data2.csv'

        if uploaded_file and uploaded_file.filename.endswith('.csv'):
            # Read the uploaded CSV file
            uploaded_df = pd.read_csv(uploaded_file)

            # Read the reference CSV files
            reference_df_1 = pd.read_csv(reference_csv_path_1)
            reference_df_2 = pd.read_csv(reference_csv_path_2)

            details = ref.get()
            
            if tag == "1":
                accuracy_result = calculate_accuracy_tcs1(uploaded_df, reference_df_1)
                if details is None:
                    new_child = {rollno: {"Name": name, "Accuracy_TCS_1": accuracy_result, "Accuracy_TCS_2": 0, "Total_Accuracy": accuracy_result/2}}
                    ref.set(new_child)
                elif rollno not in details.keys():    
                    new_child = {rollno: {"Name": name, "Accuracy_TCS_1": accuracy_result, "Accuracy_TCS_2": 0, "Total_Accuracy": accuracy_result/2}}
                    details.update(new_child)
                    ref.set(details)
                else:
                    if ref.child(rollno).get()["Accuracy_TCS_1"] < accuracy_result:
                        ref.child(rollno).update({"Accuracy_TCS_1":accuracy_result})
                        total = (ref.child(rollno).get()["Accuracy_TCS_1"] + ref.child(rollno).get()["Accuracy_TCS_2"])/2
                        ref.child(rollno).update({"Total_Accuracy":total})
                    else:
                        accuracy_result = ref.child(rollno).get()["Accuracy_TCS_1"]
                    
            elif tag == "2":
                accuracy_result = calculate_accuracy(uploaded_df, reference_df_2)
                if details is None:
                    new_child = {rollno: {"Name": name, "Accuracy_TCS_1": 0, "Accuracy_TCS_2": accuracy_result, "Total_Accuracy": accuracy_result/2}}
                    ref.set(new_child)
                elif rollno not in details.keys():
                    new_child = {rollno: {"Name": name, "Accuracy_TCS_1": 0, "Accuracy_TCS_2": accuracy_result, "Total_Accuracy": accuracy_result/2}}
                    details.update(new_child)
                    ref.set(details)   
                else:
                    if ref.child(rollno).get()["Accuracy_TCS_2"] < accuracy_result:
                        ref.child(rollno).update({"Accuracy_TCS_2": accuracy_result})
                        total = (ref.child(rollno).get()["Accuracy_TCS_1"] + ref.child(rollno).get()["Accuracy_TCS_2"])/2
                        ref.child(rollno).update({"Total_Accuracy":total})
                    else:
                        accuracy_result = ref.child(rollno).get()["Accuracy_TCS_2"]
                                                             
            return render_template("result.html", name=name, accuracy_result=accuracy_result, rollno=rollno, tag=tag)

    return render_template("index.html")

@app.route("/leaderboard")
def display_leaderboard():
    details = ref.get()
    data_list = []
    for key, value in details.items():
        data_list.append({
                    'Roll Number': key,
                    'Name': value.get('Name', ''),
                    'Accuracy_TCS_1': value.get('Accuracy_TCS_1', 0),
                    'Accuracy_TCS_2': value.get('Accuracy_TCS_2', 0),
                    'Total_Accuracy': value.get('Total_Accuracy', 0)})
    sorted_data = sorted(data_list, key=lambda x: x['Total_Accuracy'], reverse=True)
    first_three_members = sorted_data[:3]
    names_and_keys = [(item['Name'], item['Roll Number']) for item in first_three_members]
    names = []
    rollnos = []
    for name, rollno in names_and_keys:
        names.append(name)
        rollnos.append(rollno)
    leaderboard = pd.DataFrame(sorted_data)
    leaderboard_table = leaderboard.to_html(classes=["table", "table-bordered"], index=False)
    return render_template("leaderboard.html", leaderboard_table=leaderboard_table, names=names, rollnos=rollnos)

if __name__ == "__main__":
    app.run(debug=True,host='0.0.0.0',port=int(os.environ.get('PORT',8080)))
