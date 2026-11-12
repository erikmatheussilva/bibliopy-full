"""Regras do acervo e persistência das alterações do usuário."""

import json
import os
from pathlib import Path
import tempfile
import unicodedata

from .livros import Livro, LivroOnline, LivroPDFLocal
from .repositorios import RepositorioDigital


GENEROS = (
    "Literatura Clássica",
    "Fantasia e Aventura",
    "Literatura para Vestibulares",
    "Programação e Tecnologia",
    "Mistério, Suspense e Terror",
)


def _normalizar(texto: str) -> str:
    sem_acentos = "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )
    return sem_acentos.casefold().strip()


class Biblioteca:
    def __init__(self) -> None:
        self.livros: dict[int, Livro] = {}
        self.repositorios: list[RepositorioDigital] = []
        self._ids_catalogo: set[int] = set()
        self._ids_usuario: set[int] = set()
        self._ids_ocultos: set[int] = set()

    def adicionarRepositorio(self, repo: RepositorioDigital) -> None:
        if not isinstance(repo, RepositorioDigital):
            raise TypeError("O repositório deve herdar de RepositorioDigital.")
        self.repositorios.append(repo)

    def carregarCatalogos(self) -> None:
        novos_livros: dict[int, Livro] = {}
        for repositorio in self.repositorios:
            for livro in repositorio.obterLivros():
                if livro.id in novos_livros:
                    raise ValueError(f"ID duplicado nos catálogos: {livro.id}")
                if livro.genero not in GENEROS:
                    raise ValueError(f"Categoria desconhecida: {livro.genero}")
                novos_livros[livro.id] = livro
        self.livros = novos_livros
        self._ids_catalogo = set(novos_livros)
        self._ids_usuario.clear()
        self._ids_ocultos.clear()

    def carregarDados(self, arquivo: str | Path) -> None:
        caminho = Path(arquivo)
        if not caminho.exists():
            return
        with caminho.open("r", encoding="utf-8") as entrada:
            dados = json.load(entrada)
        if not isinstance(dados, dict) or dados.get("versao") != 1:
            raise ValueError("Formato do arquivo de dados não reconhecido.")
        ocultos = dados.get("ocultos", [])
        registros = dados.get("adicionados", [])
        if not isinstance(ocultos, list) or not isinstance(registros, list):
            raise ValueError("O arquivo de dados está inválido.")
        if any(
            isinstance(id, bool) or not isinstance(id, int) or id not in self._ids_catalogo
            for id in ocultos
        ):
            raise ValueError("O arquivo contém livros ocultos desconhecidos.")
        novos_ocultos = set(ocultos)

        novos_livros = {
            id: livro
            for id, livro in self.livros.items()
            if id in self._ids_catalogo and id not in novos_ocultos
        }
        novos_ids_usuario: set[int] = set()
        for registro in registros:
            if not isinstance(registro, dict):
                raise ValueError("Registro de livro inválido no arquivo de dados.")
            comum = dict(
                id=registro["id"],
                titulo=registro["titulo"],
                autor=registro["autor"],
                genero=registro["genero"],
                ano=registro["ano"],
                idioma=registro["idioma"],
                fonte="Pessoal",
                nota=registro.get("nota", ""),
            )
            if registro.get("tipo") == "pdf":
                livro = LivroPDFLocal(**comum, caminhoArquivo=registro["caminho"])
            elif registro.get("tipo") == "online":
                livro = LivroOnline(**comum, url=registro["url"])
            else:
                raise ValueError("Tipo de livro desconhecido no arquivo de dados.")
            if livro.genero not in GENEROS or livro.id in self._ids_catalogo:
                raise ValueError("Livro pessoal inválido ou com ID reservado.")
            if livro.id in novos_livros:
                raise ValueError(f"ID duplicado no arquivo de dados: {livro.id}")
            novos_livros[livro.id] = livro
            novos_ids_usuario.add(livro.id)

        self.livros = novos_livros
        self._ids_ocultos = novos_ocultos
        self._ids_usuario = novos_ids_usuario

    def salvarDados(self, arquivo: str | Path) -> None:
        caminho = Path(arquivo)
        caminho.parent.mkdir(parents=True, exist_ok=True)
        adicionados = []
        for id in sorted(self._ids_usuario):
            livro = self.livros[id]
            registro = dict(
                id=livro.id,
                titulo=livro.titulo,
                autor=livro.autor,
                genero=livro.genero,
                ano=livro.ano,
                idioma=livro.idioma,
                nota=livro.nota,
            )
            if isinstance(livro, LivroPDFLocal):
                registro.update(tipo="pdf", caminho=str(livro.caminhoArquivo))
            else:
                registro.update(tipo="online", url=livro.url)
            adicionados.append(registro)
        dados = {
            "versao": 1,
            "ocultos": sorted(self._ids_ocultos),
            "adicionados": adicionados,
        }
        temporario: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w",
                encoding="utf-8",
                dir=caminho.parent,
                prefix=".bibliopy-",
                suffix=".tmp",
                delete=False,
            ) as saida:
                temporario = Path(saida.name)
                json.dump(dados, saida, ensure_ascii=False, indent=2)
                saida.write("\n")
            os.replace(temporario, caminho)
        finally:
            if temporario is not None:
                temporario.unlink(missing_ok=True)

    def adicionarLivro(self, livro: Livro) -> None:
        if livro.id in self._ids_catalogo or livro.id in self.livros:
            raise ValueError(f"Já existe um livro com o ID {livro.id}.")
        if livro.genero not in GENEROS:
            raise ValueError("Selecione uma das cinco categorias do acervo.")
        self.livros[livro.id] = livro
        self._ids_usuario.add(livro.id)

    def removerLivro(self, id: int) -> bool:
        if id not in self.livros:
            return False
        del self.livros[id]
        if id in self._ids_catalogo:
            self._ids_ocultos.add(id)
        else:
            self._ids_usuario.discard(id)
        return True

    def buscarPorTitulo(self, titulo: str) -> list[Livro]:
        termo = _normalizar(titulo)
        return [livro for livro in self.listarLivros() if termo in _normalizar(livro.titulo)]

    def buscarPorAutor(self, autor: str) -> list[Livro]:
        termo = _normalizar(autor)
        return [livro for livro in self.listarLivros() if termo in _normalizar(livro.autor)]

    def filtrarPorGenero(self, genero: str) -> list[Livro]:
        if not genero or genero == "Todos":
            return self.listarLivros()
        termo = _normalizar(genero)
        return [livro for livro in self.listarLivros() if _normalizar(livro.genero) == termo]

    def listarLivros(self) -> list[Livro]:
        return sorted(
            self.livros.values(),
            key=lambda livro: (_normalizar(livro.titulo), livro.id),
        )

    def obterLivro(self, id: int) -> Livro | None:
        return self.livros.get(id)

    def abrirLivro(self, id: int) -> bool | Path:
        livro = self.obterLivro(id)
        return livro.abrir() if livro is not None else False

    def proximoId(self) -> int:
        return max({10_000} | self._ids_catalogo | set(self.livros)) + 1
