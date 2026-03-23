# 🚚 RotaMax — Otimizador de Rotas de Entrega

Aplicativo Streamlit com IA (Claude) para extração automática de endereços,
agrupamento por proximidade e otimização de rota (TSP).

## ⚡ Instalação rápida

```bash
# 1. Clone ou copie a pasta rotamax/
cd rotamax

# 2. Instale dependências
pip install -r requirements.txt

# 3. Execute
streamlit run app.py
```

## 🔑 API Key

Para extração de endereços em **imagens**, você precisa de uma chave da API Anthropic:
- Acesse: https://console.anthropic.com/
- Cole a chave no campo "Chave API Anthropic" na barra lateral do app

Para **CSV**, nenhuma chave é necessária.

## 📋 Como usar

### 1. Ponto de Partida (barra lateral)
- Digite o endereço e clique **Geocodificar Endereço**, ou
- Insira coordenadas GPS manualmente (latitude/longitude) e clique **Usar Coordenadas GPS**

### 2. Upload de Endereços (aba Upload & Extração)
- **Imagens** (JPG, PNG, GIF, WEBP): Claude AI extrai todos os endereços visíveis
- **CSV**: detecta automaticamente a coluna de endereços
- Clique **⚡ Extrair Endereços**

### 3. Otimizar Rota (aba Rota Otimizada)
- Ajuste o **raio de agrupamento** (padrão 100m) na barra lateral
- Clique **🚀 Otimizar Rota**
- O sistema irá:
  1. Geocodificar todos os endereços via Nominatim
  2. Agrupar pontos a ≤ 100m em uma parada única (centróide)
  3. Ordenar as paradas com algoritmo TSP (Vizinho Mais Próximo)
  4. Exibir mapa interativo + lista de paradas

### 4. Exportar (aba Exportar)
- **Google Maps**: link direto com waypoints
- **CSV**: tabela com paradas e endereços
- **JSON**: pins com coordenadas para integração

## 🏗 Arquitetura

```
app.py
├── Extração (Claude Opus via API)
│   ├── Imagens → base64 → Claude Vision → JSON de endereços
│   └── CSV → pandas → detecção automática de coluna
├── Geocodificação (Nominatim – gratuito, sem API key)
├── Agrupamento (Haversine + clustering ≤ 100m)
├── TSP (Heurística Vizinho Mais Próximo)
├── Mapa (Folium + streamlit-folium)
└── Exportação (Google Maps URL, CSV, JSON)
```

## 📦 Dependências

| Pacote | Uso |
|---|---|
| streamlit | Frontend |
| anthropic | Extração IA de endereços em imagens |
| folium + streamlit-folium | Mapa interativo |
| pandas | Leitura CSV |
| requests | Nominatim geocoding |
