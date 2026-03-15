import requests
import pandas as pd
from datetime import datetime

# ==========================================
# CONFIGURAÇÕES DO RICARDO
# ==========================================
TELEGRAM_TOKEN = "8395535169:AAHWGWhqpaLRA-Zg5LS-XDG5fadCmpTRP94"
CHAT_ID = "8044187051"
RAPID_API_KEY = "1e1ffcc779msh1bfc9eb8d05dad1p1573fajsn771bce121bea"

# Ligas: Portugal (94), Inglaterra (39), Espanha (140), Brasil (71)
LIGAS_IDS = [94, 39, 140, 71]

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"})

def obter_previsoes_api():
    url = "https://api-football-v1.p.rapidapi.com/v3/fixtures"
    hoje = datetime.now().strftime('%Y-%m-%d')
    headers = {
        "X-RapidAPI-Key": RAPID_API_KEY,
        "X-RapidAPI-Host": "api-football-v1.p.rapidapi.com"
    }

    relatorio = f"📅 *PALPITES REAIS - {datetime.now().strftime('%d/%m')}*\n━━━━━━━━━━━━━━━━━━━━\n\n"
    jogos_encontrados = False

    for liga in LIGAS_IDS:
        # 1. Procurar jogos do dia para cada liga
        params = {"date": hoje, "league": str(liga), "season": "2025"}
        response = requests.get(url, headers=headers, params=params)
        
        if response.status_code == 200:
            fixtures = response.json().get('response', [])
            
            for f in fixtures:
                jogos_encontrados = True
                f_id = f['fixture']['id']
                casa = f['teams']['home']['name']
                fora = f['teams']['away']['name']
                
                # 2. Pedir PREVISÕES detalhadas para este jogo específico
                # A API-Football já tem um "cérebro" de previsões interno
                pred_url = "https://api-football-v1.p.rapidapi.com/v3/predictions"
                pred_res = requests.get(pred_url, headers=headers, params={"fixture": f_id})
                
                if pred_res.status_code == 200:
                    p_data = pred_res.json().get('response', [{}])[0]
                    if p_data:
                        # Extrair probabilidades da própria API (que são muito precisas)
                        prob_vitoria = p_data['predictions']['winner']['name']
                        advice = p_data['predictions']['advice']
                        percent_casa = p_data['predictions']['percent']['home']
                        percent_fora = p_data['predictions']['percent']['away']
                        goals_o25 = p_data['predictions']['goals']['home'] # Tendência de golos

                        relatorio += f"🏆 *{f['league']['name']}*\n"
                        relatorio += f"🏟️ {casa} vs {fora}\n"
                        relatorio += f"✅ Prob. Vitória: {percent_casa if percent_casa else '50%'} (Casa)\n"
                        relatorio += f"⚽ Sugestão: {advice}\n"
                        relatorio += "---------------------------\n"

    if not jogos_encontrados:
        relatorio += "ℹ️ Nenhum jogo de elite encontrado para hoje nas ligas selecionadas."

    enviar_telegram(relatorio)

if __name__ == "__main__":
    obter_previsoes_api()
