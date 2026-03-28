#!/usr/bin/env python3
"""
sigfapes_submit.py — Automação Playwright para submissão do Anexo II (Lançamento de notas) no SIGFAPES.

Fluxo:
  1. Login em https://sigfapes.fapes.es.gov.br
  2. Navega até o projeto Talqui
  3. Menu lateral → "6.1 Novo Formulário"
  4. Dropdown "Formulários de Prestação de Contas" → "Anexo II - Lançamento de notas"
  5. Clica em "Novo"
  6. Preenche todos os campos do formulário com dados da nota Markdown
  7. Anexa o PDF gerado
  8. Salva e fecha

Uso:
  python3 sigfapes_submit.py --pdf output/merged_*.pdf --note output/note_*.md
  python3 sigfapes_submit.py --pdf output/merged_*.pdf --note output/note_*.md --headless
"""

import argparse
import os
import re
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # python-dotenv opcional


SIGFAPES_URL = "https://sigfapes.fapes.es.gov.br"
PROJECT_NAME = "Talqui"


def _extract_field(content: str, label: str) -> str:
    """Extrai o valor de um campo '**Label:** valor' do Markdown."""
    match = re.search(rf"\*\*{re.escape(label)}:\*\*\s+(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else ""


def _extract_section(content: str, heading: str) -> str:
    """Extrai o texto entre '## Heading' e o próximo '##'."""
    match = re.search(rf"## {re.escape(heading)}\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    return match.group(1).strip() if match else ""


def load_note(note_path: Path) -> dict:
    """Lê o arquivo .md e extrai os campos do formulário Anexo II — Lançamento de notas."""
    content = note_path.read_text(encoding="utf-8")

    # Título: primeira linha com #
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    titulo = title_match.group(1).strip() if title_match else "Nota sem título"

    # Campos diretos (formato **Label:** valor)
    data_pagamento = _extract_field(content, "Data de Pagamento")
    razao_social   = _extract_field(content, "Razão Social")
    cnpj           = _extract_field(content, "CNPJ")
    num_nf         = _extract_field(content, "Nº da Nota Fiscal")
    valor_liquido  = _extract_field(content, "Valor Líquido")
    forma_pagamento = _extract_field(content, "Forma de Pagamento")
    num_pagamento  = _extract_field(content, "Nº do Documento de Pagamento")

    # Escopo: conteúdo da seção "## Serviço / Escopo"
    escopo = _extract_section(content, "Serviço / Escopo")

    return {
        "titulo":          titulo,
        "data_pagamento":  data_pagamento,
        "razao_social":    razao_social,
        "cnpj":            cnpj,
        "num_nf":          num_nf,
        "valor_liquido":   valor_liquido,
        "forma_pagamento": forma_pagamento,
        "num_pagamento":   num_pagamento,
        "escopo":          escopo,
    }


def step(msg: str):
    print(f"\n→ {msg}")


def check_env():
    login = os.environ.get("SIGFAPES_LOGIN")
    password = os.environ.get("SIGFAPES_PASSWORD")
    if not login or not password:
        print("ERRO: SIGFAPES_LOGIN e/ou SIGFAPES_PASSWORD não estão definidos.")
        print("Configure-os com:")
        print("  export SIGFAPES_LOGIN='seu_login'")
        print("  export SIGFAPES_PASSWORD='sua_senha'")
        print("Ou crie um arquivo .env baseado em .env.example.")
        sys.exit(1)
    return login, password


def run(pdf_path: Path, note_path: Path, headless: bool):
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

    login, password = check_env()
    note = load_note(note_path)

    print(f"\n📄 PDF:       {pdf_path}")
    print(f"📝 Nota:      {note_path}")
    print(f"📌 Título:    {note['titulo']}")
    print(f"🏢 Fornecedor: {note['razao_social']} | CNPJ: {note['cnpj']}")
    print(f"📃 NF nº:     {note['num_nf']}  |  Valor: {note['valor_liquido']}")
    print(f"📅 Pagamento: {note['data_pagamento']}  |  {note['forma_pagamento']}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless, slow_mo=300 if not headless else 0)
        context = browser.new_context(accept_downloads=True)
        page = context.new_page()

        # ── 1. Login ────────────────────────────────────────────────────────────
        step("Abrindo SIGFAPES e fazendo login...")
        page.goto(f"{SIGFAPES_URL}/login", timeout=30_000)
        page.wait_for_load_state("networkidle")

        # Tenta seletores comuns de login; ajuste se necessário
        login_selectors = [
            'input[name="login"]', 'input[name="username"]', 'input[name="usuario"]',
            'input[type="text"]', '#login', '#username', '#usuario',
        ]
        password_selectors = [
            'input[name="senha"]', 'input[name="password"]', 'input[name="pass"]',
            'input[type="password"]', '#senha', '#password',
        ]

        login_field = None
        for sel in login_selectors:
            try:
                login_field = page.wait_for_selector(sel, timeout=3_000)
                if login_field:
                    break
            except PWTimeout:
                continue

        if not login_field:
            print("ERRO: Campo de login não encontrado. Verifique o seletor manualmente.")
            page.screenshot(path="output/debug_login.png")
            print("Screenshot salva em output/debug_login.png")
            browser.close()
            sys.exit(1)

        login_field.fill(login)

        for sel in password_selectors:
            try:
                pwd_field = page.wait_for_selector(sel, timeout=2_000)
                if pwd_field:
                    pwd_field.fill(password)
                    break
            except PWTimeout:
                continue

        # Clica no botão de submit
        submit_selectors = [
            'button[type="submit"]', 'input[type="submit"]',
            'button:has-text("Entrar")', 'button:has-text("Login")',
            'button:has-text("Acessar")',
        ]
        for sel in submit_selectors:
            try:
                btn = page.wait_for_selector(sel, timeout=2_000)
                if btn:
                    btn.click()
                    break
            except PWTimeout:
                continue

        page.wait_for_load_state("networkidle")
        step("Login realizado.")

        # ── 2. Navegar até o projeto Talqui ─────────────────────────────────────
        step(f"Buscando projeto '{PROJECT_NAME}'...")

        project_selectors = [
            f'a:has-text("{PROJECT_NAME}")',
            f'td:has-text("{PROJECT_NAME}")',
            f'li:has-text("{PROJECT_NAME}")',
            f'span:has-text("{PROJECT_NAME}")',
        ]
        project_found = False
        for sel in project_selectors:
            try:
                el = page.wait_for_selector(sel, timeout=5_000)
                if el:
                    el.click()
                    page.wait_for_load_state("networkidle")
                    project_found = True
                    break
            except PWTimeout:
                continue

        if not project_found:
            print(f"ERRO: Projeto '{PROJECT_NAME}' não encontrado na página atual.")
            page.screenshot(path="output/debug_project.png")
            print("Screenshot salva em output/debug_project.png")
            browser.close()
            sys.exit(1)

        step(f"Projeto '{PROJECT_NAME}' aberto.")

        # ── 3. Menu lateral → "6.1 Novo Formulário" ─────────────────────────────
        step("Menu lateral → '6.1 Novo Formulário'...")

        menu_selectors = [
            'a:has-text("6.1 Novo Formulário")',
            'a:has-text("6.1 Novo Formulario")',
            'li:has-text("6.1 Novo Formulário") a',
            'span:has-text("6.1 Novo Formulário")',
            'a:has-text("Novo Formulário")',
            '[href*="novo-formulario"]',
            '[href*="novoFormulario"]',
        ]
        menu_found = False
        for sel in menu_selectors:
            try:
                el = page.wait_for_selector(sel, timeout=5_000)
                if el:
                    el.click()
                    page.wait_for_load_state("networkidle")
                    menu_found = True
                    break
            except PWTimeout:
                continue

        if not menu_found:
            page.screenshot(path="output/debug_menu.png")
            print("ERRO: Item '6.1 Novo Formulário' não encontrado no menu lateral.")
            print("Screenshot salva em output/debug_menu.png")
            browser.close()
            sys.exit(1)

        step("Página '6.1 Novo Formulário' aberta.")

        # ── 4. Dropdown "Formulários de Prestação de Contas" → Anexo II ─────────
        step("Selecionando 'Anexo II - Lançamento de notas'...")

        anexo_selectors = [
            'select:near(:text("Formulários de Prestação de Contas"))',
            'select[name*="formulario"]',
            'select[name*="prestacao"]',
            'select[id*="formulario"]',
            'select',
        ]
        anexo_selected = False
        for sel in anexo_selectors:
            try:
                el = page.wait_for_selector(sel, timeout=4_000)
                if el:
                    for label in [
                        "Anexo II - Lançamento de notas",
                        "Anexo II - Lancamento de notas",
                        "Anexo II",
                        "Lançamento de notas",
                    ]:
                        try:
                            el.select_option(label=label)
                            anexo_selected = True
                            break
                        except Exception:
                            continue
                if anexo_selected:
                    page.wait_for_load_state("networkidle")
                    break
            except PWTimeout:
                continue

        if not anexo_selected:
            page.screenshot(path="output/debug_anexo.png")
            print("ERRO: Dropdown 'Anexo II - Lançamento de notas' não encontrado.")
            print("Screenshot salva em output/debug_anexo.png")
            browser.close()
            sys.exit(1)

        step("'Anexo II - Lançamento de notas' selecionado.")

        # ── 5. Clica em "Novo" ───────────────────────────────────────────────────
        step("Clicando no botão 'Novo'...")

        novo_selectors = [
            'button:has-text("Novo")',
            'a:has-text("Novo")',
            'input[value="Novo"]',
            'button:has-text("Adicionar")',
        ]
        for sel in novo_selectors:
            try:
                el = page.wait_for_selector(sel, timeout=4_000)
                if el:
                    el.click()
                    page.wait_for_load_state("networkidle")
                    break
            except PWTimeout:
                continue

        step("Formulário Anexo II aberto.")

        # ── 6. Preencher campos do formulário ───────────────────────────────────
        step("Preenchendo campos do formulário...")

        def fill_field(selectors: list, value: str, field_name: str = ""):
            """Tenta preencher um campo texto ou selecionar opção de dropdown."""
            if not value:
                return
            for sel in selectors:
                try:
                    el = page.wait_for_selector(sel, timeout=2_000)
                    if el:
                        tag = el.evaluate("e => e.tagName.toLowerCase()")
                        if tag == "select":
                            el.select_option(label=value)
                        else:
                            el.fill(value)
                        print(f"   ✓ {field_name or sel}: {value}")
                        return
                except (PWTimeout, Exception):
                    continue
            if value:
                print(f"   ⚠ Campo não encontrado: {field_name or selectors[0]}")

        # Data de pagamento
        fill_field(
            ['input[name*="dataPagamento"]', 'input[name*="data_pagamento"]',
             'input[placeholder*="pagamento"]', 'input[type="date"]'],
            note["data_pagamento"], "Data de pagamento",
        )

        # Natureza da despesa → Pessoa Jurídica (fixo para NF)
        fill_field(
            ['select[name*="natureza"]', 'select[name*="despesa"]',
             'select[id*="natureza"]', 'select:near(:text("Natureza"))'],
            "Pessoa Jurídica", "Natureza da despesa",
        )

        # Credor / Fornecedor
        fill_field(
            ['input[name*="credor"]', 'input[name*="fornecedor"]',
             'input[placeholder*="redor"]', 'input[placeholder*="ornecedor"]'],
            note["razao_social"], "Credor/Fornecedor",
        )

        # CNPJ
        fill_field(
            ['input[name*="cnpj"]', 'input[name*="CNPJ"]',
             'input[placeholder*="CNPJ"]', 'input[id*="cnpj"]'],
            note["cnpj"], "CNPJ",
        )

        # Tipo do Documento → Nota Fiscal
        fill_field(
            ['select[name*="tipoDocumento"]', 'select[name*="tipo_documento"]',
             'select[id*="tipoDocumento"]', 'select:near(:text("Tipo do Documento"))'],
            "Nota Fiscal", "Tipo do Documento",
        )

        # Nº Documento(s)
        fill_field(
            ['input[name*="numDocumento"]', 'input[name*="num_documento"]',
             'input[name*="numeroDocumento"]', 'input[placeholder*="ocumento"]'],
            note["num_nf"], "Nº Documento(s)",
        )

        # Item da Aquisição / Escopo
        fill_field(
            ['textarea[name*="item"]', 'textarea[name*="aquisicao"]',
             'textarea[name*="servico"]', 'textarea[placeholder*="quisição"]',
             'textarea[placeholder*="Serviço"]'],
            note["escopo"], "Item da Aquisição ou Contratação do Serviço",
        )

        # Forma de pagamento
        fill_field(
            ['select[name*="formaPagamento"]', 'select[name*="forma_pagamento"]',
             'select[id*="formaPagamento"]', 'select:near(:text("Forma de pagamento"))'],
            note["forma_pagamento"], "Forma de pagamento",
        )

        # Número do documento de pagamento
        fill_field(
            ['input[name*="numPagamento"]', 'input[name*="num_pagamento"]',
             'input[name*="numeroDocumentoPagamento"]',
             'input[placeholder*="agamento"]'],
            note["num_pagamento"], "Número do documento de pagamento",
        )

        # Valor Líquido
        fill_field(
            ['input[name*="valorLiquido"]', 'input[name*="valor_liquido"]',
             'input[name*="valorLiq"]', 'input[placeholder*="alor"]'],
            note["valor_liquido"], "Valor Líquido",
        )

        step("Campos preenchidos.")

        # ── 5. Anexar PDF ────────────────────────────────────────────────────────
        step("Anexando PDF...")

        file_input_selectors = [
            'input[type="file"]',
            'input[name="arquivo"]',
            'input[name="anexo"]',
            'input[name="documento"]',
        ]
        attached = False
        for sel in file_input_selectors:
            try:
                el = page.wait_for_selector(sel, timeout=3_000)
                if el:
                    el.set_input_files(str(pdf_path.resolve()))
                    attached = True
                    break
            except PWTimeout:
                continue

        if not attached:
            # Tenta via botão de upload que abre file picker
            try:
                with page.expect_file_chooser(timeout=4_000) as fc_info:
                    upload_btn = page.locator(
                        'button:has-text("Anexar"), button:has-text("Upload"), '
                        'button:has-text("Arquivo"), label[for]'
                    ).first
                    upload_btn.click()
                file_chooser = fc_info.value
                file_chooser.set_files(str(pdf_path.resolve()))
                attached = True
            except Exception:
                pass

        if not attached:
            print("AVISO: Não foi possível localizar o campo de upload de arquivo.")
            print("Verifique manualmente e anexe o PDF: ", pdf_path)
        else:
            step("PDF anexado.")

        # ── 6. Salvar e fechar ───────────────────────────────────────────────────
        step("Salvando formulário...")

        save_selectors = [
            'button:has-text("Salvar")',
            'button:has-text("Gravar")',
            'button:has-text("Confirmar")',
            'button[type="submit"]',
            'input[type="submit"]',
        ]
        saved = False
        for sel in save_selectors:
            try:
                el = page.wait_for_selector(sel, timeout=3_000)
                if el:
                    el.click()
                    page.wait_for_load_state("networkidle")
                    saved = True
                    break
            except PWTimeout:
                continue

        if not saved:
            print("AVISO: Botão de salvar não encontrado. Verifique manualmente.")
        else:
            step("Formulário salvo.")

        # Fecha modal/popup se houver
        close_selectors = [
            'button:has-text("Fechar")',
            'button:has-text("OK")',
            'button[aria-label="close"]',
            '.modal-close',
        ]
        for sel in close_selectors:
            try:
                el = page.query_selector(sel)
                if el and el.is_visible():
                    el.click()
                    break
            except Exception:
                continue

        print(f"\n✅ Submissão concluída!")
        print(f"   Fornecedor: {note['razao_social']}  |  CNPJ: {note['cnpj']}")
        print(f"   NF nº:      {note['num_nf']}  |  Valor: {note['valor_liquido']}")
        print(f"   Pagamento:  {note['data_pagamento']}  |  {note['forma_pagamento']}")
        browser.close()


def main():
    parser = argparse.ArgumentParser(description="Submete formulário de notas no SIGFAPES")
    parser.add_argument("--pdf", required=True, help="Caminho do PDF a anexar")
    parser.add_argument("--note", required=True, help="Caminho da nota .md com os dados")
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Executar browser sem interface gráfica (padrão: visível)",
    )
    args = parser.parse_args()

    pdf_path = Path(args.pdf)
    note_path = Path(args.note)

    if not pdf_path.exists():
        print(f"ERRO: PDF não encontrado: {pdf_path}")
        sys.exit(1)
    if not note_path.exists():
        print(f"ERRO: Nota não encontrada: {note_path}")
        sys.exit(1)

    # Garante que a pasta output existe para screenshots de debug
    Path("output").mkdir(exist_ok=True)

    run(pdf_path, note_path, headless=args.headless)


if __name__ == "__main__":
    main()
