import { useEffect, useState } from "react";

function App() {
  const [message, setMessage] = useState("Loading...");

  useEffect(() => {
    fetch("http://localhost:8000/")
    .then((res) => res.json())
    .then((data) => setMessage(data.message))
    .catch((err) => setMessage("Error: " + err.message));
  }, []);

  return (
    <div style={{ textAlign: "center", marginTop: "50px" }}>
    <h1>FastAPI + React</h1>
    <p>Backend says: {message}</p>
    </div>
  );
}

export default App;
