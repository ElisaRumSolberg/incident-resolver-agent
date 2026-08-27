"use client";

import {
  onAuthStateChanged,
  signInWithPopup,
  signOut as firebaseSignOut,
  type User,
} from "firebase/auth";
import { createContext, useContext, useEffect, useState, type ReactNode } from "react";
import { auth, googleProvider } from "./firebase";

const GUEST_STORAGE_KEY = "incident-resolver-guest";

interface AuthContextValue {
  user: User | null;
  loading: boolean;
  isGuest: boolean;
  signInWithGoogle: () => Promise<void>;
  continueAsGuest: () => void;
  signOut: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [isGuest, setIsGuest] = useState(() => {
    try {
      return sessionStorage.getItem(GUEST_STORAGE_KEY) === "1";
    } catch {
      // sessionStorage unavailable (private browsing etc.) — guest mode
      // just won't persist across reloads, not a functional blocker.
      return false;
    }
  });

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (u) => {
      setUser(u);
      setLoading(false);
    });
    return unsubscribe;
  }, []);

  async function signInWithGoogle() {
    await signInWithPopup(auth, googleProvider);
    setIsGuest(false);
    try {
      sessionStorage.removeItem(GUEST_STORAGE_KEY);
    } catch {
      // ignore
    }
  }

  function continueAsGuest() {
    setIsGuest(true);
    try {
      sessionStorage.setItem(GUEST_STORAGE_KEY, "1");
    } catch {
      // ignore — state still updates for this session
    }
  }

  async function signOut() {
    setIsGuest(false);
    try {
      sessionStorage.removeItem(GUEST_STORAGE_KEY);
    } catch {
      // ignore
    }
    await firebaseSignOut(auth);
  }

  return (
    <AuthContext.Provider value={{ user, loading, isGuest, signInWithGoogle, continueAsGuest, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
