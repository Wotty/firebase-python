import json

import pyrebase
import requests

with open("firebaseConfig.json", "r") as json_file:
    firebaseConfig = json.load(json_file)

firebase = pyrebase.initialize_app(firebaseConfig)


db = firebase.database()

# Auth
auth = firebase.auth()


loggedin = False
while not loggedin:
    # Login
    email = input("Enter your email: ")
    password = input("Enter your password: ")
    try:
        login = auth.sign_in_with_email_and_password(email, password)
        print(login["localId"])
        print("succesfully logged in")
        loggedin = True
    except requests.exceptions.HTTPError:
        print("Invalid user or password, try again")

# Sign up
email = input("Enter your email: ")
password = input("Enter your password: ")

try:
    auth.create_user_with_email_and_password(email, password)
    register = auth.create_user_with_email_and_password(email, password)
    print("localID: " + register["localId"])
    print("success")

except requests.exceptions.HTTPError:
    print("email already exists")

# Create
data = {"age": 40, "address": "new york", "employeed": True, "name": "John Smith"}
db.child("people").push(data)
# Create using custom uid
data = {"age": 31, "address": "york", "employeed": False, "name": "Mark Smith"}
db.child("people").child("myownid").set(data)

# Update known uid
db.child("people").child("myownid").update({"name": "Jane Smith"})


# Update unknown uid
people = db.child("people").get()

for person in people.each():
    if person.val()["name"] == "Jane Smith":
        db.child("people").child(person.key()).update({"name": "Steve Smith"})
        print("updated name")
    print(person.val())
    print(person.key())


# Delete using known id
db.child("people").child("myownid").child("age").remove()


# Delete using unknown id
people = db.child("people").get()

for person in people.each():
    if person.val()["name"] == "Steve Smith":
        db.child("people").child(person.key()).child("age").remove()
        print("removed age")
    print(person.val())
    print(person.key())


# Read
people = db.child("people").child("myownid").get()
print(people.val())


# Read using order
people = db.child("people").order_by_child("name").equal_to("Steve Smith").get()

for person in people.each():
    print(person.val())


# Read using > 30 and <40
people = db.child("people").order_by_child("age").start_at(30).end_at(40).get()

for person in people.each():
    print(person.val())

# Read using > 30 and <40
people = db.child("people").order_by_child("age").start_at(30).end_at(40).get()

for person in people.each():
    print(person.val())
# Read using > 30 and < 40 and only get first one
people = (
    db.child("people")
    .order_by_child("age")
    .start_at(30)
    .end_at(40)
    .limit_to_first(1)
    .get()
)

for person in people.each():
    print(person.val())
