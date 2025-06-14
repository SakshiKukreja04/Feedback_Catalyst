// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
import { getAuth } from "firebase/auth";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDL2LUw38d0P94itspyuj8v8ynXzbjM5ek",
  authDomain: "feedback-catalyst.firebaseapp.com",
  projectId: "feedback-catalyst",
  storageBucket: "feedback-catalyst.firebasestorage.app",
  messagingSenderId: "433584416719",
  appId: "1:433584416719:web:189ea23f20e45c40ea94ba",
  measurementId: "G-VS71MX8N8Q"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);

export const auth = getAuth(app);