import React, { useState, useEffect, useRef } from 'react';
import {
  SafeAreaView,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  Animated,
  Easing,
} from 'react-native';
import axios from 'axios';
import { getWeather } from './weather';

const moodWeatherVibes = {
  Clear: {
    '🥳': 'Energetic',
    '😌': 'Calm',
    '🤔': 'Contemplative',
  },
  Clouds: {
    '🥳': 'Playful',
    '😌': 'Relaxed',
    '🤔': 'Thoughtful',
  },
  Rain: {
    '🥳': 'Excited',
    '😌': 'Cozy',
    '🤔': 'Reflective',
  },
};

// Custom animated loading component – a bowl with an ingredient falling in.
const LoadingBowl = () => {
  const ingredientAnim = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.loop(
      Animated.timing(ingredientAnim, {
        toValue: 1,
        duration: 1500,
        easing: Easing.linear,
        useNativeDriver: true,
      })
    ).start();
  }, [ingredientAnim]);

  const ingredientTranslateY = ingredientAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-50, 0], // ingredient falls from above the bowl to the bowl's top
  });
  const ingredientOpacity = ingredientAnim.interpolate({
    inputRange: [0, 0.3, 1],
    outputRange: [0, 1, 0.5],
  });

  return (
    <View style={styles.loadingBowlContainer}>
      {/* Rotate bowl 180° to display right side up */}
      <View style={[styles.bowl, { transform: [{ rotate: '180deg' }] }]}>
        {/* Rotate ingredient back 180° so it appears normal */}
        <Animated.View
          style={[
            styles.ingredient,
            {
              transform: [{ translateY: ingredientTranslateY }, { rotate: '180deg' }],
              opacity: ingredientOpacity,
            },
          ]}
        />
      </View>
      <Text style={styles.loadingText}>Loading recipes...</Text>
    </View>
  );
};

