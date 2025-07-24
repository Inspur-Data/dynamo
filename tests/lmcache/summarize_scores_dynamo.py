#!/usr/bin/env python3

# Summarize and compare MMLU scores between dynamo baseline and LMCache tests.
# Reference: https://github.com/LMCache/LMCache/blob/dev/.buildkite/correctness/summarize_scores.py

import glob
import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple


def load_jsonl_results(filename: str) -> Dict:
    """Load results from a JSONL file."""
    results = {}
    try:
        with open(filename, 'r') as f:
            for line in f:
                data = json.loads(line.strip())
                results.update(data)
        return results
    except FileNotFoundError:
        print(f"⚠️ File not found: {filename}")
        return {}
    except Exception as e:
        print(f"❌ Error loading {filename}: {e}")
        return {}


def find_result_files() -> Tuple[List[str], List[str]]:
    """Find baseline and LMCache result files."""
    baseline_files = glob.glob("dynamo-baseline-*.jsonl")
    lmcache_files = glob.glob("dynamo-lmcache-*.jsonl")
    
    return sorted(baseline_files), sorted(lmcache_files)


def extract_model_name(filename: str) -> str:
    """Extract model name from filename."""
    if filename.startswith("dynamo-baseline-"):
        return filename[len("dynamo-baseline-"):-6]  # Remove prefix and .jsonl
    elif filename.startswith("dynamo-lmcache-"):
        return filename[len("dynamo-lmcache-"):-6]   # Remove prefix and .jsonl
    return filename


def compare_results(baseline_results: Dict, lmcache_results: Dict, model_name: str):
    """Compare results between baseline and LMCache for a specific model."""
    print(f"\n🔍 Model Comparison: {model_name}")
    print("=" * 80)
    
    if not baseline_results:
        print("❌ Missing baseline test results")
        return
    
    if not lmcache_results:
        print("❌ Missing LMCache test results")
        return
    
    # Compare total accuracy
    baseline_total = baseline_results.get("total", {})
    lmcache_total = lmcache_results.get("total", {})
    
    if baseline_total and lmcache_total:
        baseline_acc = baseline_total.get("accuracy", 0)
        lmcache_acc = lmcache_total.get("accuracy", 0)
        diff = abs(baseline_acc - lmcache_acc)
        
        print(f"📊 Overall Accuracy:")
        print(f"  Baseline (no LMCache):  {baseline_acc:.4f}")
        print(f"  LMCache:                {lmcache_acc:.4f}")
        print(f"  Difference:             {diff:.4f}")
        
        if diff < 0.01:  # 1% threshold
            print(f"  ✅ Results consistent (difference < 1%)")
        else:
            print(f"  ⚠️ Large difference (difference >= 1%)")
    
    # Compare by subject
    print(f"\n📚 Subject-wise Comparison:")
    subjects_baseline = set(baseline_results.keys()) - {"total"}
    subjects_lmcache = set(lmcache_results.keys()) - {"total"}
    
    common_subjects = subjects_baseline & subjects_lmcache
    missing_in_baseline = subjects_lmcache - subjects_baseline
    missing_in_lmcache = subjects_baseline - subjects_lmcache
    
    if missing_in_baseline:
        print(f"⚠️ Subjects missing in baseline test: {missing_in_baseline}")
    
    if missing_in_lmcache:
        print(f"⚠️ Subjects missing in LMCache test: {missing_in_lmcache}")
    
    # Detailed comparison for common subjects
    large_diff_subjects = []
    
    for subject in sorted(common_subjects):
        baseline_acc = baseline_results[subject].get("accuracy", 0)
        lmcache_acc = lmcache_results[subject].get("accuracy", 0)
        diff = abs(baseline_acc - lmcache_acc)
        
        status = "✅" if diff < 0.05 else "⚠️"  # 5% threshold for individual subjects
        if diff >= 0.05:
            large_diff_subjects.append((subject, baseline_acc, lmcache_acc, diff))
        
        print(f"  {status} {subject:25s}: baseline={baseline_acc:.3f}, LMCache={lmcache_acc:.3f}, diff={diff:.3f}")
    
    # Highlight subjects with large differences
    if large_diff_subjects:
        print(f"\n⚠️ Subjects with large differences (> 5%):")
        for subject, baseline_acc, lmcache_acc, diff in large_diff_subjects:
            print(f"   {subject}: baseline={baseline_acc:.3f}, LMCache={lmcache_acc:.3f}, diff={diff:.3f}")


def main():
    print("🧮 Dynamo LMCache MMLU Result Comparison Tool")
    print("=" * 80)
    
    # Find all result files
    baseline_files, lmcache_files = find_result_files()
    
    if not baseline_files and not lmcache_files:
        print("❌ No result files found")
        print("Please ensure you have run the test scripts and generated result files:")
        print("  - dynamo-baseline-*.jsonl")  
        print("  - dynamo-lmcache-*.jsonl")
        return
    
    print(f"📁 Files found:")
    print(f"  Baseline test results: {len(baseline_files)} files")
    for f in baseline_files:
        print(f"    - {f}")
    print(f"  LMCache test results: {len(lmcache_files)} files")
    for f in lmcache_files:
        print(f"    - {f}")
    
    # Group files by model
    baseline_by_model = {extract_model_name(f): f for f in baseline_files}
    lmcache_by_model = {extract_model_name(f): f for f in lmcache_files}
    
    all_models = set(baseline_by_model.keys()) | set(lmcache_by_model.keys())
    
    if not all_models:
        print("❌ No valid model results found")
        return
    
    # Compare results for each model
    overall_consistent = True
    
    for model in sorted(all_models):
        baseline_file = baseline_by_model.get(model)
        lmcache_file = lmcache_by_model.get(model)
        
        if not baseline_file:
            print(f"\n⚠️ Model {model} missing baseline test results")
            overall_consistent = False
            continue
            
        if not lmcache_file:
            print(f"\n⚠️ Model {model} missing LMCache test results")
            overall_consistent = False
            continue
        
        # Load and compare results
        baseline_results = load_jsonl_results(baseline_file)
        lmcache_results = load_jsonl_results(lmcache_file)
        
        compare_results(baseline_results, lmcache_results, model)
        
        # Check if this model passed consistency check
        baseline_total = baseline_results.get("total", {}).get("accuracy", 0)
        lmcache_total = lmcache_results.get("total", {}).get("accuracy", 0)
        diff = abs(baseline_total - lmcache_total)
        
        if diff >= 0.01:  # 1% threshold
            overall_consistent = False
    
    # Final summary
    print(f"\n" + "=" * 80)
    print(f"📋 Final Summary:")
    
    if overall_consistent:
        print(f"✅ LMCache functionality is correct for all tested models")
        print(f"   Baseline and LMCache test results are consistent (difference < 1%)")
    else:
        print(f"❌ LMCache functionality issues detected")
        print(f"   Some models show inconsistent results between baseline and LMCache tests")
        print(f"   Please check the specific differences above")
    
    print(f"\n💡 Recommendations:")
    print(f"   - If difference is small (<1%), it's usually acceptable")
    print(f"   - If difference is large (>5%), check LMCache configuration or implementation")
    print(f"   - Re-run tests to verify result reproducibility")


if __name__ == "__main__":
    main() 