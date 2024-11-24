from fastapi import FastAPI
from pydantic import BaseModel
import requests
import pandas as pd
import os
import logging
from fastapi.staticfiles import StaticFiles

app = FastAPI()

assets_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "app", "assets")

# Mount the StaticFiles directory
app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")


# Chemin vers le fichier CSV
CSV_PATH = "games.csv"

# Chemin vers l'image par défaut (logo)
DEFAULT_IMAGE_URL = "assets/logo.png"  # Ajustez le chemin selon votre structure

# Charger les données du CSV avec les noms de colonnes en français
# Assurez-vous que la colonne contenant les URLs des images est bien nommée, par exemple 'image_url'
# Si ce n'est pas le cas, ajustez le nom de la colonne dans le code ci-dessous
games_data = pd.read_csv(CSV_PATH).set_index('Nom du Jeu').to_dict('index')

# Définir les modèles pour les messages
class Message(BaseModel):
    role: str
    content: str

class ChatHistory(BaseModel):
    messages: list[Message]

# Fonction pour détecter les jeux dans la réponse
def detect_recommended_games(response_text, games_data, default_image_url):
    """Détecte les jeux mentionnés dans la réponse et retourne leurs données."""
    recommended_games = []
    for game_name, game_info in games_data.items():
        if game_name.lower() in response_text.lower():
            image_url = game_info.get("image_url", default_image_url)  # Assurez-vous que la colonne existe
            print(game_name, image_url)
            if not image_url or pd.isna(image_url):
                image_url = default_image_url
            recommended_games.append({
                "name": game_name,
                "image_url": image_url
            })
    # Limiter à 3 jeux recommandés
    return recommended_games[:3]

@app.post("/chat")
def chat_with_agent(history: ChatHistory):
    # Remplacez "YOUR_API_KEY" et "YOUR_AGENT_ID" par vos propres informations ou utilisez des variables d'environnement
    API_KEY = "nBniSjFv7mvvR1zBMqb8kk942VgENXDU"  # Utiliser une variable d'environnement pour la clé
    AGENT_ID = "ag:08f22d9e:20241124:test:b58d979f"  # Utiliser une variable d'environnement pour l'ID de l'agent
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    payload = {
        "agent_id": AGENT_ID,
        "messages": [{"role": msg.role, "content": msg.content} for msg in history.messages],
    }

    try:
        response = requests.post(
            "https://api.mistral.ai/v1/agents/completions",
            json=payload,
            headers=headers,
            timeout=40,
            verify=False
        )
        response.raise_for_status()

        response_data = response.json()
        model_response = response_data.get("choices", [{}])[0].get("message", {}).get("content", "")

        # Utiliser la détection des jeux
        recommended_games = detect_recommended_games(model_response, games_data, DEFAULT_IMAGE_URL)

        return {
            "response": model_response,
            "recommended_games": recommended_games
        }

    except requests.exceptions.RequestException as e:
        logging.error(f"Erreur réseau : {e}")
        return {"error": f"Erreur réseau : {e}"}
    except Exception as e:
        logging.error(f"Erreur inattendue : {e}")
        return {"error": f"Erreur inattendue : {e}"}

if __name__ == "__main__":
    import uvicorn

    # Lancer le serveur FastAPI
    uvicorn.run(app, host="127.0.0.1", port=8000)

print('hello')