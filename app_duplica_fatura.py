import streamlit as st
import re

st.set_page_config(page_title="Gerenciador de Faturas Pix/G", layout="wide")

st.title("📄 Gerenciador de Faturas Pix e G")
# st.markdown("Selecione as faturas e edite manualmente os totais no final.")

# --- INÍCIO DO BOTÃO DO MANUAL ---
try:
    # Lê o arquivo de texto externo
    with open("manual.txt", "r", encoding="utf-8") as file:
        texto_manual = file.read()
        
    # Cria o botão de download com o conteúdo do arquivo
    st.download_button(
        label="📖 Baixar Manual de Uso",
        data=texto_manual,
        file_name="Manual_Gerenciador_Faturas.txt",
        mime="text/plain"
    )
except FileNotFoundError:
    st.warning("⚠️ Arquivo manual.txt não encontrado na pasta.")
    
st.write("---")
# --- FIM DO BOTÃO DO MANUAL ---

# Inicializar estado
if "modo_selecao" not in st.session_state:
    st.session_state.modo_selecao = "normal"

# Upload do arquivo (Aceita PIX ou G)
arquivo_bancario = st.file_uploader("Faça upload do arquivo PIX ou arquivo G", type=["txt", "csv"])

if arquivo_bancario is not None:
    conteudo = arquivo_bancario.read().decode("utf-8")
    linhas = conteudo.split("\n")

    st.success(f"Arquivo carregado: {len(linhas)} linhas")

    # Extrair faturas
    faturas = []
    cabecalho_g = ""
    rodape_g = ""
    
    for i, linha in enumerate(linhas):
        # Ignorar linhas completamente vazias para evitar erros
        if not linha.strip():
            continue

        # Capturar cabeçalho (pode começar com A ou 0)
        if linha.startswith(("A", "0")):
            cabecalho_g = linha
            continue
            
        # Capturar rodapé (pode começar com Z ou 9)
        elif linha.startswith(("Z", "9")):
            rodape_g = linha
            continue

        # Identificar se é uma linha de fatura PIX
        if linha.startswith("500") and len(linha) > 50:
            match_fatura = re.search(r'(\d{7})\s{2,}', linha[80:120] if len(linha) > 120 else "")
            nome = ""
            match_nome = re.search(r'([A-ZÀ-Ú\s]+)\s{2,}', linha[150:250] if len(linha) > 250 else "")
            if match_nome:
                nome = match_nome.group(1).strip()

            faturas.append({
                "tipo": "PIX",
                "indice": i,
                "linha": linha,
                "fatura": match_fatura.group(1) if match_fatura else f"Fatura_{i}",
                "nome": nome if nome else f"Cliente {i}"
            })
            
        # Identificar se é uma linha de fatura G nativa
        elif linha.startswith("G") and len(linha) > 80:
            fatura_g = linha[72:79].strip() if len(linha) > 79 else f"Fatura_{i}"
            faturas.append({
                "tipo": "G",
                "indice": i,
                "linha": linha,
                "fatura": fatura_g,
                "nome": "Registro nativo do arquivo"
            })

    if not faturas:
        st.error("Nenhuma fatura encontrada no arquivo")
        st.stop()

    st.write(f"📋 **{len(faturas)} faturas encontradas**")

    # Botões de ação
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        if st.button("✅ Selecionar todas"):
            for fat in faturas:
                st.session_state[f"chk_{fat['indice']}"] = True
            st.rerun()
    with col_btn2:
        if st.button("❌ Limpar seleção"):
            for fat in faturas:
                st.session_state[f"chk_{fat['indice']}"] = False
            st.rerun()

    # Mostrar faturas com checkboxes e campos de edição
    st.subheader("Selecione e edite as faturas:")

    selecionadas = []
    for fat in faturas:
        chave_chk = f"chk_{fat['indice']}"
        chave_dt = f"dt_{fat['indice']}"
        chave_val = f"val_{fat['indice']}"

        if chave_chk not in st.session_state:
            st.session_state[chave_chk] = True

        linha_original = fat['linha']
        
        # Extrair dados para preencher a tela (Apenas para tipo G)
        data_credito = ""
        valor_atual = 0.0
        
        if fat["tipo"] == "G":
            # A data de crédito fica nas posições 29 a 37 no seu layout
            data_credito = linha_original[29:37]
            try:
                # O valor no seu layout aparece aqui nas posições 41 a 52
                valor_atual = int(linha_original[41:52]) / 100
            except ValueError:
                pass

        # Criar 3 colunas para colocar os campos lado a lado
        col_chk, col_dt, col_val = st.columns([2, 1, 1])
        
        with col_chk:
            label = f"[{fat['tipo']}] {fat['fatura']} - {fat['nome']}"
            checkbox = st.checkbox(label, key=chave_chk)

        # Renderizar campos de edição (só aparecem se estiver marcado e for G)
        nova_data = data_credito
        novo_valor = valor_atual

        with col_dt:
            if fat["tipo"] == "G" and checkbox:
                nova_data = st.text_input("Data Crédito", value=data_credito, key=chave_dt, max_chars=8)
                
        with col_val:
            if fat["tipo"] == "G" and checkbox:
                # Usa step=0.01 para permitir alteração de centavos
                novo_valor = st.number_input("Valor (R$)", value=float(valor_atual), step=0.01, key=chave_val)

        # Se o checkbox estiver marcado, tratamos a linha antes de adicionar na lista
        if checkbox:
            if fat["tipo"] == "G":
                linha_mod = linha_original
                
                # 1. Substituir a data de crédito na string
                if len(nova_data) == 8:
                    linha_mod = linha_mod[:29] + nova_data + linha_mod[37:]
                
                # 2. Substituir o primeiro valor nas posições 41 a 52 (11 posições)
                val_11 = str(int(round(novo_valor * 100))).zfill(11)
                linha_mod = linha_mod[:41] + val_11 + linha_mod[52:]
                
                # 3. Substituir o segundo valor (Valor Recebido) de forma inteligente.
                val_12 = str(int(round(novo_valor * 100))).zfill(12)
                val_orig_12 = str(int(round(valor_atual * 100))).zfill(12)
                
                # Caça o valor original do meio para o final da linha para não errar a posição do banco
                idx_valor = linha_mod.find(val_orig_12, 70)
                if idx_valor != -1:
                    linha_mod = linha_mod[:idx_valor] + val_12 + linha_mod[idx_valor+12:]
                elif len(linha_mod) > 95:
                    # Fallback para o layout padrão estrito se não encontrar
                    linha_mod = linha_mod[:81] + val_12 + linha_mod[93:]

                fat['linha'] = linha_mod
                
            selecionadas.append(fat)

    # Botão para gerar arquivos
    if st.button("🚀 Processar faturas selecionadas", type="primary"):
        if not selecionadas:
            st.error("Selecione pelo menos uma fatura")
            st.stop()

        novo_valor_centavos = 0
        novas_linhas_pix = []
        linhas_g = []

        # Identificar o tipo dominante no lote selecionado
        tem_pix = any(fat["tipo"] == "PIX" for fat in selecionadas)

        for fat in selecionadas:
            linha = fat['linha']
            
            if fat["tipo"] == "PIX":
                match_valor = re.search(r'000000000000(\d{6})', linha)
                if match_valor:
                    novo_valor_centavos += int(match_valor.group(1))
                novas_linhas_pix.append(linha)
                
                # Conversão de PIX para G
                linha_base_g = "G0590 0709 65061 7   20260605202606098289000000065231053202606013534350735343503900000000652300000690000000523705045300070454461"
                match_fatura = re.search(r'(\d{7})\s{2,}', linha[80:120] if len(linha) > 120 else "")
                numero_fatura = match_fatura.group(1) if match_fatura else "0000000"
                valor_str = match_valor.group(1) if match_valor else "000000"
                match_data = re.search(r'(\d{8})\d{6}', linha[50:80] if len(linha) > 80 else "")
                data_str = match_data.group(1) if match_data else "20260607"

                nova_linha_g = linha_base_g
                nova_linha_g = nova_linha_g.replace("7353435", numero_fatura)
                nova_linha_g = nova_linha_g.replace("000000006523", valor_str.zfill(10))
                nova_linha_g = nova_linha_g.replace("20260605", data_str, 1)
                linhas_g.append(nova_linha_g)
                
            elif fat["tipo"] == "G":
                # Se já é uma linha G, mantemos ela idêntica
                linhas_g.append(linha)
                # Extração do valor (Lemos de dentro do código de barras pos 41 a 52 que é padrão universal)
                try:
                    valor_g = int(linha[41:52].strip())
                    novo_valor_centavos += valor_g
                except ValueError:
                    pass

        # Se for um arquivo G nativo (não tem origem PIX), devolvemos o cabeçalho e rodapé originais
        if not tem_pix:
            if cabecalho_g:
                linhas_g.insert(0, cabecalho_g)
            if rodape_g:
                linhas_g.append(rodape_g)

        # Mostrar totais recalculados (Apenas visualização)
        st.subheader("📊 Totais Recalculados")
        col_valor, col_linhas = st.columns(2)

        # Calculamos os valores automáticos
        valor_reais = novo_valor_centavos / 100
        valor_editado = valor_reais  
        qtd_linhas_total = len(linhas_g)

        with col_valor:
            st.metric("Valor total recalculado (R$):", f"{valor_reais:.2f}")

        with col_linhas:
            st.metric("Quantidade de linhas recalculadas:", qtd_linhas_total)

        # Se for um arquivo G nativo, devolvemos o cabeçalho e rodapé (agora atualizados!)
        if not tem_pix:
            # 1. Limpeza de segurança: remove qualquer cabeçalho ou rodapé que tenha entrado na lista acidentalmente
            linhas_g = [linha for linha in linhas_g if not linha.startswith(("A", "0", "Z", "9"))]

            if cabecalho_g:
                linhas_g.insert(0, cabecalho_g)
                
            if rodape_g:
                # Atualiza a linha Z com os novos totais calculados
                # Atualiza a linha Z com os novos totais calculados
                if rodape_g.startswith("Z"):
                    qtd_str = str(qtd_linhas_total).zfill(6)
                    
                    # Como o arquivo sempre exige os centavos juntos (sem vírgula), 
                    # usamos o valor total em centavos direto, preenchendo com zeros!
                    valor_str = str(novo_valor_centavos).zfill(17) 
                    
                    rodape_g = f"Z{qtd_str}{valor_str}{rodape_g[24:]}"

                linhas_g.append(rodape_g)

        conteudo_g_atualizado = "\n".join(linhas_g)

        # Montar a estrutura final de saídas baseada no arquivo original
        st.subheader("✅ Arquivo processado com sucesso!")

        if tem_pix:
            # Gera PIX e G lado a lado
            valor_centavos = int(round(valor_editado * 100))
            valor_formatado = str(valor_centavos).zfill(15)
            qtd_formatada = str(qtd_linhas_total).zfill(5)
            linha_total = f"DIARIO      {valor_formatado}00000000000{qtd_formatada}"
            novas_linhas_pix.append(linha_total)
            novas_linhas_pix.append("")
            conteudo_pix_atualizado = "\n".join(novas_linhas_pix)

            col_esq, col_dir = st.columns(2)
            with col_esq:
                st.download_button(
                    label="📥 Baixar arquivo PIX",
                    data=conteudo_pix_atualizado.encode("utf-8"),
                    file_name="pix_atualizado.txt",
                    mime="text/plain"
                )
                with st.expander("Preview do PIX"):
                    st.text(conteudo_pix_atualizado[:3000])
            with col_dir:
                st.download_button(
                    label="📥 Baixar arquivo G",
                    data=conteudo_g_atualizado.encode("utf-8"),
                    file_name="g_atualizado.txt",
                    mime="text/plain"
                )
                with st.expander("Preview do G"):
                    st.text(conteudo_g_atualizado[:3000])
        else:
            # Se a origem veio de um arquivo G, mostra apenas o G
            st.download_button(
                label="📥 Baixar arquivo Atualizado",
                data=conteudo_g_atualizado.encode("utf-8"),
                file_name="arquivo_bancario_atualizado.txt",
                mime="text/plain"
            )
            with st.expander("Preview do Arquivo"):
                st.text(conteudo_g_atualizado[:3000])

        st.success(f"""
        **Resumo:**
        - Faturas selecionadas: {len(selecionadas)}
        - Valor total recalculado: R$ {valor_editado:.2f}
        - Total de registros processados: {len(linhas_g)}
        """)
else:
    st.info("👆 Faça upload de um arquivo bancário para começar")