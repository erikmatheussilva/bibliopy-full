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
