from copy import deepcopy
import pytest
from scripts import benchmark
from scripts.scenarios import EXPECTED, expected_records
from backend.tests.test_improvement import client, send

TRUTH = EXPECTED['atlas_v1.csv']
ORACLE = expected_records(TRUTH)


def result(rows):
    return dict(accepted=rows, rejected=4-len(rows), held=0, total=4,
                status='completed', mapping='Atlas@1', drift=False)


@pytest.mark.parametrize('rows,correct,wrong', [
    ([ORACLE[0]]*3, 1, 2),
    ([ORACLE[0],ORACLE[1],ORACLE[1]], 2, 1),
])
def test_summary_does_not_credit_duplicate_replacements(rows, correct, wrong):
    summary=benchmark.summarize(result(rows), TRUTH)
    assert summary['accepted_valid']==correct
    assert summary['incorrect_silent_mappings']==wrong


@pytest.mark.parametrize('rows', [ORACLE[:2], [ORACLE[0]]*3, [ORACLE[0],ORACLE[1],ORACLE[1]]])
def test_exact_accepted_oracle_detects_missing_and_replaced_identities(rows):
    with pytest.raises(AssertionError):
        benchmark.validate_canonical_rows(rows, ORACLE, 'accepted')


@pytest.mark.parametrize('mutation', ['missing','duplicate','wrong_value'])
def test_persisted_oracle_detects_coverage_and_value_mutations(mutation):
    rows=[dict(row,workflow='improved') for row in deepcopy(ORACLE)]
    if mutation=='missing': rows.pop()
    elif mutation=='duplicate': rows[-1]=dict(rows[0])
    else: rows[-1]['decision']='denied'
    with pytest.raises(AssertionError):
        benchmark.verify_persisted(rows, ORACLE, 'improved')


def test_multiset_allows_declared_duplicate_source_rows():
    benchmark.validate_canonical_rows([ORACLE[0]]*2,[ORACLE[0]]*2,'source rows')
    benchmark.verify_persisted([dict(ORACLE[0],workflow='improved')],[ORACLE[0]]*2,'improved')


def test_partial_expected_rows_are_compared_without_requiring_full_file():
    benchmark.validate_canonical_rows(ORACLE[:1],ORACLE[:1],'partial')
    assert benchmark.summarize(result(ORACLE[:1]),TRUTH)['rejected_valid']==2


def test_duplicate_source_rows_remain_accepted_and_unchanged(client):
    content=b'applicant_id,year,decision,decision_date\nSYN-DUP,2024,admitted,2024-04-01\nSYN-DUP,2024,admitted,2024-04-01\n'
    first=send(client,'duplicates.csv',content).json()
    assert len(first['accepted'])==2
    assert first['inserted']==1 and first['unchanged']==1 and first['rejected']==0
    assert send(client,'duplicates.csv',content).json()['replayed'] is True
    assert len(client.get('/api/records').json())==1
