from flask import Flask, request, jsonify
import requests, os
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

# Load the pre-trained sentence transformer model.
model = SentenceTransformer('all-MiniLM-L6-v2')

# Fetch your Spoonacular API key from environment variables.
SPOONACULAR_API_KEY = os.environ.get("EXPO_PUBLIC_SPOONACULAR_API_KEY")
SPOONACULAR_ENDPOINT = 'https://api.spoonacular.com/recipes/complexSearch'

@app.route('/get_best_recipe', methods=['POST'])
def get_best_recipe():
    try:
        req_data = request.json
        # Expect a "vibe" field from the frontend describing the user's mood.
        mood = req_data.get("vibe")
        if not mood:
            return jsonify({"error": "Missing 'vibe' in request"}), 400

        # Get a limit (default to 20 recipes from Spoonacular)
        limit = req_data.get("limit", 20)

        # Compute the semantic embedding for the mood.
        mood_embedding = model.encode([mood], convert_to_tensor=True)

        # Query Spoonacular for recipes (without ingredient filtering for this example)
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "number": limit,
            "addRecipeInformation": True
        }
        response = requests.get(SPOONACULAR_ENDPOINT, params=params)
        spoon_data = response.json()
        recipes = spoon_data.get("results", [])

        # If no recipes were returned, use a fallback (here we simply return an empty list,
        # but you could also call Spoonacular's random recipes endpoint)
        if not recipes:
            return jsonify([])

        # Compute a semantic similarity score for each recipe.
        # We combine the recipe's title and summary (if available) into a single text.
        for recipe in recipes:
            text = recipe.get("title", "")
            if "summary" in recipe:
                text += " " + recipe["summary"]
            # Compute the recipe's embedding.
            recipe_embedding = model.encode([text], convert_to_tensor=True)
            # Calculate cosine similarity between the mood and recipe.
            sim = util.cos_sim(mood_embedding, recipe_embedding)[0][0].item()
            # Scale similarity to a 0–100 score.
            recipe["score"] = sim * 100

        # Sort recipes by their semantic score in descending order.
        recipes.sort(key=lambda r: r["score"], reverse=True)
        # Slice the sorted list to return only the top 5 recipes.
        top_recipes = recipes[:5]

        return jsonify(top_recipes)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def hello():
    return "Flask is working!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
