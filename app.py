from flask import Flask, render_template, request
import json
from PIL import Image
from transformers import pipeline


# ========================================================
# FLASK APP
# ========================================================

app = Flask(__name__)

# ========================================================
# LOAD FOOD DATABASE
# ========================================================

with open("data/foods.json", "r") as file:
    foods = json.load(file)

# =========================================================
# FOOD LABEL MAPPING
# =========================================================
#
# These are the ONLY foods the photo analyzer is allowed
# to identify.
#
# This prevents the model from choosing random foods that
# do not exist in our nutrition database.
# ========================================================

FOOD_LABELS = {
    "apple": "apple",
    "banana": "banana",
    "egg": "egg",
    "rice": "rice",
    "chicken": "chicken",
    "milk": "milk",
    "bread": "bread",
    "potato": "potato",
    "tomato": "tomato",
    "paneer": "paneer",
    "dal": "dal",
    "roti": "roti"
}

# ========================================================
# AI MODEL
# ========================================================

print()
print("==========================================")
print("Loading AI food recognition model...")
print("==========================================")

food_classifier = pipeline(
    task="zero-shot-image-classification",
    model="openai/clip-vit-base-patch32"
)

print("AI model loaded successfully!")
print()


# =========================================================
# NUTRITION SCORE
# =========================================================

def calculate_nutrition_score(food):

    score = 50

    # -----------------------------------------------------
    # Protein
    # -----------------------------------------------------

    protein = food.get("protein", 0)

    if protein >= 20:
        score += 15

    elif protein >= 10:
        score += 10

    elif protein >= 5:
        score += 5


    # -----------------------------------------------------
    # Fiber
    # -----------------------------------------------------

    fiber = food.get("fiber", 0)

    if fiber >= 10:
        score += 15

    elif fiber >= 5:
        score += 10

    elif fiber >= 3:
        score += 5


    # -----------------------------------------------------
    # Sugar
    # -----------------------------------------------------

    sugar = food.get("sugar", 0)

    if sugar > 20:
        score -= 15

    elif sugar > 10:
        score -= 10

    elif sugar > 5:
        score -= 5


    # -----------------------------------------------------
    # Sodium
    # -----------------------------------------------------

    sodium = food.get("sodium", 0)

    if sodium > 500:
        score -= 15

    elif sodium > 300:
        score -= 10

    elif sodium > 150:
        score -= 5


    # ----------------------------------------------------
    # Fat
    # ----------------------------------------------------

    fat = food.get("fat", 0)

    if fat > 25:
        score -= 10

    elif fat > 15:
        score -= 5


    # -----------------------------------------------------
    # Calories
    # -----------------------------------------------------

    calories = food.get("calories", 0)

    if calories > 500:
        score -= 10

    elif calories > 350:
        score -= 5


    # -----------------------------------------------------
    # Keep score between 0 and 100
    # -----------------------------------------------------

    score = max(0, min(100, score))

    return score


# =========================================================
# SCORE LABEL
# =========================================================

def get_score_label(score):

    if score >= 80:
        return "Excellent"

    elif score >= 65:
        return "Good"

    elif score >= 50:
        return "Moderate"

    else:
        return "Needs Improvement"


# =========================================================
# TEXT SEARCH
# =========================================================

@app.route("/")
def home():

    return render_template("index.html")


# =========================================================
# TEXT FOOD ANALYSIS
# =========================================================

@app.route("/analyze", methods=["POST"])
def analyze():

    food_name = request.form.get("food", "")

    food_name = food_name.lower().strip()


    if not food_name:

        return render_template(
            "index.html",
            error="Please enter a food name."
        )


    food = foods.get(food_name)


    if not food:

        return render_template(
            "index.html",
            error="Food not found. Please try another food."
        )


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


# =========================================================
# IMAGE UPLOAD
# =========================================================

