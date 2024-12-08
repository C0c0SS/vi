import time
from playwright.sync_api import sync_playwright
import requests
import json
from pystyle import *
import os
from assets.banner import *
import datetime
import re
import argparse

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

def get_cookies(user_agent):
    url = 'https://vinted.fr'
    try:
        with sync_playwright() as p:
            # Démarrer le navigateur
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(user_agent=user_agent)
            
            # Ouvrir une nouvelle page
            page = context.new_page()
            
            # Naviguer vers l'URL
            page.goto(url)
            time.sleep(8)  # Attendre le chargement
            
            # Vérifier et cliquer sur le bouton d'acceptation des cookies si présent
            cookie_button_xpath = 'xpath=/html/body/div[43]/div[2]/div/div[1]/div/div[2]/div/button[1]'
            if page.locator(cookie_button_xpath).count() > 0:  # Vérifie si l'élément existe
                if page.locator(cookie_button_xpath).is_visible():
                    page.locator(cookie_button_xpath).click()
                    time.sleep(5)
            
            # Récupérer les cookies
            cookies = context.cookies()
            browser.close()  # Fermer le navigateur
            
            return cookies
    
    except Exception as e:
        print(f"Une erreur est survenue : {e}")
        return None
            
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
    base_url = "https://www.vinted.fr/api/v2/"
    
    def get_headers(referer_url):
        """Génère des en-têtes HTTP communs."""
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'fr',
            'Content-Type': 'application/json',
            'Referer': referer_url,
            'X-Requested-With': 'XMLHttpRequest'
        }
    
    cookies = parse_cookies(token)
    
    try:
        # Récupération des statistiques utilisateur
        stats_url = f'{base_url}users/{v_uid}/stats'
        stats_response = requests.get(stats_url, headers=get_headers("https://www.vinted.fr/catalog"), cookies=cookies)

        if stats_response.status_code == 200:
            try:
                stats_json = stats_response.json()
                stats = stats_json.get("stats", {})
                wallet_balance = stats.get("wallet_balance", 0.0)
                wallet_currency = stats.get("wallet_balance_currency", "EUR")

                wallet_msg = stage2(f"{name}, Porte-monnaie : {wallet_balance} {wallet_currency}", "Profils")
                print(wallet_msg.replace('"', '').replace("'", ""))

                if float(wallet_balance) == 0.0:
                    # Vérification des moyens de paiement
                    payment_url = f'{base_url}payments/credit_cards'
                    payment_response = requests.get(payment_url, headers=get_headers("https://www.vinted.fr/settings/payments"), cookies=cookies)

                    if payment_response.status_code == 200:
                        try:
                            payment_json = payment_response.json()
                            if not payment_json.get("cards"):
                                payment_msg = stage(f"{name}, Aucun moyen de paiement disponible {Col.pink} {Col.reset}", "Profils")
                                print(payment_msg.replace('"', '').replace("'", ""))   
                            else:
                                payment_msg = stage2(f"{name}, Carte bancaire disponible {Col.pink} {Col.reset}", "Profils")
                                print(payment_msg.replace('"', '').replace("'", ""))
                        except json.JSONDecodeError:
                            print("Erreur: La réponse des moyens de paiement n'est pas un JSON valide.")

                # Vérification de l'adresse de livraison par défaut
                address_url = f'{base_url}user_addresses/default_shipping_address'
                address_response = requests.get(address_url, headers=get_headers("https://www.vinted.fr/settings/shipping"), cookies=cookies)

                if address_response.status_code == 200:
                    try:
                        address_json = address_response.json()
                        if "user_address" in address_json:
                            address_msg = stage2(f"{name}, Adresse de facturation disponible {Col.pink} {Col.reset}", "Profils")
                            print(address_msg.replace('"', '').replace("'", ""))
                        else:
                            address_msg = stage(f"{name}, Adresse de facturation indisponible {Col.pink} {Col.reset}", "Profils")
                            print(address_msg.replace('"', '').replace("'", ""))
                    except json.JSONDecodeError:
                        print("Erreur: La réponse de l'adresse n'est pas un JSON valide.")

                phone_url = f'{base_url}users/{v_uid}/security'
                phone_response = requests.get(phone_url, headers=get_headers("https://www.vinted.fr/settings/account"), cookies=cookies)

                if phone_response.status_code == 200:
                    try:
                        phone_json = phone_response.json()
                        masked_phone_number = phone_json.get("security", {}).get("masked_phone_number")
                        if masked_phone_number is None:
                            phone_msg = stage(f"{name}, Numéro de téléphone indisponible {Col.pink} {Col.reset}", "Profils")
                            print(phone_msg.replace('"', '').replace("'", ""))
                        elif masked_phone_number == "null":
                            phone_msg = stage(f"{name}, Numéro de téléphone indisponible {Col.pink} {Col.reset}", "Profils")
                            print(phone_msg.replace('"', '').replace("'", ""))
                        else:
                            phone_msg = stage2(f"{name}, Numéro de téléphone disponible {Col.pink} {Col.reset}", "Profils")
                            print(phone_msg.replace('"', '').replace("'", ""))
                    except json.JSONDecodeError:
                        print("Erreur: La réponse de l'adresse n'est pas un JSON valide.")                            
            except json.JSONDecodeError:
                print("Erreur lors du décodage JSON des statistiques.")
        elif stats_response.status_code == 401:
            print(stage(f"{name}, Le jeton d-authentification est invalide {Col.pink} {Col.reset}", "Profils").replace('"', '').replace("'", ""))
        else:
            print(f"Erreur dans la requête GET pour {stats_url}. Statut : {stats_response.status_code}")
    except requests.RequestException as e:
        print(f"Erreur réseau lors de la requête pour {stats_url}: {e}")

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
                transaction_print = stage3(f"Transaction id récupérer avec succés ! {Col.pink} {Col.reset}", transaction_part)
                print(transaction_print.replace('"', '').replace("'", ""))
                checkout(transaction_part, token)

    elif response.status_code == 307:
        transaction_print = stage(f"Le Jeton d-authentification est invalide {Col.pink} {Col.reset}", "Transaction")
        print(transaction_print.replace('"', '').replace("'", "")) 
    elif response.status_code == 500:
        transaction_print = stage(f"Une erreur s'est produite {Col.pink} {Col.reset}", "Transaction")
        print(transaction_print.replace('"', '').replace("'", "")) 
    else : 
        print(f"[ERREUR] Requête échouée pour l'URL {url}. Statut : {response.status_code}")
        print(response.json)
    
