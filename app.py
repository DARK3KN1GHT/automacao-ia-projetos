import os
import pandas as pd
from openai import OpenAI
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()
api_key = os.environ.get("GROQ_API_KEY")

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key=api_key,
)

def processar_e_analisar_dados():
    print("[*] PASSO 1: A processar e preparar os dados com Pandas...")
    
    # 1. Simulamos a leitura/criação de um conjunto de dados (poderia ser um ficheiro CSV ou Excel)
    dados_exemplo = {
        "Produto": ["Teclado Mecânico", "Rato Gamer", "Monitor Ultrawide", "Headset Bluetooth", "Cadeira de Escritório"],
        "Categoria": ["Periféricos", "Periféricos", "Monitores", "Áudio", "Mobiliário"],
        "Preco_Unitario": [350.00, 150.00, 1800.00, 250.00, 1200.00],
        "Quantidade_Vendida": [45, 120, 15, 60, 8]
    }
    
    # Criamos o DataFrame do Pandas
    df = pd.DataFrame(dados_exemplo)
    
    # Calculamos o faturamento total por produto (Processamento de dados)
    df["Faturamento_Total"] = df["Preco_Unitario"] * df["Quantidade_Vendida"]
    
    print("\n--- Dados Processados (Tabela Interna) ---")
    print(df.to_string(index=False))
    print("-" * 45)
    
    # Convertemos os dados processados para formato de texto/tabela para a IA conseguir ler
    dados_em_texto = df.to_csv(index=False)
    
    print("\n[*] PASSO 2: A enviar os dados processados para a IA da Groq analisar...")
    
    try:
        # Definimos o modelo detetado como funcional na sua conta
        modelo_escolhido = "openai/gpt-oss-safeguard-20b"
        
        prompt = (
            "Com base nos seguintes dados de vendas processados, forneça um sumário executivo "
            "destacando qual o produto que gerou maior faturamento total, qual vendeu mais unidades "
            "e dê uma sugestão rápida de otimização de stock:\n\n"
            f"{dados_em_texto}"
        )
        
        response = client.chat.completions.create(
            model=modelo_escolhido,
            messages=[
                {"role": "system", "content": "Você é um analista de dados sénior especialista em relatórios executivos."},
                {"role": "user", "content": prompt}
            ],
        )
        
        relatorio_ia = response.choices[0].message.content
        
        print("\n[+] Relatório Analítico Gerado pela IA:")
        print("=" * 60)
        print(relatorio_ia)
        print("=" * 60)

    except Exception as e:
        print(f"\n[-] Erro ao comunicar com a IA: {e}")

if __name__ == "__main__":
    processar_e_analisar_dados()