# BiblioPy

Biblioteca digital desktop feita em Python orientado a objetos para o projeto de P.O.O. da SoloCoding. A janela usa Tkinter/ttk e lê PDFs locais dentro do próprio aplicativo. Os dados são guardados em JSON, sem banco de dados SQL.

## Como executar

1. Instale Python 3.11 ou mais recente com Tkinter.
2. Abra o PowerShell **no seu computador**, na pasta deste projeto:

   ```powershell
   cd "E:\ENGENHARIA DE SOFTWARE\bibliopy"
   python -m venv .venv
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   .\.venv\Scripts\python.exe main.py
   ```

3. A janela **BiblioPy — Biblioteca Digital** mostrará o acervo. Pesquise por título ou autor, escolha uma categoria e selecione um livro para ver os detalhes. Os PDFs locais abrem em uma janela de leitura do BiblioPy, com página anterior, próxima, zoom e rolagem. Os livros online abrem suas páginas no navegador.

Se o comando `python` não estiver disponível, use `py -m venv .venv` no primeiro passo. O ambiente `.venv` é local e fica fora dos arquivos destinados ao Git. `pypdfium2` renderiza cada página do PDF e `Pillow` a mostra no Tkinter; as versões usadas estão em `requirements.txt`.

## Acervo inicial

O catálogo tem **25 títulos, cinco por categoria**: literatura clássica, fantasia e aventura, literatura para vestibulares, programação e tecnologia, mistério, suspense e terror. Há **dois PDFs reais incluídos** em `pdfs/` (*Think Python, 2nd Edition* e *Think DSP*). Os outros 23 registros abrem páginas de edições digitais; eles não são apresentados como PDFs instalados. Essas páginas podem oferecer HTML, EPUB ou PDF, conforme cada editora ou repositório.

Os catálogos ficam em `catalogos/gutenberg.json` e `catalogos/greenteapress.json`. Título, autor, ano, idioma, categoria, fonte e localização são carregados desses arquivos JSON, sem dados de livros escritos em `main.py`. São listas selecionadas para este projeto: o programa não coleta livros automaticamente da internet. Os títulos do Gutenberg em inglês aparecem com título conhecido em português e indicação explícita do idioma da edição. **O Alienista** abre o volume *Papéis Avulsos*, que contém o conto.

A lista original da conversa recebeu três correções após a conferência das fontes:

- *A Princesa e o Goblin* usa o registro Gutenberg nº 708; *The King of Elfland's Daughter*, o nº 61077.
- *Think DSP* ocupa a vaga de um título da OpenStax para manter as duas fontes principais definidas no UML.
- *The Woman in White* ocupa a vaga de *O Misterioso Caso de Styles*, cuja redistribuição no Brasil exigiria uma análise de direitos mais cuidadosa.

## Cadastro e dados pessoais

Use **Cadastrar livro** para adicionar um PDF do computador ou uma página `http://`/`https://`. O arquivo PDF precisa existir e ter um cabeçalho PDF válido. O programa guarda o caminho do arquivo, sem copiá-lo; se você mover ou excluir o PDF, será preciso cadastrar o novo caminho.

Os cadastros e as remoções são salvos em `dados/usuario.json`, criado no primeiro uso. A remoção de um título do catálogo inicial apenas o oculta para este usuário. Os dois catálogos originais permanecem separados dos dados pessoais. Se `usuario.json` for danificado, o programa avisará ao iniciar em vez de apagar os dados.

## Organização do código

| Arquivo | Responsabilidade |
|---|---|
| `bibliopy/livros.py` | `Livro`, `LivroPDFLocal`, `LivroOnline` e abertura de livros |
| `bibliopy/repositorios.py` | `RepositorioDigital` e os dois repositórios concretos |
| `bibliopy/biblioteca.py` | Acervo, buscas, filtros, cadastro e JSON pessoal |
| `bibliopy/interface.py` | `InterfaceBiblioteca` e a janela Tkinter/ttk |
| `main.py` | Criação dos objetos e início da aplicação |

As duas hierarquias de livros e repositórios demonstram herança e polimorfismo. `Biblioteca` se associa aos livros e aos repositórios; `InterfaceBiblioteca` recebe uma `Biblioteca`. `LivroPDFLocal` contém o atributo privado `__caminhoArquivo` e o método privado `__validarArquivo`.

## Verificação

No PowerShell, na pasta do projeto:

```powershell
python -m unittest discover -s tests -v
```

Os testes verificam os 25 livros, a busca sem acentos, a persistência após reiniciar, o caminho validado dos PDFs e a abertura simulada do navegador. A interface de leitura foi conferida com os dois PDFs locais.

## Fontes e direitos

As páginas do [Project Gutenberg](https://www.gutenberg.org/) informam os formatos disponíveis e as condições de uso de cada edição. O Gutenberg avalia domínio público conforme a legislação dos EUA; confira os direitos locais antes de redistribuir arquivos ou traduções. Os dois PDFs incluídos foram obtidos diretamente da [Green Tea Press](https://greenteapress.com/wp/) e mantêm os créditos e as licenças dentro dos próprios arquivos:

- *Think Python, 2nd Edition*, © 2015 Allen Downey — [edição oficial](https://greenteapress.com/wp/think-python-2e/), Creative Commons BY-NC 3.0.
- *Think DSP*, © 2014 Allen B. Downey — [edição oficial](https://greenteapress.com/wp/think-dsp/), Creative Commons BY-NC-SA 4.0, conforme o PDF incluído.

Este projeto não inclui livros de *A Song of Ice and Fire* nem traduções sem autorização identificada.
