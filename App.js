// App.js
import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { getWeather } from './weather';
import axios from 'axios';
import RecipeScreen from './RecipeScreen';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';

const Stack = createNativeStackNavigator();

const moodWeatherVibes = {
  "Clear": {
    "🥳": "Energetic",
    "😌": "Calm",
    "🤔": "Contemplative",
  },
  "Clouds": {
    "🥳": "Playful",
    "😌": "Relaxed",
    "🤔": "Thoughtful",
  },
  "Rain": {
    "🥳": "Excited",
    "😌": "Cozy",
    "🤔": "Reflective",
  }
};

const vibeKeywords = {
  "Cozy": ["stew", "soup", "mac and cheese"],
  "Energetic": ["smoothie", "salad", "protein bowl"],
  "Excited": ["burger", "pizza", "nachos"],
  "Relaxed": ["pasta", "risotto", "grilled cheese"],
  "Playful": ["tacos", "cupcakes", "skewers"],
  "Calm": ["tea", "rice bowl", "miso soup"],
  "Contemplative": ["chickpea stew", "lentil soup", "tofu stir fry"],
  "Thoughtful": ["noodle bowl", "quiche", "baked potato"],
  "Reflective": ["ramen", "dumplings", "curry"]
};

const getTemperatureMood = (temperature) => {
  if (temperature < 5) return "Cold";
  if (temperature < 10) return "Chilly";
  if (temperature < 15) return "Cool";
  if (temperature < 20) return "Mild";
  if (temperature < 25) return "Warm";
  if (temperature < 30) return "Hot";
  return "Very Hot";
};

function HomeScreen({ navigation }) {
  const [selectedMood, setSelectedMood] = useState(null);
  const [weather, setWeather] = useState(null);

  useEffect(() => {
    getWeather('89cea4a1a1488bef89b6bc52aa155980').then((data) => {
      setWeather(data);
    });
  }, []);

  const handleMoodPress = async (mood) => {
    setSelectedMood(mood);
    const condition = weather?.condition;
    const vibe = condition ? moodWeatherVibes[condition]?.[mood] : null;

    try {
      const response = await axios.post(
        'http://192.168.86.23:5050/get_best_recipe',
        { vibe: vibe },
        { headers: { 'Content-Type': 'application/json' } }
      );

      const recipe = response.data;
      navigation.navigate('Recipe', {
        mood,
        weather,
        vibe,
        recipe,
      });
    } catch (error) {
      console.error("❌ Error fetching recipe from Flask:", error);
      navigation.navigate('Recipe', {
        mood,
        weather,
        vibe,
        recipe: null,
      });
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.logo}>🥗 MoodMeal</Text>
      <Text style={styles.slogan}>A recipe for how you feel today</Text>
      <Text style={styles.prompt}>How are you feeling?</Text>
      <View style={styles.emojiRow}>
        {['🥳', '😌', '🤔'].map((mood) => (
          <TouchableOpacity key={mood} onPress={() => handleMoodPress(mood)}>
            <Text style={styles.emoji}>{mood}</Text>
          </TouchableOpacity>
        ))}
      </View>
    </View>
  );
}

export default function App() {
  return (
    <NavigationContainer>
      <Stack.Navigator>
        <Stack.Screen name="MoodMeal" component={HomeScreen} />
        <Stack.Screen name="Recipe" component={RecipeScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 24,
  },
  logo: {
    fontSize: 36,
    fontWeight: 'bold',
    color: '#2E7D32',
    marginBottom: 8,
  },
  slogan: {
    fontSize: 18,
    color: '#4CAF50',
    textAlign: 'center',
    marginBottom: 30,
  },
  prompt: {
    fontSize: 20,
    fontWeight: '600',
    color: '#2E7D32',
    marginBottom: 20,
  },
  emojiRow: {
    flexDirection: 'row',
    justifyContent: 'center',
  },
  emoji: {
    fontSize: 40,
    margin: 10,
  },
});