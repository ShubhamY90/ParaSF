import React, { createContext, useEffect, useState } from "react";
import { onAuthStateChanged, User as FirebaseUser } from "firebase/auth";
import { doc, getDoc } from "firebase/firestore";
import { auth, db } from "../config/firebase";
import { authApi, UserOut, UserRole, RegisterPayload } from "../api/auth";
import { DEMO_ROLES } from "../config/constants";

interface AuthContextValue {
  user: UserOut | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<UserRole>;
  register: (data: RegisterPayload) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue>({} as AuthContextValue);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserOut | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Listen to Firebase Auth state
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser: FirebaseUser | null) => {
      if (firebaseUser) {
        try {
          const idToken = await firebaseUser.getIdToken();
          localStorage.setItem("pt_token", idToken);
          setToken(idToken);

          const demoRole = DEMO_ROLES[firebaseUser.email?.toLowerCase() || ""];
          let resolvedRole: UserRole = demoRole || "farmer";

          // Try Firestore — but fall back gracefully if DB not provisioned yet
          try {
            const userRef = doc(db, "users", firebaseUser.uid);
            const snap = await getDoc(userRef);

            if (snap.exists()) {
              const data = snap.data();
              resolvedRole = (data.role as UserRole) || demoRole || "farmer";
              setUser({
                id: firebaseUser.uid,
                email: firebaseUser.email || data.email,
                full_name: data.full_name || firebaseUser.displayName || null,
                role: resolvedRole,
                is_active: data.is_active !== undefined ? data.is_active : true,
                created_at: data.created_at ? data.created_at.toString() : undefined,
              });
            } else {
              setUser({
                id: firebaseUser.uid,
                email: firebaseUser.email || "",
                full_name: firebaseUser.displayName || null,
                role: demoRole || "farmer",
                is_active: true,
              });
            }
          } catch (firestoreErr: any) {
            // Firestore not provisioned yet — use Auth-only profile
            console.warn("Firestore unavailable, using Auth-only profile:", firestoreErr?.message);
            setUser({
              id: firebaseUser.uid,
              email: firebaseUser.email || "",
              full_name: firebaseUser.displayName || null,
              role: demoRole || "farmer",
              is_active: true,
            });
          }

          // Keep backend SQLite DB in sync
          if (firebaseUser.email) {
            fetch("/api/auth/sync", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                email: firebaseUser.email,
                role: resolvedRole,
                full_name: firebaseUser.displayName || null,
              }),
            }).catch(() => {});
          }
        } catch (err) {
          console.error("Auth state error:", err);
          setUser(null);
          setToken(null);
          localStorage.removeItem("pt_token");
        }
      } else {
        setUser(null);
        setToken(null);
        localStorage.removeItem("pt_token");
      }
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  async function login(email: string, password: string): Promise<UserRole> {
    const res = await authApi.login({ email, password });
    localStorage.setItem("pt_token", res.access_token);
    setToken(res.access_token);
    return res.role;
  }

  async function register(data: RegisterPayload) {
    await authApi.register(data);
  }

  async function logout() {
    await authApi.logout();
    localStorage.removeItem("pt_token");
    setToken(null);
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, token, loading, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}
