import React from 'react';
import { View, Text, Image, StyleSheet, FlatList, TouchableOpacity, Linking } from 'react-native';

export default function RecipeListScreen({ route }) {
  const { recipes, vibe } = route.params;

  if (!recipes || recipes.length === 0) {
    return (
      <View style={styles.container}>
        <Text style={styles.error}>Sorry, no recipes found. Please try again!</Text>
      </View>
    );
  }

  const renderItem = ({ item }) => (
    <View style={styles.card}>
      <Image source={{ uri: item.image }} style={styles.image} />
      <View style={styles.infoContainer}>
        <Text style={styles.title}>{item.title}</Text>
        <Text style={styles.details}>Ready in: {item.readyInMinutes} mins</Text>
        <Text style={styles.details}>Score: {item.score} / 100</Text>
        <TouchableOpacity onPress={() => Linking.openURL(item.sourceUrl)}>
          <Text style={styles.link}>View Full Recipe</Text>
        </TouchableOpacity>
      </View>
    </View>
  );

  return (
    <FlatList
      data={recipes}
      keyExtractor={(item, index) => index.toString()}
      renderItem={renderItem}
      contentContainerStyle={styles.listContainer}
    />
  );
}

const styles = StyleSheet.create({
  listContainer: {
    padding: 16,
    backgroundColor: '#E8F5E9',
  },
  card: {
    backgroundColor: '#fff',
    borderRadius: 8,
    overflow: 'hidden',
    marginBottom: 16,
    flexDirection: 'row',
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  image: {
    width: 100,
    height: 100,
  },
  infoContainer: {
    flex: 1,
    padding: 8,
  },
  title: {
    fontSize: 16,
    fontWeight: 'bold',
    marginBottom: 4,
  },
  details: {
    fontSize: 14,
    marginBottom: 2,
  },
  link: {
    marginTop: 4,
    fontSize: 14,
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
