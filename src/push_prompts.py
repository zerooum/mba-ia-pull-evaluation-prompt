"""
Script para fazer push de prompts otimizados ao LangSmith Prompt Hub.

Este script:
1. Lê os prompts otimizados de prompts/bug_to_user_story_v2.yml
2. Valida os prompts
3. Faz push PÚBLICO para o LangSmith Hub
4. Adiciona metadados (tags, descrição, técnicas utilizadas)

SIMPLIFICADO: Código mais limpo e direto ao ponto.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate
from utils import (
    load_yaml,
    check_env_vars,
    print_section_header,
    validate_prompt_structure,
)

load_dotenv()


PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"


def validate_prompt(prompt_data: dict) -> tuple[bool, list]:
    """
    Valida estrutura básica de um prompt (versão simplificada).

    Args:
        prompt_data: Dados do prompt

    Returns:
        (is_valid, errors) - Tupla com status e lista de erros
    """
    return validate_prompt_structure(prompt_data)


def _build_chat_prompt(prompt_data: dict) -> ChatPromptTemplate:
    """Monta um ChatPromptTemplate a partir dos dados do YAML."""
    system_prompt = prompt_data.get("system_prompt", "").strip()
    user_prompt = prompt_data.get("user_prompt", "{bug_report}").strip() or "{bug_report}"

    return ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("human", user_prompt),
        ]
    )


def push_prompt_to_langsmith(prompt_name: str, prompt_data: dict) -> bool:
    """
    Faz push do prompt otimizado para o LangSmith Hub (PÚBLICO).

    Args:
        prompt_name: Nome do prompt (chave no YAML)
        prompt_data: Dados do prompt

    Returns:
        True se sucesso, False caso contrário
    """
    metadata = prompt_data.get("metadata", {}) or {}
    owner = os.getenv("LANGSMITH_HUB_OWNER") or metadata.get("lc_hub_owner")

    if not owner:
        print("❌ Owner do hub não definido. Configure LANGSMITH_HUB_OWNER no .env "
              "ou inclua 'metadata.lc_hub_owner' no YAML.")
        return False

    repo_name = metadata.get("lc_hub_repo", prompt_name)
    hub_path = f"{owner}/{repo_name}"

    techniques = metadata.get("techniques", []) or []
    description = prompt_data.get("description", "")

    tags = sorted({"bugfix", "user_story", "bug_report"})

    print(f"\n📤 Fazendo push para: {hub_path}")
    print(f"   Descrição : {description}")
    print(f"   Técnicas  : {', '.join(techniques) if techniques else '(nenhuma)'}")
    print(f"   Tags      : {', '.join(tags)}")

    try:
        chat_prompt = _build_chat_prompt(prompt_data)
        client = Client()

        url = client.push_prompt(
            hub_path,
            object=chat_prompt,
            description=description,
            tags=tags,
            is_public=True,
        )

        print("✅ Prompt publicado com sucesso!")
        print(f"   URL: {url}")
        return True
    except Exception as e:
        print(f"❌ Erro ao fazer push de '{hub_path}': {e}")
        return False


def main():
    """Função principal"""
    print_section_header("Push de Prompts para o LangSmith Hub")

    if not check_env_vars(["LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT"]):
        return 1

    data = load_yaml(str(PROMPT_FILE))
    if not data:
        print(f"❌ Não foi possível carregar: {PROMPT_FILE}")
        return 1

    success_count = 0
    fail_count = 0

    for prompt_name, prompt_data in data.items():
        print_section_header(f"Prompt: {prompt_name}", char="-")

        is_valid, errors = validate_prompt(prompt_data)
        if not is_valid:
            print("❌ Prompt inválido:")
            for err in errors:
                print(f"   - {err}")
            fail_count += 1
            continue

        print("✅ Validação OK")

        if push_prompt_to_langsmith(prompt_name, prompt_data):
            success_count += 1
        else:
            fail_count += 1

    print_section_header("Resumo")
    print(f"✅ Sucesso: {success_count}")
    print(f"❌ Falhas : {fail_count}")

    return 0 if fail_count == 0 and success_count > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
