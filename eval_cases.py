"""Fixed benchmark fixtures. Tests and reference edits are never model context."""
CASES = [
    dict(id='inclusive_range', category='boundary', issue='pipeline.py inclusive_ids(3) returns [1, 2], but IDs must include 3.',
         files={'pipeline.py':'def inclusive_ids(n):\n    return list(range(1, n))\n', 'README.md':'inclusive_ids returns integers from 1 through n inclusive. n is a non-negative integer; zero returns an empty list.\n'},
         old='range(1, n)', new='range(1, n + 1)',
         tests='assert p.inclusive_ids(3) == [1,2,3]\nassert p.inclusive_ids(1) == [1]\nassert p.inclusive_ids(0) == []\nassert p.inclusive_ids(5) == [1,2,3,4,5]'),
    dict(id='numeric_strings', category='type_conversion', issue="pipeline.py total_units(['2', '10']) raises TypeError rather than returning 12.",
         files={'pipeline.py':'def total_units(values):\n    return sum(values)\n', 'README.md':'total_units sums a list of base-10 integer strings. Empty input returns zero. Negative integers are supported.\n'},
         old='sum(values)', new='sum(int(value) for value in values)',
         tests="assert p.total_units(['2','10']) == 12\nassert p.total_units([]) == 0\nassert p.total_units(['-4','6']) == 2\nassert p.total_units(['7']) == 7"),
    dict(id='numeric_sort', category='ordering', issue="pipeline.py sort_scores(['9', '100', '20']) places 100 before 9; scores should increase numerically.",
         files={'pipeline.py':'def sort_scores(scores):\n    return sorted(scores)\n', 'README.md':'sort_scores sorts integer strings by numeric value, returning the original strings in ascending order. Preserve duplicates.\n'},
         old='sorted(scores)', new='sorted(scores, key=int)',
         tests="assert p.sort_scores(['9','100','20']) == ['9','20','100']\nassert p.sort_scores(['-1','2','-10']) == ['-10','-1','2']\nassert p.sort_scores([]) == []\nassert p.sort_scores(['2','2','1']) == ['1','2','2']"),
    dict(id='stable_dedup', category='collection_logic', issue="pipeline.py unique_labels(['b', 'a', 'b']) returns ['a', 'b']; the expected order is ['b', 'a'].",
         files={'pipeline.py':'def unique_labels(labels):\n    return sorted(set(labels))\n', 'README.md':'unique_labels removes duplicate strings while preserving first occurrence order. Empty input returns an empty list.\n'},
         old='sorted(set(labels))', new='list(dict.fromkeys(labels))',
         tests="assert p.unique_labels(['b','a','b']) == ['b','a']\nassert p.unique_labels(['z','x','y','x']) == ['z','x','y']\nassert p.unique_labels([]) == []\nassert p.unique_labels(['a','a']) == ['a']"),
    dict(id='timeout_units', category='cross_file', issue='pipeline.py timeout_seconds returns 2500, but the client expects 2.5 seconds. Check the configured timeout units.',
         files={'pipeline.py':'from config import TIMEOUT_MS\n\ndef timeout_seconds():\n    return TIMEOUT_MS\n', 'config.py':'TIMEOUT_MS = 2500\n', 'README.md':'The configuration stores TIMEOUT_MS in milliseconds. timeout_seconds must return seconds, including fractional seconds.\n'},
         old='return TIMEOUT_MS', new='return TIMEOUT_MS / 1000',
         tests='for value, expected in [(2500,2.5),(100,0.1),(0,0),(1000,1)]:\n    p.TIMEOUT_MS = value\n    assert p.timeout_seconds() == expected'),
    dict(id='normalize_lookup', category='cross_file', issue="pipeline.py lookup_code(' eu ') returns None; callers expect the supported region code 2.",
         files={'pipeline.py':'from config import REGION_CODES\n\ndef lookup_code(region):\n    return REGION_CODES.get(region)\n', 'config.py':"REGION_CODES = {'us': 1, 'eu': 2}\n", 'README.md':'lookup_code accepts region strings with surrounding whitespace and mixed case. Unknown regions return None. Configuration keys are lowercase.\n'},
         old='REGION_CODES.get(region)', new='REGION_CODES.get(region.strip().lower())',
         tests="assert p.lookup_code(' eu ') == 2\nassert p.lookup_code('US') == 1\nassert p.lookup_code('Eu') == 2\nassert p.lookup_code('xx') is None\nassert p.lookup_code('') is None"),
]

