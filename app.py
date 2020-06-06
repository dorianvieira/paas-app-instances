"""
Application en Flask ->
Expose une interface utilisateur montrant 
les statistiques et infos du serveur(instance) et un bouton de basculement 
pour générer une charge du CPU et voir l'état du serveur
Possibilité de rendre op et non op une instance d'une zone
Vérification d'état de l'instance actuellement affichée sur /health
"""

from ctypes import c_bool
from flask import Flask, make_response, render_template
from multiprocessing import Process, Value
from random import random
from re import sub
from requests import get
from socket import gethostname
from time import sleep

PORT_NUMBER = 80

app = Flask(__name__)
_is_healthy = True
_cpu_burner = None


@app.before_first_request
def init(): #Initialisation de l'application
    global _cpu_burner
    _cpu_burner = CpuBurner() # interne aux métadata de Google; valeur aléatoire >70%


@app.route('/')
def index(): #Template
    """Retourne l'interface utilisateur"""
    global _cpu_burner, _is_healthy
    return render_template('index.html',
                           hostname=gethostname(),
                           zone=_get_zone(),
						   machine-type=_get_machine_type(),
                           template=_get_template(),
                           healthy=_is_healthy,
                           working=_cpu_burner.is_running())


@app.route('/health')
def health(): #fonction pour retourner le statut de la VM 
    """Retourne le statut du serveur simulé en fonction de la charge
	En fonction de la vérification de l'état
    Retourne:
        HTTP status 200 si 'healthy', HTTP status 500 si 'unhealthy'
    """
    global _is_healthy
    template = render_template('health.html', healthy=_is_healthy)
    return make_response(template, 200 if _is_healthy else 500)


@app.route('/makeHealthy')
def make_healthy(): #fonction pour simuler la bonne santé de la VM
    """Configure le serveur pour simuler un état 'sain', 
	la VM est alors opérationnel à récéptionner du trafic
	"""
    global _cpu_burner, _is_healthy
    _is_healthy = True

    template = render_template('index.html',
                               hostname=gethostname(),
                               zone=_get_zone(),
							   machine-type=_get_machine_type(),
                               template=_get_template(),
                               healthy=True,
                               working=_cpu_burner.is_running())
    response = make_response(template, 302)
    response.headers['Location'] = '/'
    return response


@app.route('/makeUnhealthy')
def make_unhealthy(): #fonction pour simuler une panne de la VM
    """Configure le serveur pour simuler un état 'non sain',
	la VM est non opérationnelle à recevoir du trafic"""
    global _cpu_burner, _is_healthy
    _is_healthy = False

    template = render_template('index.html',
                               hostname=gethostname(),
                               zone=_get_zone(),
							   machine-type=_get_machine_type(),
                               template=_get_template(),
                               healthy=False,
                               working=_cpu_burner.is_running())
    response = make_response(template, 302)
    response.headers['Location'] = '/'
    return response


@app.route('/startLoad')
def start_load(): #fonction pour simuler une augmentation de la charge du CPU pour l'app
    """Règle le serveur pour simuler une charge CPU élevée"""
    global _cpu_burner, _is_healthy
    _cpu_burner.start()

    template = render_template('index.html',
                               hostname=gethostname(),
                               zone=_get_zone(),
							   machine-type=_get_machine_type(),
                               template=_get_template(),
                               healthy=_is_healthy,
                               working=True)
    response = make_response(template, 302)
    response.headers['Location'] = '/'
    return response


@app.route('/stopLoad')
def stop_load(): #fonction pour stoper charge du CPU
    """Règle le serveur pour qu'il arrête de simuler la charge du CPU"""
    global _cpu_burner, _is_healthy
    _cpu_burner.stop()

    template = render_template('index.html',
                               hostname=gethostname(),
                               zone=_get_zone(),
							   machine-type=_get_machine_type(),
                               template=_get_template(),
                               healthy=_is_healthy,
                               working=False)
    response = make_response(template, 302)
    response.headers['Location'] = '/'
    return response


def _get_zone(): #get la zone ou se trouve le serveur de la VM
    """Récup la zone de l'instance GCE

    Retourne:
        str: Le nom de la zone si la zone a été déterminée avec succès
        Sinon string vide
    """
    r = get('http://metadata.google.internal/'
            'computeMetadata/v1/instance/zone',
            headers={'Metadata-Flavor': 'Google'})
    if r.status_code == 200:
        return sub(r'.+zones/(.+)', r'\1', r.text) #metatdata google
    else:
        return ''


def _get_template(): #get le modèle de VM sur lequel se base le groupe d'instances
    """récupérer le templace de l'intance GCE

    Retourne:
        str: Le nom du modèle si le modèle a été déterminé avec succès et si 
		cette instance a été construite en utilisant une instance = modèle
        Sinon string vide
    """
    r = get('http://metadata.google.internal/'
            'computeMetadata/v1/instance/attributes/instance-template',
            headers={'Metadata-Flavor': 'Google'})
    if r.status_code == 200:
        return sub(r'.+instanceTemplates/(.+)', r'\1', r.text) #metatdata google
    else:
        return ''
		

def _get_machine_type(): #get le type de machine utilisé par le groupe d'instances
	"""récupérer les caractéritique de l'image utilisée par le template"""
    r = get('http://metadata.google.internal/'
            'computeMetadata/v1/instance/attributes/machine-type',
            headers={'Metadata-Flavor': 'Google'})
    if r.status_code == 200:
        return sub(r'.+machineTypes/(.+)', r'\1', r.text) #metatdata google
    else:
        return ''


class CpuBurner: #Synchronisation asynchrone pour la charge du CPU
    """
    Charger de manière asynchrone les cycles du CPU 
	pour simuler une charge CPU élevée de l'application
    """
    def __init__(self):
        self._toggle = Value(c_bool, False, lock=True)
        self._process = Process(target=self._burn_cpu)
        self._process.start()

    def start(self):
        """Lancement de la charge sur le CPU"""
        self._toggle.value = True # interne aux métadata de Google; valeur aléatoire >70%

    def stop(self):
        """Stop de la charge du CPU"""
        self._toggle.value = False

    def is_running(self):
        """Retourne true si le CPU est actuellement chargé"""
        return self._toggle.value 

    def _burn_cpu(self):
        """Charge les cycles du CPU si c'est en cours, sinon 'sleep'"""
        while True:
            random()*random() if self._toggle.value else sleep(1)
			# interne aux métadata de Google; valeur aléatoire >70%


if __name__ == "__main__":
    app.run(debug=False, port=PORT_NUMBER)
