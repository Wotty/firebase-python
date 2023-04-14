import datetime
import json
import os
import requests

from flask import (
    Blueprint,
    flash,
    render_template,
    request,
    redirect,
    send_from_directory,
    url_for,
    session,
)

import pyrebase
import firebase_admin
from firebase_admin import credentials
from onesignal_sdk.client import Client

client = Client(
    rest_api_key="YjE0NDE3YjgtNjlkNy00YWVkLWFlYjAtODFmMGFjM2Y2NDI1",
    app_id="c297534c-4c51-460a-a5e7-ad932040993a",
)

app = Blueprint("app", __name__)

with open("./firebaseConfig.json", "r") as json_file:
    firebaseConfig = json.load(json_file)

firebase = pyrebase.initialize_app(firebaseConfig["project_config"])

cred = credentials.Certificate(firebaseConfig["service_account"])
firebase_admin.initialize_app(
    cred, {"databaseURL": firebaseConfig["project_config"]["databaseURL"]}
)

# Database
db = firebase.database()

# Auth
auth = firebase.auth()

# login
@app.route("/", defaults={"category": None}, methods=["GET", "POST"])
@app.route("/<category>")
def index(category):
    if "id" not in session:
        if request.method == "GET":
            return render_template("index.html")
        # Get form data
        email = request.form["email"]
        password = request.form["password"]
        try:
            login = auth.sign_in_with_email_and_password(email, password)
            flash("successfully logged in", "success")
        except requests.exceptions.HTTPError:
            flash("Invalid email or password.", "danger")
            return render_template("index.html")

        session["id"] = login["localId"]
    if category is not None:
        all_workouts = (
            db.child("workouts").order_by_child("localId").equal_to(session["id"]).get()
        )
        filtered_workouts = {}
        for workout in all_workouts.each():
            if workout.val()["body group"] == category:
                key = workout.val()["name"]
                filtered_workouts[key] = workout.val()
    else:
        filtered_workouts = (
            db.child("workouts").order_by_child("localId").equal_to(session["id"]).get()
        ).val()

    user = db.child("users").child(session["id"]).get()
    try:
        exercise_maxes = user.val()["theoretical maxes"]
    except:
        exercise_maxes = {}
    # Get workouts
    return render_template(
        "workouts.html",
        name=user.val()["name"],
        workouts=filtered_workouts,
        category=category,
        exercise_maxes=exercise_maxes,
    )


@app.route("/lifts")
def lifts():
    return render_template("lifts.html")


@app.route("/logout")
def logout():
    # remove the email from the session
    session.pop("id", None)
    # redirect to the index page
    return redirect(url_for("app.index"))


