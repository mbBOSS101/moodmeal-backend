import React, { useState, useEffect } from 'react';
import {
  SafeAreaView,
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ScrollView,
  Image,
  ActivityIndicator,
} from 'react-native';
import axios from 'axios';
import { getWeather } from './weather';

// Map weather conditions & moods to vibe
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

export default function App() {
  const [weather, setWeather] = useState(null);
  const [selectedMood, setSelectedMood] = useState(null);
  const [vibe, setVibe] = useState('');
  const [recipes, setRecipes] = useState([]); // Can store multiple recipes
  const [loading, setLoading] = useState(false);

  // Fetch current weather on mount
  useEffect(() => {
    const apiKey = process.env.EXPO_PUBLIC_OPENWEATHER_API_KEY;
    getWeather(apiKey).then((data) => {
      if (!data.error) {
        setWeather(data);
      }
    });
  }, []);

  const handleMoodPress = async (mood) => {
    setSelectedMood(mood);
    setRecipes([]); // Clear out old recipes
    setLoading(true);

    // Compute the vibe based on weather condition and mood emoji
    const condition = weather?.condition;
    const computedVibe = condition ? moodWeatherVibes[condition]?.[mood] : '';
    setVibe(computedVibe);

    const flaskURL = process.env.EXPO_PUBLIC_FLASK_URL;

    try {
      // Primary call: request more recipes (limit: 10) with randomization
      const response = await axios.post(
        `${flaskURL}/get_best_recipe`,
        { vibe: computedVibe, limit: 10, randomize: true },
        { headers: { 'Content-Type': 'application/json' } }
      );

      let fetchedRecipes = Array.isArray(response.data)
        ? response.data
        : [response.data];

      // If too few recipes are returned, perform a fallback query
      if (fetchedRecipes.length < 3) {
        const fallbackResponse = await axios.post(
          `${flaskURL}/get_best_recipe`,
          { vibe: 'Any', limit: 10, randomize: true },
          { headers: { 'Content-Type': 'application/json' } }
        );

        const fallbackRecipes = Array.isArray(fallbackResponse.data)
          ? fallbackResponse.data
          : [fallbackResponse.data];

        // Merge and remove duplicates based on title
        const merged = [...fetchedRecipes, ...fallbackRecipes];
        const uniqueRecipes = Array.from(
          new Map(merged.map((r) => [r.title, r])).values()
        );
        // Optionally, shuffle for more variety
        uniqueRecipes.sort(() => Math.random() - 0.5);
        fetchedRecipes = uniqueRecipes;
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
            {['🥳', '😌', '🤔'].map((mood) => (
              <TouchableOpacity key={mood} onPress={() => handleMoodPress(mood)}>
                <Text style={styles.emoji}>{mood}</Text>
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* LOADING INDICATOR */}
        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color="#2E7D32" />
            <Text style={styles.loadingText}>Fetching recipes...</Text>
          </View>
        )}

        {/* MOOD MATCHES HEADER */}
        {(!loading && vibe && recipes.length > 0) && (
          <View style={styles.moodMatchesRow}>
            <Text style={styles.moodMatchesTitle}>Your Mood Matches</Text>
            <Text style={styles.moodVibe}>{vibe} Vibe</Text>
          </View>
        )}

        {/* RECIPE CARDS */}
        {!loading &&
          recipes.length > 0 &&
          recipes.map((recipe, index) => {
            // Ensure recipe is a valid object with a title
            if (!recipe || typeof recipe !== 'object' || !recipe.title) return null;
            return (
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
            );
          })}

        {/* NO RECIPES FOUND */}
        {!loading && selectedMood && recipes.length === 0 && (
          <Text style={styles.noRecipesText}>
            Sorry, no recipes found. Please try again!
          </Text>
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

  /* LOADING */
  loadingContainer: { marginVertical: 20, alignItems: 'center' },
  loadingText: { marginTop: 8, fontSize: 16, color: '#2E7D32' },

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
