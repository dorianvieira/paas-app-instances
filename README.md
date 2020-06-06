# paas-app-instances
Application PaaS communiquant avec l'état des instances d'un groupe d'instances selon sa région en temps réel (+ leurs infos).  

Application qui redirige sur l'instance la plus propice à recevoir du trafic (celle qui reçoit actuellement)
 
Load possible sur une instance pour générer une forte charge sur le CPU 

Panne de zone possible pour rendre indisponible une instance à réceptionner du trafic et vice-versa pour rendre de nouveau opérationnel et disponible une instance d'une zone.

Chemin /health pour récéptionner le message de retour de la vérification d'état
