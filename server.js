
const express = require("express");
const fetch = require("node-fetch");

const app = express();
const PORT = process.env.PORT || 3000;
const TOKEN = "8GJT1XC-CYE4GYE-QKMF2Q9-40TDN1E"; // твой токен

app.get("/api/random-actor", async (req, res) => {
  try {
    const actorRes = await fetch(
      "https://openmovieapi.dev/api/v1/person/popular?language=ru",
      {
        headers: { Authorization: `Bearer ${TOKEN}` },
      }
    );

    const actorData = await actorRes.json();
    const person = actorData.results[Math.floor(Math.random() * actorData.results.length)];

    const creditsRes = await fetch(
      `https://openmovieapi.dev/api/v1/person/${person.id}/movie_credits?language=ru`,
      {
        headers: { Authorization: `Bearer ${TOKEN}` },
      }
    );

    const creditsData = await creditsRes.json();
    const works = creditsData.cast.map((w) => w.title).filter(Boolean);

    res.json({
      actor: person.name,
      works: works.slice(0, 10),
    });
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: "Произошла ошибка" });
  }
});

app.listen(PORT, () => {
  console.log(`Сервер работает на порту ${PORT}`);
});
