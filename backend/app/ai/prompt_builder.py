import json


class PromptBuilder:

    PROMPT_VERSION = "1.0"

    def __init__(self):
        self.system = ""
        self.context = ""
        self.task = ""
        self.schema = {}

    def set_system(self, text):
        self.system = text
        return self

    def set_context(self, text):
        self.context = text
        return self

    def set_task(self, text):
        self.task = text
        return self

    def set_schema(self, schema):
        self.schema = schema
        return self

    def build(self):

        schema_json = json.dumps(
            self.schema,
            indent=2,
            ensure_ascii=False,
        )

        return f"""
Prompt Version: {self.PROMPT_VERSION}

{self.system}

========================
CONTEXT
========================

{self.context}

========================
TASK
========================

{self.task}

========================
OUTPUT REQUIREMENTS
========================

Return exactly ONE valid JSON object.

Do NOT return markdown.

Do NOT return code fences.

Do NOT return explanations.

Do NOT invent new keys.

Do NOT remove any required keys.

Populate every field with the best possible value.

Use the default values only when information cannot reasonably be inferred:

- "" for strings
- [] for arrays
- 0 for numbers
- false for booleans

Maintain the exact data types shown in the schema.

Return ONLY the JSON object.

========================
REQUIRED JSON SCHEMA
========================

{schema_json}
"""