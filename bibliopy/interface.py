"""Janela Tkinter que apresenta o acervo e aciona a Biblioteca."""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from pathlib import Path
import threading

from PIL import ImageTk
import pypdfium2 as pdfium

from .biblioteca import Biblioteca, GENEROS
from .livros import Livro, LivroOnline, LivroPDFLocal


MARINHO = "#11243C"
AZUL = "#245A8D"
VERDE_AGUA = "#21A9A3"
BRANCO = "#FFFFFF"
CINZA_AZULADO = "#506073"
FUNDO = "#F4F7FA"


class InterfaceBiblioteca:
    def __init__(self, biblioteca: Biblioteca, arquivoDados: str | Path) -> None:
        self.biblioteca = biblioteca
        self.arquivoDados = Path(arquivoDados)
        self.janela: tk.Tk | None = None
        self.campoBusca: ttk.Entry | None = None
        self.listaLivros: ttk.Treeview | None = None
        self.filtroGenero: ttk.Combobox | None = None
        self._detalhes: tk.StringVar | None = None
        self._status: tk.StringVar | None = None
        self._logoImagem: tk.PhotoImage | None = None
        self._botaoAbrir: ttk.Button | None = None
        self._janelaLeitor: tk.Toplevel | None = None
        self._documentoLeitor: pdfium.PdfDocument | None = None
        self._canvasLeitor: tk.Canvas | None = None
        self._imagemLeitor: ImageTk.PhotoImage | None = None
        self._paginaLeitor = 0
        self._zoomLeitor = 1.0
        self._paginaTexto: tk.StringVar | None = None
        self._zoomTexto: tk.StringVar | None = None
        self._botaoAnterior: ttk.Button | None = None
        self._botaoProximo: ttk.Button | None = None
        self._botaoMenos: ttk.Button | None = None
        self._botaoMais: ttk.Button | None = None
        self._livroLeitorId: int | None = None
        self._dadosPdfOnline: bytes | None = None
        self._baixandoPdf = False

    def criarJanela(self) -> None:
        janela = tk.Tk()
        janela.title("BiblioPy — Biblioteca Digital")
        janela.geometry("1120x690")
        janela.minsize(840, 540)
        janela.configure(bg=FUNDO)
        janela.protocol("WM_DELETE_WINDOW", self._fechar_app)
        self.janela = janela

        estilo = ttk.Style(janela)
        estilo.theme_use("clam")
        estilo.configure("Bibliopy.TFrame", background=FUNDO)
        estilo.configure("Painel.TFrame", background=BRANCO)
        estilo.configure("Bibliopy.TLabel", background=FUNDO, foreground=MARINHO)
        estilo.configure("Painel.TLabel", background=BRANCO, foreground=MARINHO)
        estilo.configure("Titulo.TLabel", background=FUNDO, foreground=MARINHO, font=("Segoe UI", 22, "bold"))
        estilo.configure("Subtitulo.TLabel", background=FUNDO, foreground=CINZA_AZULADO, font=("Segoe UI", 10))
        estilo.configure("Secao.TLabel", background=BRANCO, foreground=MARINHO, font=("Segoe UI", 13, "bold"))
        estilo.configure("Bibliopy.TButton", padding=(12, 8), font=("Segoe UI", 9))
        estilo.configure("Destaque.TButton", padding=(13, 8), background=AZUL, foreground=BRANCO, font=("Segoe UI", 9, "bold"))
        estilo.map("Destaque.TButton", background=[("active", MARINHO)])
        estilo.configure("Bibliopy.Treeview", rowheight=30, font=("Segoe UI", 9), background=BRANCO, fieldbackground=BRANCO, foreground=MARINHO)
        estilo.configure("Bibliopy.Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#E8EEF3", foreground=MARINHO)
        estilo.map("Bibliopy.Treeview", background=[("selected", AZUL)], foreground=[("selected", BRANCO)])

        pagina = ttk.Frame(janela, style="Bibliopy.TFrame", padding=22)
        pagina.pack(fill="both", expand=True)

        cabecalho = ttk.Frame(pagina, style="Bibliopy.TFrame")
        cabecalho.pack(fill="x", pady=(0, 20))
        self._logoImagem = tk.PhotoImage(file=str(Path(__file__).resolve().parent.parent / "logo.png"))
        logo = ttk.Label(cabecalho, image=self._logoImagem, style="Bibliopy.TLabel")
        logo.pack(side="left", padx=(0, 12))
        titulos = ttk.Frame(cabecalho, style="Bibliopy.TFrame")
        titulos.pack(side="left")
        ttk.Label(titulos, text="BiblioPy", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(titulos, text="Sua biblioteca digital em um só lugar", style="Subtitulo.TLabel").pack(anchor="w")

        controles = ttk.Frame(pagina, style="Bibliopy.TFrame")
        controles.pack(fill="x", pady=(0, 14))
        controles.columnconfigure(0, weight=1)
        self.campoBusca = ttk.Entry(controles, font=("Segoe UI", 10))
        self.campoBusca.grid(row=0, column=0, sticky="ew", padx=(0, 8), ipady=5)
        self.campoBusca.bind("<Return>", lambda _evento: self.pesquisarLivro())
        ttk.Button(controles, text="Pesquisar", command=self.pesquisarLivro, style="Destaque.TButton").grid(row=0, column=1, padx=(0, 12))
        self.filtroGenero = ttk.Combobox(controles, state="readonly", values=("Todos", *GENEROS), width=27)
        self.filtroGenero.current(0)
        self.filtroGenero.grid(row=0, column=2, sticky="ew")
        self.filtroGenero.bind("<<ComboboxSelected>>", lambda _evento: self.filtrarLivros())

        conteudo = ttk.Panedwindow(pagina, orient="horizontal")
        conteudo.pack(fill="both", expand=True)
        painel_lista = ttk.Frame(conteudo, style="Painel.TFrame", padding=12)
        painel_detalhes = ttk.Frame(conteudo, style="Painel.TFrame", padding=18)
        conteudo.add(painel_lista, weight=3)
        conteudo.add(painel_detalhes, weight=2)

        ttk.Label(painel_lista, text="Acervo", style="Secao.TLabel").pack(anchor="w", pady=(0, 10))
        tabela = ttk.Frame(painel_lista, style="Painel.TFrame")
        tabela.pack(fill="both", expand=True)
        tabela.rowconfigure(0, weight=1)
        tabela.columnconfigure(0, weight=1)
        colunas = ("titulo", "autor", "categoria", "formato")
        self.listaLivros = ttk.Treeview(tabela, columns=colunas, show="headings", selectmode="browse", style="Bibliopy.Treeview")
        for coluna, texto, largura in (
            ("titulo", "Título", 230),
            ("autor", "Autor", 160),
            ("categoria", "Categoria", 175),
            ("formato", "Acesso", 90),
        ):
            self.listaLivros.heading(coluna, text=texto)
            self.listaLivros.column(coluna, width=largura, minwidth=70, stretch=coluna != "formato")
        self.listaLivros.grid(row=0, column=0, sticky="nsew")
        rolagem = ttk.Scrollbar(tabela, orient="vertical", command=self.listaLivros.yview)
        rolagem.grid(row=0, column=1, sticky="ns")
        rolagem_horizontal = ttk.Scrollbar(tabela, orient="horizontal", command=self.listaLivros.xview)
        rolagem_horizontal.grid(row=1, column=0, sticky="ew")
        self.listaLivros.configure(yscrollcommand=rolagem.set, xscrollcommand=rolagem_horizontal.set)
        self.listaLivros.bind("<<TreeviewSelect>>", self._mostrar_detalhes)
        self.listaLivros.bind("<Double-1>", lambda _evento: self.abrirLivro())

        ttk.Label(painel_detalhes, text="Detalhes do livro", style="Secao.TLabel").pack(anchor="w", pady=(0, 14))
        self._detalhes = tk.StringVar(value="Selecione um livro para ver os detalhes.")
        ttk.Label(
            painel_detalhes,
            textvariable=self._detalhes,
            style="Painel.TLabel",
            justify="left",
            anchor="nw",
            wraplength=310,
            font=("Segoe UI", 10),
        ).pack(fill="both", expand=True, anchor="nw")
        self._botaoAbrir = ttk.Button(painel_detalhes, text="Abrir livro", command=self.abrirLivro, style="Destaque.TButton")
        self._botaoAbrir.pack(fill="x", pady=(10, 8))
        ttk.Button(painel_detalhes, text="Cadastrar livro", command=self.cadastrarLivro, style="Bibliopy.TButton").pack(fill="x", pady=(0, 8))
        ttk.Button(painel_detalhes, text="Remover da biblioteca", command=self.removerLivro, style="Bibliopy.TButton").pack(fill="x")

        self._status = tk.StringVar(value="Pronto.")
        ttk.Label(pagina, textvariable=self._status, style="Subtitulo.TLabel").pack(anchor="w", pady=(12, 0))
        self.criarMenu()
        self.exibirLivros()

    def criarMenu(self) -> None:
        if self.janela is None:
            raise RuntimeError("Crie a janela antes do menu.")
        barra = tk.Menu(self.janela)
        acervo = tk.Menu(barra, tearoff=False)
        acervo.add_command(label="Cadastrar livro...", command=self.cadastrarLivro)
        acervo.add_command(label="Abrir selecionado", command=self.abrirLivro)
        acervo.add_separator()
        acervo.add_command(label="Sair", command=self._fechar_app)
        barra.add_cascade(label="Acervo", menu=acervo)
        ajuda = tk.Menu(barra, tearoff=False)
        ajuda.add_command(
            label="Sobre",
            command=lambda: messagebox.showinfo(
                "Sobre o BiblioPy",
                "BiblioPy — biblioteca digital em Python.\nProjeto de Programação Orientada a Objetos.",
                parent=self.janela,
            ),
        )
        barra.add_cascade(label="Ajuda", menu=ajuda)
        self.janela.config(menu=barra)

    def exibirLivros(self) -> None:
        if self.listaLivros is None or self.campoBusca is None or self.filtroGenero is None:
            return
        selecionados = self.listaLivros.selection()
        id_anterior = selecionados[0] if selecionados else None
        for linha in self.listaLivros.get_children():
            self.listaLivros.delete(linha)
        termo = self.campoBusca.get().strip()
        genero = self.filtroGenero.get()
        ids_pesquisa = None
        if termo:
            ids_pesquisa = {
                livro.id
                for livro in self.biblioteca.buscarPorTitulo(termo)
                + self.biblioteca.buscarPorAutor(termo)
            }
        for livro in self.biblioteca.filtrarPorGenero(genero):
            if ids_pesquisa is not None and livro.id not in ids_pesquisa:
                continue
            formato = "PDF local" if isinstance(livro, LivroPDFLocal) else "Online"
            self.listaLivros.insert(
                "", "end", iid=str(livro.id),
                values=(livro.titulo, livro.autor, livro.genero, formato),
            )
        if id_anterior and self.listaLivros.exists(id_anterior):
            self.listaLivros.selection_set(id_anterior)
        else:
            self._mostrar_detalhes()
        if self._status is not None:
            self._status.set("Pronto." if self.listaLivros.get_children() else "Nenhum livro encontrado.")

    def pesquisarLivro(self) -> None:
        self.exibirLivros()

    def filtrarLivros(self) -> None:
        self.exibirLivros()

    def _livro_selecionado(self) -> Livro | None:
        if self.listaLivros is None:
            return None
        selecao = self.listaLivros.selection()
        return self.biblioteca.obterLivro(int(selecao[0])) if selecao else None

    def _mostrar_detalhes(self, _evento: object = None) -> None:
        if self._detalhes is None:
            return
        livro = self._livro_selecionado()
        if livro is None:
            self._detalhes.set("Selecione um livro para ver os detalhes.")
            self._botaoAbrir.configure(text="Abrir livro")
            return
        formato = "PDF no computador" if isinstance(livro, LivroPDFLocal) else "PDF online"
        localizacao = str(livro.caminhoArquivo) if isinstance(livro, LivroPDFLocal) else livro.urlPdf
        self._detalhes.set(f"{livro.exibirDados()}\nFormato: {formato}\nLocalização: {localizacao}")
        self._botaoAbrir.configure(text="Ler no BiblioPy")

    def abrirLivro(self) -> None:
        livro = self._livro_selecionado()
        if livro is None:
            messagebox.showinfo("Abrir livro", "Selecione um livro do acervo.", parent=self.janela)
            return
        if self._baixandoPdf:
            return
        if isinstance(livro, LivroOnline):
            if self._janelaLeitor is not None and self._livroLeitorId == livro.id:
                self._janelaLeitor.lift()
                self._janelaLeitor.focus_set()
                return
            self._baixandoPdf = True
            self._botaoAbrir.state(["disabled"])
            self._status.set("Baixando PDF online...")
            threading.Thread(target=self._baixar_pdf_online, args=(livro,), daemon=True).start()
            return
        try:
            aberto = self.biblioteca.abrirLivro(livro.id)
        except (OSError, ValueError) as erro:
            messagebox.showerror("Não foi possível abrir", str(erro), parent=self.janela)
            return
        if isinstance(livro, LivroPDFLocal):
            self._abrir_leitor_pdf(livro, aberto)

    def _baixar_pdf_online(self, livro: LivroOnline) -> None:
        try:
            conteudo = livro.abrir()
            mensagem = None
        except (OSError, ValueError) as erro:
            conteudo = None
            mensagem = str(erro)
        try:
            self.janela.after(0, lambda: self._finalizar_download_pdf(livro, conteudo, mensagem))
        except (RuntimeError, tk.TclError):
            pass  # A janela pode ter sido fechada durante a transferência.

    def _finalizar_download_pdf(self, livro: LivroOnline, conteudo: bytes | None, mensagem: str | None) -> None:
        self._baixandoPdf = False
        self._botaoAbrir.state(["!disabled"])
        self._status.set("Pronto.")
        if mensagem is not None:
            messagebox.showerror("Não foi possível baixar o PDF", mensagem, parent=self.janela)
        elif conteudo is not None:
            self._abrir_leitor_pdf(livro, conteudo)

    def _abrir_leitor_pdf(self, livro: LivroPDFLocal | LivroOnline, fonte: Path | bytes) -> None:
        """Abre uma janela do próprio BiblioPy para o PDF selecionado."""
        if self._janelaLeitor is not None and self._livroLeitorId == livro.id:
            self._janelaLeitor.lift()
            self._janelaLeitor.focus_set()
            return
        try:
            documento = pdfium.PdfDocument(fonte if isinstance(fonte, bytes) else str(fonte))
            if len(documento) == 0:
                documento.close()
                raise ValueError("O PDF não contém páginas.")
        except (OSError, ValueError, pdfium.PdfiumError) as erro:
            messagebox.showerror("Não foi possível ler o PDF", str(erro), parent=self.janela)
            return

        self._fechar_leitor_pdf()
        janela = tk.Toplevel(self.janela)
        janela.title(f"BiblioPy — {livro.titulo}")
        janela.geometry("1000x780")
        janela.minsize(700, 500)
        janela.transient(self.janela)
        janela.configure(bg=FUNDO)
        janela.protocol("WM_DELETE_WINDOW", self._fechar_leitor_pdf)
        self._janelaLeitor = janela
        self._documentoLeitor = documento
        self._dadosPdfOnline = fonte if isinstance(fonte, bytes) else None
        self._livroLeitorId = livro.id
        self._paginaLeitor = 0
        self._zoomLeitor = 1.0

        pagina = ttk.Frame(janela, style="Bibliopy.TFrame", padding=12)
        pagina.pack(fill="both", expand=True)
        ttk.Label(pagina, text=livro.titulo, style="Titulo.TLabel").pack(anchor="w", pady=(0, 8))
        barra = ttk.Frame(pagina, style="Bibliopy.TFrame")
        barra.pack(fill="x", pady=(0, 9))
        self._botaoAnterior = ttk.Button(barra, text="◀ Anterior", command=self._pagina_anterior)
        self._botaoAnterior.pack(side="left")
        self._paginaTexto = tk.StringVar(value="Página 1")
        ttk.Label(barra, textvariable=self._paginaTexto, style="Bibliopy.TLabel").pack(side="left", padx=12)
        self._botaoProximo = ttk.Button(barra, text="Próxima ▶", command=self._proxima_pagina)
        self._botaoProximo.pack(side="left")
        self._botaoMais = ttk.Button(barra, text="Aumentar +", command=lambda: self._alterar_zoom(0.25))
        self._botaoMais.pack(side="right")
        self._zoomTexto = tk.StringVar(value="100%")
        ttk.Label(barra, textvariable=self._zoomTexto, style="Bibliopy.TLabel").pack(side="right", padx=8)
        self._botaoMenos = ttk.Button(barra, text="Diminuir −", command=lambda: self._alterar_zoom(-0.25))
        self._botaoMenos.pack(side="right")

        area = ttk.Frame(pagina, style="Painel.TFrame")
        area.pack(fill="both", expand=True)
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)
        self._canvasLeitor = tk.Canvas(area, bg="#DEE6ED", highlightthickness=0)
        self._canvasLeitor.grid(row=0, column=0, sticky="nsew")
        rolagem_vertical = ttk.Scrollbar(area, orient="vertical", command=self._canvasLeitor.yview)
        rolagem_vertical.grid(row=0, column=1, sticky="ns")
        rolagem_horizontal = ttk.Scrollbar(area, orient="horizontal", command=self._canvasLeitor.xview)
        rolagem_horizontal.grid(row=1, column=0, sticky="ew")
        self._canvasLeitor.configure(
            yscrollcommand=rolagem_vertical.set,
            xscrollcommand=rolagem_horizontal.set,
        )
        janela.bind("<Left>", lambda _evento: self._pagina_anterior())
        janela.bind("<Right>", lambda _evento: self._proxima_pagina())
        if not self._mostrar_pagina_pdf(0):
            self._fechar_leitor_pdf()
        else:
            janela.lift(self.janela)
            janela.focus_set()

    def _mostrar_pagina_pdf(self, indice: int) -> bool:
        """Renderiza só a página atual e mantém a imagem no Canvas."""
        documento = self._documentoLeitor
        if documento is None or not 0 <= indice < len(documento):
            return False
        pagina = None
        bitmap = None
        imagem_pil = None
        try:
            pagina = documento[indice]
            bitmap = pagina.render(scale=1.2 * self._zoomLeitor)
            imagem_pil = bitmap.to_pil()
            imagem = ImageTk.PhotoImage(imagem_pil, master=self._janelaLeitor)
            largura, altura = imagem_pil.size
        except (OSError, ValueError, pdfium.PdfiumError, tk.TclError) as erro:
            messagebox.showerror("Não foi possível mostrar a página", str(erro), parent=self._janelaLeitor)
            return False
        finally:
            if imagem_pil is not None:
                imagem_pil.close()
            if bitmap is not None:
                bitmap.close()
            if pagina is not None:
                pagina.close()

        self._imagemLeitor = imagem
        self._canvasLeitor.delete("all")
        self._canvasLeitor.create_image(0, 0, anchor="nw", image=imagem)
        self._canvasLeitor.configure(scrollregion=(0, 0, largura, altura))
        self._canvasLeitor.xview_moveto(0)
        self._canvasLeitor.yview_moveto(0)
        self._paginaLeitor = indice
        self._paginaTexto.set(f"Página {indice + 1} de {len(documento)}")
        self._zoomTexto.set(f"{round(self._zoomLeitor * 100)}%")
        self._atualizar_controles_leitor()
        return True

    def _pagina_anterior(self) -> None:
        self._mostrar_pagina_pdf(self._paginaLeitor - 1)

    def _proxima_pagina(self) -> None:
        self._mostrar_pagina_pdf(self._paginaLeitor + 1)

    def _alterar_zoom(self, diferenca: float) -> None:
        if self._documentoLeitor is None:
            return
        zoom_anterior = self._zoomLeitor
        self._zoomLeitor = min(2.0, max(0.5, self._zoomLeitor + diferenca))
        if not self._mostrar_pagina_pdf(self._paginaLeitor):
            self._zoomLeitor = zoom_anterior

    def _atualizar_controles_leitor(self) -> None:
        documento = self._documentoLeitor
        controles = (
            (self._botaoAnterior, self._paginaLeitor > 0),
            (self._botaoProximo, documento is not None and self._paginaLeitor < len(documento) - 1),
            (self._botaoMenos, self._zoomLeitor > 0.5),
            (self._botaoMais, self._zoomLeitor < 2.0),
        )
        for botao, habilitado in controles:
            botao.state(["!disabled"] if habilitado else ["disabled"])

    def _fechar_leitor_pdf(self) -> None:
        """Libera o PDF e fecha sua janela sem afetar o acervo."""
        if self._documentoLeitor is not None:
            self._documentoLeitor.close()
            self._documentoLeitor = None
        if self._janelaLeitor is not None:
            self._janelaLeitor.destroy()
            self._janelaLeitor = None
        self._imagemLeitor = None
        self._livroLeitorId = None
        self._dadosPdfOnline = None

    def _fechar_app(self) -> None:
        self._fechar_leitor_pdf()
        self.janela.destroy()

    def cadastrarLivro(self) -> None:
        if self.janela is None:
            return
        dialogo = tk.Toplevel(self.janela)
        dialogo.title("Cadastrar livro")
        dialogo.transient(self.janela)
        dialogo.resizable(False, False)
        dialogo.configure(bg=FUNDO)
        formulario = ttk.Frame(dialogo, padding=20, style="Bibliopy.TFrame")
        formulario.pack(fill="both", expand=True)
        formulario.columnconfigure(1, weight=1)

        campos: dict[str, tk.StringVar] = {}
        for linha, (chave, rotulo) in enumerate(
            (
                ("titulo", "Título"),
                ("autor", "Autor"),
                ("genero", "Categoria"),
                ("ano", "Ano"),
                ("idioma", "Idioma da edição"),
                ("tipo", "Tipo de acesso"),
                ("local", "Caminho ou URL do PDF"),
            )
        ):
            ttk.Label(formulario, text=rotulo, style="Bibliopy.TLabel").grid(row=linha, column=0, sticky="w", padx=(0, 14), pady=6)
            variavel = tk.StringVar()
            campos[chave] = variavel
            if chave == "genero":
                entrada = ttk.Combobox(formulario, textvariable=variavel, values=GENEROS, state="readonly", width=42)
                entrada.current(0)
            elif chave == "tipo":
                entrada = ttk.Combobox(formulario, textvariable=variavel, values=("PDF local", "PDF online"), state="readonly", width=42)
                entrada.current(0)
            else:
                entrada = ttk.Entry(formulario, textvariable=variavel, width=45)
            entrada.grid(row=linha, column=1, sticky="ew", pady=6)

        campos["idioma"].set("Português")

        def escolher_pdf() -> None:
            arquivo = filedialog.askopenfilename(
                parent=dialogo,
                title="Escolher PDF",
                filetypes=[("Arquivos PDF", "*.pdf")],
            )
            if arquivo:
                campos["local"].set(arquivo)

        ttk.Button(formulario, text="Procurar PDF...", command=escolher_pdf).grid(row=6, column=2, padx=(8, 0))

        def salvar() -> None:
            try:
                try:
                    ano = int(campos["ano"].get().strip())
                except ValueError as erro:
                    raise ValueError("Informe um ano inteiro positivo.") from erro
                comum = dict(
                    id=self.biblioteca.proximoId(),
                    titulo=campos["titulo"].get(),
                    autor=campos["autor"].get(),
                    genero=campos["genero"].get(),
                    ano=ano,
                    idioma=campos["idioma"].get(),
                )
                if campos["tipo"].get() == "PDF local":
                    livro = LivroPDFLocal(**comum, caminhoArquivo=campos["local"].get())
                    livro.verificarArquivo()
                elif campos["tipo"].get() == "PDF online":
                    endereco_pdf = campos["local"].get()
                    livro = LivroOnline(**comum, url=endereco_pdf, urlPdf=endereco_pdf)
                self.biblioteca.adicionarLivro(livro)
                self.biblioteca.salvarDados(self.arquivoDados)
            except (ValueError, OSError) as erro:
                self._restaurar_apos_erro()
                messagebox.showerror("Cadastro inválido", str(erro), parent=dialogo)
                return
            dialogo.destroy()
            self.exibirLivros()
            if self.listaLivros is not None and self.listaLivros.exists(str(livro.id)):
                self.listaLivros.selection_set(str(livro.id))
                self.listaLivros.see(str(livro.id))
            if self._status is not None:
                self._status.set("Livro cadastrado.")

        botoes = ttk.Frame(formulario, style="Bibliopy.TFrame")
        botoes.grid(row=7, column=0, columnspan=3, sticky="e", pady=(18, 0))
        ttk.Button(botoes, text="Cancelar", command=dialogo.destroy).pack(side="left", padx=(0, 8))
        ttk.Button(botoes, text="Salvar livro", command=salvar, style="Destaque.TButton").pack(side="left")
        dialogo.grab_set()
        dialogo.wait_window()

    def removerLivro(self) -> None:
        livro = self._livro_selecionado()
        if livro is None:
            messagebox.showinfo("Remover livro", "Selecione um livro do acervo.", parent=self.janela)
            return
        if not messagebox.askyesno(
            "Remover livro",
            f"Remover '{livro.titulo}' da sua biblioteca?",
            parent=self.janela,
        ):
            return
        self.biblioteca.removerLivro(livro.id)
        try:
            self.biblioteca.salvarDados(self.arquivoDados)
        except OSError as erro:
            self._restaurar_apos_erro()
            messagebox.showerror("Não foi possível salvar", str(erro), parent=self.janela)
            return
        self.exibirLivros()
        if self._status is not None:
            self._status.set("Livro removido da biblioteca.")

    def _restaurar_apos_erro(self) -> None:
        """Recupera o estado salvo quando uma alteração não pôde ser gravada."""
        self.biblioteca.carregarCatalogos()
        self.biblioteca.carregarDados(self.arquivoDados)

    def executar(self) -> None:
        if self.janela is None:
            self.criarJanela()
        self.janela.mainloop()
