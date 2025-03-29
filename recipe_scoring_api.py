from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

VERSION = "v2.1"  # or any identifier you like

# Securely fetch API key from environment variable
SPOONACULAR_API_KEY = os.environ.get("EXPO_PUBLIC_SPOONACULAR_API_KEY")
SPOONACULAR_ENDPOINT = 'https://api.spoonacular.com/recipes/complexSearch'

# A broader set of keywords for each vibe to yield more recipe results.
vibe_keywords = {
    "Cozy": ["cheese", "potato", "broth", "soup", "stew", "comfort"],
    "Energetic": ["banana", "spinach", "protein", "energy", "power", "vitality"],
    "Excited": ["jalapeno", "bacon", "beef", "spicy", "zest", "pepper"],
    "Relaxed": ["pasta", "mushroom", "butter", "creamy", "comfort", "smooth"],
    "Playful": ["chocolate", "sprinkles", "berries", "fun", "colorful", "candy"],
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
        ready_time_score = (90 - ready_in) / 60.0  # Linear scaling between 30 and 90 minutes
    base_score += ready_time_score * 0.3  # 30% weight

    # Factor 2: Keyword Relevance Score (based on vibe keywords in the title)
    # Use our broader keyword list if vibe is recognized; otherwise default to vibe as keyword.
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

        # Look up keywords; if vibe isn't found, default to using the vibe word.
        keywords = vibe_keywords.get(vibe, [vibe])
        print("🧠 Using keywords:", keywords)

        # Use the limit from the request or default to 20 (increased to yield more recipes)
        limit = req_data.get("limit", 20)

        spoonacular_response = requests.get(SPOONACULAR_ENDPOINT, params={
            "apiKey": SPOONACULAR_API_KEY,
            "includeIngredients": ','.join(keywords),
            "number": limit,
            "addRecipeInformation": True
        })

        print("📡 Spoonacular response status:", spoonacular_response.status_code)
        spoonacular_data = spoonacular_response.json()
        print("📦 Raw Spoonacular data:", spoonacular_data)

        if "results" not in spoonacular_data or not spoonacular_data["results"]:
            print("⚠️ No results found for vibe, returning fallback")
            fallback_recipe = {
                "title": "Fallback Recipe",
                "image": "https://via.placeholder.com/312x231.png?text=No+Recipe",
                "sourceUrl": "https://example.com",
                "readyInMinutes": 0,
                "vibe": vibe,
                "score": 0
            }
            return jsonify([fallback_recipe])  # Return a list with one fallback recipe

        recipes = spoonacular_data["results"]

        # Compute a score for each recipe and add it to the recipe data.
        for recipe in recipes:
            computed_score = round(score_recipe(recipe, vibe) * 100)
            recipe["score"] = computed_score

        # Sort recipes in descending order by score.
        sorted_recipes = sorted(recipes, key=lambda r: r["score"], reverse=True)

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
