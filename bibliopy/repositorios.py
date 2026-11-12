"""Catálogos selecionados das duas fontes da proposta."""

from abc import ABC, abstractmethod
import json
from pathlib import Path

from .livros import Livro, LivroOnline, LivroPDFLocal


class RepositorioDigital(ABC):
    def __init__(self, nome: str, arquivoCatalogo: str | Path) -> None:
        self.nome = nome
        self.arquivoCatalogo = Path(arquivoCatalogo).resolve()

    def _ler_registros(self) -> list[dict]:
        with self.arquivoCatalogo.open("r", encoding="utf-8") as arquivo:
            registros = json.load(arquivo)
        if not isinstance(registros, list):
            raise ValueError(f"Catálogo inválido: {self.arquivoCatalogo}")
        return registros

    @abstractmethod
    def obterLivros(self) -> list[Livro]:
        """Converte registros do catálogo em objetos Livro."""


class RepositorioGutenberg(RepositorioDigital):
    def __init__(self, arquivoCatalogo: str | Path) -> None:
        super().__init__("Project Gutenberg", arquivoCatalogo)

    def obterLivros(self) -> list[Livro]:
        livros = []
        for registro in self._ler_registros():
            numero = registro["gutenberg_id"]
            if isinstance(numero, bool) or not isinstance(numero, int) or numero <= 0:
                raise ValueError("O identificador do Gutenberg deve ser positivo.")
            livros.append(
                LivroOnline(
                    id=registro["id"],
                    titulo=registro["titulo"],
                    autor=registro["autor"],
                    genero=registro["genero"],
                    ano=registro["ano"],
                    url=f"https://www.gutenberg.org/ebooks/{numero}",
                    idioma=registro["idioma"],
                    fonte=self.nome,
                    nota=registro.get("nota", ""),
                )
            )
        return livros


class RepositorioGreenTeaPress(RepositorioDigital):
    def __init__(self, arquivoCatalogo: str | Path) -> None:
        super().__init__("Green Tea Press", arquivoCatalogo)

    def obterLivros(self) -> list[Livro]:
        livros = []
        for registro in self._ler_registros():
            dados = dict(
                id=registro["id"],
                titulo=registro["titulo"],
                autor=registro["autor"],
                genero=registro["genero"],
                ano=registro["ano"],
                idioma=registro["idioma"],
                fonte=self.nome,
                nota=registro.get("nota", ""),
            )
            caminho_relativo = registro.get("pdf_local")
            caminho = (
                self.arquivoCatalogo.parent.parent / caminho_relativo
                if caminho_relativo
                else None
            )
            if caminho is not None and caminho.is_file():
                livros.append(LivroPDFLocal(**dados, caminhoArquivo=caminho))
            else:
                livros.append(LivroOnline(**dados, url=registro["url"]))
        return livros
