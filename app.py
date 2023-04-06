from datetime import timedelta

from flask import Flask
import routes


app = Flask(__name__)
app.secret_key = "A0AKR5TGD\ R~XHH!jmN]234LWX/,?RT"
app.config["SESSION_TYPE"] = "filesystem"
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=5)

# Register the routes blueprint
app.register_blueprint(routes.app)

if __name__ == "__main__":
    app.run(debug=True)
