"""BiblioPy: acervo digital local em Python."""

from .biblioteca import Biblioteca
from .interface import InterfaceBiblioteca
from .livros import Livro, LivroOnline, LivroPDFLocal
from .repositorios import (
    RepositorioDigital,
    RepositorioGreenTeaPress,
    RepositorioGutenberg,
)

__all__ = [
    "Biblioteca",
    "InterfaceBiblioteca",
    "Livro",
    "LivroOnline",
    "LivroPDFLocal",
    "RepositorioDigital",
    "RepositorioGreenTeaPress",
    "RepositorioGutenberg",
]
