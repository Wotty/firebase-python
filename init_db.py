import json

import pyrebase
import requests
import firebase_admin

print(firebase_admin.__version__)
with open("firebaseConfig.json", "r") as json_file:
    firebaseConfig = json.load(json_file)

firebase = pyrebase.initialize_app(firebaseConfig["project_config"])

# Database
db = firebase.database()
# Auth
auth = firebase.auth()
users = db.child("users")
# Sign up
email = "william.otty@gmail.com"
password = "12345678"
try:
    register = auth.create_user_with_email_and_password(email, password)
    local_id = register["localId"]
    print("success")

except requests.exceptions.HTTPError:
    try:
        print("email already exists")
        login = auth.sign_in_with_email_and_password(email, password)
        local_id = login["localId"]
    except requests.exceptions.HTTPError:
        print("Unable to register or log in")

data = {"name": "Will Otty"}
users.child(local_id).set(data)
