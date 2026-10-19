"""Persist reports returned by the quality evaluation HTTP endpoint."""
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile

from .schemas import QualityEvaluationResponse

OUTPUT_DIR = Path(__file__).resolve().parents[2] / 'output'


def save_report(response: QualityEvaluationResponse) -> Path:
    # Use the server-generated evaluation ID, never a user-provided project path.
    if not re.fullmatch(r'QE-[A-F0-9]+', response.evaluation_id):
        raise ValueError('Invalid evaluation ID for output filename.')
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    destination = OUTPUT_DIR / f'{response.evaluation_id}.json'
    temporary = None
    try:
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=OUTPUT_DIR,
                                prefix='.report-', suffix='.tmp', delete=False) as file:
            temporary = Path(file.name)
            file.write(response.model_dump_json(indent=2) + '\n')
            file.flush()
            os.fsync(file.fileno())
        temporary.replace(destination)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
    return destination
