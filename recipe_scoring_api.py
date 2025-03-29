from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

SPOONACULAR_API_KEY = '081451a81bd948eea9e24d7e94a5fade'
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
    score = 0
    ready_in = recipe.get('readyInMinutes', 60)
    score += max(0, (60 - ready_in) / 60) * 0.4
    keywords = vibe_keywords.get(vibe, [])
    title = recipe.get('title', '').lower()
    keyword_matches = sum(1 for word in keywords if word in title)
    score += min(keyword_matches / len(keywords), 1.0) * 0.6
    return score

@app.route('/get_best_recipe', methods=['POST'])
def get_best_recipe():
    try:
        data = request.json
        print("✅ Request received:", data)

        if not data or "vibe" not in data:
            print("❌ Invalid data:", data)
            return jsonify({"error": "Missing 'vibe' in request"}), 400

        vibe = data["vibe"]
        print("🔍 Vibe is:", vibe)

        keywords = vibe_keywords.get(vibe, [vibe])
        print("🧠 Spoonacular ingredients:", keywords)

        response = requests.get(SPOONACULAR_ENDPOINT, params={
            "apiKey": SPOONACULAR_API_KEY,
            "includeIngredients": ','.join(keywords),
            "number": 10,
            "addRecipeInformation": True
        })

        data = response.json()
        print("📦 Raw Spoonacular data:", data)

        if "results" not in data or not data["results"]:
            return jsonify({"error": "No recipes found for that vibe."})

        recipes = data["results"]
        best = max(recipes, key=lambda r: score_recipe(r, vibe))

        print("🏆 Best recipe selected:", best["title"])

        return jsonify({
            "title": best.get("title"),
            "image": best.get("image"),
            "sourceUrl": best.get("sourceUrl"),
            "readyInMinutes": best.get("readyInMinutes"),
            "vibe": vibe
        })

    except Exception as e:
        print("❌ Exception:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def hello():
    return "✅ Flask is working!"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
