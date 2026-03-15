import pandas as pd
import numpy as np
from scipy.stats import poisson
import requests
import time
from datetime import datetime

# ==========================================
# CONFIGURAÇÕES DO RICARDO
# ==========================================
TELEGRAM_TOKEN = "8395535169:AAHWGWhqpaLRA-Zg5LS-XDG5fadCmpTRP94"
CHAT_ID = "8044187051"

# Filtros para varredura diária (um pouco mais flexíveis que os semanais)
MIN_PROB_VITORIA = 0.60 
MIN_PROB_OVER = 0.65

LIGAS = {
    "🇵🇹 Liga Portugal": "https://www.football-data.co.uk/mmz4281/2425/P1.csv",
    "🇧🇷 Brasileirão": "https://www.football-data.co.uk/mmz4281/2425/BRA.csv",
    "🏴󠁧󠁢󠁥󠁮󠁧󠁿 Premier League": "https://www.football-data.co.uk/mmz4281/2425/E0.csv",
    "🇪🇸 La Liga": "https://www.football-data.co.uk/mmz4281/2425/SP1.csv",
    "🇩🇪 Bundesliga": "https://www.football-data.co.uk/mmz4281/2425/D1.csv",
    "🇮🇹 Serie A": "https://www.football-data.co.uk/mmz4281/2425/I1.csv",
    "🇫🇷 Ligue 1": "https://www.football-data.co.uk/mmz4281/2425/F1.csv"
}

def enviar_telegram(mensagem):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": mensagem, "parse_mode": "Markdown"})

def gerar_relatorio_diario():
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    enviar_telegram(f"🚀 *ADRicardobot: Início da Varredura Diária ({data_hoje})*")
    
    lista_oportunidades = []
    relatorio_texto = "📅 *JOGOS COM VALOR HOJE*\n━━━━━━━━━━━━━━━━━━━━\n\n"

    for nome_liga, url in LIGAS.items():
        try:
            df = pd.read_csv(url)
            cols = ['Home', 'Away', 'HG', 'AG'] if 'Home' in df.columns else ['HomeTeam', 'AwayTeam', 'FTHG', 'FTAG']
            df = df.rename(columns={cols[0]: 'Home', cols[1]: 'Away', cols[2]: 'HG', cols[3]: 'AG'})
            
            m_h, m_a = df['HG'].mean(), df['AG'].mean()
            h_stats = df.groupby('Home').agg({'HG': 'mean', 'AG': 'mean'})
            a_stats = df.groupby('Away').agg({'AG': 'mean', 'HG': 'mean'})

            # Pega as equipas mais frequentes para simular os jogos do dia
            # (O bot analisa as combinações de maior probabilidade)
            top_teams = df['Home'].value_counts().index[:12]

            for h in top_teams:
                for a in top_teams:
                    if h == a: continue
                    
                    exp_h = h_stats.loc[h, 'HG'] * (a_stats.loc[a, 'HG'] / m_h)
                    exp_a = a_stats.loc[a, 'AG'] * (h_stats.loc[h, 'AG'] / m_a)
                    
                    p_h = [poisson.pmf(i, exp_h) for i in range(6)]
                    p_a = [poisson.pmf(i, exp_a) for i in range(6)]
                    matriz = np.outer(p_h, p_a)
                    
                    prob_h = np.sum(np.tril(matriz, -1))
                    prob_o25 = 1 - (matriz[0,0]+matriz[0,1]+matriz[0,2]+matriz[1,0]+matriz[1,1]+matriz[2,0])

                    if prob_h > MIN_PROB_VITORIA:
                        lista_oportunidades.append({'jogo': f"{h} vs {a}", 'tipo': 'Vitória', 'prob': prob_h, 'liga': nome_liga})
                    if prob_o25 > MIN_PROB_OVER:
                        lista_oportunidades.append({'jogo': f"{h} vs {a}", 'tipo': 'Over 2.5', 'prob': prob_o25, 'liga': nome_liga})
        except:
            continue

    # Organizar e enviar
    if not lista_oportunidades:
        enviar_telegram("ℹ️ Nenhuma oportunidade clara encontrada para os parâmetros de hoje.")
        return

    # Limitar aos 10 melhores jogos para o relatório diário não ficar gigante
    top_diario = sorted(lista_oportunidades, key=lambda x: x['prob'], reverse=True)[:10]

    for op in top_diario:
        relatorio_texto += f"🏆 *{op['liga']}*\n📍 {op['jogo']}\n🎯 {op['tipo']}: {op['prob']:.0%}\n\n"

    # --- MÚLTIPLA DO DIA ---
    multipla_texto = "🔥 *MÚLTIPLA DO DIA (TOP 3)*\n━━━━━━━━━━━━━━━━━━━━\n"
    top_3 = top_diario[:3]
    
    odd_acumulada = 1.0
    for i, aposta in enumerate(top_3):
        odd_estimada = 1 / aposta['prob'] + 0.15
        odd_acumulada *= odd_estimada
        multipla_texto += f"{i+1}️⃣ {aposta['jogo']}\n🔹 {aposta['tipo']} (@{odd_estimada:.2f})\n"
    
    multipla_texto += f"\n💰 *Odd Total Estimada: @{odd_acumulada:.2f}*\n⚠️ _Sucesso nos palpites!_"

    enviar_telegram(relatorio_texto)
    time.sleep(1)
    enviar_telegram(multipla_texto)

if __name__ == "__main__":
    gerar_relatorio_diario()
