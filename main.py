"""Ponto de entrada do BiblioPy."""

from pathlib import Path
import tkinter as tk
from tkinter import messagebox

from bibliopy import (
    Biblioteca,
    InterfaceBiblioteca,
    RepositorioGreenTeaPress,
)


def main() -> int:
    pasta = Path(__file__).resolve().parent
    biblioteca = Biblioteca()
    biblioteca.adicionarRepositorio(RepositorioGreenTeaPress(pasta / "catalogos" / "greenteapress.json"))
    arquivo_dados = pasta / "dados" / "usuario.json"
    try:
        biblioteca.carregarCatalogos()
        biblioteca.carregarDados(arquivo_dados)
    except (OSError, ValueError, KeyError, TypeError) as erro:
        raiz = tk.Tk()
        raiz.withdraw()
        messagebox.showerror("BiblioPy", f"Não foi possível carregar o acervo:\n{erro}", parent=raiz)
        raiz.destroy()
        return 1
    InterfaceBiblioteca(biblioteca, arquivo_dados).executar()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
