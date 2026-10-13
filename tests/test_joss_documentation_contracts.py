"""Scientific examples and active release guidance must agree with evidence."""
from pathlib import Path
import re

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]


def test_condition_documentation_distinguishes_missing_and_valid_denominators():
    text = (ROOT / 'docs/concepts/condition_contracts.md').read_text()
    example = re.search(r'<!-- condition-contract-example -->\s*```python\n(.*?)```', text, re.S)[1]
    namespace = {}
    exec(compile(example, 'condition-contract-example', 'exec'), namespace)
    assert namespace['condition']['state'].values.tolist() == [False, False, True]
    assert float(namespace['indexed']) == pytest.approx(1 / 3)
    assert float(namespace['valid_only']) == pytest.approx(1 / 2)
    assert bool(namespace['cast_mask'].isel(time=1))
    assert np.isnan(namespace['values'].isel(time=1))
    from cubedynamics import pipe, verbs as v
    from cubedynamics.grammar import SemanticGrammarError
    with pytest.raises(SemanticGrammarError, match='categorical field, condition'):
        pipe(namespace['values']) | v.binary_state()


@pytest.mark.parametrize('path', ['README.md', 'docs/index.md', 'docs/quickstart.md',
                                 'docs/getting_started/install.md'])
def test_active_installation_guides_use_verified_public_rc3(path):
    text = (ROOT / path).read_text()
    assert '0.1.0rc3' in text
    assert 'cubedynamics==0.1.0rc1' not in text
    assert 'PyPI still contains' not in text


def test_review_identity_does_not_assign_an_unselected_archive():
    text = (ROOT / 'docs/project/release_status.md').read_text()
    assert 'f777eb07d3ada8bd407b027f560727c90f6d3731' in text
    assert '**Not yet selected**' in text
    assert '319ca84f5354ebdd71f360f3fe7c888a4437f439b5cca6fe53b399c8b67ab7f6' in text
    assert (ROOT / 'CITATION.cff').read_bytes() == (ROOT / 'docs/CITATION.cff').read_bytes()
