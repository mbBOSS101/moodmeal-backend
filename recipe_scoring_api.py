from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

VERSION = "v2.1"  # or any identifier you like

# Securely fetch API key from environment variable
SPOONACULAR_API_KEY = os.environ.get("EXPO_PUBLIC_SPOONACULAR_API_KEY")
SPOONACULAR_ENDPOINT = 'https://api.spoonacular.com/recipes/complexSearch'

# Define keywords typically associated with each vibe
vibe_keywords = {
    "Cozy": ["cheese", "potato", "broth"],
    "Energetic": ["banana", "spinach", "protein"],
    "Excited": ["jalapeno", "bacon", "beef"],
    "Relaxed": ["pasta", "mushroom", "butter"],
    "Playful": ["chocolate", "sprinkles", "berries"],
    "Calm": ["ginger", "tea", "rice"],
    "Contemplative": ["tofu", "lentils", "eggplant"],
    "Thoughtful": ["zucchini", "noodles", "parmesan"],
    "Reflective": ["ramen", "soy", "curry"]
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
    keywords = vibe_keywords.get(vibe, [vibe])
    title = recipe.get('title', '').lower()
    keyword_matches = sum(1 for word in keywords if word.lower() in title)
    keyword_score = min(keyword_matches / len(keywords), 1.0)
    base_score += keyword_score * 0.3  # 30% weight

    # Factor 3: Popularity (using aggregateLikes)
    popularity = recipe.get('aggregateLikes', 0)
    popularity_score = min(popularity / 100.0, 1.0)  # Normalize assuming 100 likes is excellent
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

        keywords = vibe_keywords.get(vibe, [vibe])
        print("🧠 Spoonacular ingredients:", keywords)

        # Make request to Spoonacular API
        spoonacular_response = requests.get(SPOONACULAR_ENDPOINT, params={
            "apiKey": SPOONACULAR_API_KEY,
            "includeIngredients": ','.join(keywords),
            "number": 10,
            "addRecipeInformation": True
        })
        
        # Log status code and any potential error from Spoonacular
        print("📡 Spoonacular response status:", spoonacular_response.status_code)
        spoonacular_data = spoonacular_response.json()
        print("📦 Raw Spoonacular data:", spoonacular_data)

        if "results" not in spoonacular_data or not spoonacular_data["results"]:
            print("⚠️ No results found for vibe, returning fallback")
            return jsonify({
                "title": "Fallback Recipe",
                "image": "https://via.placeholder.com/312x231.png?text=No+Recipe",
                "sourceUrl": "https://example.com",
                "readyInMinutes": 0,
                "vibe": vibe,
                "score": 0
            })

        recipes = spoonacular_data["results"]
        best = max(recipes, key=lambda r: score_recipe(r, vibe))

        print("🏆 Best recipe selected:", best["title"])
        final_score = round(score_recipe(best, vibe) * 100)
        print("🔢 Final score sent to client:", final_score)

        return jsonify({
            "title": best.get("title"),
            "image": best.get("image"),
            "sourceUrl": best.get("sourceUrl"),
            "readyInMinutes": best.get("readyInMinutes"),
            "vibe": vibe,
            "score": final_score
        })

    except Exception as e:
        print("❌ Exception:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def hello():
    return f"✅ Flask is working! {VERSION}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
