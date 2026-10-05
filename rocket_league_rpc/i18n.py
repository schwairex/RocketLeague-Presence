"""Shared UI translations; official map/mode names and raw diagnostics stay intact."""
import json
from pathlib import Path

TRANSLATIONS = json.loads((Path(__file__).parent/'ui'/'locales.json').read_text(encoding='utf-8'))


def translate(key, language='tr', **values):
    message = TRANSLATIONS.get(language,TRANSLATIONS['tr']).get(key,key)
    return message.format(**values) if values else message
