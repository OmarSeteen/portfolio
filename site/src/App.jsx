import cv from "../cv.json";

export default function App() {
  return (
    <main>
      <h1>{cv.profile.name.en}</h1>
    </main>
  );
}
