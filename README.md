# BridgeOps

Plateforme personnelle d'orchestration de transferts de fichiers (FastAPI, Celery, Redis, PostgreSQL).  
Projet en cours de construction — ce dépôt contient pour l'instant le squelette de l'application.

![status](https://img.shields.io/badge/status-en%20d%C3%A9veloppement-yellow)

## Objectif du projet

BridgeOps vise à centraliser et automatiser des transferts de fichiers entre différentes sources (SFTP, Azure Blob Storage, etc.), avec :

- file d'attente,
- workers Celery,
- retry automatique,
- journalisation détaillée,
- stockage des métadonnées en base.

Ce projet est un travail personnel, sans lien avec un employeur.

## Stack technique (prévue)

- **API** : FastAPI  
- **Tâches asynchrones** : Celery + Redis  
- **Base de données** : PostgreSQL  
- **Stockage fichiers** : Azure Blob Storage (Azurite en local), SFTP  
- **Frontend** : Jinja2  
- **Conteneurisation** : Docker Compose  
- **Tests** : Pytest  
- **CI** : GitHub Actions (à venir)

## Lancer le projet (développement)

```bash
cp .env.example .env
docker compose up --build
```

L'API est disponible sur `http://localhost:8000`, la documentation Swagger sur `http://localhost:8000/docs`.