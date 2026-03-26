"""
RotaMax — Otimizador de Rotas de Entrega
Streamlit + Claude AI + Folium + Nominatim
"""

import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import base64
import json
import math
import time
import re
import io
import requests
import hashlib
import os
import random
import difflib
import numpy as np
from sklearn.cluster import DBSCAN, KMeans
from urllib.parse import quote
from typing import Optional
from pdf2image import convert_from_bytes
from dotenv import load_dotenv
from PIL import Image, ImageStat, ExifTags
from folium.plugins import Draw, Fullscreen, LocateControl
from streamlit_js_eval import get_geolocation
import sqlite3
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RotaMax · Otimizador de Entregas",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded",
)

load_dotenv()  # Carrega variaveis do arquivo .env

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=DM+Sans:wght@300;400;500;600&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Dark background */
.stApp { background: #0a0e1a; }
section[data-testid="stSidebar"] { background: #111827 !important; border-right: 1px solid #1e2d45; }

/* Header */
.rota-header {
    background: linear-gradient(135deg, #111827 0%, #1a2235 100%);
    border: 1px solid #1e2d45;
    border-radius: 14px;
    padding: 24px 28px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 16px;
}
.rota-logo {
    font-family: 'Space Mono', monospace;
    font-size: 2.2rem;
    font-weight: 700;
    color: #00e5a0;
    letter-spacing: -1px;
    line-height: 1;
}
.rota-logo span { color: #00b8ff; }
.rota-tag {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    color: #5a7090;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-top: 4px;
}

/* Cards */
.info-card {
    background: #141e30;
    border: 1px solid #1e2d45;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
}
.card-title {
    font-family: 'Space Mono', monospace;
    font-size: 0.65rem;
    color: #00e5a0;
    letter-spacing: 3px;
    text-transform: uppercase;
    margin-bottom: 10px;
}
.card-title::before { content: '// '; color: #5a7090; }

/* Stop items */
.stop-item {
    background: #1a2235;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 14px 16px;
    margin-bottom: 10px;
}
.stop-badge {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 26px; height: 26px;
    border-radius: 50%;
    background: #00e5a0;
    color: #000;
    font-family: 'Space Mono', monospace;
    font-size: 0.72rem;
    font-weight: 700;
    margin-right: 10px;
}
.stop-badge.cluster { background: #00b8ff; }
.stop-name { font-weight: 600; color: #e8edf5; font-size: 0.9rem; }
.stop-meta { font-family: 'Space Mono', monospace; font-size: 0.7rem; color: #5a7090; margin-top: 3px; }
.addr-sub { font-size: 0.78rem; color: #5a7090; padding: 4px 8px; background: #0a0e1a; border-radius: 5px; margin-top: 5px; }
.addr-sub::before { content: '→ '; color: #00b8ff; }

/* Summary metrics */
.metric-box {
    background: #141e30;
    border: 1px solid #1e2d45;
    border-radius: 10px;
    padding: 14px 18px;
    text-align: center;
}
.metric-val {
    font-family: 'Space Mono', monospace;
    font-size: 1.6rem;
    font-weight: 700;
    color: #00e5a0;
}
.metric-lbl {
    font-size: 0.68rem;
    color: #5a7090;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 2px;
}

/* Buttons */
.stButton > button {
    font-family: 'Space Mono', monospace !important;
    font-weight: 700 !important;
    letter-spacing: 1px !important;
    border-radius: 8px !important;
    transition: all 0.2s !important;
}
.stButton > button:hover { transform: translateY(-1px); }

/* Address list in sidebar */
.addr-pill {
    background: #1a2235;
    border: 1px solid #1e2d45;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 0.78rem;
    color: #e8edf5;
    margin-bottom: 5px;
    display: flex;
    align-items: center;
    gap: 6px;
}
.addr-dot { width:8px; height:8px; border-radius:50%; background:#00b8ff; flex-shrink:0; }

/* Status banner */
.status-ok {
    background: #001a0f; border: 1px solid #00e5a0; border-radius: 8px;
    padding: 10px 16px; color: #00e5a0;
    font-family: 'Space Mono', monospace; font-size: 0.78rem;
    margin: 8px 0;
}
.status-info {
    background: #001020; border: 1px solid #00b8ff; border-radius: 8px;
    padding: 10px 16px; color: #00b8ff;
    font-family: 'Space Mono', monospace; font-size: 0.78rem;
    margin: 8px 0;
}
.status-warn {
    background: #1a0a00; border: 1px solid #ff6b35; border-radius: 8px;
    padding: 10px 16px; color: #ff6b35;
    font-family: 'Space Mono', monospace; font-size: 0.78rem;
    margin: 8px 0;
}

/* Divider */
hr { border-color: #1e2d45 !important; }

/* Tables */
.dataframe { background: #141e30 !important; color: #e8edf5 !important; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INIT
# ─────────────────────────────────────────────────────────────────────────────
for key, default in {
    "addresses": [],
    "stops": [],
    "origin_coords": None,
    "origin_label": "",
    "geocoded_points": [],
    "route_ready": False,
    "average_urban_speed_kmh": 25, # Nova entrada para velocidade média urbana
    "_osrm_distance_cache": {}, # Cache em memória para distâncias OSRM
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ─────────────────────────────────────────────────────────────────────────────
# DATABASE (SQLite)
# ─────────────────────────────────────────────────────────────────────────────
DB_FILE = "rotas.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS routes
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT,
                  timestamp TEXT,
                  data TEXT)''')
    conn.commit()
    conn.close()

def save_route_db(name: str, state_data: dict):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO routes (name, timestamp, data) VALUES (?, ?, ?)",
              (name, ts, json.dumps(state_data)))
    conn.commit()
    conn.close()

def get_saved_routes():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT id, name, timestamp FROM routes ORDER BY id DESC")
    rows = c.fetchall()
    conn.close()
    return rows

def delete_route_db(route_id: int):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("DELETE FROM routes WHERE id=?", (route_id,))
    conn.commit()
    conn.close()

def load_route_db(route_id: int) -> Optional[dict]:
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT data FROM routes WHERE id=?", (route_id,))
    row = c.fetchone()
    conn.close()
    return json.loads(row[0]) if row else None

# ─────────────────────────────────────────────────────────────────────────────
# OSRM DISTANCE CACHE
# ─────────────────────────────────────────────────────────────────────────────
OSRM_DISTANCE_CACHE_FILE = "osrm_distance_cache.json"

def load_osrm_distance_cache() -> dict:
    if not os.path.exists(OSRM_DISTANCE_CACHE_FILE):
        return {}
    try:
        with open(OSRM_DISTANCE_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_osrm_distance_cache(new_data: dict):
    """Atualiza o cache persistente de distâncias OSRM."""
    cache = load_osrm_distance_cache()
    cache.update(new_data)
    try:
        with open(OSRM_DISTANCE_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar cache de distâncias OSRM: {e}")


init_db()

# ─────────────────────────────────────────────────────────────────────────────
# SETTINGS & AI TEST UTILS
# ─────────────────────────────────────────────────────────────────────────────
SETTINGS_FILE = "ai_settings.json"

def load_ai_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_ai_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return True
    except:
        return False

def test_ai_connection(provider, key, model, host=""):
    try:
        if provider == "Claude":
            if not key: return False, "Chave vazia"
            r = requests.post("https://api.anthropic.com/v1/messages", 
                headers={"x-api-key": key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                json={"model": model, "max_tokens": 5, "messages": [{"role": "user", "content": "Hi"}]}, timeout=8)
            return (True, "OK") if r.status_code == 200 else (False, f"Erro {r.status_code}")
        elif provider == "Gemini":
            if not key: return False, "Chave vazia"
            r = requests.post(f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}",
                headers={"Content-Type": "application/json"},
                json={"contents": [{"parts": [{"text": "Hi"}]}]}, timeout=8)
            return (True, "OK") if r.status_code == 200 else (False, f"Erro {r.status_code}")
        elif provider == "Ollama":
            r = requests.post(f"{host.rstrip('/')}/api/generate", 
                json={"model": model, "prompt": "Hi", "stream": False}, timeout=5)
            return (True, "OK") if r.status_code == 200 else (False, f"Erro {r.status_code}")
    except Exception as e:
        return False, str(e)
    return False, "Provedor inválido"

# ─────────────────────────────────────────────────────────────────────────────
# ALGORITHMS
# ─────────────────────────────────────────────────────────────────────────────

def haversine_m(a: dict, b: dict) -> float:
    """Distance in metres between two {lat, lng} dicts."""
    R = 6_371_000
    dlat = math.radians(b["lat"] - a["lat"])
    dlng = math.radians(b["lng"] - a["lng"])
    x = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(a["lat"])) * math.cos(math.radians(b["lat"]))
         * math.sin(dlng / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(x), math.sqrt(1 - x))

def get_osrm_distance_value(c1: dict, c2: dict, use_cache: bool = True) -> float:
    """
    Retorna distância de direção em metros entre duas coordenadas via OSRM.
    Retorna haversine como fallback em caso de falha da API.
    """
    # Cria uma chave de cache consistente, independente da ordem de c1 e c2
    coords_key = tuple(sorted([(c1['lat'], c1['lng']), (c2['lat'], c2['lng'])]))
    
    if use_cache and coords_key in st.session_state._osrm_distance_cache:
        return st.session_state._osrm_distance_cache[coords_key]

    url = f"http://router.project-osrm.org/route/v1/driving/{c1['lng']},{c1['lat']};{c2['lng']},{c2['lat']}?overview=false"
    try:
        r = requests.get(url, timeout=2)
        if r.status_code == 200:
            data = r.json()
            if "routes" in data and len(data["routes"]) > 0:
                distance = float(data["routes"][0]["distance"])
                if use_cache:
                    st.session_state._osrm_distance_cache[coords_key] = distance
                    # Salva no disco a cada X novas entradas ou a cada Y minutos para evitar I/O excessivo
                    # Por simplicidade, vamos salvar a cada nova entrada por enquanto.
                    save_osrm_distance_cache({str(coords_key): distance})
                return distance
    except:
        pass
    return haversine_m(c1, c2)

def get_street_info(addr: str):
    """Extrai (nome_rua_normalizado, numero) para comparação lógica."""
    # Regex para pegar "Rua Nome, 123" ou "Rua Nome, nº 123"
    match = re.search(r'^([^,]+),\s*(?:nº|num|number)?\s*(\d+)', addr, re.IGNORECASE)
    if match:
        return match.group(1).strip().lower(), int(match.group(2))
    return None, None

def cluster_points(points: list, threshold_m: float = 100.0) -> list:
    """
    Group points within `threshold_m` metres together.
    Returns list of clusters, each with 'centroid', 'members', 'is_cluster'.
    """
    visited = [False] * len(points)
    clusters = []

    for i in range(len(points)):
        if visited[i]:
            continue
        group = [i]
        visited[i] = True
        street_i, num_i = get_street_info(points[i]["address"])

        for j in range(i + 1, len(points)):
            if not visited[j] and haversine_m(points[i]["coords"], points[j]["coords"]) <= threshold_m:
                # Regra de Negócio: Se for mesma rua e diferença numérica > 100, não agrupa
                street_j, num_j = get_street_info(points[j]["address"])
                if street_i and street_j and street_i == street_j and num_i is not None and num_j is not None and abs(num_i - num_j) > 100:
                    continue
                
                # Regra de Trânsito (OSRM):
                # Se a distância de carro for muito maior que o raio (ex: barreira física, contorno longo), não agrupa.
                # Tolerância: 3x o raio linear (ex: raio 100m -> aceita até 300m de direção)
                dist_drive = get_osrm_distance_value(points[i]["coords"], points[j]["coords"])
                if dist_drive > (threshold_m * 3.0):
                    continue

                group.append(j)
                visited[j] = True
        avg_lat = sum(points[k]["coords"]["lat"] for k in group) / len(group)
        avg_lng = sum(points[k]["coords"]["lng"] for k in group) / len(group)
        clusters.append({
            "centroid": {"lat": avg_lat, "lng": avg_lng},
            "members": [points[k] for k in group],
            "is_cluster": len(group) > 1,
        })
    return clusters

def cluster_points_dbscan(points: list, eps_m: float = 100.0, min_samples: int = 2) -> list:
    """
    Agrupamento baseado em densidade (DBSCAN) com matriz de distância customizada.
    Respeita a regra de numeração de rua (>100).
    """
    n = len(points)
    if n == 0: return []

    # Pre-computa informações de rua
    street_infos = [get_street_info(p["address"]) for p in points]
    
    # Constrói matriz de distância
    dist_matrix = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = haversine_m(points[i]["coords"], points[j]["coords"])
            
            # Aplica penalidade se violar regra de numeração de rua
            s_i, n_i = street_infos[i]
            s_j, n_j = street_infos[j]
            if s_i and s_j and s_i == s_j and n_i is not None and n_j is not None and abs(n_i - n_j) > 100:
                d = 1e6 # Infinito

            dist_matrix[i, j] = dist_matrix[j, i] = d

    # Executa DBSCAN
    db = DBSCAN(eps=eps_m, min_samples=min_samples, metric='precomputed')
    labels = db.fit_predict(dist_matrix)
    
    clusters = []
    unique_labels = set(labels)
    for lbl in unique_labels:
        if lbl == -1:
            # Ruído (Noise) -> vira cluster individual
            noise_indices = [i for i, x in enumerate(labels) if x == -1]
            for idx in noise_indices:
                clusters.append({
                    "centroid": points[idx]["coords"],
                    "members": [points[idx]],
                    "is_cluster": False
                })
        else:
            indices = [i for i, x in enumerate(labels) if x == lbl]
            group = [points[i] for i in indices]
            
            avg_lat = sum(p["coords"]["lat"] for p in group) / len(group)
            avg_lng = sum(p["coords"]["lng"] for p in group) / len(group)
            
            clusters.append({
                "centroid": {"lat": avg_lat, "lng": avg_lng},
                "members": group,
                "is_cluster": len(group) > 1
            })
    return clusters

def cluster_points_kmeans(points: list, k: int) -> list:
    """Agrupamento K-Means simples baseado em coordenadas."""
    if not points: return []
    if k > len(points): k = len(points)
    
    X = np.array([[p["coords"]["lat"], p["coords"]["lng"]] for p in points])
    kmeans = KMeans(n_clusters=k, n_init=10)
    labels = kmeans.fit_predict(X)
    
    clusters = []
    for lbl in range(k):
        indices = [i for i, x in enumerate(labels) if x == lbl]
        if not indices: continue
        group = [points[i] for i in indices]
        center = kmeans.cluster_centers_[lbl]
        clusters.append({
            "centroid": {"lat": center[0], "lng": center[1]},
            "members": group,
            "is_cluster": len(group) > 1
        })
    return clusters

def solve_tsp_nn(origin: dict, clusters: list, use_osrm: bool = False) -> list:
    """
    Heurística do Vizinho Mais Próximo para o TSP.
    Melhoria: Usa Haversine por padrão para evitar milhares de chamadas de API (lento).
    """
    remaining = list(range(len(clusters)))
    route = []
    current = origin
    dist_fn = get_osrm_distance_value if use_osrm else haversine_m

    while remaining:
        nearest_idx = min(remaining, key=lambda i: dist_fn(current, clusters[i]["centroid"]))
        route.append(clusters[nearest_idx])
        current = clusters[nearest_idx]["centroid"]
        remaining.remove(nearest_idx)
    return route

def total_distance_km(origin: dict, stops: list) -> float:
    dist = 0.0
    prev = origin
    for s in stops:
        dist += haversine_m(prev, s["centroid"])
        prev = s["centroid"]
    
    # Se o TSP foi desativado, a distância OSRM é usada para o cálculo total
    if not st.session_state.use_tsp:
        dist = get_osrm_distance_value(origin, stops[0]["centroid"]) + sum(get_osrm_distance_value(stops[i]["centroid"], stops[i+1]["centroid"]) for i in range(len(stops)-1))
    return dist / 1000 # Retorna em KM

def get_cargo_zone(stop_idx: int) -> str:
    """Define a zona de carregamento baseada na ordem de entrega (Lógica do car_load.py)."""
    if 1 <= stop_idx <= 8: return "Banco Carona"
    elif 9 <= stop_idx <= 20: return "Banco Traseiro"
    elif 21 <= stop_idx <= 34: return "Porta-malas (Meio)"
    else: return "Porta-malas (Fundo)"

def expand_multi_addresses(raw_list: list[str]) -> list[str]:
    """
    Separa endereços que contêm múltiplos números no final.
    Ex: 'Rua Manoel Vilar, 22, 103' -> ['Rua Manoel Vilar, 22', 'Rua Manoel Vilar, 103']
    """
    expanded = []
    for addr in raw_list:
        parts = [p.strip() for p in addr.split(",")]
        
        # Identifica partes numéricas no final da string
        digit_parts = []
        i = len(parts) - 1
        while i > 0:
            if parts[i].isdigit():
                digit_parts.append(parts[i])
                i -= 1
            else:
                break
        
        # Se houver 2 ou mais números e houver texto antes deles
        if len(digit_parts) >= 2 and i >= 0:
            base = ", ".join(parts[:i+1])
            for d in reversed(digit_parts):
                expanded.append(f"{base}, {d}")
        else:
            expanded.append(addr)
    return expanded

def check_image_issues(file_bytes: bytes) -> list[str]:
    """
    Analisa a imagem em busca de problemas comuns antes de enviar para a IA.
    Verifica Orientação EXIF e Contraste/Nitidez básico.
    """
    issues = []
    try:
        img = Image.open(io.BytesIO(file_bytes))
        
        # 1. Verificação de Orientação EXIF (Cabeça para baixo/lado)
        # Tag 274 é Orientation. Valores comuns: 3 (180deg), 6 (90deg CW), 8 (90deg CCW)
        if hasattr(img, 'getexif'):
            exif = img.getexif()
            orientation = exif.get(274)
            if orientation and orientation in [3, 6, 8]:
                issues.append("A imagem possui rotação EXIF (pode estar virada/cabeça para baixo). A IA pode não ler corretamente.")

        # 2. Verificação de Contraste/Nitidez (Variância simplificada)
        # Converte para escala de cinza e calcula variância dos pixels
        gray = img.convert("L")
        stat = ImageStat.Stat(gray)
        variance = stat.var[0]
        
        if variance < 100:
            issues.append("A imagem parece ter baixo contraste, estar muito escura ou borrada.")
            
    except Exception:
        pass
    return issues

def optimize_image(image_bytes: bytes, max_size: int = 1024, quality: int = 75) -> bytes:
    """
    Redimensiona e otimiza imagens para reduzir uso de memória (celular) e payload de API.
    Converte para JPEG e limita dimensão máxima.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # Converte para RGB (remove canal Alpha de PNGs para salvar como JPEG)
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            
        out_buf = io.BytesIO()
        img.save(out_buf, format="JPEG", quality=quality, optimize=True)
        return out_buf.getvalue()
    except Exception:
        return image_bytes

# ─────────────────────────────────────────────────────────────────────────────
# GEOCODING (Nominatim – free)
# ─────────────────────────────────────────────────────────────────────────────

def geocode(address: str, context: str = "") -> Optional[dict]:
    """
    Geocodifica um endereço. Tenta primeiro o endereço exato.
    Tenta variações de formatação (hífen vs vírgula).
    Se falhar o número, tenta buscar apenas a rua (approx).
    Retorna também o tipo de match: 'exact' ou 'context'.
    """
    clean_addr = address.strip().strip(",.-")
    url = "https://nominatim.openstreetmap.org/search"
    headers = {"Accept-Language": "pt-BR", "User-Agent": "RotaMax/1.0"}

    def fetch(q):
        try:
            r = requests.get(url, params={"q": q, "format": "json", "limit": 1}, headers=headers, timeout=10)
            return r.json() if r.status_code == 200 else []
        except:
            return []

    # Lista de tentativas: (query, type)
    attempts = []

    # 1. Endereço formatado com vírgula (melhor para Nominatim) se tiver hífen
    if " - " in clean_addr:
        attempts.append((clean_addr.replace(" - ", ", "), "exact"))

    # 2. Exata (como veio)
    attempts.append((clean_addr, "exact"))

    # 3. Tentativa com Limpeza (Rua, Número) + Contexto
    # Regex: Captura inicio até o primeiro numero após virgula
    match = re.search(r'^(.+?,\s*(?:\d+|s/?n))', clean_addr, re.IGNORECASE)
    if match:
        street_number = match.group(1) # "Rua X, 123"
        
        # Define contexto: parametro ou extraido do sufixo
        search_ctx = context
        if not search_ctx and " - " in clean_addr:
            parts = clean_addr.split(" - ")
            if len(parts) > 1:
                search_ctx = parts[-1].strip() # "Juiz de Fora"
        
        q_struct = f"{street_number}, {search_ctx}" if search_ctx else street_number
        attempts.append((q_struct, "exact"))

        # 4. Fallback: Apenas Rua + Contexto (sem número) -> approx
        if "," in street_number:
            street_only = street_number.rsplit(",", 1)[0].strip()
            q_approx = f"{street_only}, {search_ctx}" if search_ctx else street_only
            attempts.append((q_approx, "approx"))

    # Executa tentativas em ordem
    seen = set()
    for q, q_type in attempts:
        if q in seen: continue
        seen.add(q)
        
        data = fetch(q)
        if data:
            return {
                "lat": float(data[0]["lat"]),
                "lng": float(data[0]["lon"]),
                "display": data[0]["display_name"],
                "type": q_type
            }

    return None

def geocode_reverse(lat_data, long_data) -> Optional[dict]:
    """
    Geocodifica um endereço. Tenta primeiro o endereço exato.
    Tenta variações de formatação (hífen vs vírgula).
    Se falhar o número, tenta buscar apenas a rua (approx).
    Retorna também o tipo de match: 'exact' ou 'context'.
    """
    #clean_addr = address.strip().strip(",.-")
    url = f"https://nominatim.openstreetmap.org/reverse?format=geocodejson&lat={lat_data}&lon={long_data}&zoom=18&addressdetails=1&layer=address"
    headers = {"Accept-Language": "pt-BR", "User-Agent": "RotaMax/1.0"}


    try:
        r = requests.get(url, params={"limit": 1}, headers=headers, timeout=10)
        return r.json() if r.status_code == 200 else None
    except:
        return None


# ─────────────────────────────────────────────────────────────────────────────
# GEMINI AI — EXTRACT ADDRESSES FROM IMAGE
# ─────────────────────────────────────────────────────────────────────────────
def normalize_address(addr: str) -> str:
    addr = addr.strip()

    # Remove complementos comuns
    addr = re.split(
        r",\s*(apto|apartamento|bloco|edif[ií]cio|edificio|apt\.?|bl\.?|fundos|loja).*",
        addr,
        flags=re.IGNORECASE
    )[0]

    # Remove "Casa" quando não tem número relevante
    addr = re.sub(r",\s*Casa\s*$", "", addr, flags=re.IGNORECASE)

    # Mantém "Casa 02" se tiver número
    addr = re.sub(r",\s*Casa\s+(\d+).*", r", Casa \1", addr, flags=re.IGNORECASE)

    # Remove qualquer sobra depois disso
    addr = addr.strip().rstrip(",")

    # Garante formato final
    # Verifica se já possui Juiz de Fora para evitar duplicação
    if "juiz de fora" not in addr.lower():
        return f"{addr}, Juiz de Fora"
    
    return addr


def process_json_response(text: str) -> list[str]:
    """
    Processa o texto JSON retornado pelas IAs:
    1. Remove blocos de código markdown
    2. Faz o parse do JSON
    3. Extrai e normaliza a lista de endereços
    """
    text = re.sub(r"```json|```", "", text).strip()
    
    try:
        data = json.loads(text)
        return data.get("enderecos", [])
    except json.JSONDecodeError:
        return []

def extract_addresses_from_image_gemini(image_bytes: bytes, media_type: str, api_key: str, model: str) -> list[str]:
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "contents": [{
            "parts": [
                {"text": (
                        "Extraia TODOS os endereços postais desta imagem.\n"
                        "Retorne SOMENTE rua e número.\n"
                        "Remova qualquer complemento como: apartamento, apto, bloco, edifício, fundos, loja.\n"
                        "Exemplo:\n"
                        "Entrada: Rua X, 123, Apto 202\n"
                        "Saída: Rua X, 123\n\n"
                        "Se houver 'Casa' com número (ex: Casa 02), mantenha.\n"
                        "Adicione ' , Juiz de Fora' ao final de cada endereço.\n\n"
                        "Retorne no formato JSON:\n"
                        "{\"enderecos\": [\"endereço 1\", \"endereço 2\"]}\n"
                        "NÃO inclua texto fora do JSON."
                    )},
                {
                    "inline_data": {
                        "mime_type": media_type,
                        "data": b64
                    }
                }
            ]
        }]
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    resp = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        json=payload,
        timeout=30,
    )
    
    if resp.status_code != 200:
        error_msg = resp.text
        try:
            error_json = resp.json()
            if "error" in error_json:
                error_msg = error_json["error"].get("message", error_msg)
        except:
            pass
        raise Exception(f"Erro Gemini ({resp.status_code}): {error_msg}")

    resp.raise_for_status()
    try:
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return process_json_response(text)
    except Exception as e:
        raise Exception(f"Erro ao processar resposta do Gemini: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# CLAUDE AI — EXTRACT ADDRESSES FROM IMAGE
# ─────────────────────────────────────────────────────────────────────────────

def extract_addresses_from_image(image_bytes: bytes, media_type: str, api_key: str, model: str) -> list[str]:
    b64 = base64.b64encode(image_bytes).decode()
    payload = {
        "model": model,
        "max_tokens": 1024,
        "messages": [{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": media_type, "data": b64}},
                {"type": "text", "text": (
                    "Extraia TODOS os endereços postais desta imagem. "
                    "Retorne SOMENTE um JSON válido no formato: "
                    '{\"enderecos\": [\"endereço 1\", \"endereço 2\"]}. '
                    "Inclua rua, número, bairro e cidade quando visíveis. "
                    "Se não houver endereços, retorne {\"enderecos\": []}. "
                    "NÃO inclua texto fora do JSON."
                )},
            ],
        }],
    }
    resp = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    text = resp.json()["content"][0]["text"]
    return process_json_response(text)

# ─────────────────────────────────────────────────────────────────────────────
# OLLAMA (LOCAL) — EXTRACT ADDRESSES FROM IMAGE
# ─────────────────────────────────────────────────────────────────────────────

def extract_addresses_from_image_ollama(image_bytes: bytes, media_type: str, model: str, host: str) -> list[str]:
    b64 = base64.b64encode(image_bytes).decode()
    
    payload = {
        "model": model,
        "prompt": (
            "Extraia TODOS os endereços postais desta imagem. "
            "Retorne SOMENTE um JSON válido no formato: "
            '{"enderecos": ["endereço 1", "endereço 2"]}. '
            "Inclua rua, número, bairro e cidade quando visíveis. "
            "NÃO explique nada, apenas JSON."
        ),
        "images": [b64],
        "stream": False,
        "format": "json" 
    }
    
    url = f"{host.rstrip('/')}/api/generate"
    resp = requests.post(url, json=payload, timeout=60)
    
    if resp.status_code != 200:
        raise Exception(f"Erro Ollama ({resp.status_code}): {resp.text}")
        
    try:
        data = resp.json()
        text = data.get("response", "")
        return process_json_response(text)
    except Exception as e:
        raise Exception(f"Erro ao processar resposta do Ollama: {e}")



def extract_addresses_from_csv(file_bytes: bytes, filename: str) -> list[str]:
    try:
        df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding="utf-8")
    except Exception:
        df = pd.read_csv(io.BytesIO(file_bytes), sep=None, engine="python", encoding="latin-1")

    addr_keywords = ["endereco", "endereço", "address", "logradouro", "rua", "destino"]
    chosen_col = None
    for col in df.columns:
        if any(k in col.lower() for k in addr_keywords):
            chosen_col = col
            break
    if chosen_col is None:
        # Pick column with longest average string
        str_cols = df.select_dtypes(include="object").columns
        if len(str_cols) == 0:
            return []
        chosen_col = max(str_cols, key=lambda c: df[c].dropna().astype(str).str.len().mean())

    return df[chosen_col].dropna().astype(str).str.strip().tolist()

def extract_data_from_xlsx(file_bytes: bytes) -> list[dict]:
    """
    Extrai endereços e coordenadas de um arquivo Excel.
    Retorna uma lista de dicionários com chaves: address, lat, lng.
    """
    try:
        df = pd.read_excel(io.BytesIO(file_bytes))
    except Exception as e:
        st.error(f"Erro ao ler Excel: {e}")
        return []

    cols = df.columns.tolist()
    
    # Mapeamento flexível de colunas
    addr_col = next((c for c in cols if any(k in c.lower() for k in ["endereco", "endereço", "address", "rua"])), None)
    lat_col = next((c for c in cols if any(k in c.lower() for k in ["lat", "latitude"])), None)
    lng_col = next((c for c in cols if any(k in c.lower() for k in ["lng", "long", "longitude"])), None)
    info_col = next((c for c in cols if any(k in c.lower() for k in ["nome", "cliente", "pedido", "order"])), None)

    results = []
    for _, row in df.iterrows():
        addr = str(row[addr_col]).strip() if addr_col and pd.notnull(row[addr_col]) else ""
        if not addr: continue

        # Captura o metadado (ID/Nome) separadamente para não poluir a busca
        extra_info = str(row[info_col]).strip() if info_col and pd.notnull(row[info_col]) else None
        
        results.append({
            "address": normalize_address(addr),
            "lat": float(row[lat_col]) if lat_col and pd.notnull(row[lat_col]) else None,
            "lng": float(row[lng_col]) if lng_col and pd.notnull(row[lng_col]) else None,
            "extra_info": extra_info,
            "original_addr": addr
        })
    return results

# ─────────────────────────────────────────────────────────────────────────────
# LOCAL CACHE SYSTEM
# ─────────────────────────────────────────────────────────────────────────────
CACHE_FILE = "cache_addresses.json"
GEO_CACHE_FILE = "cache_geocoding.json"

def load_geo_cache() -> dict:
    if not os.path.exists(GEO_CACHE_FILE):
        return {}
    try:
        with open(GEO_CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_geo_cache(new_data: dict):
    """Atualiza o cache persistente de geocodificação."""
    cache = load_geo_cache()
    cache.update(new_data)
    try:
        with open(GEO_CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar cache de geocodificação: {e}")

def get_file_hash(file_bytes: bytes) -> str:
    """Gera um hash MD5 único para o conteúdo do arquivo."""
    return hashlib.md5(file_bytes).hexdigest()

def load_cache() -> dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_to_cache(file_hash: str, addresses: list[str]):
    cache = load_cache()
    cache[file_hash] = addresses
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro ao salvar cache: {e}")

def get_cached_addresses(file_bytes: bytes) -> Optional[list[str]]:
    h = get_file_hash(file_bytes)
    cache = load_cache()
    return cache.get(h)

# ─────────────────────────────────────────────────────────────────────────────
# AUTOSAVE SYSTEM (SESSION PERSISTENCE)
# ─────────────────────────────────────────────────────────────────────────────
AUTOSAVE_FILE = "rotamax_autosave.json"

def autosave_session():
    """Salva o estado crítico da sessão em disco para recuperação."""
    timestamp = time.time()
    state_dump = {
        "addresses": st.session_state.addresses,
        "stops": st.session_state.stops,
        "origin_coords": st.session_state.origin_coords,
        "origin_label": st.session_state.origin_label,
        "geocoded_points": st.session_state.geocoded_points,
        "route_ready": st.session_state.route_ready,
        "timestamp": timestamp
    }    
    try:
        with open(AUTOSAVE_FILE, 'w', encoding='utf-8') as f:
            json.dump(state_dump, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Erro no autosave: {e}")

def load_autosave():
    """Carrega o estado salvo."""
    if os.path.exists(AUTOSAVE_FILE):
        try:
            with open(AUTOSAVE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Verificação de timestamp
                if "timestamp" in data and (time.time() - data["timestamp"]) < 3600:  # Validade de 1 hora (3600 segundos)
                    for k, v in data.items():
                        st.session_state[k] = v
        except Exception as e:
            print(f"Erro ao carregar autosave: {e}")
            os.remove(AUTOSAVE_FILE)

# ─────────────────────────────────────────────────────────────────────────────
# FOLIUM MAP
# ─────────────────────────────────────────────────────────────────────────────

def get_osrm_route(coordinates: list) -> Optional[dict]:
    """
    Obtém a geometria da rota via OSRM para desenhar nas ruas.
    coordinates: lista de tuplas (lat, lon).
    """
    if len(coordinates) < 2:
        return None
    
    # OSRM espera "lon,lat"
    locs = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
    url = f"http://router.project-osrm.org/route/v1/driving/{locs}?overview=full&geometries=geojson"
    
    try:
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            if "routes" in data and len(data["routes"]) > 0:
                return data["routes"][0]["geometry"]
    except:
        pass
    return None

def build_map(origin: dict, stops: list) -> folium.Map:
    center = [origin["lat"], origin["lng"]]
    m = folium.Map(location=center, zoom_start=13, tiles="cartodbpositron")

    # Origin
    folium.Marker(
        location=[origin["lat"], origin["lng"]],
        popup=folium.Popup("<b>🏠 Partida</b>", max_width=200),
        tooltip=f"Partida: {origin.get('label', 'Inicio')}",
        icon=folium.Icon(color="black", icon="home", prefix="fa"),
        z_index_offset=1000
    ).add_to(m)

    # Route line
    route_coords = [(origin["lat"], origin["lng"])]
    for s in stops:
        route_coords.append((s["centroid"]["lat"], s["centroid"]["lng"]))
    
    # Tenta rota via ruas (OSRM), senão fallback para linha reta
    route_geometry = get_osrm_route(route_coords)
    
    if route_geometry:
        folium.GeoJson(route_geometry, name="Rota (Vias)", style_function=lambda x: {"color": "#00e5a0", "weight": 4, "opacity": 0.8}).add_to(m)
    else:
        folium.PolyLine(route_coords, color="#00e5a0", weight=3, opacity=0.7, dash_array="10 5").add_to(m)

    # Stop markers
    for i, stop in enumerate(stops, start=1):
        # Cor baseada no status e tipo
        if stop.get("completed", False):
            bg_color = "#6c757d" # Cinza (Concluída)
            border_color = "#343a40"
        elif stop["is_cluster"]:
            bg_color = "#00b8ff" # Azul Cluster
            border_color = "#000"
        else:
            # Se for parada unica, verifica a qualidade do geocode
            q_type = stop["members"][0].get("type", "exact")
            if q_type == "exact":
                bg_color = "#00e5a0" # Verde (Exato)
            else:
                bg_color = "#ff9f1c" # Laranja (Contexto/Aprox)
            border_color = "#000"

        # Marcadores individuais para cada endereço (Visualização "um a um")
        for member in stop["members"]:
            # Aplica jitter determinístico baseado no endereço para evitar "looping" de renderização do mapa
            seed_val = int(hashlib.md5(member["address"].encode("utf-8")).hexdigest(), 16)
            rng = random.Random(seed_val)
            lat_jit = rng.uniform(-0.0001, 0.0001)
            lng_jit = rng.uniform(-0.0001, 0.0001)
            
            extra_label = f"<b>[{member['extra_info']}]</b> " if member.get("extra_info") else ""

            folium.CircleMarker(
                location=[member["coords"]["lat"] + lat_jit, member["coords"]["lng"] + lng_jit],
                radius=4,
                color="white",
                weight=1,
                fill=True,
                fill_color=bg_color,
                fill_opacity=0.9,
                tooltip=member["address"],
                popup=folium.Popup(f"<div style='font-size:12px'>{extra_label}{member['address']}</div>", max_width=200)
            ).add_to(m)
            
            # Se for um cluster, conecta o endereço ao centróide da parada
            if stop["is_cluster"]:
                folium.PolyLine(
                    locations=[
                        (stop["centroid"]["lat"], stop["centroid"]["lng"]),
                        (member["coords"]["lat"], member["coords"]["lng"])
                    ],
                    color=bg_color, weight=1, opacity=0.5, dash_array="3 3"
                ).add_to(m)

        members_html = "".join(f"<li style='margin:2px 0;font-size:12px'>{'<b>['+str(m['extra_info'])+']</b> ' if m.get('extra_info') else ''}{m['address']}</li>" for m in stop["members"])
        popup_html = f"""
        <b>Parada {i}</b>{'  📦 Agrupada' if stop['is_cluster'] else ''}<br>
        <ul style='padding-left:14px;margin:6px 0'>{members_html}</ul>
        """
        
        # HTML Limpo para o ícone (remove quebras de linha para evitar erros de JS no Folium)
        div_html = f"""<div style="background:{bg_color};color:#000;width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;font-size:13px;border:2px solid {border_color};box-shadow:0 2px 8px #00000080;font-family:monospace;">{i}</div>"""

        folium.Marker(
            location=[stop["centroid"]["lat"], stop["centroid"]["lng"]],
            popup=folium.Popup(popup_html, max_width=280),
            tooltip=f"Parada {i} — {len(stop['members'])} endereço(s)",
            icon=folium.DivIcon(html=div_html,icon_size=(28, 28), icon_anchor=(14, 14),),
            z_index_offset=1000
        ).add_to(m)

    # Draw Control for Visual Correction
    Draw(
        export=False,
        position="topleft",
        draw_options={
            "polyline": False,
            "polygon": False,
            "circle": False,
            "rectangle": False,
            "circlemarker": False,
            "marker": True,
        },
        edit_options={"edit": False, "remove": True}
    ).add_to(m)

    # ── FULLSCREEN & GPS REAL-TIME ──
    Fullscreen(
        position="topright",
        title="Expandir para Tela Cheia",
        title_cancel="Sair da Tela Cheia",
        force_separate_button=True,
    ).add_to(m)

    LocateControl(
        auto_start=False,
        locateOptions={'enableHighAccuracy': True, 'maxZoom': 16},
        strings={"title": "Mostrar minha localização atual", "popup": "Você está aqui"},
        position="topright",
    ).add_to(m)

    # ── CAMADA DE TRÂNSITO ──
    # AVISO: O uso direto das camadas do Google viola os Termos de Serviço e pode parar de funcionar.
    # Para um ambiente de produção, é recomendado usar uma API como a do HERE Maps, que oferece um plano gratuito.
    google_traffic_url = "https://mt1.google.com/vt/lyrs=h&x={x}&y={y}&z={z}"
    folium.TileLayer(
        tiles=google_traffic_url,
        attr='Google Traffic',
        name='Trânsito em Tempo Real (Google)',
        overlay=True,
        control=True,
        show=False  # A camada começa desabilitada por padrão
    ).add_to(m)

    # Adiciona o controle que permite ligar/desligar as camadas (como a de trânsito)
    folium.LayerControl().add_to(m)

    # Fit bounds
    all_lats = [origin["lat"]] + [s["centroid"]["lat"] for s in stops]
    all_lngs = [origin["lng"]] + [s["centroid"]["lng"] for s in stops]
    m.fit_bounds([[min(all_lats), min(all_lngs)], [max(all_lats), max(all_lngs)]])
    return m


# ─────────────────────────────────────────────────────────────────────────────
# GOOGLE MAPS EXPORT URL
# ─────────────────────────────────────────────────────────────────────────────

def build_gmaps_url(origin: dict, stops: list) -> str:
    org = f"{origin['lat']},{origin['lng']}"
    waypoints = [f"{s['centroid']['lat']},{s['centroid']['lng']}" for s in stops[:9]]
    dest = f"{stops[-1]['centroid']['lat']},{stops[-1]['centroid']['lng']}" if stops else org
    parts = [org] + waypoints + [dest]
    return "https://www.google.com/maps/dir/" + "/".join(parts)

# ─────────────────────────────────────────────────────────────────────────────
# WAZE URL
# ─────────────────────────────────────────────────────────────────────────────

def build_waze_url(lat: float, lng: float) -> str:
    return f"https://www.waze.com/ul?ll={lat}%2C{lng}&navigate=yes"

# ─────────────────────────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='font-family:Space Mono,monospace;font-size:1.1rem;font-weight:700;
                color:#00e5a0;letter-spacing:-0.5px;padding:8px 0 4px;'>
        RotaMax<span style='color:#00b8ff;'>⚙</span>
    </div>
    <div style='font-size:0.65rem;color:#5a7090;letter-spacing:3px;
                text-transform:uppercase;margin-bottom:16px;'>Configurações</div>
    """, unsafe_allow_html=True)
    with st.expander("Provedor de IA", expanded=False):       
        # Carrega configurações salvas ou usa variáveis de ambiente/default
        saved_settings = load_ai_settings()
        
        default_provider_idx = ["Claude", "Gemini", "Ollama"].index(saved_settings.get("provider", "Gemini")) if saved_settings.get("provider") in ["Claude", "Gemini", "Ollama"] else 1
        provider = st.radio("Provedor IA", ["Claude", "Gemini", "Ollama"], horizontal=True, index=default_provider_idx)
        
        env_claude = saved_settings.get("claude_key", os.getenv("ANTHROPIC_API_KEY", ""))
        env_gemini = saved_settings.get("gemini_key", os.getenv("GEMINI_API_KEY", ""))
        env_ollama_host = saved_settings.get("ollama_host", os.getenv("OLLAMA_HOST", "http://localhost:11434"))
        env_ollama_model = saved_settings.get("ollama_model", os.getenv("OLLAMA_MODEL", "llava"))
        
        # Defaults de modelos para Claude/Gemini se não salvos
        def_claude_model = saved_settings.get("claude_model", "claude-3-5-sonnet-20240620")
        def_gemini_model = saved_settings.get("gemini_model", "gemini-2.0-flash")

        env_lat = float(os.getenv("DEFAULT_ORIGIN_LAT", -23.550520))
        env_lng = float(os.getenv("DEFAULT_ORIGIN_LNG", -46.633308))
        env_city_ctx = os.getenv("DEFAULT_CITY_CONTEXT", "")

        api_key = env_gemini
        selected_model = ""
        if provider == "Claude":
            api_key = st.text_input("🔑 Chave API Anthropic", type="password", help="Necessária para Claude")
            selected_model = st.text_input("Modelo Claude", value=def_claude_model)
        elif provider == "Gemini":
            api_key_input = st.text_input("🔑 Chave API Gemini", type="password", help="Necessária para Gemini")
            if api_key == "":
                api_key = env_gemini
            selected_model = st.text_input("Modelo Gemini", value=def_gemini_model)
        else:
            # Configurações Ollama
            ollama_host = st.text_input("Host Ollama", value=env_ollama_host)
            selected_model = st.text_input("Modelo (Vision)", value=env_ollama_model)

        # Botões de Teste e Salvar
        c_test, c_save = st.columns(2)
        with c_test:
            if st.button("🧪 Testar Conexão", use_container_width=True):
                ok, msg = test_ai_connection(provider, api_key, selected_model, ollama_host if provider == "Ollama" else "")
                if ok:
                    st.success(f"Sucesso: {msg}")
                else:
                    st.error(f"Falha: {msg}")
        with c_save:
            if st.button("💾 Salvar Config", use_container_width=True):
                new_settings = saved_settings.copy()
                new_settings["provider"] = provider
                if provider == "Claude":
                    #new_settings["claude_key"] = api_key
                    new_settings["claude_model"] = selected_model
                elif provider == "Gemini":
                    #new_settings["gemini_key"] = api_key
                    new_settings["gemini_model"] = selected_model
                else:
                    new_settings["ollama_host"] = ollama_host
                    new_settings["ollama_model"] = selected_model
                
                if save_ai_settings(new_settings):
                    st.toast("Configurações salvas em ai_settings.json!", icon="💾")
                else:
                    st.error("Erro ao salvar arquivo.")

    st.divider()    

    # ── ORIGIN ──────────────────────────────────────────────────────────────
    st.markdown('<div class="card-title">Cidade/Estado Padrão</div>', unsafe_allow_html=True)
    
    # Input de contexto para geocodificação
    city_context = st.text_input("Cidade/Estado Padrão", value=env_city_ctx, 
                                 help="Será adicionado aos endereços incompletos (ex: 'São Paulo, SP')")
    
    st.markdown('<div class="card-title">Geocodificação de Endereço</div>', unsafe_allow_html=True)
    origin_text = st.text_input("Geocodificar Endereço", placeholder="Digite o endereço", key="origin_input")
    if st.button("🔍 Geocodificar Endereço", width='stretch'):
        if origin_text.strip():
            with st.spinner("Geocodificando..."):
                # Usa a mesma função melhorada
                result = geocode(origin_text)
            if result:
                st.session_state.origin_coords = {"lat": result["lat"], "lng": result["lng"]}
                st.session_state.origin_label = origin_text
                st.success(f"✓ {result['lat']:.5f}, {result['lng']:.5f}")
            else:
                st.error("Endereço não encontrado.")
        else:
            st.warning("Digite o endereço.")
    st.divider()

    # ── GPS AUTOMÁTICO ──
    st.markdown('<div class="card-title">Obter minha Localização</div>', unsafe_allow_html=True)

    # Inicializa o estado dos inputs de GPS se não existirem, para evitar conflito com o `value`
    if 'lat_in' not in st.session_state:
        st.session_state.lat_in = env_lat
    if 'lng_in' not in st.session_state:
        st.session_state.lng_in = env_lng

    if st.session_state["lat_in"] and   st.session_state["lng_in"] not in st.session_state:
        geo_loc = get_geolocation(component_key='get_gps_loc')
        geo_data = geo_loc["coords"] if geo_loc else None
        geo_data_lat = geo_data["latitude"] if geo_data else None
        geo_data_lng = geo_data["longitude"] if geo_data else None
        if geo_loc:
            st.session_state["lat_in"] = geo_data_lat
            st.session_state["lng_in"] = geo_data_lng
            
        st.caption("Localização Capturada:")
        addr_geo_loc = geocode_reverse( st.session_state["lat_in"], st.session_state["lng_in"])
        if addr_geo_loc:            
            if "features" in addr_geo_loc and len(addr_geo_loc["features"]) > 0:
                properties = addr_geo_loc["features"][0].get("properties", {})
                geocoding = properties.get("geocoding", {})
                label = geocoding.get("name", "Endereço não identificado")
                bairro = geocoding.get("district", "Bairro não identificado")
                city = geocoding.get("city", "Cidade não identificada")
                state = geocoding.get("state", "Estado não identificado")
                st.write(f"📍 {label} - {bairro}")
                st.caption(f"{city} - {state}")
            else:
                st.write("Endereço não identificado")
    col_gps1, col_gps2 = st.columns([1, 1])
    with col_gps1:
        lat_in = st.number_input("Latitude", value=st.session_state.lat_in, format="%.5f", key="lat_in")
    with col_gps2:
        lng_in = st.number_input("Longitude", value=st.session_state.lng_in, format="%.5f", key="lng_in")

   
    if lat_in != 0.0 and lng_in != 0.0:
        st.session_state.origin_coords = {"lat": lat_in, "lng": lng_in}
        st.session_state.origin_label = f"GPS ({lat_in:.5f}, {lng_in:.5f})"
        st.success("Coordenadas GPS salvas!")
    else:
        st.session_state.origin_coords = None # Limpa se os valores forem inválidos
        st.warning("Preencha lat/lng válidos.")

    st.divider()

    st.markdown('<div class="card-title">Restaurar Última Sessão</div>', unsafe_allow_html=True)
    # Botão de Restaurar Sessão (se existir autosave)
    if os.path.exists(AUTOSAVE_FILE):
        if st.button("♻️ Restaurar Sessão", help="Recarrega endereços e rotas salvos automaticamente."):
            load_autosave()
            st.success("Sessão restaurada!")
            st.session_state._osrm_distance_cache = load_osrm_distance_cache() # Carrega cache OSRM
            time.sleep(1)
            st.rerun()

    # ── LIMPAR CACHE OSRM ───────────────────────────────────────────────────
    st.markdown('<div class="card-title">Manutenção</div>', unsafe_allow_html=True)
    if st.button("🗑 Limpar Cache OSRM", help="Apaga o cache de distâncias do OSRM para forçar novas consultas à API."):
        st.session_state._osrm_distance_cache = {}
        if os.path.exists(OSRM_DISTANCE_CACHE_FILE):
            os.remove(OSRM_DISTANCE_CACHE_FILE)
        st.success("Cache OSRM limpo!")
        # Recarrega o cache do disco (que agora está vazio)
        st.session_state._osrm_distance_cache = load_osrm_distance_cache()
        st.rerun()

    # ── ROTAS SALVAS (DB) ──
    st.markdown('<div class="card-title">Restaurar Rotas Salvas</div>', unsafe_allow_html=True)
    with st.expander("💾 Lista de Rotas", expanded=False):
        saved_routes = get_saved_routes()
        if saved_routes:
            for rid, rname, rtime in saved_routes:
                # Layout compacto
                c_info, c_load, c_del = st.columns([3, 1, 1])
                with c_info:
                    st.markdown(f"**{rname}**<br><span style='font-size:0.7em;color:#aaa'>{rtime}</span>", unsafe_allow_html=True)
                with c_load:
                    if st.button("📂", key=f"load_db_{rid}", help="Carregar Rota"):
                        data = load_route_db(rid)
                        if data:
                            for k, v in data.items():
                                # Não sobrescreve o cache OSRM da sessão
                                st.session_state[k] = v
                            st.success("Carregada!")
                            time.sleep(0.5)
                            st.rerun()
                with c_del:
                    if st.button("❌", key=f"del_db_{rid}", help="Apagar Rota"):
                        delete_route_db(rid)
                        st.rerun()
                st.markdown("<hr style='margin:4px 0;border-color:#333'>", unsafe_allow_html=True)
        else:
            st.info("Nenhuma rota salva.")
    
    st.divider()

    # ── CLUSTERING THRESHOLD ─────────────────────────────────────────────────
    st.markdown('<div class="card-title">Parâmetros Clusterização</div>', unsafe_allow_html=True)
    
    clustering_algo = st.selectbox("Algoritmo de Agrupamento", ["Simples (Greedy)", "DBSCAN", "K-Means"], key="clustering_algo", index=0, help="Algoritimo para junção de endereços em paradas unicas(Cluster)")

    st.session_state.use_tsp = st.checkbox("Otimizar Ordem (TSP)", value=True, help="Se marcado, calcula a melhor sequência de entrega. Se desmarcado, mantém a ordem do upload.")

    cluster_thresh = 60
    min_samples = 2
    kmeans_k = 5
    
    if clustering_algo == "Simples (Greedy)":
        cluster_thresh = st.slider("Raio de agrupamento (metros)", 25, 200, 50, 10)
    elif clustering_algo == "DBSCAN":
        cluster_thresh = st.slider("Raio (eps) metros", 25, 200, 50, 10)
        min_samples = st.slider("Mínimo de Pontos (MinPts)", 1, 5, 2)
    elif clustering_algo == "K-Means":
        # Garante que k não seja maior que o número de endereços disponíveis
        # e que seja no mínimo 1 se houver endereços.
        # Se não houver endereços, k pode ser 1 (ou 0, dependendo da lógica)
        max_k = len(st.session_state.addresses) if st.session_state.addresses else 10
        kmeans_k = st.slider("Número de Paradas (K)", 1, max(2, max_k), max(1, max_k//3))
    
    st.divider()
    with st.expander(f'Lista de Endereços ({len(st.session_state.addresses)})', expanded=False):
        # ── ADDRESS LIST ─────────────────────────────────────────────────────────
        if st.session_state.addresses:
            st.markdown(f'<div class="card-title">Endereços ({len(st.session_state.addresses)})</div>',
                        unsafe_allow_html=True)
            for i, a in enumerate(st.session_state.addresses):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.markdown(f'<div class="addr-pill"><div class="addr-dot"></div>{a[:38]}{"…" if len(a)>38 else ""}</div>',
                                unsafe_allow_html=True)
                with c2:
                    if st.button("✕", key=f"del_{i}"):
                        st.session_state.addresses.pop(i)
                        st.rerun()

            if st.button("♻ Remover Duplicatas", width='stretch'):
                seen = set()
                unique_list = []
                for addr in st.session_state.addresses:
                    # Normalização para comparação (lowercase + espaços)
                    norm = " ".join(addr.split()).lower()
                    if norm not in seen:
                        seen.add(norm)
                        unique_list.append(addr)
                st.session_state.addresses = unique_list
                st.rerun()

            if st.button("🗑 Limpar Todos", width='stretch', type="secondary"):
                st.session_state.addresses.clear()
                st.session_state.stops.clear()
                st.session_state.route_ready = False
                st.rerun()

    st.markdown('<div class="card-title">Configurações de Rota</div>', unsafe_allow_html=True)
    st.session_state.average_urban_speed_kmh = st.slider("Velocidade Média Urbana (km/h)", 10, 60, value=st.session_state.average_urban_speed_kmh, help="Usada para estimar o tempo total da rota.")
    #st.rerun()

# ─────────────────────────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────────────────────────

st.markdown("""
<div class="rota-header">
  <div>
    <div class="rota-logo">Rota<span>Max</span></div>
    <div class="rota-tag">Otimizador de Entregas · TSP + IA</div>
  </div>
</div>
""", unsafe_allow_html=True)

tab_upload, tab_route, tab_nav, tab_export = st.tabs(["📂 Upload & Extração", "🧭 Rota Otimizada", "📍 Navegação", "🗺 Exportar"])

# ═══════════════════════════════════════════════════════════════════════════
# TAB 1 — UPLOAD & EXTRACTION
# ═══════════════════════════════════════════════════════════════════════════
with tab_upload:
    st.markdown("### Upload de Arquivos")
    
    col_u1, col_u2 = st.columns([2, 1])
    with col_u1:
        uploaded = st.file_uploader(
            "Selecione arquivos (Imagens, PDF, CSV ou Excel)",
            type=["jpg", "jpeg", "png", "webp", "pdf", "csv", "xlsx"],
            accept_multiple_files=True,
            help="No celular, prefira enviar poucas imagens por vez para evitar travamentos."
        )
    with col_u2:
        camera_photo = st.camera_input("Tirar Foto")

    # Consolida as fontes de entrada
    files_to_process = []
    if uploaded:
        files_to_process.extend(uploaded)
    if camera_photo:
        files_to_process.append(camera_photo)

    if files_to_process:
        col_proc, col_clear = st.columns([1, 1])
        with col_proc:
            do_extract = st.button("⚡ Extrair Endereços", type="primary", width='stretch')
        with col_clear:
            if st.button("✕ Limpar Arquivos", width='stretch'):
                st.session_state.addresses = []
                st.rerun()

        if do_extract:
            progress = st.progress(0, text="Iniciando extração…")
            new_found = []

            for idx, f in enumerate(files_to_process):
                progress.progress((idx) / len(files_to_process), text=f"Processando {f.name}…")
                
                # Lê os bytes uma única vez
                raw = f.getvalue()
                file_hash = get_file_hash(raw)

                if f.name.lower().endswith(".csv"):
                    addrs = extract_addresses_from_csv(raw, f.name)
                    addrs_norm = [normalize_address(a) for a in addrs]
                    new_found.extend(addrs_norm)
                    st.success(f"CSV processado: {len(addrs)} endereços.")
                    del raw
                elif f.name.lower().endswith(".xlsx"):
                    data_list = extract_data_from_xlsx(raw)
                    count_coords = 0
                    for item in data_list:
                        addr = item["address"]
                        if addr not in st.session_state.addresses:
                            st.session_state.addresses.append(addr)
                            # Se já tem coordenadas, injeta direto no cache de geocodificação da sessão
                            if item["lat"] is not None and item["lng"] is not None:
                                pt_obj = {
                                    "address": addr,
                                    "coords": {"lat": item["lat"], "lng": item["lng"]},
                                    "type": "exact",
                                    "display": addr,
                                    "extra_info": item.get("extra_info")
                                }
                                st.session_state.geocoded_points.append(pt_obj)
                                count_coords += 1
                    st.success(f"Excel processado: {len(data_list)} endereços ({count_coords} com GPS).")
                    del raw # Libera memória
                else:
                    if provider != "Ollama" and not api_key:
                        st.markdown('<div class="status-warn">⚠ Chave API necessária para processar imagens.</div>',
                                    unsafe_allow_html=True)
                        continue

                    cached_res = get_cached_addresses(file_hash)
                    if cached_res is not None:
                        new_found.extend(cached_res)
                        st.markdown(f'<div class="status-ok">⚡ Cache "{f.name}" → {len(cached_res)} endereço(s)</div>',
                                    unsafe_allow_html=True)
                        time.sleep(0.1)
                        continue

                    # Processamento sequencial para economizar RAM
                    if f.name.lower().endswith(".pdf"):
                        try:
                            pil_images = convert_from_bytes(raw)
                            for p_idx, p_img in enumerate(pil_images):
                                buf = io.BytesIO()
                                p_img.save(buf, format="JPEG")
                                page_bytes = optimize_image(buf.getvalue())
                                
                                # Extração imediata por página
                                if provider == "Gemini":
                                    p_addrs = extract_addresses_from_image_gemini(page_bytes, "image/jpeg", api_key, selected_model)
                                elif provider == "Ollama":
                                    p_addrs = extract_addresses_from_image_ollama(page_bytes, "image/jpeg", selected_model, ollama_host)
                                else:
                                    p_addrs = extract_addresses_from_image(page_bytes, "image/jpeg", api_key, selected_model)
                                
                                p_final = [normalize_address(a) for a in expand_multi_addresses(p_addrs)]
                                new_found.extend(p_final)
                                del page_bytes, buf # Limpeza agressiva
                        except Exception as e:
                            st.error(f"Erro ao converter PDF {f.name}: {e}")
                    else:
                        # Otimiza imagem única
                        optimized_raw = optimize_image(raw)
                        issues = check_image_issues(raw)
                        if issues:
                            for issue in issues:
                                st.warning(f"⚠ Alerta em '{f.name}': {issue}")

                        try:
                            mime = f.type or "image/jpeg"
                            if provider == "Gemini":
                                addrs = extract_addresses_from_image_gemini(optimized_raw, mime, api_key, selected_model)
                            elif provider == "Ollama":
                                addrs = extract_addresses_from_image_ollama(optimized_raw, mime, selected_model, ollama_host)
                            else:
                                addrs = extract_addresses_from_image(optimized_raw, mime, api_key, selected_model)

                            addrs_final = [normalize_address(a) for a in expand_multi_addresses(addrs)]
                            new_found.extend(addrs_final)
                            save_to_cache(file_hash, addrs_final)
                        except Exception as e:
                            st.error(f"Erro na extração ({f.name}): {e}")
                        
                        del optimized_raw, raw # Libera memória do arquivo original e otimizado


                time.sleep(0.3)  # small delay between calls

            # Deduplicate and add
            before = len(st.session_state.addresses)
            for a in new_found:
                # Garante normalização final antes de salvar no state (cobre cache e CSV)
                a = normalize_address(a)
                if a and a not in st.session_state.addresses:
                    st.session_state.addresses.append(a)

            added = len(st.session_state.addresses) - before
            progress.progress(1.0, text="Concluído!")
            st.success(f"✓ {added} novo(s) endereço(s) adicionado(s). Total: {len(st.session_state.addresses)}")

    # Preview current list
    if st.session_state.addresses:
        st.markdown(f"---\n### Lista de Endereços ({len(st.session_state.addresses)})")
        df_preview = pd.DataFrame({"#": range(1, len(st.session_state.addresses)+1),
                                   "Endereço": st.session_state.addresses})
        st.data_editor(df_preview, width='stretch', hide_index=True, on_change=st.rerun)        
    else:
        st.markdown('<div class="status-info">ℹ Nenhum endereço ainda. Faça upload ou adicione manualmente na barra lateral.</div>',
                    unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 2 — ROUTE OPTIMIZATION
# ═══════════════════════════════════════════════════════════════════════════
with tab_route:
    col_tab_route = st.columns(3)
    with col_tab_route[0]:
        st.markdown('<div class="card-title">Geração de Roteamento</div>', unsafe_allow_html=True)
        st.space(8)
        ready_to_optimize = (
            len(st.session_state.addresses) > 0
            and st.session_state.origin_coords is not None
        )

        if not ready_to_optimize:
            missing = []
            if not st.session_state.origin_coords:
                missing.append("ponto de partida (barra lateral)")
            if not st.session_state.addresses:
                missing.append("endereços (aba Upload)")
            st.markdown(f'<div class="status-warn">⚠ Faltando: {" e ".join(missing)}.</div>',
                        unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="status-ok">✓ {len(st.session_state.addresses)} endereço(s) prontos. Clique em Otimizar.</div>',
                        unsafe_allow_html=True)
    
        if st.button("🚀 Otimizar Rota", type="primary", disabled=not ready_to_optimize):
            origin = st.session_state.origin_coords
            addrs = st.session_state.addresses

            # Step 1: geocode
            with st.spinner("Processando endereços..."):
                # Cache local da sessão anterior para evitar requests repetidos
                session_cache = {p["address"]: p for p in st.session_state.geocoded_points}
                # Cache persistente em arquivo
                file_cache = load_geo_cache()
                
                prog = st.progress(0)
                points = []
                new_cache_entries = {}

                for i, addr in enumerate(addrs):
                    # 1. Prioridade: Cache da Sessão (memória)
                    if addr in session_cache:
                        points.append(session_cache[addr])
                        prog.progress((i+1)/len(addrs), text=f"Cache Memória {i+1}/{len(addrs)}: {addr[:30]}…")
                        continue

                    # 2. Cache de Arquivo (persistente)
                    if addr in file_cache:
                        data = file_cache[addr]
                        points.append({
                            "address": addr,
                            "coords": {"lat": data["lat"], "lng": data["lng"]},
                            "type": data.get("type", "approx"),
                            "display": data.get("display")
                        })
                        prog.progress((i+1)/len(addrs), text=f"Cache Disco {i+1}/{len(addrs)}: {addr[:30]}…")
                        continue

                    # 3. Request API
                    prog.progress((i+1)/len(addrs), text=f"Geocodificando {i+1}/{len(addrs)}: {addr[:30]}…")
                    # Passa o contexto da cidade configurado na sidebar
                    coords = geocode(addr, context=city_context)
                    if coords:
                        pt_obj = {
                            "address": addr, 
                            "coords": {"lat": coords["lat"], "lng": coords["lng"]},
                            "type": coords.get("type", "approx"),
                            "display": coords.get("display")
                        }
                        points.append(pt_obj)
                        
                        # Prepara para salvar no arquivo
                        new_cache_entries[addr] = {
                            "lat": coords["lat"],
                            "lng": coords["lng"],
                            "type": coords.get("type", "approx"),
                            "display": coords.get("display")
                        }
                    else:
                        st.toast(f"Não geocodificado: {addr}", icon="⚠️", duration='infinite')
                        # Adiciona como erro para permitir edição manual posterior
                        points.append({
                            "address": addr,
                            "coords": {"lat": 0.0, "lng": 0.0},
                            "type": "error",
                            "display": "Não encontrado"
                        })
                    time.sleep(0.55)  # Nominatim rate limit
                
                # Salva novos dados no disco de uma vez
                if new_cache_entries:
                    save_geo_cache(new_cache_entries)
                    
                prog.progress(1.0)

            # Filtra apenas pontos válidos para o clustering inicial
            valid_points = [p for p in points if p.get("type") != "error"]

            if not valid_points and not points:
                st.error("Nenhum endereço pôde ser geocodificado.")
            elif not valid_points and points:
                st.warning("Todos os endereços falharam na geocodificação. Use a seção abaixo para corrigir manualmente.")
                st.session_state.geocoded_points = points
                st.session_state.stops = []
                st.session_state.route_ready = True
            else:
                # Step 2: cluster
                with st.spinner("Agrupando paradas próximas…"):
                    if clustering_algo == "DBSCAN":
                        clusters = cluster_points_dbscan(valid_points, eps_m=cluster_thresh, min_samples=min_samples)
                    elif clustering_algo == "K-Means":
                        clusters = cluster_points_kmeans(valid_points, k=kmeans_k)
                    else:
                        clusters = cluster_points(valid_points, threshold_m=cluster_thresh)

                # Step 3: TSP
                if st.session_state.use_tsp:
                    with st.spinner("Calculando rota TSP…", show_time=True):
                        ordered_stops = solve_tsp_nn(origin, clusters)
                else:
                    ordered_stops = clusters
                    st.info("Otimização TSP desativada. A ordem das paradas segue a ordem de upload.")

                st.session_state.stops = ordered_stops
                st.session_state.geocoded_points = points
                st.session_state.route_ready = True
                autosave_session() # Salva após calcular
                st.success(f"✓ Rota otimizada! {len(ordered_stops)} parada(s) para {len(points)} ponto(s).")
        
    with col_tab_route[1]:
        st.markdown('<div class="card-title">Adicionar Endereço</div>', unsafe_allow_html=True)
        # ── MANUAL ADDRESS ───────────────────────────────────────────────────────        
        manual_addr = st.text_input("Endereço", placeholder="Rua X, 123, Cidade", key="manual_input")  
        if st.button("➕ Adicionar", width='stretch'):
            v = manual_addr.strip()
            if v:
                v = normalize_address(v)
            if v and v not in st.session_state.addresses:
                st.session_state.addresses.append(v)
                st.rerun()
            else:
                st.warning("Endereço inválido.")

    with col_tab_route[2]:
        # ── SALVAR ROTA (DB) ──
        st.markdown('<div class="card-title">Salvar Rotas</div>', unsafe_allow_html=True)
        save_name_input = st.text_input("Nome da Rota para Salvar", value=f"Rota {datetime.now().strftime('%d/%m %H:%M')}")
        if st.button("💾 Salvar Rota", use_container_width=True):
                state_dump = {
                    "addresses": st.session_state.addresses,
                    "stops": st.session_state.stops,
                    "origin_coords": st.session_state.origin_coords,
                    "origin_label": st.session_state.origin_label,
                    "geocoded_points": st.session_state.geocoded_points,
                    "route_ready": st.session_state.route_ready
                }
                save_route_db(save_name_input, state_dump)
                st.toast("Rota salva no banco de dados!", icon="💾")

    col_mid_tab_route = st.columns(2)
    with col_mid_tab_route[0]:
        # ── MANUAL EDIT FOR APPROXIMATE ADDRESSES ──────────────────────────────
        if st.session_state.route_ready and st.session_state.geocoded_points:
            # Filtra pontos que não são 'exact' ou já foram editados manualmente ('manual')
            approx_points = [
                (i, p) for i, p in enumerate(st.session_state.geocoded_points) 
                if p.get("type") in ["context", "manual", "approx", "error"]
            ]
            
            if approx_points:
                with st.popover("⚠️ Ajustar Endereços (Aproximados ou Não Encontrados)", width='stretch'):
                    st.info("Abaixo estão os endereços que precisam de atenção. Corrija o nome ou insira as coordenadas.")
                    
                    # Lista de endereços válidos para sugestão (fuzzy match)
                    valid_addrs_for_fuzzy = [
                        p["address"] for p in st.session_state.geocoded_points 
                        if p.get("type") not in ["error"] and p["address"]
                    ]

                    # Formulário para edição (Endereço e Coordenadas)
                    with st.form("edit_coords_form"):
                        for i, pt in approx_points:
                            status_icon = "❌" if pt.get("type") == "error" else "⚠️"
                            c1, c2, c3 = st.columns([4, 1, 1])
                            with c1:
                                # Agora o endereço é editável
                                st.text_input(f"{status_icon} Endereço ({i})", value=pt['address'], key=f"txt_{i}")
                                if pt.get("type") == "error":
                                    st.caption("Não encontrado. Tente simplificar o endereço (ex: apenas Rua e Número).")
                                else:
                                    st.caption(f"Nominatim: {pt.get('display', 'N/A')}")
                                
                                # Sugestão de correção (Fuzzy Matching)
                                if valid_addrs_for_fuzzy:
                                    suggs = difflib.get_close_matches(pt['address'], valid_addrs_for_fuzzy, n=3, cutoff=0.6)
                                    # Remove sugestão se for igual ao próprio endereço (caso de approx)
                                    suggs = [s for s in suggs if s != pt['address']]
                                    if suggs:
                                        st.markdown(f"<div style='font-size:0.8em;color:#00b8ff;'>💡 Talvez você quis dizer: <i>{', '.join(suggs)}</i></div>", unsafe_allow_html=True)

                            with c2:
                                st.number_input(f"Lat ({i})", value=pt["coords"]["lat"], format="%.6f", key=f"lat_{i}")
                            with c3:
                                st.number_input(f"Lng ({i})", value=pt["coords"]["lng"], format="%.6f", key=f"lng_{i}")
                            st.divider()
                        
                        if st.form_submit_button("🔄 Atualizar e Recalcular Rota"):
                            needs_rerun = False
                            updates_to_save = {}
                            
                            # Atualiza geocoded_points com os valores do form
                            for i, pt in approx_points:
                                new_text = st.session_state.get(f"txt_{i}")
                                current_text = pt["address"]
                                
                                # Se o texto mudou, tenta re-geocodificar
                                if new_text and new_text != current_text:
                                    new_geo = geocode(new_text, context=city_context)
                                    if new_geo:
                                        pt["address"] = new_text
                                        pt["coords"] = {"lat": new_geo["lat"], "lng": new_geo["lng"]}
                                        pt["type"] = "manual" # Considera resolvido/manual
                                        pt["display"] = new_geo["display"]
                                        updates_to_save[new_text] = {
                                            "lat": new_geo["lat"],
                                            "lng": new_geo["lng"],
                                            "type": "manual",
                                            "display": new_geo["display"]
                                        }
                                        continue # Pula a atualização manual de lat/lng pois a geocodificação prevalece

                                # Se o texto não mudou (ou geocode falhou), pega as coords manuais dos inputs
                                man_lat = st.session_state.get(f"lat_{i}")
                                man_lng = st.session_state.get(f"lng_{i}")
                                
                                if man_lat is not None and man_lng is not None:
                                    # Verifica se houve mudança nas coordenadas
                                    if man_lat != pt["coords"]["lat"] or man_lng != pt["coords"]["lng"]:
                                        pt["coords"]["lat"] = man_lat
                                        pt["coords"]["lng"] = man_lng
                                        pt["type"] = "manual"
                                        updates_to_save[pt["address"]] = {
                                            "lat": man_lat,
                                            "lng": man_lng,
                                            "type": "manual",
                                            "display": pt.get("display")
                                        }
                            
                            # Salva correções manuais no cache persistente
                            if updates_to_save:
                                save_geo_cache(updates_to_save)
                            
                            # Recalcula Cluster e TSP (sem geocodificar tudo de novo)
                            valid_points_refresh = [p for p in st.session_state.geocoded_points if p.get("type") != "error"]
                            
                            if clustering_algo == "DBSCAN":
                                clusters = cluster_points_dbscan(valid_points_refresh, eps_m=cluster_thresh, min_samples=min_samples)
                            elif clustering_algo == "K-Means":
                                clusters = cluster_points_kmeans(valid_points_refresh, k=kmeans_k)
                            else:
                                clusters = cluster_points(valid_points_refresh, threshold_m=cluster_thresh)
                            
                            # Recalcula TSP apenas se estiver ativo
                            st.session_state.stops = solve_tsp_nn(st.session_state.origin_coords, clusters, use_osrm=not st.session_state.use_tsp)
                            autosave_session() # Salva após edição manual
                            st.rerun()
            elif approx_points: # Only show if there were points to adjust, but they are all resolved
                with st.popover("⚠️ Sem Endereços para Ajustar ", width='stretch', disabled=True):
                    pass
    with col_mid_tab_route[1]:
        # ── RESULTS ─────────────────────────────────────────────────────────────
        if st.session_state.route_ready and st.session_state.stops and st.session_state.origin_coords:
            stops = st.session_state.stops
            origin = st.session_state.origin_coords            
            # ── MANUAL REORDERING ───────────────────────────────────────────────
            with st.popover("📝 Reordenar Paradas Manualmente", width='stretch'):
                st.caption("Edite a coluna 'Ordem' para alterar a sequência.")
                
                # Prepara DataFrame para edição
                reorder_data = []
                for idx, s in enumerate(stops):
                    reorder_data.append({
                        "Ordem": idx + 1,
                        "Endereço": s["members"][0]["address"],
                        "Qtd": len(s["members"]),
                        "_original_idx": idx # Hidden index reference
                    })
                
                df_reorder = pd.DataFrame(reorder_data)
                edited_df = st.data_editor(df_reorder, hide_index=True, column_config={"_original_idx": None}, disabled=["Endereço Principal", "Qtd"], width='stretch')
                
                if st.button("🔄 Aplicar Nova Ordem"):
                    # Ordena pelo input do usuário e reconstrói a lista de stops
                    edited_df.sort_values("Ordem", inplace=True)
                    new_order_indices = edited_df["_original_idx"].tolist()
                    st.session_state.stops = [st.session_state.stops[i] for i in new_order_indices]
                    autosave_session() # Salva após reordenar
                    st.rerun()       

            # Metrics
            total_km = total_distance_km(origin, stops)
            estimated_time_hours = total_km / st.session_state.average_urban_speed_kmh
            estimated_time_minutes = estimated_time_hours * 60
            total_addr = sum(len(s["members"]) for s in stops)
            clusters_count = sum(1 for s in stops if s["is_cluster"])
            
    if st.session_state.route_ready and st.session_state.stops and st.session_state.origin_coords:
        c1, c2, c3, c4, c5 = st.columns(5)
        for col, val, lbl in zip(
            [c1, c2, c3, c4, c5],
            [len(stops), total_addr, clusters_count, f"{total_km:.1f} km", 
             f"{int(estimated_time_hours)}h {int(estimated_time_minutes % 60)}m"],
            ["Paradas", "Endereços", "Agrupamentos", "Dist. Total", "Tempo Est."],
        ):
            with col:
                st.markdown(f"""<div class="metric-box">
                    <div class="metric-val">{val}</div>
                    <div class="metric-lbl">{lbl}</div>
                </div>""", unsafe_allow_html=True)

    st.markdown("---")
    if st.session_state.route_ready and st.session_state.stops and st.session_state.origin_coords:
        # Map + Stop list side by side
        map_col, list_col = st.columns([3, 2])

        with map_col:
            st.markdown("#### 🗺 Mapa da Rota")
            st.caption("Para corrigir um local, selecione o Marcador (📍) no mapa e clique na posição correta.")
            fmap = build_map(origin, stops)
            
            # 'returned_objects' limita o que volta do frontend. 
            # Removendo zoom/bounds do retorno evita recarregamento da página ao interagir com o mapa.
            map_out = st_folium(fmap, width=None, height=480, 
                                returned_objects=["last_active_drawing"])
            
            # Handle Draw Events (Visual Correction)
            if map_out and map_out.get("last_active_drawing"):
                drawing = map_out["last_active_drawing"]
                if drawing["geometry"]["type"] == "Point":
                    new_lng, new_lat = drawing["geometry"]["coordinates"]
                    
                    # Find nearest stop to this new point
                    # We compare against the current geocoded points
                    closest_idx = -1
                    min_dist = float("inf")
                    
                    current_points = st.session_state.geocoded_points
                    for i, pt in enumerate(current_points):
                        dist = haversine_m(
                            {"lat": new_lat, "lng": new_lng}, 
                            {"lat": pt["coords"]["lat"], "lng": pt["coords"]["lng"]}
                        )
                        if dist < min_dist:
                            min_dist = dist
                            closest_idx = i
                    
                    if closest_idx != -1:
                        target = current_points[closest_idx]
                        with st.expander("📍 Confirmar Correção Visual", expanded=True):
                            st.write(f"Deseja mover **{target['address']}** para este novo local?")
                            st.write(f"Distância do original: {min_dist:.1f}m")
                            if st.button("✅ Confirmar Nova Posição"):
                                st.session_state.geocoded_points[closest_idx]["coords"] = {"lat": new_lat, "lng": new_lng}
                                st.session_state.geocoded_points[closest_idx]["type"] = "manual"
                                
                                # Salva correção visual no cache
                                addr_key = st.session_state.geocoded_points[closest_idx]["address"]
                                save_geo_cache({addr_key: {
                                    "lat": new_lat, "lng": new_lng, "type": "manual", 
                                    "display": st.session_state.geocoded_points[closest_idx].get("display")
                                }})
                                
                                # Recalcula cluster
                                if clustering_algo == "DBSCAN":
                                    new_clusters = cluster_points_dbscan(st.session_state.geocoded_points, eps_m=cluster_thresh, min_samples=min_samples)
                                elif clustering_algo == "K-Means":
                                    new_clusters = cluster_points_kmeans(st.session_state.geocoded_points, k=kmeans_k)
                                else:
                                    new_clusters = cluster_points(st.session_state.geocoded_points, threshold_m=cluster_thresh)

                                st.session_state.stops = solve_tsp_nn(st.session_state.origin_coords, new_clusters)
                                autosave_session() # Salva após correção visual
                                st.rerun()
            
            # ── EXPORT PDF BUTTON (MOVED HERE) ──
            st.markdown("---")
            if st.button("📄 Baixar Relatório PDF (HTML)", width='stretch'):
                # 1. Gera o mapa
                m_report = build_map(origin, stops)
                full_html = m_report.get_root().render()

                # 2. Constrói o HTML da lista
                rows_html = ""
                for i, stop in enumerate(stops, start=1):
                    current_zone = get_cargo_zone(i)
                    addr_items = []
                    for m in stop['members']:
                        safe_addr = quote(m['address'])
                        waze_link = f"https://waze.com/ul?ll={m['coords']['lat']}%2C{m['coords']['lng']}&navigate=yes"
                        gmaps_link = f"https://www.google.com/maps/search/?api=1&query={safe_addr}"
                        links_html = f"""<span style="margin-left:6px; font-size:0.75em;"><a href="{waze_link}" target="_blank" style="text-decoration:none; color:#333; border:1px solid #ccc; padding:0 3px; border-radius:3px;">Waze</a> <a href="{gmaps_link}" target="_blank" style="text-decoration:none; color:#333; border:1px solid #ccc; padding:0 3px; border-radius:3px;">Maps</a></span>"""
                        addr_items.append(f"<li>{m['address']}{links_html}</li>")
                    
                    addr_list = "".join(addr_items)
                    tag_color = "#00b8ff" if stop["is_cluster"] else "#00e5a0"
                    rows_html += f"""
                    <div class="stop-card">
                        <div class="stop-num" style="background: {tag_color};">{i}</div>
                        <div class="stop-content">
                            <div class="stop-title">{'📦 Agrupamento' if stop['is_cluster'] else '📍 Parada Individual'}</div>
                            <div style="font-size:0.8rem; font-weight:bold; color:#e67e22; margin-bottom:4px;">📦 Zona: {current_zone}</div>
                            <ul class="addr-ul">{addr_list}</ul>
                        </div>
                    </div>
                    """

                # Visualização do Carro
                n_stops = len(stops)
                z1_on = "active" if n_stops >= 1 else ""
                z2_on = "active" if n_stops >= 9 else ""
                z3_on = "active" if n_stops >= 21 else ""
                z4_on = "active" if n_stops >= 35 else ""
                
                car_html = f"""
                <div class="car-box">
                    <h3>🚗 Esquema de Carregamento</h3>
                    <div class="car-layout">
                        <div class="car-row"><div class="car-seat driver">Motorista</div><div class="car-seat {z1_on}"><div class="z-name">Banco Carona</div><div class="z-range">1-8</div></div></div>
                        <div class="car-row"><div class="car-seat full {z2_on}"><div class="z-name">Banco Traseiro</div><div class="z-range">9-20</div></div></div>
                        <div class="car-row trunk-area"><div class="car-seat half {z3_on}"><div class="z-name">Meio</div><div class="z-range">21-34</div></div><div class="car-seat half {z4_on}"><div class="z-name">Fundo</div><div class="z-range">35+</div></div></div>
                    </div>
                </div>
                """

                custom_content = f"""
                <div id="report-container">
                    <div class="rep-header"><h1>Relatório RotaMax</h1><p>Partida: {origin.get('label','GPS')} • Paradas: {len(stops)}</p></div>
                    {car_html}<div class="rep-list">{rows_html}</div>
                </div>
                <style>
                    html,body{{height:auto!important;overflow:visible!important;}} .folium-map{{position:relative!important;height:450px!important;width:100%!important;border-bottom:5px solid #111827;}}
                    #report-container{{padding:20px;font-family:'Segoe UI',sans-serif;background:white;color:#111;}}
                    .stop-card{{display:flex;border-bottom:1px solid #eee;padding:12px 0;page-break-inside:avoid;}}
                    .stop-num{{font-size:1.2rem;font-weight:bold;color:#fff;width:36px;height:36px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin-right:15px;flex-shrink:0;-webkit-print-color-adjust:exact;}}
                    .car-box{{margin-bottom:20px;padding:15px;background:#f9f9f9;border:1px solid #eee;border-radius:8px;page-break-inside:avoid;}}
                    .car-layout{{display:flex;flex-direction:column;gap:5px;max-width:320px;margin:0 auto;border:2px solid #555;padding:10px;background:white;}} .car-row{{display:flex;gap:5px;}} .car-seat{{flex:1;border:1px solid #ccc;background:#f0f0f0;padding:8px;text-align:center;border-radius:4px;font-size:0.8rem;}} .car-seat.active{{background:#d1fae5;border:1px solid #10b981;font-weight:bold;}}
                </style>"""
                final_html = full_html.replace("</body>", f"{custom_content}</body>")
                st.download_button("⬇ Baixar HTML", data=final_html, file_name="Relatorio.html", mime="text/html", width='stretch')

        with list_col:
            st.markdown("#### 📋 Lista de Paradas")        
            # Input opcional para cálculo de itens por parada
            stops = st.session_state.stops
            total_vols = st.number_input("Total de Volumes (Opcional)", min_value=1, value=len(stops), help="Para calcular média de itens por parada")
            items_per_stop = math.ceil(total_vols / len(stops))

            for i, stop in enumerate(stops, start=1):
                is_done = stop.get("completed", False)
                
                badge_class = "cluster" if stop["is_cluster"] else ""
                tag = "📦 Agrupada" if stop["is_cluster"] else "📍 Individual"
                if is_done:
                    tag += " (Concluída)"
                members_items = []
                for m in stop["members"]:
                    if m.get("type") in ["approx", "context"]:
                        members_items.append(f'<div class="addr-sub" style="border-left: 3px solid #ff9f1c; padding-left: 8px;">⚠️ {m["address"]} <span style="color:#ff9f1c;font-size:0.7em">(Aprox)</span></div>')
                    else:
                        members_items.append(f'<div class="addr-sub">{m["address"]}</div>')
                members_html = "".join(members_items)
                
                # Cálculo da Zona de Carga
                zone = get_cargo_zone(i)
                
                icon_status = "✅ " if is_done else ""
                with st.expander(f"{icon_status}Parada {i} — {len(stop['members'])} endereço(s) {tag}", expanded=False):
                    # Botão de Conclusão
                    btn_label = "↩ Desmarcar Entrega" if is_done else "✅ Marcar como Concluída"
                    btn_type = "secondary" if is_done else "primary"
                    if st.button(btn_label, key=f"btn_done_{i}", type=btn_type, use_container_width=True):
                        stop["completed"] = not is_done
                        autosave_session()
                        st.rerun()

                    # Botões de navegação rápida
                    lat, lng = stop['centroid']['lat'], stop['centroid']['lng']
                    col_waze, col_maps = st.columns(2)
                    with col_waze:
                        st.link_button("🚙 Waze", build_waze_url(lat, lng), use_container_width=True)
                    with col_maps:
                        st.link_button("🗺 Google Maps", f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}", use_container_width=True)

                    st.markdown(f"""<div class="info-card">
                        <div style='margin-bottom:8px; font-weight:700; color:#ff9f1c; border-bottom:1px solid #333; padding-bottom:4px;'>
                            📦 Zona: {zone} <span style='font-weight:400; color:#aaa; font-size:0.8em'>({items_per_stop} itens est.)</span>
                        </div>
                        <div style='font-size:0.75rem;color:#5a7090;font-family:Space Mono,monospace;'>
                            Lat: {stop['centroid']['lat']:.5f} | Lng: {stop['centroid']['lng']:.5f}
                        </div>
                        {members_html}
                    </div>""", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 3 — NAVEGAÇÃO
# ═══════════════════════════════════════════════════════════════════════════
with tab_nav:
    st.markdown("### 📍 Navegação Ponto a Ponto")
    
    if not st.session_state.route_ready:
        st.markdown('<div class="status-warn">⚠ Gere a rota primeiro na aba "Rota Otimizada".</div>',
                    unsafe_allow_html=True)
    else:
        stops = st.session_state.stops
        nav_tabs = st.tabs(["🚘 Lista Waze", "🗺 Lista Google Maps"])
        
        with nav_tabs[0]:
            st.caption("Clique para abrir diretamente no Waze:")
            for i, stop in enumerate(stops, start=1):
                lat, lng = stop["centroid"]["lat"], stop["centroid"]["lng"]
                main_addr = stop["members"][0]["address"]
                waze_url = build_waze_url(lat, lng)
                # Botão full width para facilitar o toque no celular
                col_tab_nav_btn = st.columns(2)
                with col_tab_nav_btn[0]:
                    st.markdown(f":yellow-background[{main_addr} ] ", width='stretch')
                with col_tab_nav_btn[1]:
                    st.link_button(f"🚀 Navegar | Parada: {i}", waze_url, width='stretch')
        
        with nav_tabs[1]:
            st.caption("Clique para abrir navegação no Google Maps:")
            for i, stop in enumerate(stops, start=1):
                lat, lng = stop["centroid"]["lat"], stop["centroid"]["lng"]
                main_addr = stop["members"][0]["address"]
                gmaps_url = f"https://www.google.com/maps/dir/?api=1&destination={lat},{lng}"
                st.link_button(f"📍 Parada {i} | {main_addr}", gmaps_url, use_container_width=True)


# ═══════════════════════════════════════════════════════════════════════════
# TAB 4 — EXPORT
# ═══════════════════════════════════════════════════════════════════════════
with tab_export:
    st.markdown("### Exportar Rota")

    if not st.session_state.route_ready:
        st.markdown('<div class="status-warn">⚠ Gere a rota primeiro na aba "Rota Otimizada".</div>',
                    unsafe_allow_html=True)
    else:
        stops = st.session_state.stops
        origin = st.session_state.origin_coords

        # ── CHART: LOAD DISTRIBUTION ──────────────────────────────────────
        st.markdown("#### 📊 Distribuição de Carga")
        
        # Prepara dados para o gráfico
        zone_stats = []
        for i, stop in enumerate(stops, start=1):
            z = get_cargo_zone(i)
            # Conta itens (membros) nesta parada
            zone_stats.append({"Zona": z, "Volumes": len(stop["members"])})
        
        if zone_stats:
            df_zones = pd.DataFrame(zone_stats)
            # Agrupa e soma volumes por zona
            df_chart = df_zones.groupby("Zona")["Volumes"].sum().reset_index()
            
            # Ordem lógica das zonas para o eixo X
            zone_order = ["Banco Carona", "Banco Traseiro", "Porta-malas (Meio)", "Porta-malas (Fundo)"]
            
            st.bar_chart(df_chart, x="Zona", y="Volumes", color="Zona", width='stretch')

        # Cria abas internas para organizar a exportação
        exp_tabs = st.tabs(["🗺 Google Maps (Rota)", "💾 CSV/JSON"])

        # ── TAB: GOOGLE MAPS ──────────────────────────────────────────────
        with exp_tabs[0]:
            st.markdown("#### Rota Sequencial")
            gmaps_url = build_gmaps_url(origin, stops)
            st.info("Google Maps suporta até 10 waypoints no link direto. Paradas excedentes serão ignoradas na prévia, mas estão completas nos arquivos.")
            st.link_button("🗺 Abrir no Google Maps", gmaps_url, width='stretch', type="primary")
            st.text_area("Link direto", gmaps_url, height=70)

        # ── TAB: CSV / JSON ───────────────────────────────────────────────
        with exp_tabs[1]:
            st.markdown("#### Arquivos de Dados")
            
            # Preparar dados CSV
            rows = []
            for i, stop in enumerate(stops, start=1):
                for m in stop["members"]:
                    rows.append({
                        "Parada": i,
                        "Tipo": "Agrupada" if stop["is_cluster"] else "Individual",
                        "Endereço": m["address"],
                        "Lat": stop["centroid"]["lat"],
                        "Lng": stop["centroid"]["lng"],
                        "Link Waze": build_waze_url(stop["centroid"]["lat"], stop["centroid"]["lng"])
                    })
            df_export = pd.DataFrame(rows)
            csv_bytes = df_export.to_csv(index=False).encode("utf-8")

            # Preparar JSON
            pins = []
            for i, stop in enumerate(stops, start=1):
                pins.append({
                    "pin": i,
                    "lat": stop["centroid"]["lat"],
                    "lng": stop["centroid"]["lng"],
                    "type": "cluster" if stop["is_cluster"] else "single",
                    "addresses": [m["address"] for m in stop["members"]],
                })
            json_bytes = json.dumps({"origin": origin, "stops": pins}, ensure_ascii=False, indent=2).encode("utf-8")

            c1, c2 = st.columns(2)
            with c1:
                st.download_button("⬇ Baixar Planilha (.csv)", data=csv_bytes,
                                file_name="rotamax_rota.csv", mime="text/csv", width='stretch')
            with c2:
                st.download_button("⬇ Baixar JSON (.json)", data=json_bytes,
                                file_name="rotamax_pins.json", mime="application/json", width='stretch')
            
            st.markdown("##### Prévia dos Dados")
            st.dataframe(df_export, width='stretch', hide_index=True, height=250, 
                         column_config={"Link Waze": st.column_config.LinkColumn("Navegar")})
