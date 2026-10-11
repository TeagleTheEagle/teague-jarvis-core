"""Read-only aggregate of retained shadow logs. Never prints raw request content."""
import argparse
import json
import math
from pathlib import Path


def summarize(records):
    records = list(records)
    valid = [r for r in records if r.get('schema_valid') is True and type(r.get('match')) is bool]
    durations = sorted(r['latency_ms'] for r in valid if type(r.get('latency_ms')) in (int, float) and math.isfinite(r['latency_ms']) and r['latency_ms'] >= 0)
    def mean(values):
        return round(sum(values)/len(values), 3) if values else None
    def percentile(p):
        return durations[max(0, math.ceil(p*len(durations))-1)] if durations else None
    matches = sum(r['match'] for r in valid)
    errors = [r.get('error') for r in records if r.get('error')]
    return dict(total_shadow_requests=len(records), valid_comparisons=len(valid), matches=matches,
        mismatches=len(valid)-matches, agreement_rate=matches/len(valid) if valid else None,
        schema_failures=sum(e in {'invalid_schema','unknown_intent','invalid_target','malformed_json','invalid_json','duplicate_json_field','unexpected_output','incomplete_response'} for e in errors),
        timeouts=errors.count('timeout'), ollama_errors=len(errors), average_latency_ms=mean(durations),
        p50_latency_ms=percentile(.5), p95_latency_ms=percentile(.95),
        cold_latency_ms=mean([r['latency_ms'] for r in valid if r.get('lifecycle')=='cold' and r.get('latency_ms') in durations]),
        warm_latency_ms=mean([r['latency_ms'] for r in valid if r.get('lifecycle')=='warm' and r.get('latency_ms') in durations]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='+', type=Path)
    args = parser.parse_args()
    records, invalid_lines = [], 0
    for path in args.paths:
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            try:
                row = json.loads(line)
                if not isinstance(row, dict):
                    raise ValueError()
                records.append(row)
            except (ValueError, TypeError):
                invalid_lines += 1
    print(json.dumps({'scope':'retained logs only; successful classification latencies; nearest-rank percentiles',
                      'invalid_lines':invalid_lines, **summarize(records)}, indent=2))


if __name__ == '__main__':
    main()
