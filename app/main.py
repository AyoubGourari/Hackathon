import gradio as gr
import requests
import os

# Chemin vers l'image par défaut (logo)
DEFAULT_IMAGE_PATH = "assets/dishonored.jpg"  # Ajustez le chemin selon votre structure

# Fonction pour interagir avec le backend
def chat_with_agent(user_message, history):
    API_URL = "http://localhost:8000/chat"
    if not user_message.strip():
        return history, "Veuillez entrer un message.", [DEFAULT_IMAGE_PATH]*3

    # Ajouter le message utilisateur à l'historique
    history.append({"role": "user", "content": user_message})

    try:
        response = requests.post(
            API_URL,
            json={"messages": history},
            timeout=40  # Timeout de 10 secondes
        )

        if response.status_code == 200:
            resp_json = response.json()
            if "response" in resp_json:
                bot_reply = resp_json["response"]
                recommended_games = resp_json.get("recommended_games", [])
                print('these are the rec games')
                print(recommended_games)
                # Récupérer les images des jeux recommandés (jusqu'à 3)
                images = []
                for game in recommended_games:
                    if (game['image_url']):
                        image_url = '/assets/'+game['image_url']
                    else:
                        image_url = DEFAULT_IMAGE_PATH
                    images.append(image_url)
                # Compléter avec l'image par défaut si moins de 3 jeux
                while len(images) < 3:
                    images.append(DEFAULT_IMAGE_PATH)
                history.append({"role": "assistant", "content": bot_reply})
                return history, bot_reply, images
            elif "error" in resp_json:
                bot_reply = f"Erreur du serveur : {resp_json['error']}"
                history.append({"role": "assistant", "content": bot_reply})
                return history, bot_reply, [DEFAULT_IMAGE_PATH]*3
            else:
                bot_reply = "Réponse imprécise."
                history.append({"role": "assistant", "content": bot_reply})
                return history, bot_reply, [DEFAULT_IMAGE_PATH]*3
        else:
            bot_reply = f"Erreur du serveur : {response.status_code}."
            history.append({"role": "assistant", "content": bot_reply})
            return history, bot_reply, [DEFAULT_IMAGE_PATH]*3
    except requests.exceptions.Timeout:
        bot_reply = "Délai d'attente dépassé. Veuillez réessayer plus tard."
        history.append({"role": "assistant", "content": bot_reply})
        return history, bot_reply, [DEFAULT_IMAGE_PATH]*3
    except requests.exceptions.ConnectionError:
        bot_reply = "Impossible de se connecter au serveur. Vérifiez votre connexion."
        history.append({"role": "assistant", "content": bot_reply})
        return history, bot_reply, [DEFAULT_IMAGE_PATH]*3
    except requests.exceptions.RequestException as e:
        bot_reply = f"Erreur : {e}"
        history.append({"role": "assistant", "content": bot_reply})
        return history, bot_reply, [DEFAULT_IMAGE_PATH]*3

# Fonction pour formater les jeux recommandés en Markdown
def format_recommended_games(images):
    """Formate les jeux recommandés en affichant les images."""
    if not images:
        return "### Jeux Recommandés :\nAucune recommandation pour le moment."
    markdown = "### Jeux Recommandés :\n"
    for img in images:
        markdown += f"![Jeu](/{img})\n"  # Utilisation de Markdown pour afficher les images
    return markdown

# Fonction principale de l'interface
def chatbot_ui(user_input, state):
    history, bot_reply, images = chat_with_agent(user_input, state)
    state = history  # Met à jour l'historique
    conversation = "\n".join([f"👤 Vous : {m['content']}" if m['role'] == 'user' else f"🤖 Assistant : {m['content']}" for m in history])
    games_markdown = format_recommended_games(images)
    return conversation, state, games_markdown, ""  # Réinitialise l'entrée utilisateur

# Charger le logo
logo_path = os.path.join("assets", "logo.png")

with gr.Blocks() as demo:
    # Ajouter un logo
    gr.Markdown("# 🎮 GameFinder - Votre Assistant Virtuel")
    if os.path.exists(logo_path):
        gr.Image(logo_path, elem_id="logo", show_label=False, height=100)

    with gr.Row():
        conversation_box = gr.Textbox(
            label="Conversation",
            interactive=False,
            lines=15,
            placeholder="L'historique de votre conversation apparaîtra ici..."
        )
        with gr.Column():
            games_markdown_box = gr.Markdown("### Jeux Recommandés :\nAucune recommandation pour le moment.")

    user_input = gr.Textbox(
        label="Entrez votre message",
        placeholder="Que voulez-vous savoir ?",
        lines=1
    )
    submit_button = gr.Button("Envoyer")

    state = gr.State([])

    submit_button.click(
        chatbot_ui,
        inputs=[user_input, state],
        outputs=[conversation_box, state, games_markdown_box, user_input],
        show_progress=True  # Affiche une animation de chargement
    )
    user_input.submit(  # Associer la touche Entrée à l'envoi du message
        chatbot_ui,
        inputs=[user_input, state],
        outputs=[conversation_box, state, games_markdown_box, user_input],
        show_progress=True  # Affiche une animation de chargement
    )

demo.launch()