# Fresh cases: run after the development rerun without further prompt tuning.
HOLDOUT_CASES = [
    dict(id='clamp_bounds', category='boundary_contract', issue='pipeline.py clamp_score(130) returns 130, but scores above the allowed range should return 100.',
         files={'pipeline.py':'def clamp_score(score):\n    return max(0, score)\n', 'README.md':'clamp_score limits numeric scores to the inclusive range 0 through 100. Values inside the range are unchanged. Negative values become zero.\n'},
         old='max(0, score)', new='min(100, max(0, score))',
         tests='assert p.clamp_score(130) == 100\nassert p.clamp_score(-7) == 0\nassert p.clamp_score(42.5) == 42.5\nassert p.clamp_score(0) == 0\nassert p.clamp_score(100) == 100'),
    dict(id='batch_count', category='integer_arithmetic', issue='pipeline.py batch_count(11, 5) returns 2, but processing 11 records with capacity 5 needs 3 batches.',
         files={'pipeline.py':'def batch_count(count, capacity):\n    return count // capacity\n', 'README.md':'batch_count returns the number of batches required. count is a non-negative integer and capacity a positive integer. A partial batch counts as one. Zero records require zero batches; exact multiples require no extra batch.\n'},
         old='count // capacity', new='(count + capacity - 1) // capacity',
         tests='assert p.batch_count(11,5) == 3\nassert p.batch_count(10,5) == 2\nassert p.batch_count(0,5) == 0\nassert p.batch_count(1,5) == 1\nassert p.batch_count(7,1) == 7'),
    dict(id='explicit_zero', category='default_semantics', issue="pipeline.py retry_limit({'retries': 0}) returns 3, but explicitly configuring zero should disable retries.",
         files={'pipeline.py':"def retry_limit(settings):\n    return settings.get('retries') or 3\n", 'README.md':'retry_limit returns the configured non-negative integer number of retries. Zero is valid. Use the default of 3 only when the retries key is absent. If present the value is always an integer.\n'},
         old="settings.get('retries') or 3", new="settings.get('retries', 3)",
         tests="assert p.retry_limit({'retries':0}) == 0\nassert p.retry_limit({}) == 3\nassert p.retry_limit({'retries':5}) == 5\nassert p.retry_limit({'retries':1}) == 1"),
    dict(id='filter_boundary', category='filter_contract', issue='pipeline.py nonnegative([0, -2, 3]) drops zero, producing [3] instead of [0, 3].',
         files={'pipeline.py':'def nonnegative(values):\n    return [value for value in values if value > 0]\n', 'README.md':'nonnegative returns a new list containing every value greater than or equal to zero. Preserve original order and duplicates; do not modify the input list. Values are integers.\n'},
         old='value > 0', new='value >= 0',
         tests='values = [0,-2,3]\nassert p.nonnegative(values) == [0,3]\nassert values == [0,-2,3]\nassert p.nonnegative([2,0,2,-1,0]) == [2,0,2,0]\nassert p.nonnegative([]) == []\nassert p.nonnegative([-5,-1]) == []'),
]
SUITES = {'development': CASES, 'holdout': HOLDOUT_CASES}

PUBLIC_CHECKS = {
    'inclusive_range': 'assert p.inclusive_ids(3) == [1,2,3]',
    'numeric_strings': "assert p.total_units(['2','10']) == 12",
    'numeric_sort': "assert p.sort_scores(['9','100','20']) == ['9','20','100']",
    'stable_dedup': "assert p.unique_labels(['b','a','b']) == ['b','a']",
    'timeout_units': 'assert p.timeout_seconds() == 2.5',
    'normalize_lookup': "assert p.lookup_code(' eu ') == 2",
    'clamp_bounds': 'assert p.clamp_score(130) == 100',
    'batch_count': 'assert p.batch_count(11,5) == 3',
    'explicit_zero': "assert p.retry_limit({'retries':0}) == 0",
    'filter_boundary': 'assert p.nonnegative([0,-2,3]) == [0,3]',
}
IMPORT_CASE = dict(id='import_conversion', category='cross_file',
    issue='pipeline.py report_duration(2500) returns 2500000 instead of 2.5 seconds.',
    files={'pipeline.py':'from conversions import to_seconds\n\ndef report_duration(milliseconds):\n    return to_seconds(milliseconds)\n',
           'conversions.py':'from units import SCALE\n\ndef to_seconds(value):\n    return value * SCALE\n',
           'units.py':'SCALE = 1000\n',
           'README.md':'report_duration accepts non-negative milliseconds and returns seconds, including fractional parts. 2500 milliseconds is 2.5 seconds.\n'},
    repair_file='conversions.py', old='value * SCALE', new='value / SCALE',
    tests='assert p.report_duration(2500) == 2.5\nassert p.report_duration(1000) == 1\nassert p.report_duration(1) == 0.001\nassert p.report_duration(0) == 0')
SUITES['integration'] = [IMPORT_CASE]
PUBLIC_CHECKS['import_conversion'] = 'assert p.report_duration(2500) == 2.5'
