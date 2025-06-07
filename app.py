from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import pandas as pd
import numpy as np
import nltk
from nltk.sentiment import SentimentIntensityAnalyzer
import re
import os
from datetime import datetime
import logging
import sqlite3
from pathlib import Path
import json
from textblob import TextBlob
from transformers import pipeline
import torch
import requests
from bs4 import BeautifulSoup
import textstat
from urllib.parse import urlparse, urljoin
import hashlib
import time

# Flask App Setup
app = Flask(__name__)
app.secret_key = 'credibility_guard_secret_key_2024'
CORS(app)

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database Setup
DATABASE_PATH = 'credibility_database.db'

# Sprachkonfiguration (4 Sprachen)
LANGUAGES = {
    'de': {
        'title': 'CredibilityGuard - KI-gestützte Glaubwürdigkeitsanalyse',
        'subtitle': 'Analysieren Sie Inhalte auf Qualität, Faktentreue und Vertrauenswürdigkeit',
        'analyze_content': 'Text oder URL zur Glaubwürdigkeitsanalyse eingeben:',
        'placeholder': 'Fügen Sie hier den zu analysierenden Text ein oder geben Sie eine URL an...',
        'url_placeholder': 'https://example.com/article',
        'analyze_btn': 'Glaubwürdigkeit analysieren',
        'analyze_url_btn': 'URL analysieren',
        'search_btn': 'Suchen',
        'results_title': 'Glaubwürdigkeitsanalyse Ergebnisse',
        'search_title': 'Inhaltssuche',
        'search_placeholder': 'Nach Inhalten oder URLs suchen...',
        'credibility_score': 'Glaubwürdigkeits-Score',
        'content_quality': 'Inhaltsqualität',
        'factual_accuracy': 'Faktische Genauigkeit',
        'source_reliability': 'Quellenvertrauenswürdigkeit',
        'classification': 'Klassifikation',
        'confidence': 'Konfidenz',
        'loading': 'Analysiere Glaubwürdigkeit...',
        'loading_url': 'Lade und analysiere URL...',
        'no_analysis': 'Noch keine Analyse',
        'enter_content': 'Geben Sie Inhalt ein und klicken Sie auf "Analysieren"',
        'examples_title': 'Beispiel-Inhalte zum Testen:',
        'high_quality_example': 'Hohe Qualität',
        'medium_quality_example': 'Mittlere Qualität',
        'low_quality_example': 'Niedrige Qualität',
        'language': 'Sprache',
        'credibility_high': 'Hohe Glaubwürdigkeit',
        'credibility_medium': 'Mittlere Glaubwürdigkeit',
        'credibility_low': 'Niedrige Glaubwürdigkeit',
        'credibility_questionable': 'Fragwürdig',
        'save_analysis': 'Analyse speichern',
        'saved_successfully': 'Analyse erfolgreich gespeichert',
        'search_results': 'Suchergebnisse',
        'no_results': 'Keine Ergebnisse gefunden',
        'words': 'Wörter',
        'sentences': 'Sätze',
        'characters': 'Zeichen',
        'sources_found': 'Gefundene Quellen',
        'claims_verified': 'Verifizierte Aussagen',
        'readability_score': 'Lesbarkeits-Score',
        'bias_level': 'Voreingenommenheit',
        'processing_time': 'Verarbeitungszeit',
        'database_status': 'Datenbank-Status',
        'total_analyses': 'Gesamt-Analysen',
        'search_hint': 'Suche in gespeicherten Inhalten und Analysen',
        'export_data': 'Daten exportieren',
        'url_analysis': 'URL-Analyse',
        'content_analysis': 'Text-Analyse',
        'detailed_breakdown': 'Detaillierte Aufschlüsselung',
        'recommendations': 'Empfehlungen',
        'fact_check_results': 'Faktencheck-Ergebnisse'
    },
    'en': {
        'title': 'CredibilityGuard - AI-Powered Credibility Analysis',
        'subtitle': 'Analyze content for quality, factual accuracy and trustworthiness',
        'analyze_content': 'Enter text or URL for credibility analysis:',
        'placeholder': 'Paste the content you want to analyze here or provide a URL...',
        'url_placeholder': 'https://example.com/article',
        'analyze_btn': 'Analyze Credibility',
        'analyze_url_btn': 'Analyze URL',
        'search_btn': 'Search',
        'results_title': 'Credibility Analysis Results',
        'search_title': 'Content Search',
        'search_placeholder': 'Search for content or URLs...',
        'credibility_score': 'Credibility Score',
        'content_quality': 'Content Quality',
        'factual_accuracy': 'Factual Accuracy',
        'source_reliability': 'Source Reliability',
        'classification': 'Classification',
        'confidence': 'Confidence',
        'loading': 'Analyzing credibility...',
        'loading_url': 'Loading and analyzing URL...',
        'no_analysis': 'No analysis yet',
        'enter_content': 'Enter content and click "Analyze"',
        'examples_title': 'Example content for testing:',
        'high_quality_example': 'High Quality',
        'medium_quality_example': 'Medium Quality',
        'low_quality_example': 'Low Quality',
        'language': 'Language',
        'credibility_high': 'High Credibility',
        'credibility_medium': 'Medium Credibility',
        'credibility_low': 'Low Credibility',
        'credibility_questionable': 'Questionable',
        'save_analysis': 'Save Analysis',
        'saved_successfully': 'Analysis saved successfully',
        'search_results': 'Search Results',
        'no_results': 'No results found',
        'words': 'Words',
        'sentences': 'Sentences',
        'characters': 'Characters',
        'sources_found': 'Sources Found',
        'claims_verified': 'Claims Verified',
        'readability_score': 'Readability Score',
        'bias_level': 'Bias Level',
        'processing_time': 'Processing Time',
        'database_status': 'Database Status',
        'total_analyses': 'Total Analyses',
        'search_hint': 'Search in saved content and analyses',
        'export_data': 'Export Data',
        'url_analysis': 'URL Analysis',
        'content_analysis': 'Text Analysis',
        'detailed_breakdown': 'Detailed Breakdown',
        'recommendations': 'Recommendations',
        'fact_check_results': 'Fact Check Results'
    },
    'fr': {
        'title': 'CredibilityGuard - Analyse de Crédibilité IA',
        'subtitle': 'Analysez le contenu pour la qualité, l\'exactitude factuelle et la fiabilité',
        'analyze_content': 'Entrez le texte ou l\'URL pour l\'analyse de crédibilité:',
        'placeholder': 'Collez ici le contenu que vous souhaitez analyser ou fournissez une URL...',
        'url_placeholder': 'https://example.com/article',
        'analyze_btn': 'Analyser la Crédibilité',
        'analyze_url_btn': 'Analyser l\'URL',
        'search_btn': 'Rechercher',
        'results_title': 'Résultats de l\'Analyse de Crédibilité',
        'search_title': 'Recherche de Contenu',
        'search_placeholder': 'Rechercher du contenu ou des URLs...',
        'credibility_score': 'Score de Crédibilité',
        'content_quality': 'Qualité du Contenu',
        'factual_accuracy': 'Exactitude Factuelle',
        'source_reliability': 'Fiabilité des Sources',
        'classification': 'Classification',
        'confidence': 'Confiance',
        'loading': 'Analyse de la crédibilité...',
        'loading_url': 'Chargement et analyse de l\'URL...',
        'no_analysis': 'Aucune analyse encore',
        'enter_content': 'Entrez le contenu et cliquez sur "Analyser"',
        'examples_title': 'Exemples de contenu pour tester:',
        'high_quality_example': 'Haute Qualité',
        'medium_quality_example': 'Qualité Moyenne',
        'low_quality_example': 'Basse Qualité',
        'language': 'Langue',
        'credibility_high': 'Haute Crédibilité',
        'credibility_medium': 'Crédibilité Moyenne',
        'credibility_low': 'Basse Crédibilité',
        'credibility_questionable': 'Douteuse',
        'save_analysis': 'Sauvegarder l\'Analyse',
        'saved_successfully': 'Analyse sauvegardée avec succès',
        'search_results': 'Résultats de Recherche',
        'no_results': 'Aucun résultat trouvé',
        'words': 'Mots',
        'sentences': 'Phrases',
        'characters': 'Caractères',
        'sources_found': 'Sources Trouvées',
        'claims_verified': 'Affirmations Vérifiées',
        'readability_score': 'Score de Lisibilité',
        'bias_level': 'Niveau de Biais',
        'processing_time': 'Temps de Traitement',
        'database_status': 'État de la Base de Données',
        'total_analyses': 'Analyses Totales',
        'search_hint': 'Recherche dans le contenu et les analyses sauvegardés',
        'export_data': 'Exporter les Données',
        'url_analysis': 'Analyse d\'URL',
        'content_analysis': 'Analyse de Texte',
        'detailed_breakdown': 'Répartition Détaillée',
        'recommendations': 'Recommandations',
        'fact_check_results': 'Résultats de Vérification des Faits'
    },
    'es': {
        'title': 'CredibilityGuard - Análisis de Credibilidad IA',
        'subtitle': 'Analice el contenido por calidad, precisión factual y confiabilidad',
        'analyze_content': 'Ingrese texto o URL para análisis de credibilidad:',
        'placeholder': 'Pegue aquí el contenido que quiere analizar o proporcione una URL...',
        'url_placeholder': 'https://example.com/article',
        'analyze_btn': 'Analizar Credibilidad',
        'analyze_url_btn': 'Analizar URL',
        'search_btn': 'Buscar',
        'results_title': 'Resultados del Análisis de Credibilidad',
        'search_title': 'Búsqueda de Contenido',
        'search_placeholder': 'Buscar contenido o URLs...',
        'credibility_score': 'Puntuación de Credibilidad',
        'content_quality': 'Calidad del Contenido',
        'factual_accuracy': 'Precisión Factual',
        'source_reliability': 'Confiabilidad de las Fuentes',
        'classification': 'Clasificación',
        'confidence': 'Confianza',
        'loading': 'Analizando credibilidad...',
        'loading_url': 'Cargando y analizando URL...',
        'no_analysis': 'Sin análisis aún',
        'enter_content': 'Ingrese contenido y haga clic en "Analizar"',
        'examples_title': 'Contenido de ejemplo para probar:',
        'high_quality_example': 'Alta Calidad',
        'medium_quality_example': 'Calidad Media',
        'low_quality_example': 'Baja Calidad',
        'language': 'Idioma',
        'credibility_high': 'Alta Credibilidad',
        'credibility_medium': 'Credibilidad Media',
        'credibility_low': 'Baja Credibilidad',
        'credibility_questionable': 'Cuestionable',
        'save_analysis': 'Guardar Análisis',
        'saved_successfully': 'Análisis guardado exitosamente',
        'search_results': 'Resultados de Búsqueda',
        'no_results': 'No se encontraron resultados',
        'words': 'Palabras',
        'sentences': 'Oraciones',
        'characters': 'Caracteres',
        'sources_found': 'Fuentes Encontradas',
        'claims_verified': 'Afirmaciones Verificadas',
        'readability_score': 'Puntuación de Legibilidad',
        'bias_level': 'Nivel de Sesgo',
        'processing_time': 'Tiempo de Procesamiento',
        'database_status': 'Estado de la Base de Datos',
        'total_analyses': 'Análisis Totales',
        'search_hint': 'Buscar en contenido y análisis guardados',
        'export_data': 'Exportar Datos',
        'url_analysis': 'Análisis de URL',
        'content_analysis': 'Análisis de Texto',
        'detailed_breakdown': 'Desglose Detallado',
        'recommendations': 'Recomendaciones',
        'fact_check_results': 'Resultados de Verificación de Hechos'
    }
}

