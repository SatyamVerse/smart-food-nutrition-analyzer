from flask import Flask, render_template, request
import json

app = Flask(__name__)


# ==========================================
# LOAD FOOD DATABASE
# ==========================================

with open("data/foods.json", "r") as file:
    foods = json.load(file)


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")


# ==========================================
# ANALYZE FOOD
# ==========================================

@app.route("/analyze", methods=["POST"])
def analyze():

    food_name = request.form.get("food")

    if not food_name:
        return "Please enter a food name."

    food_name = food_name.lower().strip()

    food = foods.get(food_name)

    if not food:
        return "Food not found. Please try another food."

    return render_template(
        "result.html",
        food=food
    )


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)