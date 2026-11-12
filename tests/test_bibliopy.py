"""Fluxos essenciais do acervo sem abrir janelas ou navegador."""

from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bibliopy import (
    Biblioteca,
    LivroOnline,
    LivroPDFLocal,
    RepositorioGreenTeaPress,
    RepositorioGutenberg,
)
from bibliopy.biblioteca import GENEROS


RAIZ = Path(__file__).resolve().parents[1]


def carregar_biblioteca() -> Biblioteca:
    biblioteca = Biblioteca()
    biblioteca.adicionarRepositorio(RepositorioGutenberg(RAIZ / "catalogos" / "gutenberg.json"))
    biblioteca.adicionarRepositorio(RepositorioGreenTeaPress(RAIZ / "catalogos" / "greenteapress.json"))
    biblioteca.carregarCatalogos()
    return biblioteca


class TestCatalogo(unittest.TestCase):
    def test_acervo_inicial_tem_25_livros_e_cinco_por_categoria(self) -> None:
        biblioteca = carregar_biblioteca()
        livros = biblioteca.listarLivros()
        self.assertEqual(len(livros), 25)
        self.assertEqual(Counter(livro.genero for livro in livros), {genero: 5 for genero in GENEROS})
        self.assertEqual(sum(isinstance(livro, LivroPDFLocal) for livro in livros), 2)
        self.assertEqual(sum(isinstance(livro, LivroOnline) for livro in livros), 23)
        for livro in livros:
            if isinstance(livro, LivroPDFLocal):
                self.assertTrue(livro.verificarArquivo())

    def test_busca_ignora_acentos_e_combina_com_filtro(self) -> None:
        biblioteca = carregar_biblioteca()
        self.assertEqual([livro.titulo for livro in biblioteca.buscarPorTitulo("memorias postumas")], ["Memórias Póstumas de Brás Cubas"])
        self.assertIn("Dom Casmurro", [livro.titulo for livro in biblioteca.buscarPorAutor("machado")])
        self.assertEqual(len(biblioteca.filtrarPorGenero("fantasia e aventura")), 5)
        self.assertEqual(biblioteca.obterLivro(15).fonte, "Project Gutenberg")


class TestPersistencia(unittest.TestCase):
    def test_cadastro_e_remocao_continuam_apos_reiniciar(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "usuario.json"
            biblioteca = carregar_biblioteca()
            biblioteca.removerLivro(1)
            novo = LivroOnline(
                biblioteca.proximoId(),
                "Livro de teste",
                "Autora Exemplo",
                GENEROS[0],
                2020,
                "https://example.org/livro",
            )
            biblioteca.adicionarLivro(novo)
            biblioteca.salvarDados(arquivo)

            salvo = json.loads(arquivo.read_text(encoding="utf-8"))
            self.assertEqual(salvo["ocultos"], [1])
            self.assertEqual(len(salvo["adicionados"]), 1)
            restaurada = carregar_biblioteca()
            restaurada.carregarDados(arquivo)
            self.assertIsNone(restaurada.obterLivro(1))
            self.assertEqual(restaurada.obterLivro(novo.id).titulo, "Livro de teste")
            self.assertEqual(len(restaurada.listarLivros()), 25)

            restaurada.removerLivro(novo.id)
            restaurada.salvarDados(arquivo)
            novamente = carregar_biblioteca()
            novamente.carregarDados(arquivo)
            self.assertIsNone(novamente.obterLivro(novo.id))
            self.assertEqual(len(novamente.listarLivros()), 24)

    def test_dados_invalidos_nao_alteram_o_acervo(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "usuario.json"
            for conteudo in (
                '{"versao": 1, "ocultos": [999], "adicionados": []}',
                '{"versao": 1, "ocultos": [[1]], "adicionados": []}',
            ):
                with self.subTest(conteudo=conteudo):
                    arquivo.write_text(conteudo, encoding="utf-8")
                    biblioteca = carregar_biblioteca()
                    with self.assertRaises(ValueError):
                        biblioteca.carregarDados(arquivo)
                    self.assertEqual(len(biblioteca.listarLivros()), 25)

    def test_pdf_pessoal_persiste_com_seu_caminho(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "livro.pdf"
            caminho.write_bytes(b"%PDF-1.4\nconteudo de teste")
            arquivo = Path(pasta) / "usuario.json"
            biblioteca = carregar_biblioteca()
            livro = LivroPDFLocal(
                biblioteca.proximoId(), "Meu PDF", "Autora", GENEROS[0], 2020, caminho
            )
            biblioteca.adicionarLivro(livro)
            biblioteca.salvarDados(arquivo)

            restaurada = carregar_biblioteca()
            restaurada.carregarDados(arquivo)
            recuperado = restaurada.obterLivro(livro.id)
            self.assertIsInstance(recuperado, LivroPDFLocal)
            self.assertEqual(recuperado.caminhoArquivo, caminho.resolve())
            self.assertTrue(recuperado.verificarArquivo())


class TestAbertura(unittest.TestCase):
    def test_pdf_local_entrega_caminho_validado_para_leitor_interno(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "teste.pdf"
            caminho.write_bytes(b"arquivo incorreto")
            livro = LivroPDFLocal(10001, "Exemplo", "Autora", GENEROS[0], 2020, caminho)
            with self.assertRaisesRegex(ValueError, "PDF válido"):
                livro.abrir()
            caminho.write_bytes(b"%PDF-1.4\nconteudo de teste")
            self.assertEqual(livro.abrir(), caminho.resolve())

    def test_livro_online_usa_o_navegador(self) -> None:
        livro = LivroOnline(10001, "Exemplo", "Autora", GENEROS[0], 2020, "https://example.org/livro")
        with patch("bibliopy.livros.webbrowser.open", return_value=True) as abrir:
            self.assertTrue(livro.abrir())
            abrir.assert_called_once_with("https://example.org/livro")
        with self.assertRaises(ValueError):
            LivroOnline(10002, "Exemplo", "Autora", GENEROS[0], 2020, "file:///segredo")


if __name__ == "__main__":
    unittest.main()