function App() {
  const [weather, setWeather] = useState(null);
  const [selectedMood, setSelectedMood] = useState(null);
  const [vibe, setVibe] = useState('');
  const [recipes, setRecipes] = useState([]); // Array of recipe objects
  const [loading, setLoading] = useState(false);

  // Fallback to localhost if the environment variable is missing
  const flaskURL = process.env.EXPO_PUBLIC_FLASK_URL || 'http://localhost:5000';

  // Fetch current weather on mount
  useEffect(() => {
    const apiKey = process.env.EXPO_PUBLIC_OPENWEATHER_API_KEY;
    getWeather(apiKey).then((data) => {
      if (!data.error) {
        setWeather(data);
      }
    });
  }, []);

  const handleMoodPress = async (moodEmoji) => {
    setSelectedMood(moodEmoji);
    setRecipes([]); // Clear previous recipes
    setLoading(true);

    // Compute vibe from weather condition and selected emoji.
    const condition = weather?.condition;
    const computedVibe = condition ? moodWeatherVibes[condition]?.[moodEmoji] : '';
    setVibe(computedVibe);

    // Normalize flaskURL and set the endpoint
    const endpoint = `${flaskURL.replace(/\/$/, '')}/get_best_recipe`;
    console.log('Calling Flask endpoint:', endpoint);

    try {
      const response = await axios.post(
        endpoint,
        { vibe: computedVibe, limit: 20, randomize: true },
        { headers: { 'Content-Type': 'application/json' } }
      );

      console.log('Response data:', response.data);

      let fetchedRecipes = Array.isArray(response.data)
        ? response.data
        : [response.data];

      if (!fetchedRecipes || fetchedRecipes.length === 0) {
        console.warn('No recipes returned from the backend.');
      }

      // Sort recipes in descending order by their score (use 0 as fallback)
      fetchedRecipes.sort((a, b) => (b.score || 0) - (a.score || 0));

      // If there are more than 5, slice the array to display only the top 5 recipes.
      if (fetchedRecipes.length > 5) {
        fetchedRecipes = fetchedRecipes.slice(0, 5);
      }

      setRecipes(fetchedRecipes);
    } catch (error) {
      console.error('Error fetching recipes:', error);
      setRecipes([]);
    }
    setLoading(false);
  };

  return (
    <SafeAreaView style={styles.safeArea}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.contentContainer}>
        {/* TOP BAR */}
        <View style={styles.topBar}>
          <Text style={styles.moodMealTitle}>MoodMeal</Text>
        </View>

        {/* WEATHER CARD */}
        <View style={styles.weatherCard}>
          <Text style={styles.weatherLabel}>Current Weather</Text>
          {weather && !weather.error ? (
            <View style={styles.weatherRow}>
              <Text style={styles.weatherIcon}>☁️</Text>
              <Text style={styles.weatherText}>
                {weather.condition}, {Math.round(weather.temperature)}°C
              </Text>
              <Text style={styles.locationPin}>📍</Text>
            </View>
          ) : (
            <Text style={styles.weatherText}>Loading weather...</Text>
          )}
        </View>

        {/* MOOD CARD */}
        <View style={styles.moodCard}>
          <Text style={styles.moodPrompt}>How are you feeling today?</Text>
          <View style={styles.emojiRow}>
            {['🥳', '😌', '🤔'].map((moodEmoji) => (
              <TouchableOpacity key={moodEmoji} onPress={() => handleMoodPress(moodEmoji)}>
                <Text style={styles.emoji}>{moodEmoji}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* LOADING INDICATOR */}
        {loading && <LoadingBowl />}

        {/* MOOD MATCHES HEADER */}
        {!loading && vibe && recipes.length > 0 && (
          <View style={styles.moodMatchesRow}>
            <Text style={styles.moodMatchesTitle}>Your Mood Matches</Text>
            <Text style={styles.moodVibe}>{vibe} Vibe</Text>
          </View>
        )}

        {/* RECIPE CARDS */}
        {!loading &&
          recipes.length > 0 &&
          recipes.map((recipe, index) => (
            <View key={index} style={styles.recipeCard}>
              <View style={styles.imageContainer}>
                <Image source={{ uri: recipe.image }} style={styles.recipeImage} />
                {'score' in recipe && (
                  <View style={styles.scoreBadge}>
                    <Text style={styles.scoreBadgeText}>Score: {recipe.score}</Text>
                  </View>
                )}
              </View>
              <View style={styles.recipeDetails}>
                <View>
                  <Text style={styles.recipeTitle}>{recipe.title}</Text>
                  {recipe.readyInMinutes && (
                    <Text style={styles.recipeTime}>{recipe.readyInMinutes} mins</Text>
                  )}
                </View>
                <Text style={styles.arrow}>›</Text>
              </View>
            </View>
          ))}

        {/* NO RECIPES FOUND */}
        {!loading && selectedMood && recipes.length === 0 && (
          <Text style={styles.noRecipesText}>Sorry, no recipes found. Please try again!</Text>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#F8F8F8' },
  scrollView: { flex: 1 },
  contentContainer: { paddingHorizontal: 16, paddingVertical: 16 },

  /* TOP BAR */
  topBar: {
    marginBottom: 8,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  moodMealTitle: { fontSize: 24, fontWeight: 'bold', color: '#2E7D32' },

  /* WEATHER CARD */
  weatherCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  weatherLabel: { fontSize: 14, color: '#888', marginBottom: 4 },
  weatherRow: { flexDirection: 'row', alignItems: 'center' },
  weatherIcon: { fontSize: 24, marginRight: 6 },
  weatherText: { fontSize: 16, fontWeight: '600', color: '#333' },
  locationPin: { marginLeft: 'auto', fontSize: 20 },

  /* MOOD CARD */
  moodCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  moodPrompt: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 12 },
  emojiRow: { flexDirection: 'row', justifyContent: 'space-around' },
  emoji: { fontSize: 32 },

  /* LOADING BOWL */
  loadingBowlContainer: { alignItems: 'center', justifyContent: 'center', marginVertical: 20 },
  bowl: {
    width: 100,
    height: 50,
    backgroundColor: '#2E7D32',
    borderTopLeftRadius: 50,
    borderTopRightRadius: 50,
    borderBottomLeftRadius: 10,
    borderBottomRightRadius: 10,
    overflow: 'hidden',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  ingredient: { width: 15, height: 15, backgroundColor: '#FFD700', borderRadius: 7.5, marginBottom: 10 },
  loadingText: { marginTop: 10, fontSize: 16, color: '#2E7D32' },

  /* MOOD MATCHES HEADER */
  moodMatchesRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
    marginTop: 8,
  },
  moodMatchesTitle: { fontSize: 18, fontWeight: '600', color: '#333' },
  moodVibe: { fontSize: 16, color: '#6D5BD0', fontWeight: '500' },

  /* RECIPE CARD */
  recipeCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 4,
    shadowOffset: { width: 0, height: 2 },
    elevation: 1,
  },
  imageContainer: {
    position: 'relative',
    width: '100%',
    height: 180,
    borderTopLeftRadius: 12,
    borderTopRightRadius: 12,
    overflow: 'hidden',
  },
  recipeImage: { width: '100%', height: '100%' },
  scoreBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: '#2E7D32',
    borderRadius: 16,
    paddingVertical: 4,
    paddingHorizontal: 8,
  },
  scoreBadgeText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  recipeDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 12,
  },
  recipeTitle: { fontSize: 16, fontWeight: '600', color: '#333', marginBottom: 4 },
  recipeTime: { fontSize: 14, color: '#777' },
  arrow: { fontSize: 24, color: '#ccc', marginLeft: 8 },

  /* NO RECIPES */
  noRecipesText: { fontSize: 16, color: 'red', marginTop: 20, textAlign: 'center' },
});

export default App;
