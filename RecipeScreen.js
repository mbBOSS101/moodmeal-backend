import React from 'react';
import { View, Text, Image, StyleSheet, ScrollView, Linking, TouchableOpacity } from 'react-native';

export default function RecipeScreen({ route }) {
  const { recipe, vibe } = route.params;

  console.log("🧾 RecipeScreen received:", recipe); // Debug log

  if (!recipe || !recipe.title) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>Sorry, no recipe found. Please try again!</Text>
      </View>
    );
  }

  return (
    <ScrollView contentContainerStyle={styles.container}>
      <Text style={styles.vibe}>Mood Vibe: {vibe}</Text>
      <Text style={styles.title}>{recipe.title}</Text>
      <Image source={{ uri: recipe.image }} style={styles.image} />

      {recipe.readyInMinutes && (
        <Text style={styles.time}>⏱️ Ready in: {recipe.readyInMinutes} minutes</Text>
      )}

      {/* Always try to show score, even if 0 */}
      {'score' in recipe && (
        <Text style={styles.score}>⭐ Score: {recipe.score} / 100</Text>
      )}

      {recipe.sourceUrl && (
        <TouchableOpacity onPress={() => Linking.openURL(recipe.sourceUrl)}>
          <Text style={styles.link}>View Full Recipe 🔗</Text>
        </TouchableOpacity>
      )}
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flexGrow: 1,
    backgroundColor: '#E8F5E9',
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'center',
    marginVertical: 12,
    color: '#2E7D32',
  },
  image: {
    width: 260,
    height: 180,
    borderRadius: 12,
    marginBottom: 12,
  },
  vibe: {
    fontSize: 18,
    color: '#4CAF50',
    marginBottom: 8,
  },
  time: {
    fontSize: 16,
    color: '#555',
    marginBottom: 8,
  },
  score: {
    fontSize: 16,
    color: '#388E3C',
    marginBottom: 10,
  },
  link: {
    marginTop: 10,
    fontSize: 16,
    color: '#1E88E5',
    textDecorationLine: 'underline',
  },
  error: {
    fontSize: 18,
    color: 'red',
    textAlign: 'center',
    padding: 20,
  },
});
