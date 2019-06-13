# Used to parse HTML
from bs4 import BeautifulSoup

# Standard lib for regex
import re

# Lib to Execute https request and execute the javascript (without open a window)
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QUrl
from PyQt5.QtWebEngineWidgets import QWebEnginePage

from datetime import datetime, date, timedelta, time


class Page(QWebEnginePage):
    def __init__(self, url):
        self.app = QApplication(sys.argv)
        QWebEnginePage.__init__(self)
        self.html = ''
        self.loadFinished.connect(self._on_load_finished)
        self.load(QUrl(url))
        self.app.exec_()

    def _on_load_finished(self):
        self.html = self.toHtml(self.Callable)

    def Callable(self, html_str):
        self.html = html_str
        self.app.quit()


def get_info(annonce, today_datetime, today_date, size):
    """This function extract all the informations for one ad of type ''
    """

    id_ = annonce.get('data-id')
    prix = annonce.find('div', class_='%s-price rangePrice' % size)

    if prix:
        prix = prix.text
        # Create a list with all the different price
        prix = [int(re.sub('[.]', '', item)) for item in re.findall(r'[0-9.]*', prix) if item != '']

        # est_nouveau will be True if there is only one price
        est_nouveau = True if len(prix) == 1 else False
    else:
        prix = []
        est_nouveau = True

    sur_ch = annonce.find('div', class_='%s-surface-ch' % size).text
    sur, ch = None, None

    # split by 'm', if there isn't 'm' in sur_ch -> tmp = [sur_ch]
    tmp = sur_ch.split('m')

    if len(tmp) == 2:
        # get the surface
        sur = [int(re.sub('[.]', '', item)) for item in re.findall(r'[0-9.]*', tmp[0]) if item != ''][0]

    # select the string where the information about the rooms is present
    tmp = tmp[1] if len(tmp) == 2 else tmp[0]
    tmp = tmp.split('c')
    if len(tmp) == 2:
        # get the number of rooms
        ch = [int(re.sub('[.]', '', item)) for item in re.findall(r'[0-9.]*', tmp[0]) if item != ''][0]

    # strip() remove all invisible charachter at the begging and end of a string
    typ = annonce.find('div', class_='title-bar-left').text.strip()
    commune = annonce.find('div', class_='title-bar-right').text.strip()

    # find the zip code
    code_postal = int(re.match(r'[0-9]{4}', commune)[0])

    # remove the zip code
    nom_commune = re.sub(r'^%i ' % code_postal, '', commune)

    heures, minutes = list(map(int, annonce.find('div', class_='prix-heure').text.split('h')))

    if heures > today_datetime.hour:
        heure = datetime.combine(today_date - timedelta(1), time(hour=heures, minute=minutes))
    else:
        heure = datetime.combine(today_date, time(hour=heures, minute=minutes))

    lien = annonce.a.get('href')

    return {'id': id_,
            'prix': prix,
            'surface': sur,
            'chambres': ch,
            'est_nouveau': est_nouveau,
            'code_postal': code_postal,
            'nom_commune': nom_commune,
            'date': heure,
            'lien': lien,
            'type': typ}


def get_lastest_ads(number_pages=1):
    sizes = ['m', 'l', 'xl']
    today_date = date.today()
    today_datetime = datetime.now()

    annonces_json_dict = dict()
    annonces_json_list = list()

    for i in range(1, number_pages + 1):
        # Get the HTML for the last real estate ad
        url = 'https://www.immoweb.be/fr/recherche/dernieres-annonces-immobilieres-publiees/a-vendre?page=%i'
        client_response = Page(url)
        html_source = client_response.html

        # create the BeautifulSoup object from the html
        soup = BeautifulSoup(html_source)

        # Get only the part with the real estate ad
        annonces = soup.find('div', {"id": "result"})

        # Iterate over the different ad of type 'result-m'
        for size in sizes:
            for i, annonce in enumerate(annonces.findAll('div', class_='result-%s' % size)):
                infos = get_info(annonce, today_datetime, today_date, size)
                annonces_json_dict[infos['id']] = infos
                annonces_json_list.append(infos)

    return annonces_json_list, annonces_json_dict
