from flask import Flask, render_template, request
from action import Action
from spech_to_text import spech_to_text

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    response = ""
    if request.method == "POST":
        if 'command' in request.form:
            user_input = request.form["command"]
        elif 'voice' in request.form:
            user_input = spech_to_text()
        else:
            user_input = ""

        if user_input:
            response = Action(user_input)

    return render_template("index.html", response=response)

if __name__ == "__main__":
    app.run(debug=True)
