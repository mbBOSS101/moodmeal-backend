// weather.js
import * as Location from 'expo-location';

export async function getWeather(apiKey) {
  const { status } = await Location.requestForegroundPermissionsAsync();

  if (status !== 'granted') {
    console.log("Location permission denied");
    return { error: 'Permission denied' };
  }

  const location = await Location.getCurrentPositionAsync({});
  const { latitude, longitude } = location.coords;

  console.log("📍 Location Coordinates:", latitude, longitude);

  const response = await fetch(
    `https://api.openweathermap.org/data/2.5/weather?lat=${latitude}&lon=${longitude}&units=metric&appid=${apiKey}`
  );

  const data = await response.json();
  console.log("☁️ Raw weather data:", data);

  if (data.cod !== 200) {
    console.log("⚠️ Error fetching weather:", data.message);
    return { error: data.message };
  }

  return {
    temperature: data.main.temp,
    condition: data.weather[0].main,
  };
}
