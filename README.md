# PROJETO TCC UNINTER - COMPARAÇÃO DE TEXTOS

## Como rodar o projeto?

Antes de executar o projeto, verifique se o Python está instalado no computador.
Download oficial: https://www.python.org/downloads/
Versão recomendada: Python 3.12 ou outra versão compatível com as dependências do projeto.

```bash
python -m pip install -r requirements.txt
python -m nltk.downloader stopwords
python app.py
```

Caso o "requirements.txt" não funcione, tente isso!
```bash
python -m pip install nltk
python -m nltk.downloader stopwords
python app.py
```

Abra http://localhost:8000 no navegador


## Arquivos

- `similarity.py`: algoritmos de similaridade
- `app.py`: Servidor HTTP com a API JSON
- `index.html`: Interface
- `style.css`: Estilização do site
- `script.js`: Códigos de funcionamento do site

## Como o cálculo é feito?

1. **Pré-processamento**: Minúsculas, Remoção de acentos, StopWords(PT/EN) e Stemming.
2. **Métricas**
   - Cosseno sobre vetores TF-IDF (50%): Peso das palavras
   - Jaccard (20%): Vocabulário compartilhado
   - Dice sobre bigramas (30%): Frases e ordem das palavras
3. **Índice combinado** = Média ponderada das três métricas, classificado em faixas:
   Idênticos(85% ou mais), Muito similares(60% ou mais), Moderados(35% ou mais), Pouco similar(15% ou mais) e abaixo disso é sem similaridade.
4. **Extras**: Termos relevantes em comum e trechos literais compartilhados (difflib).

## API

### POST /api/compare
```json
{"text_a": "...", "text_b": "...", "options": {"stopwords": true, "stemming": true, "accents": true}}
```

### POST /api/compare-many
```json
{"texts": ["...", "...", "..."], "options": {}}
```
