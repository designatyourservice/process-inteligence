#!/usr/bin/env python3
"""
sigfapes_submit.py — Automação Playwright para submissão de formulário de notas no SIGFAPES.

Fluxo:
  1. Login em https://sigfapes.fapes.es.gov.br
  2. Navega até o projeto Talqui
  3. Sidebar → Novo Formulário → cria formulário de notas
  4. Preenche campos com dados da nota Markdown
  5. Anexa o PDF gerado
  6. Salva e fecha

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


def load_note(note_path: Path) -> dict:
    """Lê o arquivo .md e extrai título, data, tipo, descrição e pontos-chave."""
    content = note_path.read_text(encoding="utf-8")

    # Título: primeira linha com #
    title_match = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else "Nota sem título"

    # Data
    date_match = re.search(r"\*\*Data:\*\*\s+(.+)$", content, re.MULTILINE)
    date = date_match.group(1).strip() if date_match else ""

    # Tipo
    tipo_match = re.search(r"\*\*Tipo:\*\*\s+(.+)$", content, re.MULTILINE)
    tipo = tipo_match.group(1).strip() if tipo_match else ""

    # Descrição (entre ## Descrição e o próximo ##)
    desc_match = re.search(r"## Descrição\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    descricao = desc_match.group(1).strip() if desc_match else ""

    # Pontos-chave (lista de bullets)
    pontos_match = re.search(r"## Pontos-chave\s*\n(.*?)(?=\n##|\Z)", content, re.DOTALL)
    pontos_raw = pontos_match.group(1).strip() if pontos_match else ""
    pontos = [
        line.lstrip("- •*").strip()
        for line in pontos_raw.splitlines()
        if line.strip().startswith(("-", "•", "*"))
    ]

    return {
        "titulo": title,
        "data": date,
        "tipo": tipo,
        "descricao": descricao,
        "pontos": pontos,
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

    print(f"\n📄 PDF:  {pdf_path}")
    print(f"📝 Nota: {note_path}")
    print(f"📌 Título extraído: {note['titulo']}")

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

        # ── 3. Sidebar → Novo Formulário ────────────────────────────────────────
        step("Navegando para Novo Formulário no menu lateral...")

        form_nav_selectors = [
            'a:has-text("Novo Formulário")',
            'a:has-text("Novo Formulario")',
            'li:has-text("Novo Formulário") a',
            'span:has-text("Novo Formulário")',
            '[href*="novo-formulario"]',
            '[href*="novoFormulario"]',
        ]
        for sel in form_nav_selectors:
            try:
                el = page.wait_for_selector(sel, timeout=5_000)
                if el:
                    el.click()
                    page.wait_for_load_state("networkidle")
                    break
            except PWTimeout:
                continue

        # Clica no botão de criar novo formulário de notas
        new_form_selectors = [
            'button:has-text("Nova Nota")',
            'button:has-text("Novo")',
            'a:has-text("Nova Nota")',
            'button:has-text("Adicionar")',
            'button:has-text("Criar")',
            '[title*="nova nota"]',
            '[title*="novo formulário"]',
        ]
        for sel in new_form_selectors:
            try:
                el = page.wait_for_selector(sel, timeout=4_000)
                if el:
                    el.click()
                    page.wait_for_load_state("networkidle")
                    break
            except PWTimeout:
                continue

        step("Formulário de notas aberto.")

        # ── 4. Preencher campos do formulário ───────────────────────────────────
        step("Preenchendo campos do formulário...")

        field_map = [
            (['input[name="titulo"]', 'input[placeholder*="ítulo"]', '#titulo'], note["titulo"]),
            (['input[name="data"]', 'input[type="date"]', '#data'], note["data"]),
            (['input[name="tipo"]', 'select[name="tipo"]', '#tipo'], note["tipo"]),
            (['textarea[name="descricao"]', 'textarea[name="descricaoo"]', '#descricao',
              'textarea'], note["descricao"]),
        ]

        for selectors, value in field_map:
            if not value:
                continue
            for sel in selectors:
                try:
                    el = page.wait_for_selector(sel, timeout=2_000)
                    if el:
                        tag = el.evaluate("e => e.tagName.toLowerCase()")
                        if tag == "select":
                            # Tenta selecionar opção que contém o texto
                            el.select_option(label=value)
                        else:
                            el.fill(value)
                        break
                except (PWTimeout, Exception):
                    continue

        # Pontos-chave em campo separado, se existir
        if note["pontos"]:
            pontos_text = "\n".join(f"- {p}" for p in note["pontos"])
            for sel in ['textarea[name="pontos"]', 'textarea[name="observacoes"]',
                        'textarea[name="obs"]']:
                try:
                    el = page.wait_for_selector(sel, timeout=1_500)
                    if el:
                        el.fill(pontos_text)
                        break
                except PWTimeout:
                    continue

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