@app.route("/reset", methods=["POST"])
def reset():
    email = request.form.get("email")
    if not email:
        flash("Please provide an email address", "danger")
        return redirect(url_for("app.index"))

    auth.send_password_reset_email(email)
    flash(f"Password reset email sent to {email}", "success")
    return redirect(url_for("app.index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    # Get form data
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]
    confirm_password = request.form["confirm_password"]

    if password != confirm_password:
        flash("Passwords do not match", "danger")
        return redirect(url_for("app.register"))

    user_exist = db.child("users").order_by_child("email").equal_to(email).get()
    if not user_exist.val():
        register = auth.create_user_with_email_and_password(email, password)
        session["id"] = register["localId"]
        db.child("users").child(session["id"]).update({"name": name, "email": email})
        # Log user in
    else:
        print(user_exist.val())

        flash("User already created", "danger")

    # Redirect to homepage
    return redirect(url_for("app.index"))


@app.route("/create_workout", methods=["GET", "POST"])
def create_workout():
    if request.method == "POST":
        # Insert the new workout into the database
        workout_name = request.form["name"]
        body_group = request.form["body_group"]
        workout_time = request.form["time"]
        localId = session["id"]
        db.child("workouts").child(workout_name).update(
            {
                "name": f"{workout_name} - {workout_time}",
                "localId": localId,
                "body group": body_group,
                "workout time": workout_time,
            }
        )
        return redirect(url_for("app.index"))
    else:
        # Display a form to add a new workout
        return render_template("create_workout.html")


@app.route("/workout/<workout_id>")
def view_workout(workout_id):
    # Display the details of a specific workout
    workout = db.child("workouts").child(workout_id).get()
    return render_template("workout.html", workout=workout)


@app.route("/edit_workout/<workout_id>", methods=["GET", "POST"])
def edit_workout(workout_id):
    # Display the details of a specific workout
    if request.method == "POST":
        if "id" not in session:
            flash("please log in first", "primary")
            return redirect("/")
        name = request.form["name"]
        localId = session["id"]
        body_group = request.form["body_group"]
        workout_time = request.form["time"]

        db.child("workouts").child(workout_id).update(
            {
                "name": name,
                "localId": localId,
                "body group": body_group,
                "workout time": workout_time,
            }
        )

        flash("Workout updated successfully", "success")
        return redirect(url_for("app.index"))

    workouts = db.child("workouts").child(workout_id).get()
    return render_template("edit_workout.html", workout=workouts, workout_id=workout_id)


@app.route("/delete_workout/<workout_id>", methods=["POST"])
def delete_workout(workout_id):
    db.child("workouts").child(workout_id).remove()
    flash("Workout deleted successfully", "success")
    return redirect(url_for("app.index"))


@app.route("/exercises")
def exercises():
    # Display a list of workouts
    exercises = db.child("exercises").get()
    return render_template("exercises.html", exercises=exercises)


@app.route("/create_exercise", methods=["GET", "POST"])
def create_exercise():
    if request.method == "GET":
        # Display a form to add a new exercise
        return render_template("create_exercise.html")
    # Insert the new exercise into the database
    name = request.form["name"]
    description = request.form["description"]
    video_link = request.form["video_link"]
    db.child("exercises").child(name).update(
        {
            "name": name,
            "video link": video_link,
            "description": description,
        }
    )
    return redirect(url_for("app.exercises"))


@app.route("/edit_exercise/<exercise_id>", methods=["GET", "POST"])
def edit_exercise(exercise_id):
    exercise = db.child("exercises").child(exercise_id).get()
    if request.method == "POST":
        name = request.form["exercise_name"]
        description = request.form["description"]
        video_link = request.form["video_link"]
        db.child("exercises").child(exercise_id).update(
            {
                "name": name,
                "video link": video_link,
                "description": description,
            }
        )
        flash("Exercise updated successfully", "success")
        return redirect(url_for("app.exercises"))

    return render_template("edit_exercise.html", exercise=exercise)


@app.route("/delete_exercise/<exercise_id>", methods=["POST"])
def delete_exercise(exercise_id):
    db.child("exercises").child(exercise_id).remove()
    flash("Exercise deleted successfully", "success")
    return redirect(url_for("app.exercises"))


def update_one_rep_max(exercise_name, weight, reps):
    exercise_max = (
        db.child("users")
        .child(session["id"])
        .child("exercise maxes")
        .child(exercise_name)
        .get()
        .val()
    )
    theoretical_max = round(weight / (1.0278 - (0.0278 * float(reps))), 1)
    if exercise_max:
        theoretical_max = max(exercise_max["theoretical max"], theoretical_max)
    db.child("users").child(session["id"]).child("theoretical maxes").child(
        exercise_name
    ).update(
        {
            "name": exercise_name,
            "theoretical max": theoretical_max,
        }
    )


@app.route("/create_set/<workout_id>", methods=["POST", "GET"])
def create_set(workout_id):
    if request.method == "GET":
        exercises = db.child("exercises").get()
        return render_template(
            "create_set.html", workout_id=workout_id, exercises=exercises
        )
    # Insert the new exercise into the database
    weight = float(request.form["weight"])
    reps = int(request.form["reps"])
    sets = int(request.form["sets"])

    exercise_id = request.form["exercise_id"]
    db.child("workouts").child(workout_id).child("exercises").child(exercise_id).update(
        {
            "weight": weight,
            "reps": reps,
            "sets": sets,
            "exercise name": exercise_id,
        }
    )

    # Update theoretical maxes
    update_one_rep_max(exercise_id, weight, reps)
    return redirect(url_for("app.view_workout", workout_id=workout_id))


@app.route("/edit_set/<workout_id>/<exercise_id>", methods=["GET", "POST"])
def edit_set(workout_id, exercise_id):
    workout_set = (
        db.child("workouts")
        .child(workout_id)
        .child("exercises")
        .child(exercise_id)
        .get()
    )
    if request.method == "GET":
        return render_template("edit_set.html", set=workout_set, workout_id=workout_id)
    weight = float(request.form["weight"])
    reps = int(request.form["reps"])
    sets = int(request.form["sets"])
    db.child("workouts").child(workout_id).child("exercises").child(exercise_id).update(
        {"weight": weight, "reps": reps, "sets": sets, "exercise name": exercise_id}
    )
    flash("Set updated successfully", "success")
    print(workout_set.val())
    # Update theoretical maxes
    update_one_rep_max(exercise_id, weight, reps)
    return redirect(url_for("app.view_workout", workout_id=workout_id))


@app.route("/delete_set/<workout_id>/<exercise_id>", methods=["POST"])
def delete_set(workout_id, exercise_id):

    db.child("workouts").child(workout_id).child("exercises").child(
        exercise_id
    ).remove()
    flash("Set deleted successfully", "success")
    return redirect(url_for("app.view_workout", workout_id=workout_id))


@app.route("/todos")
def todos():
    todos = db.child("users").child(session["id"]).child("todos").get()
    name = db.child("users").child(session["id"]).child("name").get().val()
    return render_template("todos.html", todos=todos, name=name)


def send_push_notification(
    message, headings=None, player_ids=None, included_segments=None
):
    notification = {
        "app_id": "c297534c-4c51-460a-a5e7-ad932040993a",
        "contents": {"en": message},
        "headings": {"en": headings} if headings else None,
    }
    if player_ids:
        notification["include_player_ids"] = player_ids
    if included_segments:
        notification["included_segments"] = included_segments

    response = client.send_notification(notification)
    return response


@app.route("/todos/create", methods=["GET", "POST"])
def create_todo():
    if request.method == "POST":
        todo_name = request.form["name"]
        todo_description = request.form["description"]
        todo_due_date = request.form["due date"]
        todo = {
            "description": todo_description,
            "done": False,
            "due_date": todo_due_date,
        }
        send_push_notification(todo_name)
        db.child("users").child(session["id"]).child("todos").child(todo_name).set(todo)
        # Schedule a notification if the due date is in the past
        flash(f"Todo {todo_name} created successfully!", "success")
        return redirect(url_for("app.todos"))
    else:
        return render_template("create_todo.html")


@app.route("/todos/<todo_id>/update", methods=["POST"])
def update_todo(todo_id):
    todo_ref = db.child("users").child(session["id"]).child("todos").child(todo_id)
    completed = request.form.get("completed")
    due_date = request.form.get("due date")

    if not due_date:
        todo_ref.update({"done": completed})
    else:
        todo_ref.update({"due date": due_date})

    return redirect(url_for("app.todos"))


@app.route("/todos/<todo_id>/delete", methods=["POST"])
def delete_todo(todo_id):
    print(todo_id)
    db.child("users").child(session["id"]).child("todos").child(todo_id).remove()
    return redirect(url_for("app.todos"))


# define the function to filter data by category
def filter_by_category(category):
    all_workouts = (
        db.child("workouts").order_by_child("localId").equal_to(session["id"]).get()
    )
    for item in all_workouts.each():
        if category == "all":
            print(item.key(), item.val())
        elif item.val()["category"] == category:
            print(item.key(), item.val())


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )
