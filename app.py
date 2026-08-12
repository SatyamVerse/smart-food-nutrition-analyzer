from flask import Flask, render_template, request
import json

app = Flask(__name__)


# ==========================================
# LOAD FOOD DATABASE
# ==========================================

with open("data/foods.json", "r") as file:
    foods = json.load(file)


# ==========================================
# CALCULATE NUTRITION SCORE
# ==========================================

def calculate_nutrition_score(food):

    score = 50

    # --------------------------------------
    # Positive factors
    # --------------------------------------

    # Protein
    protein = food.get("protein", 0)

    if protein >= 20:
        score += 15
    elif protein >= 10:
        score += 10
    elif protein >= 5:
        score += 5

    # Fiber
    fiber = food.get("fiber", 0)

    if fiber >= 10:
        score += 15
    elif fiber >= 5:
        score += 10
    elif fiber >= 3:
        score += 5

    # --------------------------------------
    # Negative factors
    # --------------------------------------

    # Sugar
    sugar = food.get("sugar", 0)

    if sugar > 20:
        score -= 15
    elif sugar > 10:
        score -= 10
    elif sugar > 5:
        score -= 5

    # Sodium
    sodium = food.get("sodium", 0)

    if sodium > 500:
        score -= 15
    elif sodium > 300:
        score -= 10
    elif sodium > 150:
        score -= 5

    # Fat
    fat = food.get("fat", 0)

    if fat > 25:
        score -= 10
    elif fat > 15:
        score -= 5

    # Calories
    calories = food.get("calories", 0)

    if calories > 500:
        score -= 10
    elif calories > 350:
        score -= 5

    # --------------------------------------
    # Keep score between 0 and 100
    # --------------------------------------

    score = max(0, min(100, score))

    return score


# ==========================================
# GET SCORE LABEL
# ==========================================

def get_score_label(score):

    if score >= 80:
        return "Excellent"

    elif score >= 65:
        return "Good"

    elif score >= 50:
        return "Moderate"

    else:
        return "Needs Improvement"


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

    # Get food entered by user
    food_name = request.form.get("food")

    # Check empty input
    if not food_name:
        return "Please enter a food name."

    # Clean input
    food_name = food_name.lower().strip()

    # Search food database
    food = foods.get(food_name)

    # Food not found
    if not food:
        return "Food not found. Please try another food."

    # Calculate nutrition score
    nutrition_score = calculate_nutrition_score(food)

    # Get score label
    score_label = get_score_label(nutrition_score)

    # Send everything to result.html
    return render_template(
        "result.html",
        food=food,
        food_name=food_name,
        nutrition_score=nutrition_score,
        score_label=score_label
    )


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":
    app.run(debug=True)
