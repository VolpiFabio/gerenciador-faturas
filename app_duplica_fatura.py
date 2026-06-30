import streamlit as st
import re

st.set_page_config(page_title="Gerenciador de Faturas Pix/G", layout="wide")

st.title("📄 Gerenciador de Faturas Arrecadação")

# --- INÍCIO DO BOTÃO DO MANUAL ---
try:
    with open("manual.txt", "r", encoding="utf-8") as file:
        texto_manual = file.read()
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

if "modo_selecao" not in st.session_state:
    st.session_state.modo_selecao = "normal"

arquivo_bancario = st.file_uploader("Faça upload do arquivo PIX ou arquivo G", type=["txt", "csv"])

if arquivo_bancario is not None:
    conteudo = arquivo_bancario.read().decode("utf-8")
    linhas = conteudo.split("\n")

    st.success(f"Arquivo carregado: {len(linhas)} linhas")

    faturas = []
    cabecalho_g = ""
    rodape_g = ""
    cabecalho_pix = ""
    trailer_pix = ""

    for i, linha in enumerate(linhas):
        if not linha.strip():
            continue

        if linha.startswith("02RETORNO"):
            cabecalho_pix = linha
            continue

        if linha.startswith(("A", "0")) and not linha.startswith("02RETORNO"):
            cabecalho_g = linha
            continue

        if linha.startswith("9202"):
            trailer_pix = linha
            continue

        if linha.startswith(("Z", "9")):
            rodape_g = linha
            continue

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

    st.subheader("Selecione e edite as faturas:")

    selecionadas = []
    for fat in faturas:
        chave_chk = f"chk_{fat['indice']}"
        chave_dt = f"dt_{fat['indice']}"
        chave_val = f"val_{fat['indice']}"

        if chave_chk not in st.session_state:
            st.session_state[chave_chk] = True

        linha_original = fat['linha']
        data_credito = ""
        valor_atual = 0.0

        if fat["tipo"] == "G":
            data_credito = linha_original[29:37]
            try:
                valor_atual = int(linha_original[41:52]) / 100
            except ValueError:
                pass

        col_chk, col_dt, col_val = st.columns([2, 1, 1])

        with col_chk:
            label = f"[{fat['tipo']}] {fat['fatura']} - {fat['nome']}"
            checkbox = st.checkbox(label, key=chave_chk)

        nova_data = data_credito
        novo_valor = valor_atual

        with col_dt:
            if fat["tipo"] == "G" and checkbox:
                nova_data = st.text_input("Data Crédito", value=data_credito, key=chave_dt, max_chars=8)

        with col_val:
            if fat["tipo"] == "G" and checkbox:
                novo_valor = st.number_input("Valor (R$)", value=float(valor_atual), step=0.01, key=chave_val)

        if checkbox:
            if fat["tipo"] == "G":
                linha_mod = linha_original
                if len(nova_data) == 8:
                    linha_mod = linha_mod[:29] + nova_data + linha_mod[37:]
                val_11 = str(int(round(novo_valor * 100))).zfill(11)
                linha_mod = linha_mod[:41] + val_11 + linha_mod[52:]
                val_12 = str(int(round(novo_valor * 100))).zfill(12)
                val_orig_12 = str(int(round(valor_atual * 100))).zfill(12)
                idx_valor = linha_mod.find(val_orig_12, 70)
                if idx_valor != -1:
                    linha_mod = linha_mod[:idx_valor] + val_12 + linha_mod[idx_valor+12:]
                elif len(linha_mod) > 95:
                    linha_mod = linha_mod[:81] + val_12 + linha_mod[93:]
                fat['linha'] = linha_mod
            selecionadas.append(fat)

    if st.button("🚀 Processar faturas selecionadas", type="primary"):
        if not selecionadas:
            st.error("Selecione pelo menos uma fatura")
            st.stop()

        novo_valor_centavos = 0
        novas_linhas_pix = []
        linhas_g = []

        tem_pix = any(fat["tipo"] == "PIX" for fat in selecionadas)

        for fat in selecionadas:
            linha = fat['linha']

            if fat["tipo"] == "PIX":
                match_regex = re.search(r'00000000000(\d{4,8})', linha[100:130])
                match_valor_texto = match_regex.group(1) if match_regex else ""
                if match_valor_texto.isdigit():
                    novo_valor_centavos += int(match_valor_texto)
                else:
                    # Fallback: tenta encontrar o valor em outra posição
                    match_regex2 = re.search(r'00000000000(\d{4,8})', linha[300:330])
                    if match_regex2:
                        match_valor_texto = match_regex2.group(1)
                        if match_valor_texto.isdigit():
                            novo_valor_centavos += int(match_valor_texto)

                novas_linhas_pix.append(linha)

                linha_base_g = "G0590 0709 65061 7   20260605202606098289000000065231053202606013534350735343503900000000652300000690000000523705045300070454461"
                match_fatura = re.search(r'(\d{7})\s{2,}', linha[80:120] if len(linha) > 120 else "")
                numero_fatura = match_fatura.group(1) if match_fatura else "0000000"
                valor_str = match_valor_texto if match_valor_texto else "000000"
                match_data = re.search(r'(\d{8})\d{6}', linha[50:80] if len(linha) > 80 else "")
                data_str = match_data.group(1) if match_data else "20260607"

                nova_linha_g = linha_base_g
                nova_linha_g = nova_linha_g.replace("7353435", numero_fatura)
                nova_linha_g = nova_linha_g.replace("000000006523", valor_str.zfill(10))
                nova_linha_g = nova_linha_g.replace("20260605", data_str, 1)
                linhas_g.append(nova_linha_g)

            elif fat["tipo"] == "G":
                linhas_g.append(linha)
                try:
                    valor_g = int(linha[41:52].strip())
                    novo_valor_centavos += valor_g
                except ValueError:
                    pass

        if not tem_pix:
            if cabecalho_g:
                linhas_g.insert(0, cabecalho_g)
            if rodape_g:
                linhas_g.append(rodape_g)

        st.subheader("📊 Totais Recalculados")
        col_valor, col_linhas = st.columns(2)

        valor_reais = novo_valor_centavos / 100
        valor_editado = valor_reais
        qtd_linhas_total = len(linhas_g)

        with col_valor:
            st.metric("Valor total recalculado (R$):", f"R$ {valor_reais:.2f}".replace(".", ","))

        with col_linhas:
            st.metric("Quantidade de linhas recalculadas:", qtd_linhas_total)

        if not tem_pix:
            linhas_g = [linha for linha in linhas_g if not linha.startswith(("A", "0", "Z", "9"))]
            if cabecalho_g:
                linhas_g.insert(0, cabecalho_g)
            if rodape_g:
                if rodape_g.startswith("Z"):
                    qtd_str = str(qtd_linhas_total).zfill(6)
                    valor_str = str(novo_valor_centavos).zfill(17)
                    rodape_g = f"Z{qtd_str}{valor_str}{rodape_g[24:]}"
                linhas_g.append(rodape_g)

        conteudo_g_atualizado = "\n".join(linhas_g)

        st.subheader("✅ Arquivo processado com sucesso!")

        if tem_pix:
            valor_centavos = novo_valor_centavos
            valor_formatado = str(valor_centavos).zfill(15)
            qtd_formatada = str(len(selecionadas)).zfill(5)

            linha_diario_nova = f"DIARIO       {valor_formatado}00000000000{qtd_formatada}"

            if trailer_pix:
                prefixo = trailer_pix[:4]
                espacamento = " " * 702
                trailer_pix_modificado = prefixo + espacamento + linha_diario_nova
                novas_linhas_pix.append(trailer_pix_modificado)
            else:
                novas_linhas_pix.append(linha_diario_nova)

            linhas_pix_final = []
            if cabecalho_pix:
                linhas_pix_final.append(cabecalho_pix)
            for fat in selecionadas:
                if fat["tipo"] == "PIX":
                    linhas_pix_final.append(fat['linha'])

            linhas_pix_final.append(trailer_pix_modificado)
            conteudo_pix_atualizado = "\n".join(linhas_pix_final) + "\n"

            # Montar a lista final do PIX
            linhas_pix_final = []

            # 1. Cabeçalho PIX
            if cabecalho_pix:
                linhas_pix_final.append(cabecalho_pix)

            # 2. Faturas selecionadas
            for fat in selecionadas:
                if fat["tipo"] == "PIX":
                    linhas_pix_final.append(fat['linha'])

            # 3. Trailer 9202 + DIARIO (UMA LINHA SÓ)
            linhas_pix_final.append(trailer_pix_modificado)

            # 4. Linha em branco no final
            conteudo_pix_atualizado = "\n".join(linhas_pix_final) + "\n"

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
