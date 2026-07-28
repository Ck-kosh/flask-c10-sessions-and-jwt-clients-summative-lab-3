import React, { useEffect, useState } from "react";
import NavBar from "./NavBar";
import Login from "../pages/Login";

function App() {
  const [user, setUser] = useState(null);

  useEffect(() => {
    const token = localStorage.getItem("token");
    if (!token) return;

    fetch("/check_session", {
      credentials: "include",
      headers: {
        Authorization: `Bearer ${token}`
      }
    }).then((r) => {
      if (r.ok) {
        r.json().then((user) => setUser(user));
      } else {
        localStorage.removeItem("token");
      }
    });
  }, []);

  const onLogin = (payload) => {
    const user = payload?.user ?? payload;
    const token = payload?.token;

    if (token) {
      localStorage.setItem("token", token);
    }

    setUser(user || null);
  }

  if (!user) return <Login onLogin={onLogin} />;

  return (
    <>
      <NavBar setUser={setUser} />
      <main>
        <p>You are logged in!</p>
      </main>
    </>
  );
}

export default App;
