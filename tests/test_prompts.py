"""
Testes automatizados para validação de prompts.
"""
import re
import pytest
import yaml
import sys
from pathlib import Path

# Adicionar src ao path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from utils import validate_prompt_structure

PROMPT_FILE = Path(__file__).parent.parent / "prompts" / "bug_to_user_story_v2.yml"
PROMPT_KEY = "bug_to_user_story_v2"


def load_prompts(file_path: str):
    """Carrega prompts do arquivo YAML."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def prompt_data():
    """Carrega os dados do prompt v2 uma única vez para todos os testes."""
    data = load_prompts(PROMPT_FILE)
    assert PROMPT_KEY in data, f"Chave '{PROMPT_KEY}' não encontrada no YAML"
    return data[PROMPT_KEY]


@pytest.fixture(scope="module")
def system_prompt(prompt_data):
    """Retorna o system_prompt do prompt v2."""
    return prompt_data.get("system_prompt", "")


class TestPrompts:
    def test_prompt_has_system_prompt(self, prompt_data):
        """Verifica se o campo 'system_prompt' existe e não está vazio."""
        assert "system_prompt" in prompt_data, "Campo 'system_prompt' não existe"
        assert isinstance(prompt_data["system_prompt"], str)
        assert prompt_data["system_prompt"].strip(), "system_prompt está vazio"

    def test_prompt_has_role_definition(self, system_prompt):
        """Verifica se o prompt define uma persona (ex: "Você é um Product Manager")."""
        assert re.search(r"você é um\w*\s+\w+", system_prompt, re.IGNORECASE), \
            "Prompt não define uma persona (esperado algo como 'Você é um ...')"
        assert "Product Manager" in system_prompt, \
            "Persona esperada 'Product Manager' não encontrada"

    def test_prompt_mentions_format(self, system_prompt):
        """Verifica se o prompt exige formato Markdown ou User Story padrão."""
        mentions_markdown = "markdown" in system_prompt.lower()
        mentions_user_story = (
            "user story" in system_prompt.lower()
            and "Como um" in system_prompt
            and "eu quero" in system_prompt
            and "para que" in system_prompt
        )
        assert mentions_markdown or mentions_user_story, \
            "Prompt não exige formato Markdown nem User Story padrão"

    def test_prompt_has_few_shot_examples(self, system_prompt):
        """Verifica se o prompt contém exemplos de entrada/saída (técnica Few-shot)."""
        examples = re.findall(r"###\s*Exemplo", system_prompt)
        assert len(examples) >= 2, \
            f"Esperado pelo menos 2 exemplos few-shot, encontrados: {len(examples)}"
        # Cada exemplo deve ter par entrada/saída
        assert system_prompt.count("Relato de Bug:") >= 2, \
            "Exemplos não contêm entradas ('Relato de Bug:')"
        assert system_prompt.count("User Story:") >= 2, \
            "Exemplos não contêm saídas ('User Story:')"

    def test_prompt_no_todos(self, prompt_data):
        """Garante que você não esqueceu nenhum `[TODO]` no texto."""
        raw_text = PROMPT_FILE.read_text(encoding="utf-8")
        assert "[TODO]" not in raw_text, "Arquivo ainda contém marcadores [TODO]"
        assert "TODO" not in prompt_data.get("system_prompt", ""), \
            "system_prompt ainda contém TODOs"
        assert "TODO" not in prompt_data.get("user_prompt", ""), \
            "user_prompt ainda contém TODOs"

    def test_minimum_techniques(self, prompt_data):
        """Verifica (através dos metadados do yaml) se pelo menos 2 técnicas foram listadas."""
        techniques = (prompt_data.get("metadata") or {}).get("techniques") or []
        assert len(techniques) >= 2, \
            f"Mínimo de 2 técnicas requeridas, encontradas: {len(techniques)}"

    def test_prompt_structure_is_valid(self, prompt_data):
        """Valida a estrutura completa do prompt usando o helper do projeto."""
        is_valid, errors = validate_prompt_structure(prompt_data)
        assert is_valid, f"Estrutura do prompt inválida: {errors}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
