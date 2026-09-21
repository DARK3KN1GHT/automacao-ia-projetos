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

def processar_ficheiro_e_gerar_relatorio():
    nome_ficheiro = "vendas.csv"
    print(f"[*] A ler o ficheiro real '{nome_ficheiro}' com o Pandas...")
    
    try:
        # 1. Leitura do ficheiro CSV real
        df = pd.read_csv(nome_ficheiro)
        
        # Processamento de dados: Cálculo do Faturamento Total
        df["Faturamento_Total"] = df["Preco_Unitario"] * df["Quantidade_Vendida"]
        
        print("\n--- Dados Lidos e Processados do Ficheiro ---")
        print(df.to_string(index=False))
        print("-" * 45)
        
        # Converte para texto para enviar à IA
        dados_em_texto = df.to_csv(index=False)
        
        print("\n[*] A enviar os dados reais para análise da IA (Groq)...")
        
        # Modelo validado na sua conta
        modelo_escolhido = "openai/gpt-oss-safeguard-20b"
        
        prompt = (
            "Com base nestes dados reais de vendas, elabore um sumário executivo profissional "
            "destacando o produto com maior faturamento, o mais vendido e sugestões de otimização de stock:\n\n"
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
        
        # 2. Geração automática do relatório num ficheiro de saída
        nome_saida = "relatorio_executivo.md"
        with open(nome_saida, "w", encoding="utf-8") as f:
            f.write("# Relatório Executivo Automatizado\n\n")
            f.write(relatorio_ia)
            
        print(f"\n[+] Sucesso! O relatório foi gerado e guardado automaticamente no ficheiro: '{nome_saida}'")

    except FileNotFoundError:
        print(f"[-] Erro: O ficheiro '{nome_ficheiro}' não foi encontrado na pasta do projeto.")
    except Exception as e:
        print(f"[-] Erro ao processar: {e}")

if __name__ == "__main__":
    processar_ficheiro_e_gerar_relatorio()