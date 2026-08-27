import { initializeApp, getApps, getApp } from "firebase/app";
import { getAuth, GoogleAuthProvider } from "firebase/auth";

// Public web config — safe to embed client-side, this is how every Firebase
// web app identifies itself to Firebase's backend (not a secret; access is
// governed by Identity Platform provider config + Firebase security rules,
// not by keeping this value hidden).
const firebaseConfig = {
  apiKey: "AIzaSyDH4W1vOgw_IG4Q-qCzmypC2l5Ym56PXBg",
  authDomain: "incident-resolver-agent.firebaseapp.com",
  projectId: "incident-resolver-agent",
  storageBucket: "incident-resolver-agent.firebasestorage.app",
  messagingSenderId: "722901486266",
  appId: "1:722901486266:web:0fd5c4bf270fe331f59083",
};

const app = getApps().length ? getApp() : initializeApp(firebaseConfig);

export const auth = getAuth(app);
export const googleProvider = new GoogleAuthProvider();
