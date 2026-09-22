#!/bin/bash
echo "Running bench_live..."
python3 backend/bench_live.py > bench_result.log
cat bench_result.log
if grep -q "INVALID RUN" bench_result.log; then
    echo "Benchmark had errors or zero data!"
    exit 1
else
    echo "Benchmark passed! Merging and pushing..."
    git checkout main
    git merge merge-team -m "Consolidate team work and fix regressions"
    git push origin main
fi
