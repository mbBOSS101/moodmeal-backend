from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

VERSION = "v4.2"  # Updated version identifier

# Securely fetch API key from environment variable
SPOONACULAR_API_KEY = os.environ.get("EXPO_PUBLIC_SPOONACULAR_API_KEY")
# Endpoints
SPOONACULAR_SEARCH_ENDPOINT = 'https://api.spoonacular.com/recipes/complexSearch'
SPOONACULAR_RANDOM_ENDPOINT = 'https://api.spoonacular.com/recipes/random'

# Expanded set of keywords per vibe to yield more recipe results.
vibe_keywords = {
    "Cozy": [
        "stew", "soup", "roast", "casserole", "potpie", "gravy", 
        "chili", "bisque", "gumbo", "porridge", "braise", "hotpot", 
        "broth", "comfort", "warmth", "hearty", "homey", "snug", 
        "cuddle", "simmer", "frittata", "bake", "mac", "cheddar", 
        "mash", "risotto", "saucy", "stewpot", "sourdough", "crust"
    ],
    "Energetic": [
        "smoothie", "salad", "oats", "wrap", "bowl", "juice", 
        "granola", "protein", "bar", "shake", "muesli", "cereal", 
        "fruit", "yogurt", "energize", "vitamin", "zest", "spark", 
        "pep", "boost", "quinoa", "pulse", "berry", "snack", "fizz", 
        "juicebox", "sprout", "mealprep", "active", "pulses", "grain"
    ],
    "Excited": [
        "tacos", "ribs", "wings", "chili", "curry", "salsa", 
        "burger", "steak", "nacho", "burrito", "hotdog", "sriracha", 
        "kimchi", "jerky", "spice", "fiery", "dynamic", "zippy", 
        "vivid", "intense", "electric", "fajita", "sizzler", "pepper", 
        "barbecue", "sizzle", "flame", "zing", "kick", "zestful"
    ],
    "Relaxed": [
        "pasta", "risotto", "noodles", "soup", "stew", "pizza", 
        "salad", "casserole", "pie", "bake", "grill", "roast", 
        "sandwich", "omelette", "quiche", "comfort", "slowcook", 
        "smooth", "mellow", "lounge", "medley", "frittata", "lasagna", 
        "curry", "bowl", "wrap", "dip", "simmer", "sauce", "mash"
    ],
    "Playful": [
        "tapas", "slider", "snack", "bites", "sushi", "dumpling", 
        "cookie", "cupcake", "muffin", "popsicle", "chips", "popcorn", 
        "nugget", "kebab", "samosa", "finger", "fritter", "mini", 
        "tater", "roll", "scoop", "dip", "bite", "puff", "truffle", 
        "tart", "scone", "bento", "sushiroll", "puffin"
    ],
    "Calm": [
        "salad", "soup", "bowl", "sushi", "poke", "plate", 
        "risotto", "pasta", "smoothie", "quinoa", "curry", "stew", 
        "broth", "chowder", "grill", "chilled", "mint", "herb", 
        "vegan", "light", "zest", "lemon", "detox", "calm", "zen", 
        "medley", "fresco", "garden", "rosemary", "sauce"
    ],
    "Contemplative": [
        "tofu", "lentils", "grains", "stirfry", "burger", "bowl", 
        "medley", "porridge", "risotto", "salad", "soup", "curry", 
        "stew", "wrap", "quinoa", "mushroom", "beans", "peas", 
        "barley", "rice", "oats", "polenta", "dhal", "pottage", 
        "millet", "couscous", "tabbouleh", "pilaf", "mash", "pulse"
    ],
    "Thoughtful": [
        "pizza", "salad", "roast", "risotto", "soup", "artisan", 
        "curry", "tart", "quiche", "bagel", "pasta", "bake", "stew", 
        "sushi", "wrap", "grill", "panini", "focaccia", "gnocchi", 
        "pesto", "sauce", "biscotti", "scone", "frittata", "bruschetta", 
        "croissant", "muffin", "sourdough", "granola", "pudding"
    ],
    "Reflective": [
        "stew", "braise", "simmer", "sauce", "casserole", "soup", 
        "roast", "grill", "bake", "potpie", "hotpot", "chili", 
        "curry", "risotto", "gumbo", "stewpot", "brew", "ragu", 
        "gravy", "pottage", "pasta", "starch", "dumpling", "pilaf", 
        "braised", "stewed", "simmered", "confit", "roasted", "saucepot"
    ]
}

