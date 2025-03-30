from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

VERSION = "v3.1"  # Updated version identifier

# Securely fetch API key from environment variable
SPOONACULAR_API_KEY = os.environ.get("EXPO_PUBLIC_SPOONACULAR_API_KEY")
# Endpoints
SPOONACULAR_SEARCH_ENDPOINT = 'https://api.spoonacular.com/recipes/complexSearch'
SPOONACULAR_RANDOM_ENDPOINT = 'https://api.spoonacular.com/recipes/random'

# Broader set of keywords per vibe to yield more recipe results.
vibe_keywords = {
    "Cozy": ["cheese", "potato", "broth", "soup", "stew", "comfort"],
    "Energetic": ["banana", "spinach", "protein", "energy", "power", "vitality"],
    "Excited": ["jalapeno", "bacon", "beef", "spicy", "zest", "pepper"],
    "Relaxed": ["pasta", "mushroom", "butter", "creamy", "comfort", "smooth"],
    "Playful": ["zucchini", "noodles", "parmesan", "savor", "mellow", "subtle"],
    "Calm": ["ginger", "tea", "rice", "herbal", "soothing", "calm"],
    "Contemplative": ["tofu", "lentils", "eggplant", "meditate", "mindful", "quiet"],
    "Thoughtful": ["zucchini", "noodles", "parmesan", "savor", "mellow", "subtle"],
    "Reflective": ["ramen", "soy", "curry", "introspective", "ponder", "soulful"]
}

def score_recipe(recipe, vibe):
    base_score = 0.0

    # Factor 1: Ready Time Score (full score if <=30 minutes, 0 if >=90 minutes)
    ready_in = recipe.get('readyInMinutes', 60)
    if ready_in <= 30:
        ready_time_score = 1.0
    elif ready_in >= 90:
        ready_time_score = 0.0
    else:
        ready_time_score = (90 - ready_in) / 60.0
    base_score += ready_time_score * 0.3  # 30% weight

    # Factor 2: Keyword Relevance Score (based on vibe keywords in the title)
    keywords = vibe_keywords.get(vibe, [vibe])
    title = recipe.get('title', '').lower()
    keyword_matches = sum(1 for word in keywords if word.lower() in title)
    keyword_score = min(keyword_matches / len(keywords), 1.0)
    base_score += keyword_score * 0.3  # 30% weight

    # Factor 3: Popularity (using aggregateLikes)
    popularity = recipe.get('aggregateLikes', 0)
    popularity_score = min(popularity / 100.0, 1.0)
    base_score += popularity_score * 0.2  # 20% weight

    # Factor 4: Spoonacular's own score (normalized from 0 to 1)
    spoonacular_score = recipe.get('spoonacularScore', 0) / 100.0
    base_score += spoonacular_score * 0.1  # 10% weight

    # Factor 5: Health Score (rewarding higher nutritional value)
    health_score = recipe.get('healthScore', 0) / 100.0
    base_score += health_score * 0.1  # 10% weight

    return base_score

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

        # Look up keywords; if vibe not found, default to using the vibe word.
        keywords = vibe_keywords.get(vibe, [vibe])
        print("🧠 Using keywords:", keywords)

        # Use the limit from the request or default to 20.
        limit = req_data.get("limit", 20)

        # Query 1: Vibe-specific query using the keywords.
        params1 = {
            "apiKey": SPOONACULAR_API_KEY,
            "includeIngredients": ','.join(keywords),
            "number": limit,
            "addRecipeInformation": True
        }
        response1 = requests.get(SPOONACULAR_SEARCH_ENDPOINT, params=params1)
        data1 = response1.json()
        results1 = data1.get("results", [])
        print("📦 Vibe-specific results:", len(results1))

        # Query 2: Generic query without filtering ingredients.
        params2 = {
            "apiKey": SPOONACULAR_API_KEY,
            "number": limit,
            "addRecipeInformation": True
        }
        response2 = requests.get(SPOONACULAR_SEARCH_ENDPOINT, params=params2)
        data2 = response2.json()
        results2 = data2.get("results", [])
        print("📦 Generic results:", len(results2))

        # Merge both sets.
        merged = results1 + results2

        # Deduplicate based on a unique property (use recipe 'id' if available; fallback to title).
        unique_dict = {}
        for recipe in merged:
            key = recipe.get("id") or recipe.get("title")
            if key:
                unique_dict[key] = recipe
        unique_recipes = list(unique_dict.values())

        # Fallback Handling:
        # If no recipes are found from both queries, fetch random recipes.
        if not unique_recipes:
            print("⚠️ No recipes found from queries; fetching random recipes fallback.")
            params_random = {
                "apiKey": SPOONACULAR_API_KEY,
                "number": limit,
                "addRecipeInformation": True
            }
            response_random = requests.get(SPOONACULAR_RANDOM_ENDPOINT, params=params_random)
            data_random = response_random.json()
            unique_recipes = data_random.get("recipes", [])
            print("📦 Random recipes fallback results:", len(unique_recipes))

        # Score each recipe and add the score to its data.
        for recipe in unique_recipes:
            computed_score = round(score_recipe(recipe, vibe) * 100)
            recipe["score"] = computed_score

        # Sort recipes by score in descending order.
        sorted_recipes = sorted(unique_recipes, key=lambda r: r["score"], reverse=True)
        print("🏆 Returning", len(sorted_recipes), "recipes for vibe", vibe)
        return jsonify(sorted_recipes)

    except Exception as e:
        print("❌ Exception:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def hello():
    return f"✅ Flask is working! {VERSION}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
