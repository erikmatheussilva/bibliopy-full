"""Tipos de livro e comportamento de abertura."""

from abc import ABC, abstractmethod
from pathlib import Path
from urllib.parse import urlparse
import webbrowser


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
    def abrir(self) -> bool | Path:
        """Entrega o PDF local ao leitor ou abre o endereço online."""

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
    ) -> None:
        super().__init__(id, titulo, autor, genero, ano, idioma, fonte, nota)
        if not isinstance(url, str):
            raise ValueError("Informe um endereço HTTP ou HTTPS válido.")
        url = url.strip()
        endereco = urlparse(url)
        if endereco.scheme not in {"http", "https"} or not endereco.netloc:
            raise ValueError("Informe um endereço HTTP ou HTTPS válido.")
        self.url = url

    def abrir(self) -> bool:
        return webbrowser.open(self.url)
