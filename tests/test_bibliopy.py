"""Fluxos essenciais do acervo sem abrir janelas ou navegador."""

from collections import Counter
from io import BytesIO
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
)
from bibliopy.biblioteca import GENEROS


RAIZ = Path(__file__).resolve().parents[1]


def carregar_biblioteca() -> Biblioteca:
    biblioteca = Biblioteca()
    biblioteca.adicionarRepositorio(RepositorioGreenTeaPress(RAIZ / "catalogos" / "greenteapress.json"))
    biblioteca.carregarCatalogos()
    return biblioteca


class TestCatalogo(unittest.TestCase):
    def test_acervo_inicial_tem_apenas_cinco_pdfs(self) -> None:
        biblioteca = carregar_biblioteca()
        livros = biblioteca.listarLivros()
        self.assertEqual(len(livros), 5)
        self.assertEqual(Counter(livro.genero for livro in livros), {"Programação e Tecnologia": 5})
        self.assertEqual(sum(isinstance(livro, LivroPDFLocal) for livro in livros), 2)
        self.assertEqual(sum(isinstance(livro, LivroOnline) for livro in livros), 3)
        self.assertEqual(sum(isinstance(livro, LivroOnline) and livro.urlPdf is not None for livro in livros), 3)
        for livro in livros:
            if isinstance(livro, LivroPDFLocal):
                self.assertTrue(livro.verificarArquivo())

    def test_busca_e_filtro_encontram_pdfs_do_acervo(self) -> None:
        biblioteca = carregar_biblioteca()
        self.assertEqual([livro.titulo for livro in biblioteca.buscarPorTitulo("complexity")], ["Think Complexity, 2nd Edition"])
        self.assertEqual(len(biblioteca.buscarPorAutor("downey")), 5)
        self.assertEqual(len(biblioteca.filtrarPorGenero("programacao e tecnologia")), 5)
        self.assertEqual(biblioteca.obterLivro(18).fonte, "Green Tea Press")


class TestPersistencia(unittest.TestCase):
    def test_cadastro_e_remocao_continuam_apos_reiniciar(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "usuario.json"
            biblioteca = carregar_biblioteca()
            biblioteca.removerLivro(16)
            novo = LivroOnline(
                biblioteca.proximoId(),
                "Livro de teste",
                "Autora Exemplo",
                GENEROS[0],
                2020,
                "https://example.org/livro.pdf",
                urlPdf="https://example.org/livro.pdf",
            )
            biblioteca.adicionarLivro(novo)
            biblioteca.salvarDados(arquivo)

            salvo = json.loads(arquivo.read_text(encoding="utf-8"))
            self.assertEqual(salvo["ocultos"], [16])
            self.assertEqual(len(salvo["adicionados"]), 1)
            restaurada = carregar_biblioteca()
            restaurada.carregarDados(arquivo)
            self.assertIsNone(restaurada.obterLivro(16))
            self.assertEqual(restaurada.obterLivro(novo.id).titulo, "Livro de teste")
            self.assertEqual(len(restaurada.listarLivros()), 5)

            restaurada.removerLivro(novo.id)
            restaurada.salvarDados(arquivo)
            novamente = carregar_biblioteca()
            novamente.carregarDados(arquivo)
            self.assertIsNone(novamente.obterLivro(novo.id))
            self.assertEqual(len(novamente.listarLivros()), 4)

    def test_dados_invalidos_nao_alteram_o_acervo(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "usuario.json"
            for conteudo in (
                '{"versao": 1, "ocultos": [0], "adicionados": []}',
                '{"versao": 1, "ocultos": [[1]], "adicionados": []}',
            ):
                with self.subTest(conteudo=conteudo):
                    arquivo.write_text(conteudo, encoding="utf-8")
                    biblioteca = carregar_biblioteca()
                    with self.assertRaises(ValueError):
                        biblioteca.carregarDados(arquivo)
                    self.assertEqual(len(biblioteca.listarLivros()), 5)

    def test_dados_antigos_nao_reintroduzem_paginas_web(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "usuario.json"
            arquivo.write_text(json.dumps({"versao": 1, "ocultos": [1], "adicionados": [
                {"tipo": "online", "id": 10001, "url": "https://example.org/livro"}
            ]}), encoding="utf-8")
            biblioteca = carregar_biblioteca()
            biblioteca.carregarDados(arquivo)
            self.assertEqual(len(biblioteca.listarLivros()), 5)
            self.assertIsNone(biblioteca.obterLivro(10001))

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

    def test_pdf_online_pessoal_persiste_com_seu_endereco(self) -> None:
        with tempfile.TemporaryDirectory() as pasta:
            arquivo = Path(pasta) / "usuario.json"
            biblioteca = carregar_biblioteca()
            livro = LivroOnline(
                biblioteca.proximoId(), "Meu PDF online", "Autora", GENEROS[0], 2020,
                "https://example.org/livro", urlPdf="https://example.org/livro.pdf",
            )
            biblioteca.adicionarLivro(livro)
            biblioteca.salvarDados(arquivo)
            restaurada = carregar_biblioteca()
            restaurada.carregarDados(arquivo)
            self.assertEqual(restaurada.obterLivro(livro.id).urlPdf, "https://example.org/livro.pdf")


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

    def test_livro_online_exige_pdf_direto(self) -> None:
        with self.assertRaises(ValueError):
            LivroOnline(10002, "Exemplo", "Autora", GENEROS[0], 2020, "https://example.org/pagina")

    def test_pdf_online_e_recebido_em_memoria_e_rejeita_resposta_invalida(self) -> None:
        livro = LivroOnline(
            10001, "Exemplo", "Autora", GENEROS[0], 2020,
            "https://example.org/livro", urlPdf="https://example.org/livro.pdf",
        )
        conteudo = b"%PDF-1.4\nconteudo de teste"
        with patch("bibliopy.livros.urlopen", return_value=BytesIO(conteudo)) as obter:
            self.assertEqual(livro.abrir(), conteudo)
            self.assertEqual(obter.call_args.kwargs["timeout"], 20)
        with patch("bibliopy.livros.urlopen", return_value=BytesIO(b"<html>nao e pdf</html>")):
            with self.assertRaisesRegex(ValueError, "PDF válido"):
                livro.baixarPdf()
        with patch.object(livro, "LIMITE_PDF", 5):
            with patch("bibliopy.livros.urlopen", return_value=BytesIO(conteudo)):
                with self.assertRaisesRegex(ValueError, "50 MB"):
                    livro.baixarPdf()


if __name__ == "__main__":
    unittest.main()