def score_recipe(recipe, vibe, alpha=0.5, boost_vibe=1.2):
    """
    Compute a composite score for a recipe relative to the user's mood.
    If a recipe is tagged as vibe-specific, its computed score is multiplied by boost_vibe.
    
    We use:
      - Ready Time: 30%
      - Keyword Relevance: 30% (with smoothing)
      - Popularity: 20%
      - Spoonacular Score: 10%
      - Health Score: 10%
    """
    base_score = 0.0

    # Factor 1: Ready Time Score (30% weight)
    ready_in = recipe.get('readyInMinutes', 60)
    if ready_in <= 30:
        ready_time_score = 1.0
    elif ready_in >= 90:
        ready_time_score = 0.0
    else:
        ready_time_score = (90 - ready_in) / 60.0
    base_score += ready_time_score * 0.3

    # Factor 2: Keyword Relevance Score (30% weight with smoothing)
    keywords = vibe_keywords.get(vibe, [vibe])
    title = recipe.get('title', '').lower()
    # Count occurrences of each keyword in the title.
    keyword_matches = sum(title.count(word.lower()) for word in keywords)
    keyword_score = (keyword_matches + alpha) / (len(keywords) + alpha)
    base_score += keyword_score * 0.3

    # Factor 3: Popularity (20% weight)
    popularity = recipe.get('aggregateLikes', 0)
    popularity_score = min(popularity / 100.0, 1.0)
    base_score += popularity_score * 0.2

    # Factor 4: Spoonacular Score (10% weight)
    spoonacular_score = recipe.get('spoonacularScore', 0) / 100.0
    base_score += spoonacular_score * 0.1

    # Factor 5: Health Score (10% weight)
    health_score = recipe.get('healthScore', 0) / 100.0
    base_score += health_score * 0.1

    # If the recipe came from the vibe-specific query, boost its score.
    if recipe.get("source") == "vibe":
        base_score *= boost_vibe

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

        # Use expanded keywords for the given vibe.
        keywords = vibe_keywords.get(vibe, [vibe])
        print("🧠 Using keywords:", keywords)

        limit = req_data.get("limit", 20)

        # Query 1: Vibe-specific query using keywords.
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
        # Tag these recipes with source "vibe".
        for r in results1:
            r["source"] = "vibe"

        # If we have at least 5 vibe-specific recipes, use them exclusively.
        if len(results1) >= 5:
            merged_results = results1
        else:
            # Otherwise, merge with generic results.
            params2 = {
                "apiKey": SPOONACULAR_API_KEY,
                "number": limit,
                "addRecipeInformation": True
            }
            response2 = requests.get(SPOONACULAR_SEARCH_ENDPOINT, params=params2)
            data2 = response2.json()
            results2 = data2.get("results", [])
            print("📦 Generic results:", len(results2))
            # Tag generic recipes with source "generic".
            for r in results2:
                r["source"] = "generic"
            merged_results = results1 + results2

        # Deduplicate based on unique property (recipe 'id' or title).
        unique_dict = {}
        for recipe in merged_results:
            key = recipe.get("id") or recipe.get("title")
            if key:
                unique_dict[key] = recipe
        unique_recipes = list(unique_dict.values())

        # Fallback: If no recipes found, fetch random recipes.
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

        # Score each recipe using the improved ranking algorithm.
        for recipe in unique_recipes:
            computed_score = round(score_recipe(recipe, vibe) * 100)
            recipe["score"] = computed_score
            recipe["mood"] = vibe  # Attach the mood for personalization.

        # Sort recipes by score in descending order.
        sorted_recipes = sorted(unique_recipes, key=lambda r: r.get("score", 0), reverse=True)
        print("🏆 Returning", len(sorted_recipes), "recipes for vibe", vibe)

        # Return only the top 5 recipes.
        top_recipes = sorted_recipes[:5]
        return jsonify(top_recipes)
    except Exception as e:
        print("❌ Exception:", str(e))
        return jsonify({"error": str(e)}), 500

@app.route('/', methods=['GET'])
def hello():
    return f"✅ Flask is working! {VERSION}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5050)
