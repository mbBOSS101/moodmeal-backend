from flask import Flask, request, jsonify
import requests
import os
from sentence_transformers import SentenceTransformer, util

app = Flask(__name__)

VERSION = "v3.semantic_only"  # Updated version identifier

# Use a light model variant and lazy-load it.
MODEL_NAME = "paraphrase-MiniLM-L3-v2"
model = None  # Global cache for the model

def get_model():
    global model
    if model is None:
        print("Loading SentenceTransformer model...")
        model = SentenceTransformer(MODEL_NAME)
    return model

# Securely fetch API key and define endpoints.
SPOONACULAR_API_KEY = os.environ.get("EXPO_PUBLIC_SPOONACULAR_API_KEY")
SPOONACULAR_SEARCH_ENDPOINT = 'https://api.spoonacular.com/recipes/complexSearch'
SPOONACULAR_RANDOM_ENDPOINT = 'https://api.spoonacular.com/recipes/random'

@app.route('/get_best_recipe', methods=['POST'])
def get_best_recipe():
    try:
        req_data = request.json
        print("✅ Request received:", req_data)

        if not req_data or "vibe" not in req_data:
            print("❌ Invalid data:", req_data)
            return jsonify({"error": "Missing 'vibe' in request"}), 400

        vibe = req_data["vibe"]
        print("🔍 Vibe is:", vibe)

        # Use the limit from the request or default to 20 recipes.
        limit = req_data.get("limit", 20)

        # Perform a generic query without filtering ingredients.
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "number": limit,
            "addRecipeInformation": True
        }
        response = requests.get(SPOONACULAR_SEARCH_ENDPOINT, params=params)
        data = response.json()
        recipes = data.get("results", [])
        print("📦 Retrieved results:", len(recipes))

        # Fallback: if no recipes are found, fetch random recipes.
        if not recipes:
            print("⚠️ No recipes found; fetching random recipes fallback.")
            params_random = {
                "apiKey": SPOONACULAR_API_KEY,
                "number": limit,
                "addRecipeInformation": True
            }
            response_random = requests.get(SPOONACULAR_RANDOM_ENDPOINT, params=params_random)
            data_random = response_random.json()
            recipes = data_random.get("recipes", [])
            print("📦 Random recipes fallback results:", len(recipes))

        # Deduplicate recipes based on a unique property (recipe 'id' or title).
        unique_dict = {}
        for recipe in recipes:
            key = recipe.get("id") or recipe.get("title")
            if key:
                unique_dict[key] = recipe
        unique_recipes = list(unique_dict.values())

        # Compute semantic similarity for ranking.
        model_instance = get_model()
        mood_embedding = model_instance.encode([vibe], convert_to_tensor=True)

        for recipe in unique_recipes:
            text = recipe.get("title", "")
            if "summary" in recipe:
                text += " " + recipe["summary"]
            recipe_embedding = model_instance.encode([text], convert_to_tensor=True)
            sim = util.cos_sim(mood_embedding, recipe_embedding)[0][0].item()
            # Scale similarity to a 0–100 score.
            recipe["score"] = sim * 100
            recipe["mood"] = vibe

        # Sort recipes by score in descending order.
        sorted_recipes = sorted(unique_recipes, key=lambda r: r["score"], reverse=True)
        top_recipes = sorted_recipes[:5]
        print("🏆 Returning", len(top_recipes), "recipes for vibe", vibe)
        return jsonify(top_recipes)
    except Exception as e:
        print("❌ Exception:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def hello():
    return f"✅ Flask is working! {VERSION}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