def checkout(transaction_part, token):
    url = f'https://www.vinted.fr/api/v2/transactions/{transaction_part}/checkout'
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
    # Envoi de la requête GET avec suivi des redirections désactivé
    response = requests.get(url, headers=headers, cookies=cookies, allow_redirects=False)
    if response.status_code == 200:
        # Obtenir le texte brut de la réponse
        response_text = response.text
        # Expression régulière pour trouver le checksum
        checksum_match = re.search(r'"checksum"\s*:\s*"([a-fA-F0-9]{32})"', response_text)
        
        if checksum_match:
            # Récupère le checksum depuis le premier groupe capturé
            checksum = checksum_match.group(1)
            print("Checksum trouvé :", checksum)
        else:
            print("Checksum introuvable dans la réponse.")
    else:
        print(f"Erreur : Statut HTTP {response.status_code}")

def oauth(cookies, username, password):
    url = 'https://www.vinted.fr/web/api/auth/oauth'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'fr',
        'Content-Type': 'application/json',
        'Referer': 'https://www.vinted.fr/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    data = {
        "client_id": "web",
        "scope": "user",
        "fingerprint": "63a76e4155c1bddd2f56a163d39c9684",
        "username": username,
        "password": password,
        "grant_type": "password"
    }
    cookies_dict = {cookie['name']: cookie['value'] for cookie in cookies}
    response = requests.post(url, headers=headers, json=data, cookies=cookies_dict)
    if response.status_code == 200:
        response_json = response.json()
        access_token_web = response_json.get("access_token")
        refresh_token_web = response_json.get("refresh_token")
        token = (f"access_token_web={access_token_web};refresh_token_web={refresh_token_web};")
        return token
    else:
        print(f"Erreur {response.status_code}: {response.reason} {url}")
        try:
            print(response.json())
        except ValueError:
            print(response.text)
    