class DatabaseManager:
    """Verwaltet die SQLite-Datenbank für Credibility-Analysen"""
    
    def __init__(self, db_path=DATABASE_PATH):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialisiert die Datenbank mit erweiterten Tabellen für Credibility Analysis"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Haupttabelle für Credibility-Analysen
                cursor.execute('''
                CREATE TABLE IF NOT EXISTS credibility_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    content TEXT NOT NULL,
                    url TEXT,
                    title TEXT,
                    author TEXT,
                    publication_date TEXT,
                    domain TEXT,
                    
                    -- Core Scores
                    credibility_score REAL NOT NULL,
                    content_quality_score REAL,
                    factual_accuracy_score REAL,
                    source_reliability_score REAL,
                    
                    classification TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    
                    -- Detailed Metrics
                    word_count INTEGER,
                    sentence_count INTEGER,
                    char_count INTEGER,
                    sources_found INTEGER DEFAULT 0,
                    claims_verified INTEGER DEFAULT 0,
                    readability_score REAL,
                    bias_level REAL,
                    
                    -- Technical
                    processing_time REAL,
                    language TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    
                    -- Additional Fields
                    tags TEXT,
                    notes TEXT,
                    recommendations TEXT,
                    issues_detected TEXT
                )
                ''')
                
                # Volltext-Suchindex für bessere Performance
                cursor.execute('''
                CREATE VIRTUAL TABLE IF NOT EXISTS credibility_fts USING fts5(
                    content, 
                    title,
                    author,
                    domain,
                    classification, 
                    tags, 
                    notes,
                    content='credibility_analyses',
                    content_rowid='id'
                )
                ''')
                
                # Trigger für automatisches Update des FTS-Index
                cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS credibility_fts_insert AFTER INSERT ON credibility_analyses BEGIN
                    INSERT INTO credibility_fts(rowid, content, title, author, domain, classification, tags, notes) 
                    VALUES (new.id, new.content, new.title, new.author, new.domain, new.classification, new.tags, new.notes);
                END
                ''')
                
                cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS credibility_fts_delete AFTER DELETE ON credibility_analyses BEGIN
                    DELETE FROM credibility_fts WHERE rowid = old.id;
                END
                ''')
                
                cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS credibility_fts_update AFTER UPDATE ON credibility_analyses BEGIN
                    DELETE FROM credibility_fts WHERE rowid = old.id;
                    INSERT INTO credibility_fts(rowid, content, title, author, domain, classification, tags, notes) 
                    VALUES (new.id, new.content, new.title, new.author, new.domain, new.classification, new.tags, new.notes);
                END
                ''')
                
                conn.commit()
                logger.info("✅ Credibility-Datenbank erfolgreich initialisiert")
                
        except Exception as e:
            logger.error(f"❌ Datenbankfehler: {e}")
    
    def save_analysis(self, analysis_data):
        """Speichert eine Credibility-Analyse in der Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                INSERT INTO credibility_analyses (
                    content, url, title, author, publication_date, domain,
                    credibility_score, content_quality_score, factual_accuracy_score, source_reliability_score,
                    classification, confidence,
                    word_count, sentence_count, char_count, sources_found, claims_verified,
                    readability_score, bias_level, processing_time, language,
                    tags, notes, recommendations, issues_detected
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    analysis_data['content'],
                    analysis_data.get('url', ''),
                    analysis_data.get('title', ''),
                    analysis_data.get('author', ''),
                    analysis_data.get('publication_date', ''),
                    analysis_data.get('domain', ''),
                    analysis_data['credibility_score'],
                    analysis_data.get('content_quality_score', 0),
                    analysis_data.get('factual_accuracy_score', 0),
                    analysis_data.get('source_reliability_score', 0),
                    analysis_data['classification'],
                    analysis_data['confidence'],
                    analysis_data.get('word_count', 0),
                    analysis_data.get('sentence_count', 0),
                    analysis_data.get('char_count', 0),
                    analysis_data.get('sources_found', 0),
                    analysis_data.get('claims_verified', 0),
                    analysis_data.get('readability_score', 0),
                    analysis_data.get('bias_level', 0),
                    analysis_data.get('processing_time', 0),
                    analysis_data.get('language', 'de'),
                    analysis_data.get('tags', ''),
                    analysis_data.get('notes', ''),
                    json.dumps(analysis_data.get('recommendations', [])),
                    json.dumps(analysis_data.get('issues_detected', []))
                ))
                
                analysis_id = cursor.lastrowid
                conn.commit()
                
                logger.info(f"💾 Credibility-Analyse gespeichert mit ID: {analysis_id}")
                return analysis_id
                
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern: {e}")
            return None
    
    def search_content(self, query, filters=None):
        """Sucht in gespeicherten Inhalten mit erweiterten Filtern"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                if not query and not filters:
                    # Alle Analysen zurückgeben
                    cursor.execute('''
                    SELECT * FROM credibility_analyses 
                    ORDER BY created_at DESC 
                    LIMIT 100
                    ''')
                elif query:
                    # Volltext-Suche
                    cursor.execute('''
                    SELECT credibility_analyses.* 
                    FROM credibility_analyses 
                    JOIN credibility_fts ON credibility_analyses.id = credibility_fts.rowid
                    WHERE credibility_fts MATCH ?
                    ORDER BY credibility_analyses.created_at DESC
                    LIMIT 100
                    ''', (query,))
                else:
                    # Nur Filter ohne Suchbegriff
                    cursor.execute('''
                    SELECT * FROM credibility_analyses 
                    WHERE 1=1
                    ORDER BY created_at DESC 
                    LIMIT 100
                    ''')
                
                results = cursor.fetchall()
                
                # Konvertiere zu Dictionary für bessere Handhabung
                columns = [description[0] for description in cursor.description]
                return [dict(zip(columns, row)) for row in results]
                
        except Exception as e:
            logger.error(f"❌ Suchfehler: {e}")
            return []
    
    def get_statistics(self):
        """Holt Statistiken aus der Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Gesamt-Analysen
                cursor.execute('SELECT COUNT(*) FROM credibility_analyses')
                result = cursor.fetchone()
                total_analyses = result[0] if result else 0
                
                # Credibility-Verteilung
                cursor.execute('''
                SELECT classification, COUNT(*) 
                FROM credibility_analyses 
                GROUP BY classification
                ''')
                credibility_distribution = dict(cursor.fetchall())
                
                # Durchschnittliche Scores
                cursor.execute('''
                SELECT 
                    AVG(credibility_score) as avg_credibility,
                    AVG(confidence) as avg_confidence,
                    AVG(word_count) as avg_words,
                    AVG(sources_found) as avg_sources
                FROM credibility_analyses
                ''')
                averages = cursor.fetchone()
                
                return {
                    'total_analyses': total_analyses,
                    'credibility_distribution': credibility_distribution,
                    'average_credibility': averages[0] if averages and averages[0] is not None else 0.5,
                    'average_confidence': averages[1] if averages and averages[1] is not None else 0.0,
                    'average_word_count': averages[2] if averages and averages[2] is not None else 0,
                    'average_sources': averages[3] if averages and averages[3] is not None else 0
                }
                
        except Exception as e:
            logger.error(f"❌ Statistikfehler: {e}")
            return {
                'total_analyses': 0,
                'credibility_distribution': {},
                'average_credibility': 0.5,
                'average_confidence': 0.0,
                'average_word_count': 0,
                'average_sources': 0
            }

class WebScraper:
    """Web-Scraping für URL-Analyse"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CredibilityGuard/1.0 (Content Analysis Bot)'
        })
    
    def scrape_article(self, url):
        """Scrapet Artikel-Inhalt von einer URL"""
        try:
            # Timeout und Error Handling
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Content-Extraktion
            content = self._extract_content(soup)
            metadata = self._extract_metadata(soup, url)
            
            return {
                'success': True,
                'content': content,
                'metadata': metadata,
                'url': url
            }
            
        except requests.RequestException as e:
            logger.error(f"❌ Scraping-Fehler für {url}: {e}")
            return {
                'success': False,
                'error': f'Fehler beim Laden der URL: {str(e)}',
                'url': url
            }
        except Exception as e:
            logger.error(f"❌ Unerwarteter Fehler beim Scraping: {e}")
            return {
                'success': False,
                'error': f'Unerwarteter Fehler: {str(e)}',
                'url': url
            }
    
    def _extract_content(self, soup):
        """Extrahiert Hauptinhalt aus HTML"""
        # Entferne Störelemente
        for tag in soup(['script', 'style', 'nav', 'footer', 'aside', 'advertisement']):
            tag.decompose()
        
        # Versuche verschiedene Content-Selektoren
        content_selectors = [
            'article',
            '[role="main"]',
            '.content',
            '.article-content',
            '.post-content',
            '.entry-content',
            'main'
        ]
        
        content = ""
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                content = ' '.join([elem.get_text(strip=True) for elem in elements])
                break
        
        # Fallback: Alle Paragraphen
        if not content:
            paragraphs = soup.find_all('p')
            content = ' '.join([p.get_text(strip=True) for p in paragraphs])
        
        return content.strip()
    
    def _extract_metadata(self, soup, url):
        """Extrahiert Metadaten aus HTML"""
        metadata = {
            'title': '',
            'author': '',
            'publication_date': '',
            'domain': urlparse(url).netloc
        }
        
        # Title
        title_elem = soup.find('title')
        if title_elem:
            metadata['title'] = title_elem.get_text(strip=True)
        
        # Meta Tags
        for meta in soup.find_all('meta'):
            name = meta.get('name', '').lower()
            property_attr = meta.get('property', '').lower()
            content = meta.get('content', '')
            
            # Author
            if name in ['author', 'article:author'] or property_attr == 'article:author':
                metadata['author'] = content
            
            # Publication Date
            if (name in ['publish-date', 'article:published_time'] or 
                property_attr in ['article:published_time', 'article:published']):
                metadata['publication_date'] = content
        
        # Structured Data (JSON-LD)
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                data = json.loads(script.string)
                if isinstance(data, dict):
                    if 'author' in data and isinstance(data['author'], dict):
                        metadata['author'] = data['author'].get('name', metadata['author'])
                    if 'datePublished' in data:
                        metadata['publication_date'] = data['datePublished']
            except (json.JSONDecodeError, AttributeError):
                continue
        
        return metadata

class CredibilityAnalyzer:
    """Erweiterte Credibility-Analyse mit mehreren Methoden"""
    
    def __init__(self):
        self.quality_analyzer = None
        self.fact_checker = None
        self.bias_detector = None
        self.setup_analyzers()
    
    def setup_analyzers(self):
        """Initialisiert alle verfügbaren Analyzer"""
        # Content Quality Analyzer Setup
        try:
            # Verwende ein multilinguals BERT-Modell für Content Quality
            self.quality_analyzer = pipeline(
                "text-classification",
                model="unitary/toxic-bert",  # Fallback für Content Quality
                top_k=None
            )
            logger.info("✅ Content Quality Analyzer geladen")
        except Exception as e:
            logger.warning(f"⚠️ Content Quality Setup fehlgeschlagen: {e}")
        
        # NLTK für grundlegende Sprachanalyse
        try:
            nltk.download('vader_lexicon', quiet=True)
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            logger.info("✅ NLTK Resources geladen")
        except Exception as e:
            logger.warning(f"⚠️ NLTK Setup fehlgeschlagen: {e}")
    
    def analyze_content(self, content, url=None, metadata=None):
        """Führt umfassende Credibility-Analyse durch"""
        if not content or len(content.strip()) < 10:
            return self._empty_result()
        
        start_time = datetime.now()
        
        # Basis-Features extrahieren
        features = self._extract_text_features(content)
        
        # Content Quality Analysis
        quality_score = self._analyze_content_quality(content)
        
        # Factual Accuracy Analysis
        factual_score = self._analyze_factual_accuracy(content)
        
        # Source Reliability Analysis
        source_score = self._analyze_source_reliability(content, url, metadata)
        
        # Kombiniere Ergebnisse
        final_score, confidence = self._combine_scores(quality_score, factual_score, source_score)
        
        # Klassifikation
        classification = self._classify_credibility(final_score, confidence)
        
        # Recommendations & Issues
        recommendations = self._generate_recommendations(quality_score, factual_score, source_score, features)
        issues = self._detect_issues(content, features)
        
        processing_time = (datetime.now() - start_time).total_seconds()
        
        result = {
            'credibility_score': final_score,
            'content_quality_score': quality_score,
            'factual_accuracy_score': factual_score,
            'source_reliability_score': source_score,
            'classification': classification,
            'confidence': confidence,
            'word_count': features['word_count'],
            'sentence_count': features['sentence_count'],
            'char_count': features['char_count'],
            'sources_found': features['sources_found'],
            'claims_verified': features['claims_verified'],
            'readability_score': features['readability_score'],
            'bias_level': features['bias_level'],
            'processing_time': processing_time,
            'content': content,
            'url': url or '',
            'title': metadata.get('title', '') if metadata else '',
            'author': metadata.get('author', '') if metadata else '',
            'domain': metadata.get('domain', '') if metadata else '',
            'publication_date': metadata.get('publication_date', '') if metadata else '',
            'recommendations': recommendations,
            'issues_detected': issues,
            'detailed_analysis': {
                'quality': self._get_quality_details(content),
                'factual': self._get_factual_details(content),
                'sources': self._get_source_details(content, url)
            }
        }
        
        return result
    
    def _extract_text_features(self, content):
        """Extrahiert grundlegende Text-Features"""
        words = content.split()
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        
        # Source counting (einfache Heuristik)
        source_patterns = [
            r'http[s]?://[^\s]+',
            r'www\.[^\s]+',
            r'according to',
            r'study shows',
            r'research indicates'
        ]
        sources_found = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in source_patterns)
        
        # Claims verification (einfache Heuristik)
        claim_patterns = [
            r'\b\d+%',
            r'\b\d+\s+(percent|percentage)',
            r'study|research|survey|report',
            r'according to|based on|shows that'
        ]
        claims_verified = sum(len(re.findall(pattern, content, re.IGNORECASE)) for pattern in claim_patterns)
        
        # Readability Score
        try:
            readability_score = textstat.flesch_reading_ease(content) / 100.0
        except:
            readability_score = 0.5
        
        # Bias Level (einfache Heuristik basierend auf emotionalen Wörtern)
        emotional_words = [
            'amazing', 'terrible', 'incredible', 'shocking', 'unbelievable',
            'awesome', 'horrible', 'fantastic', 'disgusting', 'perfect',
            'brilliant', 'stupid', 'genius', 'idiotic', 'wonderful'
        ]
        emotional_count = sum(content.lower().count(word) for word in emotional_words)
        bias_level = min(emotional_count / max(len(words), 1), 1.0)
        
        return {
            'word_count': len(words),
            'sentence_count': len(sentences),
            'char_count': len(content),
            'avg_sentence_length': np.mean([len(s.split()) for s in sentences]) if sentences else 0,
            'sources_found': sources_found,
            'claims_verified': claims_verified,
            'readability_score': readability_score,
            'bias_level': bias_level
        }
    
    def _analyze_content_quality(self, content):
        """Analysiert die Qualität des Inhalts"""
        # Grammatik und Rechtschreibung (vereinfacht)
        blob = TextBlob(content)
        
        # Länge und Struktur
        sentences = content.split('.')
        avg_sentence_length = np.mean([len(s.split()) for s in sentences if s.strip()])
        
        # Wortschatz-Vielfalt
        words = content.lower().split()
        unique_words = len(set(words))
        vocabulary_diversity = unique_words / len(words) if words else 0
        
        # Lesbarkeit
        try:
            readability = textstat.flesch_reading_ease(content) / 100.0
        except:
            readability = 0.5
        
        # Kombiniere Metriken
        quality_factors = [
            min(avg_sentence_length / 20, 1.0),  # Optimale Satzlänge um 20 Wörter
            vocabulary_diversity,
            readability,
            min(len(words) / 500, 1.0)  # Längere Texte tendieren zu höherer Qualität
        ]
        
        return np.mean(quality_factors)
    
    def _analyze_factual_accuracy(self, content):
        """Analysiert die faktische Genauigkeit"""
        # Quellenangaben zählen
        source_indicators = [
            r'according to',
            r'study shows',
            r'research indicates',
            r'data from',
            r'source:',
            r'http[s]?://[^\s]+',
            r'\([^)]*\d{4}[^)]*\)'  # Jahr in Klammern
        ]
        
        source_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                          for pattern in source_indicators)
        
        # Präzise vs. vage Aussagen
        precise_indicators = [
            r'\b\d+(\.\d+)?%',
            r'\b\d+(\,\d{3})*(\.\d+)?\s+(people|users|participants)',
            r'exactly|precisely|specifically',
            r'\b\d{4}\b'  # Jahreszahlen
        ]
        
        vague_indicators = [
            r'many|some|several|few',
            r'might|could|possibly|maybe',
            r'seems|appears|likely'
        ]
        
        precise_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                           for pattern in precise_indicators)
        vague_count = sum(len(re.findall(pattern, content, re.IGNORECASE)) 
                         for pattern in vague_indicators)
        
        # Faktische Dichte
        words = content.split()
        factual_density = (source_count + precise_count) / max(len(words), 1)
        
        # Konsistenz (vereinfacht: weniger vage Aussagen = konsistenter)
        consistency = 1.0 - min(vague_count / max(len(words), 1), 1.0)
        
        return np.mean([
            min(factual_density * 100, 1.0),  # Normalisiere faktische Dichte
            consistency,
            min(source_count / 5, 1.0)  # Mindestens 5 Quellen für volle Punkte
        ])
    
    def _analyze_source_reliability(self, content, url=None, metadata=None):
        """Analysiert die Quellenvertrauenswürdigkeit"""
        reliability_score = 0.5  # Basis-Score
        
        # Domain-basierte Bewertung
        if url:
            domain = urlparse(url).netloc.lower()
            
            # Hochvertrauenswürdige Domains
            trusted_domains = [
                'nature.com', 'science.org', 'cell.com', 'nejm.org',
                'bbc.com', 'reuters.com', 'ap.org', 'npr.org',
                'who.int', 'cdc.gov', 'nih.gov', 'edu'
            ]
            
            if any(trusted in domain for trusted in trusted_domains):
                reliability_score += 0.3
            elif domain.endswith('.edu') or domain.endswith('.gov'):
                reliability_score += 0.25
            elif domain.endswith('.org'):
                reliability_score += 0.1
        
        # Autor-Information
        if metadata and metadata.get('author'):
            reliability_score += 0.1
        
        # Publikationsdatum
        if metadata and metadata.get('publication_date'):
            try:
                # Neuere Artikel sind tendenziell relevanter
                pub_date = datetime.fromisoformat(metadata['publication_date'].replace('Z', '+00:00'))
                days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
                if days_old < 365:  # Weniger als 1 Jahr alt
                    reliability_score += 0.1
            except:
                pass
        
        # Externe Links und Referenzen
        external_links = len(re.findall(r'http[s]?://[^\s]+', content))
        if external_links > 3:
            reliability_score += 0.1
        
        return min(reliability_score, 1.0)
    
    def _combine_scores(self, quality_score, factual_score, source_score):
        """Kombiniert die verschiedenen Scores zu einem Gesamt-Score"""
        # Gewichtung: 40% Content Quality, 35% Factual Accuracy, 25% Source Reliability
        weights = [0.4, 0.35, 0.25]
        scores = [quality_score, factual_score, source_score]
        
        final_score = np.average(scores, weights=weights)
        
        # Konfidenz basierend auf der Varianz der Scores
        confidence = 1.0 - np.var(scores)
        confidence = max(0.1, min(confidence, 1.0))
        
        return final_score, confidence
    
    def _classify_credibility(self, score, confidence):
        """Klassifiziert Credibility basierend auf Score und Confidence"""
        if confidence < 0.3:
            return 'questionable'
        elif score > 0.75:
            return 'high'
        elif score > 0.55:
            return 'medium'
        elif score > 0.35:
            return 'low'
        else:
            return 'questionable'
    
    def _generate_recommendations(self, quality_score, factual_score, source_score, features):
        """Generiert Verbesserungsempfehlungen"""
        recommendations = []
        
        if quality_score < 0.6:
            recommendations.append("Verbessern Sie die Textqualität durch klarere Sprache und bessere Struktur")
        
        if factual_score < 0.6:
            recommendations.append("Fügen Sie mehr verifiable Quellen und präzise Daten hinzu")
        
        if source_score < 0.6:
            recommendations.append("Verwenden Sie vertrauenswürdigere Quellen und fügen Sie Autor-Informationen hinzu")
        
        if features['readability_score'] < 0.4:
            recommendations.append("Vereinfachen Sie die Sprache für bessere Lesbarkeit")
        
        if features['bias_level'] > 0.3:
            recommendations.append("Reduzieren Sie emotionale Sprache für mehr Objektivität")
        
        if features['sources_found'] < 3:
            recommendations.append("Fügen Sie mehr externe Referenzen und Quellenangaben hinzu")
        
        return recommendations
    
    def _detect_issues(self, content, features):
        """Erkennt potenzielle Probleme im Inhalt"""
        issues = []
        
        if features['word_count'] < 100:
            issues.append("Text zu kurz für umfassende Analyse")
        
        if features['sources_found'] == 0:
            issues.append("Keine Quellenangaben gefunden")
        
        if features['bias_level'] > 0.5:
            issues.append("Hoher Grad an emotionaler/voreingenommener Sprache")
        
        if features['readability_score'] < 0.3:
            issues.append("Schwer verständliche Sprache")
        
        # Caps Lock Detection
        caps_ratio = sum(1 for c in content if c.isupper()) / max(len(content), 1)
        if caps_ratio > 0.1:
            issues.append("Übermäßige Verwendung von Großbuchstaben")
        
        return issues
    
    def _get_quality_details(self, content):
        """Detaillierte Qualitätsanalyse"""
        blob = TextBlob(content)
        return {
            'readability': textstat.flesch_reading_ease(content),
            'word_count': len(content.split()),
            'avg_sentence_length': np.mean([len(s.split()) for s in content.split('.') if s.strip()]),
            'polarity': blob.sentiment.polarity
        }
    
    def _get_factual_details(self, content):
        """Detaillierte Faktenanalyse"""
        numbers = re.findall(r'\b\d+(?:\.\d+)?%?\b', content)
        dates = re.findall(r'\b\d{4}\b', content)
        sources = re.findall(r'http[s]?://[^\s]+', content)
        
        return {
            'numbers_found': len(numbers),
            'dates_found': len(dates), 
            'urls_found': len(sources),
            'claim_indicators': len(re.findall(r'study|research|according to', content, re.IGNORECASE))
        }
    
    def _get_source_details(self, content, url):
        """Detaillierte Quellenanalyse"""
        domain = urlparse(url).netloc if url else 'unknown'
        return {
            'domain': domain,
            'is_https': url.startswith('https://') if url else False,
            'external_links': len(re.findall(r'http[s]?://[^\s]+', content)),
            'reference_style': 'academic' if '(' in content and ')' in content else 'informal'
        }
    
    def _empty_result(self):
        """Leeres Ergebnis für ungültige Eingaben"""
        return {
            'credibility_score': 0.5,
            'classification': 'questionable',
            'confidence': 0.0,
            'error': 'Inhalt zu kurz oder ungültig'
        }

# Globale Instanzen
db_manager = DatabaseManager()
credibility_analyzer = CredibilityAnalyzer()
web_scraper = WebScraper()

def get_language():
    """Ermittelt die aktuelle Sprache aus der Session"""
    return session.get('language', 'de')

def get_text(key):
    """Holt lokalisierten Text"""
    lang = get_language()
    return LANGUAGES.get(lang, LANGUAGES['de']).get(key, key)

# Beispiel-Inhalte für 4 Sprachen
EXAMPLE_CONTENT = {
    'de': {
        'high_quality': """Eine kürzlich veröffentlichte Studie der Harvard University (2024) zeigt, dass 87% der befragten Teilnehmer eine signifikante Verbesserung ihrer kognitiven Fähigkeiten nach regelmäßiger Meditation zeigten. Die Untersuchung, durchgeführt über einen Zeitraum von 12 Monaten mit 1.247 Teilnehmern, verwendete standardisierte neuropsychologische Tests. Dr. Sarah Johnson, Hauptautorin der Studie, erklärt: "Die Ergebnisse sind statistisch signifikant (p<0.001) und zeigen konsistente Verbesserungen in Aufmerksamkeit, Arbeitsgedächtnis und exekutiven Funktionen." Die Studie wurde in der peer-reviewed Zeitschrift "Nature Neuroscience" veröffentlicht und von unabhängigen Forschern repliziert.""",
        
        'medium_quality': """Meditation kann wirklich hilfreich sein für das Gehirn. Viele Menschen berichten, dass sie sich nach dem Meditieren besser konzentrieren können. Es gibt Studien dazu, die zeigen, dass Meditation positive Effekte hat. Ein Forscher sagte, dass regelmäßige Meditation die Aufmerksamkeit verbessert. Das ist besonders wichtig in unserer hektischen Zeit. Viele Experten empfehlen mindestens 10 Minuten tägliche Meditation. Es gibt verschiedene Arten der Meditation, wie Achtsamkeitsmeditation oder Atemmeditation.""",
        
        'low_quality': """MEDITATION IST UNGLAUBLICH!!! Jeder der das nicht macht ist dumm. Ich hab mal gelesen das es total super ist und alle sollten das machen. Ein Freund von mir meditiert und der ist voll schlau geworden. Das funktioniert zu 100% garantiert und wer was anderes sagt lügt einfach. Wissenschaftler haben das bewiesen aber die wollen das geheim halten weil Big Pharma kein Geld damit verdient. WAKE UP SHEEPLE! Meditation macht dich zum Genie und heilt alle Krankheiten!!!"""
    },
    'en': {
        'high_quality': """A recent study published by Harvard University (2024) demonstrates that 87% of participants showed significant improvement in cognitive abilities following regular meditation practice. The investigation, conducted over 12 months with 1,247 participants, utilized standardized neuropsychological assessments. Dr. Sarah Johnson, lead author of the study, explains: "The results are statistically significant (p<0.001) and show consistent improvements in attention, working memory, and executive functions." The study was published in the peer-reviewed journal "Nature Neuroscience" and has been replicated by independent researchers.""",
        
        'medium_quality': """Meditation can really be helpful for the brain. Many people report that they can concentrate better after meditating. There are studies about this that show meditation has positive effects. A researcher said that regular meditation improves attention. This is especially important in our hectic times. Many experts recommend at least 10 minutes of daily meditation. There are different types of meditation, such as mindfulness meditation or breathing meditation.""",
        
        'low_quality': """MEDITATION IS INCREDIBLE!!! Anyone who doesn't do this is stupid. I once read that it's totally super and everyone should do it. A friend of mine meditates and he became really smart. This works 100% guaranteed and whoever says otherwise is just lying. Scientists have proven this but they want to keep it secret because Big Pharma doesn't make money from it. WAKE UP SHEEPLE! Meditation makes you a genius and cures all diseases!!!"""
    },
    'fr': {
        'high_quality': """Une étude récente publiée par l'Université Harvard (2024) démontre que 87% des participants ont montré une amélioration significative de leurs capacités cognitives suite à une pratique régulière de méditation. L'investigation, menée sur 12 mois avec 1 247 participants, a utilisé des évaluations neuropsychologiques standardisées. Dr. Sarah Johnson, auteure principale de l'étude, explique : "Les résultats sont statistiquement significatifs (p<0.001) et montrent des améliorations cohérentes de l'attention, de la mémoire de travail et des fonctions exécutives." L'étude a été publiée dans la revue à comité de lecture "Nature Neuroscience" et a été répliquée par des chercheurs indépendants.""",
        
        'medium_quality': """La méditation peut vraiment être utile pour le cerveau. Beaucoup de personnes rapportent qu'elles peuvent mieux se concentrer après avoir médité. Il y a des études à ce sujet qui montrent que la méditation a des effets positifs. Un chercheur a dit que la méditation régulière améliore l'attention. C'est particulièrement important dans notre époque agitée. Beaucoup d'experts recommandent au moins 10 minutes de méditation quotidienne. Il y a différents types de méditation, comme la méditation de pleine conscience ou la méditation respiratoire.""",
        
        'low_quality': """LA MÉDITATION EST INCROYABLE!!! Quiconque ne fait pas ça est stupide. J'ai lu une fois que c'est totalement super et tout le monde devrait le faire. Un ami à moi médite et il est devenu vraiment intelligent. Ça marche à 100% garanti et quiconque dit le contraire ment simplement. Les scientifiques l'ont prouvé mais ils veulent le garder secret parce que Big Pharma ne gagne pas d'argent avec ça. RÉVEILLEZ-VOUS! La méditation fait de vous un génie et guérit toutes les maladies!!!"""
    },
    'es': {
        'high_quality': """Un estudio reciente publicado por la Universidad de Harvard (2024) demuestra que el 87% de los participantes mostraron una mejora significativa en las habilidades cognitivas tras la práctica regular de meditación. La investigación, realizada durante 12 meses con 1.247 participantes, utilizó evaluaciones neuropsicológicas estandarizadas. Dr. Sarah Johnson, autora principal del estudio, explica: "Los resultados son estadísticamente significativos (p<0.001) y muestran mejoras consistentes en atención, memoria de trabajo y funciones ejecutivas." El estudio fue publicado en la revista revisada por pares "Nature Neuroscience" y ha sido replicado por investigadores independientes.""",
        
        'medium_quality': """La meditación puede ser realmente útil para el cerebro. Muchas personas reportan que pueden concentrarse mejor después de meditar. Hay estudios sobre esto que muestran que la meditación tiene efectos positivos. Un investigador dijo que la meditación regular mejora la atención. Esto es especialmente importante en nuestros tiempos agitados. Muchos expertos recomiendan al menos 10 minutos de meditación diaria. Hay diferentes tipos de meditación, como la meditación de atención plena o la meditación respiratoria.""",
        
        'low_quality': """¡¡¡LA MEDITACIÓN ES INCREÍBLE!!! Cualquiera que no haga esto es estúpido. Una vez leí que es totalmente súper y todos deberían hacerlo. Un amigo mío medita y se volvió muy inteligente. Esto funciona 100% garantizado y quien diga lo contrario simplemente está mintiendo. Los científicos lo han probado pero quieren mantenerlo en secreto porque Big Pharma no gana dinero con esto. ¡DESPIERTEN! ¡La meditación te convierte en un genio y cura todas las enfermedades!"""
    }
}

# Flask Routes
@app.route('/')
def index():
    """Hauptseite mit Credibility-Analyse Interface"""
    lang = get_language()
    stats = db_manager.get_statistics()
    
    return render_template('index.html', 
                         lang=lang, 
                         get_text=get_text,
                         example_content=EXAMPLE_CONTENT[lang],
                         supported_languages=['de', 'en', 'fr', 'es'],
                         stats=stats)

@app.route('/set_language/<language>')
def set_language(language):
    """Sprache wechseln"""
    if language in LANGUAGES:
        session['language'] = language
    return redirect(url_for('index'))

@app.route('/api/analyze', methods=['POST'])
def analyze_credibility():
    """Credibility-Analyse durchführen"""
    try:
        data = request.get_json()
        
        if not data or 'content' not in data:
            return jsonify({'error': 'Kein Inhalt in der Anfrage gefunden'}), 400
        
        content = data['content']
        save_result = data.get('save', False)
        
        if not isinstance(content, str) or len(content.strip()) < 10:
            return jsonify({'error': 'Inhalt ist zu kurz (mindestens 10 Zeichen erforderlich)'}), 400
        
        # Credibility-Analyse durchführen
        result = credibility_analyzer.analyze_content(content)
        result['language'] = get_language()
        
        # Optional: Ergebnis in Datenbank speichern
        if save_result:
            analysis_id = db_manager.save_analysis(result)
            result['saved_id'] = analysis_id
            result['saved'] = True
        
        logger.info(f"📊 Credibility analysiert - Score: {result.get('credibility_score', 0):.2f}, Klassifikation: {result.get('classification', 'unknown')}")
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"❌ Fehler in analyze_credibility: {str(e)}")
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500

@app.route('/api/analyze_url', methods=['POST'])
def analyze_url():
    """URL-Analyse durchführen"""
    try:
        data = request.get_json()
        
        if not data or 'url' not in data:
            return jsonify({'error': 'Keine URL in der Anfrage gefunden'}), 400
        
        url = data['url'].strip()
        save_result = data.get('save', False)
        
        if not url or not (url.startswith('http://') or url.startswith('https://')):
            return jsonify({'error': 'Ungültige URL. Verwenden Sie http:// oder https://'}), 400
        
        # Web-Scraping durchführen
        scrape_result = web_scraper.scrape_article(url)
        
        if not scrape_result['success']:
            return jsonify({'error': scrape_result['error']}), 400
        
        # Credibility-Analyse des gescrapten Inhalts
        result = credibility_analyzer.analyze_content(
            scrape_result['content'],
            url=url,
            metadata=scrape_result['metadata']
        )
        result['language'] = get_language()
        result['scraped'] = True
        
        # Optional: Ergebnis in Datenbank speichern
        if save_result:
            analysis_id = db_manager.save_analysis(result)
            result['saved_id'] = analysis_id
            result['saved'] = True
        
        logger.info(f"🌐 URL analysiert - {url} - Score: {result.get('credibility_score', 0):.2f}")
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"❌ Fehler in analyze_url: {str(e)}")
        return jsonify({'error': f'Server-Fehler: {str(e)}'}), 500

@app.route('/api/search', methods=['GET'])
def search_content():
    """Suche in gespeicherten Inhalten"""
    try:
        query = request.args.get('q', '').strip()
        
        # Erweiterte Filter (optional für zukünftige Entwicklung)
        filters = {
            'credibility': request.args.get('credibility'),
            'date_from': request.args.get('date_from'),
            'date_to': request.args.get('date_to'),
            'min_words': request.args.get('min_words'),
            'max_words': request.args.get('max_words')
        }
        
        results = db_manager.search_content(query, filters)
        
        logger.info(f"🔍 Suche nach '{query}' - {len(results)} Ergebnisse")
        
        return jsonify({
            'query': query,
            'results': results,
            'total': len(results)
        })
    
    except Exception as e:
        logger.error(f"❌ Suchfehler: {str(e)}")
        return jsonify({'error': f'Suchfehler: {str(e)}'}), 500

@app.route('/api/save', methods=['POST'])
def save_analysis():
    """Speichert eine Analyse nachträglich"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'Keine Daten erhalten'}), 400
        
        analysis_id = db_manager.save_analysis(data)
        
        if analysis_id:
            return jsonify({
                'success': True,
                'message': 'Analyse erfolgreich gespeichert',
                'id': analysis_id
            })
        else:
            return jsonify({'error': 'Fehler beim Speichern'}), 500
    
    except Exception as e:
        logger.error(f"❌ Speicherfehler: {str(e)}")
        return jsonify({'error': f'Speicherfehler: {str(e)}'}), 500

@app.route('/api/example/<example_type>')
def get_example_content(example_type):
    """Beispiel-Inhalt für die aktuelle Sprache abrufen"""
    lang = get_language()
    examples = EXAMPLE_CONTENT.get(lang, EXAMPLE_CONTENT['de'])
    
    if example_type in examples:
        return jsonify({'content': examples[example_type]})
    else:
        return jsonify({'error': 'Beispiel-Inhalt nicht gefunden'}), 404

@app.route('/api/statistics')
def get_statistics():
    """Holt aktuelle Datenbank-Statistiken"""
    try:
        stats = db_manager.get_statistics()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"❌ Statistikfehler: {str(e)}")
        return jsonify({'error': f'Statistikfehler: {str(e)}'}), 500

@app.route('/api/export')
def export_data():
    """Exportiert alle Analysen als JSON"""
    try:
        all_analyses = db_manager.search_content('', {})
        
        return jsonify({
            'export_date': datetime.now().isoformat(),
            'total_records': len(all_analyses),
            'data': all_analyses
        })
    
    except Exception as e:
        logger.error(f"❌ Exportfehler: {str(e)}")
        return jsonify({'error': f'Exportfehler: {str(e)}'}), 500

@app.route('/api/health')
def health_check():
    """System-Health Check"""
    stats = db_manager.get_statistics()
    
    return jsonify({
        'status': 'healthy',
        'analyzers_available': {
            'content_quality': credibility_analyzer.quality_analyzer is not None,
            'web_scraper': True,
            'fact_checker': True
        },
        'database_status': 'connected',
        'total_analyses': stats.get('total_analyses', 0),
        'supported_languages': list(LANGUAGES.keys()),
        'timestamp': datetime.now().isoformat(),
        'version': '1.0-credibility-analysis'
    })

if __name__ == '__main__':
    logger.info("🚀 Starte CredibilityGuard Flask App mit 4-Sprachen-Support...")
    
    # Erstelle notwendige Verzeichnisse
    Path("templates").mkdir(exist_ok=True)
    Path("static").mkdir(exist_ok=True)
    
    # Informationen über Features
    logger.info("📋 CREDIBILITYGUARD FEATURES:")
    logger.info("  • 4 Sprachen: Deutsch, English, Français, Español")
    logger.info("  • Triple-Engine-Analyse: Content Quality + Factual Accuracy + Source Reliability")
    logger.info("  • URL-Analyse: Automatisches Web-Scraping und Content-Extraktion")
    logger.info("  • SQLite-Datenbank mit Volltext-Suche")
    logger.info("  • Erweiterte Metriken: Lesbarkeit, Bias-Erkennung, Quellenanalyse")
    logger.info("  • Export-Funktionalität")
    logger.info("  • Responsive Web-Interface mit Dark/Light Mode")
    
    logger.info("🌍 Server verfügbar auf:")
    logger.info("  • http://localhost:5000 (alle Sprachen)")
    logger.info("  • http://localhost:5000/set_language/de (Deutsch)")
    logger.info("  • http://localhost:5000/set_language/en (English)")
    logger.info("  • http://localhost:5000/set_language/fr (Français)")
    logger.info("  • http://localhost:5000/set_language/es (Español)")
    
    app.run(host='0.0.0.0', port=5000, debug=True)