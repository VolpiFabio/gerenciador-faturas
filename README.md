## 📄 Manual de Uso: Gerenciador de Faturas Pix e G

**O que essa ferramenta faz?**
Este aplicativo facilita a manipulação de arquivos bancários (formatos PIX e G nativo). Ele permite visualizar os registros de forma clara, remover faturas indesejadas, editar datas e valores (no caso de arquivos G) para testes ou correções, e exportar um novo arquivo perfeitamente formatado, com os totais recalculados automaticamente.

### 🛠️ Passo a Passo de Utilização

**1. Importando o Arquivo**
* Na tela inicial, clique em **"Browse files"** ou simplesmente arraste o seu arquivo bancário .txt para a área indicada.
* O sistema fará a leitura inicial e exibirá uma mensagem verde confirmando o número total de faturas encontradas.

**2. Seleção e Filtragem de Faturas**
* O sistema listará todos os registros encontrados.
* Utilize os botões **"✅ Selecionar todas"** ou **"❌ Limpar seleção"** para facilitar o trabalho com arquivos grandes.
* Para excluir um registro específico do arquivo final, basta **desmarcar a caixinha (checkbox)** ao lado do nome do cliente. Essa linha será totalmente ignorada na geração do novo arquivo.

**3. Edição Manual e Comportamento dos Arquivos (Pix vs. G)**
O sistema trata as faturas de maneira diferente dependendo de sua origem:
* **Faturas nativas do arquivo G:** Os campos **"Data Crédito"** e **"Valor (R$)"** estarão disponíveis para edição ao lado de cada registro selecionado. Você pode digitar uma nova data ou ajustar o valor pago (inclusive os centavos). O aplicativo cuida de encaixar o seu novo número exatamente na posição que o layout bancário exige.
* **Faturas do arquivo PIX:** Arquivos do tipo PIX **não são manipuláveis** (não é possível editar datas e valores neles). A importação de um arquivo PIX serve apenas para ler os dados e **replicar essas faturas gerando um arquivo G correspondente**. Isso é ideal para realizar testes de validação no sistema simulando faturas duplicadas que trafegam nos dois tipos de arquivos.

**4. Recálculo Automático de Totais**
* Na seção **"📊 Totais Recalculados"**, você pode visualizar como o arquivo ficará.
* Não é necessário fazer contas: ao desmarcar faturas ou editar os valores no arquivo G, o sistema recalcula sozinho o **Valor Total** e a **Quantidade de Linhas**, preparando a linha de rodapé (linha Z) para o fechamento correto.

**5. Processamento e Download**
* Quando tudo estiver certo, clique no botão principal **"🚀 Processar faturas selecionadas"**.
* O aplicativo vai compilar os dados. Você pode conferir como ficou expandindo a opção **"Preview do Arquivo"**.
* Por fim, clique em **"📥 Baixar arquivo Atualizado"** (ou baixe separadamente os arquivos PIX e G gerados) para salvar a versão final na sua máquina, pronta para ser importada ou enviada.

### ⚠️ Informações Importantes sobre Estrutura
* **Cabeçalhos e Rodapés:** O sistema preserva automaticamente a estrutura do banco. Linhas iniciais (como as que começam com A ou 0) e linhas finais (Z ou 9) são lidas e mantidas intactas nos arquivos G.
* **Zeros e Centavos:** O recálculo da última linha (Z) já trata automaticamente a exigência do layout, garantindo que o número total de centavos seja preenchido com zeros à esquerda no tamanho exato exigido pela FEBRABAN.