def get_v_uid(token):
    url = 'https://www.vinted.fr/api/v2/users/current'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'fr',
        'Content-Type': 'application/json',
        'Referer': 'https://www.vinted.fr/',
        'X-Requested-With': 'XMLHttpRequest'
    }
    cookies = parse_cookies(token)
    # Effectuer une requête avec les cookies passés en paramètre
    response = requests.get(url, headers=headers, cookies=cookies)
    if response.status_code == 200:
        # Extraire les cookies
        cookies = response.cookies.get_dict()
        
        # Retourner le v_uid si disponible
        v_uid = cookies.get('v_uid')
        if v_uid:
            return v_uid
        else:
            return "v_uid non trouvé dans les cookies."
    else:
        # En cas d'erreur HTTP
        return f"Erreur {response.status_code}: {response.reason}"

def main():
    parser = argparse.ArgumentParser(description="Bots vinted settings.")
    parser.add_argument('-o', '--oauth', action='store_true', help="Connexion Vinted avec mots de passe et identifiant")
    args = parser.parse_args()
    filters = load_filters('assets/filters.json')  # Charge les URLs des filtres depuis le fichier
    if args.oauth:
        cookie_true = stage2(f"Récupération des cookies en cours {Col.pink} {Col.reset}", "!")
        print(cookie_true.replace('"', '').replace("'", ""))
        cookies = get_cookies(user_agent)
        cookie_true = stage2(f"Récupération des cookies effectués {Col.pink} {Col.reset}", "!")
        print(cookie_true.replace('"', '').replace("'", ""))
        username = input(stage2(f"Veuillez entrer votre identifiant vinted {Col.blue}-> {Col.reset}", "?")).replace('"','').replace("'","")
        password = input(stage2(f"Veuillez entrer votre mots de passe vinted {Col.blue}-> {Col.reset}", "?")).replace('"','').replace("'","")
        token = oauth(cookies, username, password)
        v_uid = get_v_uid(token)
        stats(username, v_uid, token)
        requests_to_vinted(cookies, filters, token)
    else:
        all_profiles = extract_all_profiles(file_path='assets/auth.json')
        cookie_true = stage2(f"Initialisations des profiles en cours {Col.pink} {Col.reset}", "!")
        print(cookie_true.replace('"', '').replace("'", ""))
        if all_profiles:
            for profile in all_profiles:
                stats(profile["name"], profile["v_uid"], profile["token"])
        try:
            cookie_true = stage2(f"Récupération des cookies en cours {Col.pink} {Col.reset}", "!")
            print(cookie_true.replace('"', '').replace("'", ""))
            cookies = get_cookies(user_agent)
            cookie_true = stage2(f"Récupération des cookies effectués {Col.pink} {Col.reset}", "!")
            print(cookie_true.replace('"', '').replace("'", ""))
            requests_to_vinted(cookies, filters, profile["token"])
        except Exception as e:
            cookie_false = stage(f"Récupération des cookies échouée : {e} {Col.pink} {Col.reset}", "!")
            print(cookie_false.replace('"', '').replace("'", ""))

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    print(Colorate.Diagonal(Colors.purple_to_blue, Center.XCenter(banner + '\n\n' )))
    main()
