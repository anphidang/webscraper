import time
import json
import random
import os
from typing import List, Dict

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def setup_driver() -> webdriver.Chrome:
    """
    Initialisiert und konfiguriert den ChromeDriver (mit benutzerdefiniertem User-Agent).
    """
    options = webdriver.ChromeOptions()
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    # options.add_argument("--headless")  # Bei Bedarf einkommentieren
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    return driver

def scroll_page(driver: webdriver.Chrome, times: int = 3, pause: float = 2.0):
    """
    Scrollt die Seite n-mal nach unten, jeweils mit kleiner Pause.
    """
    for _ in range(times):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(pause)

def collect_bibtex(driver: webdriver.Chrome, collected_data: Dict[str, List[Dict]], author_name: str):
    """
    Sammelt alle BibTeX-Einträge von der aktuellen Seite und fügt sie zur Liste hinzu.
    """
    try:
        # Warte, bis der BibTeX-Bereich sichtbar ist
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, "verbatim"))
        )

        # Finde alle <pre>-Tags mit BibTeX-Einträgen
        bibtex_entries = driver.find_elements(By.CLASS_NAME, "verbatim")
        if author_name not in collected_data:
            collected_data[author_name] = []
        for entry in bibtex_entries:
            collected_data[author_name].append({"bibtex": entry.text})

        print(f"{len(bibtex_entries)} BibTeX-Einträge gesammelt für {author_name}.")
    except Exception as e:
        print(f"Fehler beim Sammeln der BibTeX-Daten für {author_name}: {e}")

def main() -> None:
    driver = setup_driver()
    collected_data = {}
    collected_authors = 0

    while collected_authors < 10:
        driver.get("https://dblp.org/")

        # Warte, bis die Seite geladen ist (z. B. bis das DBLP-Logo sichtbar ist)
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "header nav"))
        )

        # 1) Klick auf einen zufälligen Buchstaben unter "browse authors | editors"
        try:
            # Suche nach dem Bereich, der die Buchstaben enthält
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul#browsable"))
            )
            letters_section = driver.find_element(By.CSS_SELECTOR, "ul#browsable")
            letter_links = [link for link in letters_section.find_elements(By.TAG_NAME, "a") if "pers" in link.get_attribute("href")]

            if not letter_links:
                raise Exception("Keine Buchstaben-Links gefunden unter 'browse authors'.")

            random_letter_link = random.choice(letter_links)  # Zufälligen Buchstaben auswählen
            print(f"Klicke auf Buchstaben: {random_letter_link.text}")
            random_letter_link.click()
            time.sleep(random.uniform(1, 3))  # Zufällige Pause, um wie ein Mensch zu wirken
        except Exception as e:
            print(f"Fehler beim Klicken auf Buchstaben-Link: {e}")
            print("Aktueller Seiten-HTML-Inhalt:")
            print(driver.page_source)  # Ausgabe des aktuellen Seiteninhalts zur Analyse
            driver.quit()
            return

        # Warte kurz, bis die Seite lädt
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "browse-person-output"))  # Container für Autoren
            )
            authors_section = driver.find_element(By.ID, "browse-person-output")
            author_links = authors_section.find_elements(By.TAG_NAME, "a")

            if not author_links:
                raise Exception("Keine Autoren-Links gefunden auf der Seite.")

            # Zufällig einen Autor auswählen
            selected_author = random.choice(author_links)
            author_name = selected_author.text
            print(f"Rufe Autorenseite auf: {author_name}")
            selected_author.click()
            time.sleep(random.uniform(1, 3))  # Pause nach dem Klick

            # Warte auf die Autorenseite und klicke auf den Export-Button
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "export"))  # Export-Dropdown
                )
                export_button = driver.find_element(By.CLASS_NAME, "export")
                export_link = export_button.find_element(By.TAG_NAME, "a")  # Link im Export-Dropdown
                export_link.click()
                time.sleep(random.uniform(1, 3))  # Pause nach dem Klick
                print("Export-Seite erfolgreich geöffnet.")

                # BibTeX-Daten sammeln
                collect_bibtex(driver, collected_data, author_name)
                collected_authors += 1

            except Exception as e:
                print(f"Fehler beim Klicken auf den Export-Button oder Sammeln der BibTeX-Daten für {author_name}: {e}")

        except Exception as e:
            print(f"Fehler beim Auswählen eines Autors: {e}")

    # Speichere alle gesammelten BibTeX-Daten in einer einzigen JSON-Datei
    with open("all_bibtex_records.json", "w", encoding="utf-8") as f:
        json.dump(collected_data, f, ensure_ascii=False, indent=4)

    print(f"Alle BibTeX-Daten wurden in 'all_bibtex_records.json' gespeichert.")
    driver.quit()

if __name__ == "__main__":
    main()
