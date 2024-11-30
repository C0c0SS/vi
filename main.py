import time
from playwright.sync_api import sync_playwright
import requests
import json
from pystyle import *
import os
from assets.banner import *
import datetime

purple = Col.StaticMIX([Col.blue, Col.purple])
def stage2(text: str, symbol: str = '...') -> str:
    ppurple = purple if symbol == '...' else Col.light_blue
    return f""" {Col.Symbol(symbol, ppurple, Col.blue)} {ppurple}{text}{Col.reset}"""

pred = Col.StaticMIX([Col.red, Col.red])
def stage(text: str, symbol: str = '...') -> str:
    ppred = pred if symbol == '...' else Col.red
    return f""" {Col.Symbol(symbol, ppred, Col.blue)} {ppred}{text}{Col.reset}"""

green = Col.StaticMIX([Col.green, Col.light_green])  # Dégradé vert clair
dark_green = Col.StaticMIX([Col.dark_green, Col.green])  # Dégradé vert foncé
def stage3(text: str, symbol: str = '...') -> str:
    pgreen = green if symbol == '...' else Col.light_green  # Utilisation de vert clair pour le texte
    return f""" {Col.Symbol(symbol, dark_green, Col.green)} {pgreen}{text}{Col.reset}"""

pink = Col.StaticMIX([Col.red, Col.pink])
def stage1(text: str, symbol: str = '...') -> str:
    ppink = pink if symbol == '...' else Col.pink
    return f""" {Col.Symbol(symbol, ppink, Col.red)} {ppink}{text}{Col.reset}"""

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'

def parse_cookies(cookie_str):
    """
    Convertit une chaîne de cookies au format `clé=valeur; clé=valeur; ...` en un dictionnaire Python.

    :param cookie_str: Chaîne de cookies.
    :return: Dictionnaire de cookies.
    """
    cookies = {}
    for cookie in cookie_str.split("; "):
        if "=" in cookie:
            key, value = cookie.split("=", 1)
            cookies[key] = value
    return cookies

def extract_all_profiles(file_path='assets/auth.json'):
    """
    Lit un fichier JSON et extrait les informations de tous les profils.

    :param file_path: Chemin vers le fichier JSON.
    :return: Une liste de dictionnaires contenant les informations de chaque profil.
    """
    try:
        # Lecture du fichier JSON
        with open(file_path, 'r') as file:
            data = json.load(file)
        
        # Vérifier si des profils existent
        if "profles" in data:
            profiles = []
            
            for profile in data["profles"]:
                profiles.append({
                    "name": profile.get("name", ""),
                    "token": profile.get("token", ""),
                    "v_uid": profile.get("v_uid", "")
                })
            
            return profiles
        else:
            raise ValueError("Aucun profil trouvé dans le fichier JSON.")
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Erreur lors de la lecture du fichier JSON : {e}")
        return None

def load_filters(file_path='assets/filters.json'):
    """Charge les filtres depuis un fichier JSON dans le dossier assets contenant des URLs complètes."""
    # Construire le chemin absolu vers le fichier
    full_path = os.path.join(file_path)
    
    # Charger les données JSON
    with open(full_path, 'r') as f:
        data = json.load(f)
        
    # Extraire uniquement les URLs de chaque filtre
    filters_urls = [{'name': filter_item['name'], 'url': filter_item['url']} for filter_item in data['filters']]
    return filters_urls