@app.route("/upload", methods=["POST"])
def upload():

    image_file = request.files.get("food_image")


    # -----------------------------------------------------
    # Check whether image was uploaded
    # -----------------------------------------------------

    if not image_file:

        return render_template(
            "upload_result.html",
            success=False,
            error="Please select a food image."
        )


    if image_file.filename == "":

        return render_template(
            "upload_result.html",
            success=False,
            error="Please select a food image."
        )


    # -----------------------------------------------------
    # Check file type
    # -----------------------------------------------------

    allowed_extensions = {
        "jpg",
        "jpeg",
        "png",
        "webp"
    }

    filename = image_file.filename.lower()

    extension = filename.rsplit(".", 1)[-1]


    if extension not in allowed_extensions:

        return render_template(
            "upload_result.html",
            success=False,
            error="Please upload JPG, JPEG, PNG, or WEBP image."
        )


    try:

        # -------------------------------------------------
        # Open image
        # -------------------------------------------------

        image = Image.open(image_file)

        image = image.convert("RGB")


        # -------------------------------------------------
        # Candidate labels
        # -------------------------------------------------

        candidate_labels = list(FOOD_LABELS.keys())


        # -------------------------------------------------
        # Ask AI to compare the image ONLY against our
        # supported food list.
        # -------------------------------------------------

        predictions = food_classifier(
            image,
            candidate_labels=candidate_labels
        )


        # -------------------------------------------------
        # Sort predictions
        # -------------------------------------------------

        predictions = sorted(
            predictions,
            key=lambda item: item["score"],
            reverse=True
        )


        # -------------------------------------------------
        # Best prediction
        # -------------------------------------------------

        best_prediction = predictions[0]

        best_label = best_prediction["label"]

        best_score = best_prediction["score"]


        # -------------------------------------------------
        # Second-best prediction
        # -------------------------------------------------

        second_score = 0

        if len(predictions) > 1:

            second_score = predictions[1]["score"]


        # -------------------------------------------------
        # Confidence percentage
        # -------------------------------------------------

        confidence = round(best_score * 100, 2)


        # -------------------------------------------------
        # Difference between first and second prediction
        #
        # Example:
        #
        # Apple   72%
        # Tomato  12%
        #
        # Difference = 60%
        #
        # Strong separation.
        #
        # But:
        #
        # Apple   31%
        # Tomato  29%
        #
        # Difference = 2%
        #
        # Very uncertain.
        # -------------------------------------------------

        prediction_margin = best_score - second_score

        margin_percentage = round(
            prediction_margin * 100,
            2
        )


        # -------------------------------------------------
        # SAFETY RULES
        # -------------------------------------------------
        #
        # We do NOT automatically accept every prediction.
        #
        # Minimum confidence:
        # 50%
        #
        # Minimum difference from second prediction:
        # 10%
        #
        # These thresholds can be adjusted later.
        # -------------------------------------------------

        MIN_CONFIDENCE = 0.50

        MIN_MARGIN = 0.10


        confident_enough = (
            best_score >= MIN_CONFIDENCE
        )


        clearly_ahead = (
            prediction_margin >= MIN_MARGIN
        )


        # -------------------------------------------------
        # If prediction is uncertain, DO NOT give
        # nutrition information.
        # -------------------------------------------------

        if not confident_enough or not clearly_ahead:

            alternatives = []

            for prediction in predictions[:3]:

                alternatives.append({
                    "name": prediction["label"].title(),
                    "confidence": round(
                        prediction["score"] * 100,
                        2
                    )
                })


            return render_template(
                "upload_result.html",
                success=False,
                uncertain=True,
                detected_food=best_label.title(),
                confidence=confidence,
                margin=margin_percentage,
                alternatives=alternatives
            )


        # -------------------------------------------------
        # Get database key
        # -------------------------------------------------

        food_key = FOOD_LABELS.get(best_label)


        if not food_key or food_key not in foods:

            return render_template(
                "upload_result.html",
                success=False,
                error="This food is not available in the nutrition database."
            )


        # -------------------------------------------------
        # Get nutrition data
        # -------------------------------------------------

        food = foods[food_key]


        # -------------------------------------------------
        # Calculate nutrition score
        # -------------------------------------------------

        nutrition_score = calculate_nutrition_score(food)

        score_label = get_score_label(
            nutrition_score
        )


        # -------------------------------------------------
        # Return successful result
        # -------------------------------------------------

        return render_template(
            "upload_result.html",
            success=True,
            uncertain=False,

            detected_food=food.get("name"),

            confidence=confidence,

            margin=margin_percentage,

            food=food,

            nutrition_score=nutrition_score,

            score_label=score_label,

            predictions=[
                {
                    "name": prediction["label"].title(),
                    "confidence": round(
                        prediction["score"] * 100,
                        2
                    )
                }

                for prediction in predictions[:3]
            ]
        )


    except Exception as error:

        print("IMAGE ERROR:", error)

        return render_template(
            "upload_result.html",
            success=False,
            error="Unable to process this image. Please try another photo."
        )


# =========================================================
# RUN APPLICATION
# =========================================================

if __name__ == "__main__":

    app.run(debug=True)
