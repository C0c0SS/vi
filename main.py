import time
from playwright.sync_api import sync_playwright
import requests
from random import randint
import random
import string
import names
import re
import json
from discord import Embed, File, SyncWebhook
from pystyle import *
import os
import argparse
import logging
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

pink = Col.StaticMIX([Col.red, Col.pink])
def stage1(text: str, symbol: str = '...') -> str:
    ppink = pink if symbol == '...' else Col.pink
    return f""" {Col.Symbol(symbol, ppink, Col.red)} {ppink}{text}{Col.reset}"""

user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.121 Safari/537.36'

def load_filters(file_path='assets/filters.json'):
    """Charge les filtres depuis un fichier JSON dans le dossier assets contenant des URLs complètes."""
    # Construire le chemin absolu vers le fichier
    full_path = os.path.join(file_path)
    
    # Charger les données JSON
    with open(full_path, 'r') as f:
        data = json.load(f)
        
    # Extraire uniquement les URLs de chaque filtre
    filters_urls = [filter_item['url'] for filter_item in data['filters']]
    return filters_urls

def check_new_items(url, cookies, seen_item_ids):
    """Vérifie les nouveaux articles pour un filtre donné."""
    headers = {
        'User-Agent': user_agent,
        'Accept': 'application/json, text/plain, */*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'fr',
        'Content-Type': 'application/json',
        'Referer': 'https://www.vinted.fr/catalog',
        'X-Requested-With': 'XMLHttpRequest'
    }

    try:
        # Envoi de la requête GET avec cookies et en-têtes
        response = requests.get(url, headers=headers, cookies={cookie['name']: cookie['value'] for cookie in cookies})

        # Vérifier si la requête a réussi
        if response.status_code == 200:
            try:
                response_json = response.json()
                if 'items' in response_json:
                    items = response_json['items']
                    # Parcourir les articles pour détecter les nouveaux
                    for item in items:
                        item_id = item.get('id')
                        if item_id not in seen_item_ids:
                            title = item.get('title', 'Sans titre')
                            price = item.get('price', 'N/A')
                            added_date = item.get('created_at_ts', None)  # Timestamp de l'ajout

                            # Convertir le timestamp en date lisible si disponible
                            added_date_str = datetime.fromtimestamp(added_date).strftime('%Y-%m-%d %H:%M:%S') if added_date else 'Date non disponible'
                            
                            print(f"NOUVEL ARTICLE : {title}, Prix : {price} EUR, ID : {item_id}, Date d'ajout : {added_date_str}")
                            
                            seen_item_ids.add(item_id)  # Ajouter l'article à la liste des vus
                else:
                    print("Aucun article trouvé.")
            except json.JSONDecodeError:
                print("Erreur lors du décodage JSON.")
        else:
            print(f"Erreur dans la requête GET pour l'URL {url}. Statut : {response.status_code}")
            print(response.text)
    except requests.RequestException as e:
        print(f"Erreur lors de la requête pour l'URL {url}: {e}")

def requests_to_vinted(cookies, filters):
    """Vérifie en boucle les nouveaux articles pour chaque filtre dans une boucle infinie."""
    seen_items_per_filter = {url: set() for url in filters}

    while True:
        for url in filters:
            check_new_items(url, cookies, seen_items_per_filter[url])
            time.sleep(0.5)  # Intervalle de 2 secondes entre les vérifications pour chaque filtre

        
        time.sleep(0.5)  # Pause de 10 secondes avant de vérifier de nouveau tous les filtres

def main():
    filters = load_filters('assets/filters.json')  # Charge les URLs des filtres depuis le fichier
    
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
            # Affiche les cookies récupérés
            for cookie in cookies:
                vinted_cookie_print = stage1(f"{cookie['name']}: {cookie['value']} {Col.pink} {Col.reset}", "+")
                print(vinted_cookie_print.replace('"', '').replace("'", ""))
            cookie_true = stage2(f"Récupération des cookies effectués {Col.pink} {Col.reset}", "!")
            print(cookie_true.replace('"', '').replace("'", ""))
            # Début de la vérification continue des nouveaux articles
            requests_to_vinted(cookies, filters)
        except Exception as e:
            cookie_false = stage(f"Récupération des cookies échouée : {e} {Col.pink} {Col.reset}", "!")
            print(cookie_false.replace('"', '').replace("'", ""))

        # Fermer le navigateur
        browser.close()

if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    print(Colorate.Diagonal(Colors.purple_to_blue, Center.XCenter(banner + '\n\n' )))
    main()