def check_new_items(url, cookies, seen_items_list, filter_name, token):
    """
    Vérifie les nouveaux articles pour un filtre donné.
    Appelle `get_transaction_id` si plus d'un nouvel article est détecté.
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'fr',
        'Content-Type': 'application/json',
        'Referer': 'https://www.vinted.fr/catalog',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        response = requests.get(url, headers=headers, cookies={cookie['name']: cookie['value'] for cookie in cookies})

        if response.status_code == 200:
            try:
                response_json = response.json()
                if 'items' in response_json:
                    items = response_json['items']
                    new_items = []

                    # Récupérer ou initialiser la liste des articles vus pour ce filtre
                    seen_item_ids = seen_items_list.setdefault(filter_name, [])

                    # Vérifie si chaque article est nouveau
                    for item in items:
                        item_id = item.get('id')
                        title = item.get('title', 'Sans titre')
                        price_data = item.get('price', {'amount': 'N/A', 'currency_code': ''})
                        price = f"{price_data.get('amount', 'N/A')} {price_data.get('currency_code', '').upper()}"

                        if item_id not in seen_item_ids:
                            seen_item_ids.append(item_id)  # Ajoute à la liste des vus
                            new_items.append({
                                "id": item_id,
                                "title": title,
                                "price": price
                            })

                            # Affiche un message pour chaque nouvel article trouvé
                            NOUVEL_ARTICLE = stage3(f"{title}, Prix : {price} EUR, ID : {item_id}, Filtre : {filter_name} {Col.pink} {Col.reset}", "NOUVEL ARTICLE")
                            print(NOUVEL_ARTICLE.replace('"', '').replace("'", ""))

                    # Si plusieurs nouveaux articles sont trouvés
                    if len(seen_item_ids) > 1:
                        for new_item in new_items:
                            get_transaction_id(new_item["id"], token)
            except json.JSONDecodeError:
                print(f"[ERREUR] Décodage JSON échoué pour le filtre : {filter_name}")
        elif response.status_code == 429:
            rate_limited_print = stage(f"Vous êtes rate limit !  {Col.pink} {Col.reset}", "!")
            print(rate_limited_print.replace('"', '').replace("'", "")) 
            exit()
        else:
            print(f"[ERREUR] Requête échouée pour l'URL {url}. Statut : {response.status_code}")
            print(response.text)
    except requests.RequestException as e:
        print(f"[ERREUR] Erreur réseau lors de la requête pour l'URL {url}: {e}")

def requests_to_vinted(cookies, filters, token):
    """
    Vérifie les nouveaux articles pour chaque filtre dans une boucle infinie.
    Stocke les articles vus par filtre dans un dictionnaire.
    """
    # Dictionnaire pour stocker les articles vus par filtre
    seen_items_dict = {}

    while True:
        for filter_item in filters:
            url = filter_item['url']
            filter_name = filter_item['name']

            # Appelle `check_new_items` pour vérifier les articles
            check_new_items(url, cookies, seen_items_dict, filter_name, token)

            time.sleep(0.5)  # Pause entre les vérifications des filtres

        time.sleep(0.5)  # Pause avant de re-parcourir tous les filtres

def stats(name, v_uid, token):
    """
    Fonction pour récupérer les statistiques d'un utilisateur Vinted via l'API.

    :param access_token: Le token d'accès pour l'authentification.
    :param name: Nom de l'utilisateur.
    :param v_uid: L'identifiant unique de l'utilisateur.
    """
    url = f'https://www.vinted.fr/api/v2/users/{v_uid}/stats'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'fr',
        'Content-Type': 'application/json',
        'Referer': 'https://www.vinted.fr/catalog',
        'X-Requested-With': 'XMLHttpRequest'
    }
    cookies = parse_cookies(token)
    try:
        # Envoi de la requête GET avec cookies et en-têtes
        response = requests.get(url, headers=headers, cookies=cookies)

        # Vérifier si la requête a réussi
        if response.status_code == 200:
            try:
                response_json = response.json()
                wallet_balance = response_json.get("stats", {}).get("wallet_balance")
                wallet_balance_currency = response_json.get("stats", {}).get("wallet_balance_currency")
                wallet_balance_print = stage2(f"{name}, Porte monnaie : {wallet_balance} {wallet_balance_currency} ", "Profils")
                print(wallet_balance_print.replace('"', '').replace("'", ""))
                if float(wallet_balance) == 0.0 :
                    wallet_balance_0 = stage(f"Le porte monnaie ne contient pas d' argent {Col.pink} {Col.reset}", "!")
                    print(wallet_balance_0.replace('"', '').replace("'", ""))  
                     
            except json.JSONDecodeError:
                print("Erreur lors du décodage JSON.")
        elif response.status_code == 401:
            token_print = stage(f"Le Jeton d'authentification est invalide {Col.pink} {Col.reset}", "!")
            print(token_print.replace('"', '').replace("'", ""))  
        else:
            print(f"Erreur dans la requête GET pour l'URL {url}. Statut : {response.status_code}")
            print(response.text)
    except requests.RequestException as e:
        print(f"Erreur lors de la requête pour l'URL {url}: {e}")

def get_transaction_id(item_id, token):
    url = f'https://www.vinted.fr/transaction/buy/new?source_screen=item&transaction%5Bitem_id%5D={item_id}'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br, zstd',
        'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
    }
    cookies = parse_cookies(token)

    # Envoi de la requête GET avec suivi des redirections désactivé
    response = requests.get(url, headers=headers, cookies=cookies, allow_redirects=False)
    if response.status_code == 302:
        # Vérifie si l'en-tête x-internal-url est présent
        if 'location' in response.headers:
            internal_url = response.headers['location']
            # Extrait la partie contenant 'checkout?transaction_id'
            if 'checkout?transaction_id' in internal_url:
                transaction_part = internal_url.split('checkout?transaction_id=')[-1]
                transaction_print = stage3(f"Transaction id récupérer avec succés ! {Col.pink} {Col.reset}", {transaction_part})
                print(transaction_print.replace('"', '').replace("'", ""))
    else : 
        print(f"[ERREUR] Requête échouée pour l'URL {url}. Statut : {response.status_code}")
        print(response.json)
    
def main():
    filters = load_filters('assets/filters.json')  # Charge les URLs des filtres depuis le fichier
    all_profiles = extract_all_profiles(file_path='assets/auth.json')
    cookie_true = stage2(f"Initialisations des profiles en cours {Col.pink} {Col.reset}", "!")
    print(cookie_true.replace('"', '').replace("'", ""))
    if all_profiles:
        for profile in all_profiles:
           stats(profile["name"], profile["v_uid"], profile["token"])
    url = 'https://vinted.fr'
    with sync_playwright() as p:
        # Démarrer le navigateur
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent=user_agent)
        
        # Ouvrir une nouvelle page
        page = context.new_page()
        
        # Naviguer vers l'URL et accepter les cookies si nécessaire
        page.goto(url)
        time.sleep(8)
        
        cookie_true = stage2(f"Récupération des cookies en cours {Col.pink} {Col.reset}", "!")
        print(cookie_true.replace('"', '').replace("'", ""))
        
        # Vérifier et cliquer sur le bouton d'acceptation des cookies si présent
        cookie_button_xpath = 'xpath=/html/body/div[43]/div[2]/div/div[1]/div/div[2]/div/button[1]'
        if page.locator(cookie_button_xpath).is_visible():
            page.locator(cookie_button_xpath).click()
            time.sleep(5)
        
        try:
            cookies = context.cookies()
            cookie_true = stage2(f"Récupération des cookies effectués {Col.pink} {Col.reset}", "!")
            print(cookie_true.replace('"', '').replace("'", ""))
            # Début de la vérification continue des nouveaux articles
            requests_to_vinted(cookies, filters, profile["token"])
        except Exception as e:
            cookie_false = stage(f"Récupération des cookies échouée : {e} {Col.pink} {Col.reset}", "!")
            print(cookie_false.replace('"', '').replace("'", ""))

        # Fermer le navigateur
        browser.close()

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    print(Colorate.Diagonal(Colors.purple_to_blue, Center.XCenter(banner + '\n\n' )))
    main()
