from flask import Flask, render_template, request
import json
from PIL import Image
from transformers import pipeline
import os

app = Flask(__name__)


# ==========================================
# LOAD FOOD DATABASE
# ==========================================

with open("data/foods.json", "r") as file:
    foods = json.load(file)


# ==========================================
# AI FOOD IMAGE CLASSIFIER
# ==========================================

print("Loading food recognition model...")

food_classifier = pipeline(
    "image-classification",
    model="nateraw/food"
)

print("Food recognition model loaded!")


# ==========================================
# CALCULATE NUTRITION SCORE
# ==========================================

def calculate_nutrition_score(food):

    score = 50

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

    score = max(0, min(100, score))

    return score


# ==========================================
# SCORE LABEL
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
# FIND FOOD IN DATABASE
# ==========================================

def find_food(food_label):

    food_label = food_label.lower()

    # Direct match
    if food_label in foods:
        return foods[food_label]

    # Search inside food names
    for key, food in foods.items():

        database_name = food.get("name", "").lower()

        if food_label in database_name:
            return food

        if database_name in food_label:
            return food

    return None


# ==========================================
# HOME PAGE
# ==========================================

@app.route("/")
def home():

    return render_template("index.html")


# ==========================================
# TEXT FOOD ANALYSIS
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

    nutrition_score = calculate_nutrition_score(food)

    score_label = get_score_label(nutrition_score)

    return render_template(
        "result.html",
        food=food,
        food_name=food_name,
        nutrition_score=nutrition_score,
        score_label=score_label,
        detected_food=food.get("name")
    )


# ==========================================
# IMAGE FOOD ANALYSIS
# ==========================================

@app.route("/upload", methods=["POST"])
def upload():

    image = request.files.get("food_image")

    # Check image
    if not image:

        return "Please upload a food image."

    if image.filename == "":

        return "Please select an image."


    try:

        # Open uploaded image
        img = Image.open(image)

        # Convert image to RGB
        img = img.convert("RGB")


        # AI prediction
        predictions = food_classifier(
            img,
            top_k=5
        )


        # Get highest prediction
        detected_label = predictions[0]["label"]

        confidence = predictions[0]["score"] * 100


        # Find matching food in our database
        food = find_food(detected_label)


        # If detected food isn't in database
        if not food:

            return render_template(
                "upload_result.html",
                detected_food=detected_label,
                confidence=round(confidence, 2),
                found=False
            )


        # Calculate nutrition score
        nutrition_score = calculate_nutrition_score(food)

        score_label = get_score_label(nutrition_score)


        # Show result
        return render_template(
            "upload_result.html",
            food=food,
            detected_food=food.get("name"),
            confidence=round(confidence, 2),
            nutrition_score=nutrition_score,
            score_label=score_label,
            found=True
        )


    except Exception as e:

        return f"Error processing image: {str(e)}"


# ==========================================
# RUN APPLICATION
# ==========================================

if __name__ == "__main__":

    app.run(debug=True)
