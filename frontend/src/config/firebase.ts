import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth } from "firebase/auth";
import { getFirestore } from "firebase/firestore";
import { getAnalytics, isSupported } from "firebase/analytics";

export const firebaseConfig = {
  apiKey: "AIzaSyBmEvAwhT2VHuaC-M8SFRevdLejJJTISEY",
  authDomain: "parasf-3b57b.firebaseapp.com",
  projectId: "parasf-3b57b",
  storageBucket: "parasf-3b57b.firebasestorage.app",
  messagingSenderId: "764690849093",
  appId: "1:764690849093:web:db6d7555ea42fba3b1322c",
  measurementId: "G-NW27MCWNJJ",
};

// Initialize Firebase once
export const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app);

// Initialize analytics if supported in current browser environment
export let analytics: ReturnType<typeof getAnalytics> | null = null;
if (typeof window !== "undefined") {
  isSupported().then((supported) => {
    if (supported) {
      analytics = getAnalytics(app);
    }
  });
}

