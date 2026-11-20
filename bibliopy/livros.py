"""Tipos de livro e comportamento de abertura."""

from abc import ABC, abstractmethod
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse


class Livro(ABC):
    def __init__(
        self,
        id: int,
        titulo: str,
        autor: str,
        genero: str,
        ano: int,
        idioma: str = "Português",
        fonte: str = "Pessoal",
        nota: str = "",
    ) -> None:
        if isinstance(id, bool) or not isinstance(id, int) or id <= 0:
            raise ValueError("O ID do livro deve ser um inteiro positivo.")
        if isinstance(ano, bool) or not isinstance(ano, int) or ano <= 0:
            raise ValueError("O ano deve ser um inteiro positivo.")
        for rotulo, valor in (
            ("título", titulo),
            ("autor", autor),
            ("gênero", genero),
            ("idioma", idioma),
            ("fonte", fonte),
        ):
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"O campo {rotulo} é obrigatório.")
        if not isinstance(nota, str):
            raise ValueError("A observação deve ser um texto.")

        self.id = id
        self.titulo = titulo.strip()
        self.autor = autor.strip()
        self.genero = genero.strip()
        self.ano = ano
        self.idioma = idioma.strip()
        self.fonte = fonte.strip()
        self.nota = nota.strip()

    @abstractmethod
    def abrir(self) -> Path | bytes:
        """Entrega um PDF local ou online ao leitor."""

    def exibirDados(self) -> str:
        dados = (
            f"{self.titulo}\n"
            f"Autor: {self.autor}\n"
            f"Categoria: {self.genero}\n"
            f"Ano: {self.ano}\n"
            f"Idioma da edição: {self.idioma}\n"
            f"Fonte: {self.fonte}"
        )
        if self.nota:
            dados += f"\nObservação: {self.nota}"
        return dados


class LivroPDFLocal(Livro):
    def __init__(
        self,
        id: int,
        titulo: str,
        autor: str,
        genero: str,
        ano: int,
        caminhoArquivo: str | Path,
        idioma: str = "Português",
        fonte: str = "Pessoal",
        nota: str = "",
    ) -> None:
        super().__init__(id, titulo, autor, genero, ano, idioma, fonte, nota)
        self.__caminhoArquivo = Path(caminhoArquivo).expanduser().resolve()

    @property
    def caminhoArquivo(self) -> Path:
        return self.__caminhoArquivo

    def __validarArquivo(self) -> bool:
        caminho = self.__caminhoArquivo
        if not caminho.is_file():
            raise FileNotFoundError(f"PDF não encontrado: {caminho}")
        if caminho.suffix.lower() != ".pdf":
            raise ValueError("O arquivo selecionado deve ter extensão .pdf.")
        with caminho.open("rb") as arquivo:
            if arquivo.read(5) != b"%PDF-":
                raise ValueError("O arquivo selecionado não é um PDF válido.")
        return True

    def verificarArquivo(self) -> bool:
        """Confere o PDF antes do cadastro ou da abertura."""
        return self.__validarArquivo()

    def abrir(self) -> Path:
        """Devolve o PDF validado para a interface exibir dentro do app."""
        self.verificarArquivo()
        return self.__caminhoArquivo


class LivroOnline(Livro):
    LIMITE_PDF = 50 * 1024 * 1024

    def __init__(
        self,
        id: int,
        titulo: str,
        autor: str,
        genero: str,
        ano: int,
        url: str,
        idioma: str = "Português",
        fonte: str = "Pessoal",
        nota: str = "",
        urlPdf: str | None = None,
    ) -> None:
        super().__init__(id, titulo, autor, genero, ano, idioma, fonte, nota)
        if not isinstance(url, str):
            raise ValueError("Informe um endereço HTTP ou HTTPS válido.")
        url = url.strip()
        endereco = urlparse(url)
        if endereco.scheme not in {"http", "https"} or not endereco.netloc:
            raise ValueError("Informe um endereço HTTP ou HTTPS válido.")
        self.url = url
        if not isinstance(urlPdf, str):
            raise ValueError("Informe um endereço HTTP ou HTTPS para o PDF online.")
        urlPdf = urlPdf.strip()
        endereco_pdf = urlparse(urlPdf)
        if endereco_pdf.scheme not in {"http", "https"} or not endereco_pdf.netloc:
            raise ValueError("Informe um endereço HTTP ou HTTPS para o PDF online.")
        self.urlPdf = urlPdf

    def baixarPdf(self) -> bytes:
        """Recebe um PDF direto em memória, sem gravá-lo no acervo."""
        requisicao = Request(self.urlPdf, headers={"User-Agent": "BiblioPy/1.0"})
        with urlopen(requisicao, timeout=20) as resposta:
            conteudo = resposta.read(self.LIMITE_PDF + 1)
        if len(conteudo) > self.LIMITE_PDF:
            raise ValueError("O PDF online ultrapassa o limite de 50 MB.")
        if not conteudo.startswith(b"%PDF-"):
            raise ValueError("O endereço não retornou um PDF válido.")
        return conteudo

    def abrir(self) -> bytes:
        return self.baixarPdf()
