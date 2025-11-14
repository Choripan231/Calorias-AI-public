
import React, { useState, useEffect } from 'react';
import { StyleSheet, Text, View, Button, ScrollView } from 'react-native';
import axios from 'axios';
import { StatusBar } from 'expo-status-bar';

export default function App() {
  const [profile, setProfile] = useState({tdee:2000});
  const [macros, setMacros] = useState({protein_g:0, carbs_g:0, fat_g:0});
  const [consumed, setConsumed] = useState(0);

  const API_URL = 'http://10.0.2.2:8000'; // Cambia a IP de tu backend

  const refresh = async () => {
    try {
      const resProfile = await axios.get(API_URL+'/profile/demo');
      setProfile(resProfile.data.user ? resProfile.data.user : {tdee:2000});
      const resMacro = await axios.post(API_URL+'/macro-plan', null, { params:{user_id:'demo'}});
      setMacros(resMacro.data);
      const resMeals = await axios.get(API_URL+'/daily-summary/demo').catch(()=>({data:{total_kcal:0}}));
      setConsumed(resMeals.data.total_kcal || 0);
    } catch(e){
      console.log('No se pudo conectar con backend', e);
    }
  }

  useEffect(()=>{refresh()},[]);

  return (
    <ScrollView style={styles.container}>
      <StatusBar style="light" />
      <Text style={styles.title}>Calorias AI</Text>
      <Text style={styles.text}>Consumidas: {consumed} kcal</Text>
      <Text style={styles.text}>Objetivo: {Math.round(profile.tdee)} kcal</Text>
      <Text style={styles.text}>Proteína: {macros.protein_g} g</Text>
      <Text style={styles.text}>Carbohidratos: {macros.carbs_g} g</Text>
      <Text style={styles.text}>Grasas: {macros.fat_g} g</Text>
      <View style={{marginTop:20}}>
        <Button title="Actualizar" color="#ff2d55" onPress={refresh}/>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container:{flex:1,backgroundColor:'#000',padding:20},
  title:{fontSize:28,fontWeight:'bold',color:'#ff2d55',marginBottom:12},
  text:{fontSize:18,color:'#ff2d55',marginBottom:8}
});
