import json
import os
import secrets
import requests

from flask import Flask, flash, render_template, request, redirect, url_for, session
import pyrebase

app = Flask(__name__)
with open("./firebaseConfig.json", "r") as json_file:
    firebaseConfig = json.load(json_file)

firebase = pyrebase.initialize_app(firebaseConfig)

# Database
db = firebase.database()
# Auth
auth = firebase.auth()
app.secret_key = "A0AKR5TGD\ R~XHH!jmN]234LWX/,?RT"
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = True

# login
@app.route("/", methods=["POST", "GET"])
def index():
    if "id" not in session:
        if request.method == "GET":
            return render_template("index.html")
        # Get form data
        email = request.form["email"]
        password = request.form["password"]
        try:
            login = auth.sign_in_with_email_and_password(email, password)
            session["id"] = login["localId"]
            flash("succesfully logged in", "success")
        except requests.exceptions.HTTPError:
            flash("Invalid email or password.", "danger")
            return render_template("index.html")
    workouts = db.child("workouts").get()
    return render_template("workouts.html", workouts=workouts)


@app.route("/logout")
def logout():
    # remove the email from the session
    session.pop("id", None)
    # redirect to the index page
    return redirect(url_for("index"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")
    # Get form data
    name = request.form["name"]
    email = request.form["email"]
    password = request.form["password"]

    # TODO: Insert user data into database
    register = auth.create_user_with_email_and_password(email, password)
    # Log user in
    session["id"] = register["localId"]

    # Redirect to homepage
    return redirect(url_for("index"))


@app.route("/create_workout", methods=["GET", "POST"])
def create_workout():
    if request.method == "POST":
        # Insert the new workout into the database
        workout_name = request.form["name"]
        body_group = request.form["body_group"]
        localId = session["id"]
        db.child("workouts").child(workout_name).update(
            {"name": workout_name, "localId": localId, "body group": body_group}
        )
        return redirect(url_for("index"))
    else:
        # Display a form to add a new workout
        return render_template("create_workout.html")


@app.route("/workout/<workout_id>")
def view_workout(workout_id):
    # Display the details of a specific workout
    workouts = db.child("workouts").child(workout_id).get()
    return render_template("workout.html", workout=workouts)


@app.route("/edit_workout/<workout_id>", methods=["GET", "POST"])
def edit_workout(workout_id):
    # Display the details of a specific workout
    if request.method == "POST":
        name = request.form["name"]
        if "id" in session:
            localId = session["id"]
        else:
            session["id"] = ""
        body_group = request.form["body_group"]

        db.child("workouts").child(workout_id).update(
            {"name": name, "localId": localId, "body group": body_group}
        )

        flash("Workout updated successfully", "success")
        return redirect(url_for("index"))

    workouts = db.child("workouts").child(workout_id).get()

    return render_template("edit_workout.html", workout=workouts, workout_id=workout_id)


@app.route("/delete_workout/<workout_id>", methods=["POST"])
def delete_workout(workout_id):
    db.child("workouts").child(workout_id).remove()
    flash("Workout deleted successfully", "success")
    return redirect(url_for("index"))


@app.route("/exercises")
def exercises():
    # Display a list of workouts
    exercises = db.child("exercises").get()
    return render_template("exercises.html", exercises=exercises)


@app.route("/create_exercise", methods=["GET", "POST"])
def create_exercise():
    if request.method == "POST":
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
        return redirect(url_for("exercises"))
    else:
        # Display a form to add a new exercise
        return render_template("create_exercise.html")


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
        return redirect(url_for("exercises"))

    return render_template("edit_exercise.html", exercise=exercise)


@app.route("/delete_exercise/<exercise_id>", methods=["POST"])
def delete_exercise(exercise_id):
    db.child("exercises").child(exercise_id).remove()
    flash("Exercise deleted successfully", "success")
    return redirect(url_for("exercises"))


@app.route("/create_set/<workout_id>", methods=["POST", "GET"])
def create_set(workout_id):
    if request.method == "POST":
        # Insert the new exercise into the database
        weight = request.form["weight"]
        reps = request.form["reps"]
        sets = request.form["sets"]
        exercise_id = request.form["exercise_id"]
        db.child("workouts").child(workout_id).child("exercises").child(
            exercise_id
        ).update(
            {"weight": weight, "reps": reps, "sets": sets, "exercise name": exercise_id}
        )
        return redirect(url_for("view_workout", workout_id=workout_id))
    exercises = db.child("exercises").get()
    return render_template(
        "create_set.html", workout_id=workout_id, exercises=exercises
    )


@app.route("/edit_set/<workout_id>/<exercise_id>", methods=["GET", "POST"])
def edit_set(workout_id, exercise_id):
    set = (
        db.child("workouts")
        .child(workout_id)
        .child("exercises")
        .child(exercise_id)
        .get()
    )
    if request.method == "GET":
        return render_template("edit_set.html", set=set, workout_id=workout_id)
    weight = request.form["weight"]
    reps = request.form["reps"]
    sets = request.form["sets"]
    db.child("workouts").child(workout_id).child("exercises").child(exercise_id).update(
        {"weight": weight, "reps": reps, "sets": sets, "exercise name": exercise_id}
    )
    flash("Set updated successfully", "success")
    print(set)
    return redirect(url_for("view_workout", workout_id=workout_id))


@app.route("/delete_set/<workout_id>/<exercise_id>", methods=["POST"])
def delete_set(workout_id, exercise_id):

    db.child("workouts").child(workout_id).child("exercises").child(
        exercise_id
    ).remove()
    flash("Set deleted successfully", "success")
    return redirect(url_for("view_workout", workout_id=workout_id))


if __name__ == "__main__":
    app.run(
        debug=True, host="0.0.0.0", port=int(os.environ.get("PORT", 8080))
    )  # Make sure debug is false on production environment
