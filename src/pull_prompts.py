"""
Script para fazer pull de prompts do LangSmith Prompt Hub.

Este script:
1. Conecta ao LangSmith usando credenciais do .env
2. Faz pull dos prompts do Hub
3. Salva localmente em prompts/bug_to_user_story_v1.yml

SIMPLIFICADO: Usa serialização nativa do LangChain para extrair prompts.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
from langsmith import Client
from utils import save_yaml, check_env_vars, print_section_header

load_dotenv()

def prompt_user_input(message: str, default: str = "") -> str:
    """Solicita entrada do usuário, retornando default se vazio."""
    suffix = f" [{default}]" if default else ""
    value = input(f"{message}{suffix}: ").strip()
    return value or default


def collect_prompt_config():
    """Coleta interativamente as configurações do prompt a ser baixado."""
    print("\nInforme os dados do prompt a ser baixado do LangSmith Hub.")
    print("(Ex.: hub path no formato 'owner/prompt_name' ou 'owner/prompt_name:commit')\n")

    hub_path = ""
    while not hub_path:
        hub_path = prompt_user_input("Hub path do prompt (owner/nome)")
        if not hub_path:
            print("⚠️  Hub path é obrigatório.")

    description = prompt_user_input("Descrição do prompt (opcional)")

    filename = ""
    while not filename:
        filename = prompt_user_input("Nome do arquivo para salvar (sem extensão)")
        if not filename:
            print("⚠️  Nome do arquivo é obrigatório.")
    if filename.endswith(".yml") or filename.endswith(".yaml"):
        filename = filename.rsplit(".", 1)[0]

    local_path = Path(__file__).parent.parent / "prompts" / f"{filename}.yml"

    return {
        "hub_path": hub_path,
        "description": description,
        "filename": filename,
        "local_path": local_path,
    }


def pull_prompts_from_langsmith():
    """Faz pull de um prompt do LangSmith e salva localmente."""
    print_section_header("Pull de Prompts do LangSmith")

    required_vars = ["LANGSMITH_API_KEY", "LANGSMITH_ENDPOINT"]
    if not check_env_vars(required_vars):
        return False

    prompt_cfg = collect_prompt_config()
    hub_path = prompt_cfg["hub_path"]
    local_path = str(prompt_cfg["local_path"])

    print(f"\nFazendo pull de: {hub_path}")
    try:
        client = Client()
        prompt = client.pull_prompt(hub_path)

        # Extrai system e user templates das mensagens
        system_prompt = ""
        user_prompt = ""
        for msg in prompt.messages:
            role = msg.__class__.__name__.replace("MessagePromptTemplate", "").lower()
            template = msg.prompt.template if hasattr(msg, "prompt") else str(msg)
            if role == "system":
                system_prompt = template
            elif role == "human":
                user_prompt = template

        repo_name = hub_path.split("/")[-1].split(":")[0]
        version_parts = repo_name.split("_")
        version = version_parts[-1] if len(version_parts) > 1 else "v1"

        prompt_data = {
            prompt_cfg["filename"]: {
                "description": prompt_cfg["description"],
                "system_prompt": system_prompt,
                "user_prompt": user_prompt,
                "version": version,
                "metadata": prompt.metadata,
                "input_variables": prompt.input_variables,
            }
        }

        if save_yaml(prompt_data, local_path):
            print(f"✅ Prompt salvo em: {local_path}")
            return True
        print(f"❌ Falha ao salvar prompt: {local_path}")
        return False
    except Exception as e:
        print(f"❌ Erro ao fazer pull de '{hub_path}': {e}")
        return False


def main():
    """Função principal"""
    result = pull_prompts_from_langsmith()
    return 0 if result else 1


if __name__ == "__main__":
    sys.exit(main())
