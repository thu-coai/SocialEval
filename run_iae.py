#!/usr/bin/env python3
"""
Interpersonal Ability Evaluation (IAE) Script

This script evaluates models on interpersonal social skills based on the
SOCIALEVAL_FINAL dataset format.

Usage:
    python run_iae.py --model <model_name> --data_path <path_to_data>
"""

import os
import json
import random
import argparse
from typing import Dict, List, Optional, Union
from openai_util import gpt_call
from evalprompt import Skill_Evaluation_Prompt_zhou


def gpt_api(prompt: str, model_name: str = 'gpt-4') -> str:
    """API call with retry logic."""
    for _ in range(10):
        try:
            return gpt_call(prompt, model=model_name)
        except Exception as e:
            print(f"GPT API error: {e}")
    raise RuntimeError("Failed to get a response from GPT API after multiple attempts.")


def rcpairs2str(rcpair: List[Dict]) -> str:
    """Convert role-content pairs to string format."""
    return "\n".join([f"{rc.get('role','system')}: {rc['content']}" for rc in rcpair])


def choices2str(choices: List[Dict]) -> tuple:
    """Convert choices to string format and identify correct answer."""
    random.shuffle(choices)
    # Identify the correct answer letter
    answer = next(chr(65 + i) for i, c in enumerate(choices) if c.get("type") == "skill choice")
    text = "\n".join([f"{chr(65 + i)}. {c['content']['content']}" for i, c in enumerate(choices)])
    return text, answer


def simple_profile(profile: Dict) -> Dict:
    """Simplify profile format."""
    return {
        "name": profile.get("name"),
        "public": profile.get("public profile"),
        "private": profile.get("private profile"),
        "goal": profile.get("goal"),
    }


def simple_other_profile(profile: Dict) -> Dict:
    """Simplify other character profile format."""
    return {
        "name": profile.get("name"),
        "info": profile.get("public profile"),
    }


# Category definitions for social skills
CATEGORIES = {
    "Self Management Skills": [
        "task management", "time management", "detail management", 
        "organizational skill", "responsibility management", 
        "capacity for consistency", "goal regulation", "rule-following skill", 
        "decision-making skill", "adaptability", "capacity for independence", "self-reflection skill"
    ],
    "Social Engagement Skills": [
        "leadership skill", "persuasive skill", "conversational skill", 
        "expressive skill", "energy regulation"
    ],
    "Cooperation Skills": [
        "teamwork skill", "capacity for trust", "perspective-taking skill", 
        "capacity for social warmth", "ethical competence"
    ],
    "Emotional Resilience Skills": [
        "stress regulation", "capacity for optimism", "anger management", 
        "confidence regulation", "impulse regulation"
    ],
    "Innovation Skills": [
        "abstract thinking skill", "creative skill", "artistic skill", 
        "cultural competence", "information processing skill"
    ]
}


def eval_interpersonal_abilities(model_name: str, data_path: str, interactional_ability: Optional[str] = None) -> Union[Dict, float]:
    """
    Evaluate interpersonal abilities using the SOCIALEVAL dataset.
    
    Args:
        model_name (str): Model name for evaluation (e.g., 'gpt-4', 'deepseek-chat')
        data_path (str): Path to the interpersonal abilities data directory
        interactional_ability (str, optional): Specific ability to evaluate
        
    Returns:
        Dict or float: Accuracy percentages by skill or specific skill accuracy
    """
    # Initialize counters
    skill_counts = {}  # normalized_skill -> {'correct': int, 'total': int}
    
    # Process both Chinese and English data files
    data_files = []
    if os.path.isdir(data_path):
        # If data_path is a directory, look for standard files
        cn_file = os.path.join(data_path, "cn_interpersonal_abilities_data.json")
        en_file = os.path.join(data_path, "en_interpersonal_abilities_data.json")
        if os.path.exists(cn_file):
            data_files.append(cn_file)
        if os.path.exists(en_file):
            data_files.append(en_file)
    else:
        # If data_path is a file, use it directly
        data_files.append(data_path)
    
    if not data_files:
        raise ValueError(f"No valid data files found in {data_path}")
    
    for data_file in data_files:
        print(f"Processing {data_file}...")
        
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                data_list = json.load(f)
        except Exception as e:
            print(f"Error loading {data_file}: {e}")
            continue
            
        for entry in data_list:
            try:
                # Extract question information
                q_info = entry.get("question", [{}])[0]
                skills = [s.strip() for s in q_info.get("skill", [])]
                qs = q_info.get("question", [])
                
                if not qs:
                    continue
                    
                question = qs[0]
                
                # Build prompt components
                profiles = entry.get("profile", [])
                if not profiles:
                    continue
                    
                self_prof = simple_profile(profiles[0])
                other_profs = [simple_other_profile(p) for p in profiles[1:]]
                dialog = rcpairs2str(entry.get("content", []))
                choices_text, correct_letter = choices2str(entry.get("choice", []))
                
                # Format the prompt
                prompt = Skill_Evaluation_Prompt_zhou.format(
                    character_name=self_prof['name'],
                    public=self_prof['public'] or "",
                    private=self_prof['private'] or "",
                    goal=self_prof['goal'] or "",
                    user_profile=other_profs,
                    dialogue_context=dialog,
                    question=question,
                    choices=choices_text
                )
                
                # Get model prediction
                try:
                    resp = gpt_api(prompt, model_name=model_name)
                except RuntimeError:
                    print("Skipping item due to API failure")
                    continue
                
                # Extract JSON response
                if "[My Output]" in resp:
                    resp = resp.split("[My Output]")[-1]
                if "```json" in resp:
                    resp = resp.split("```json")[-1]
                    
                try:
                    result = json.loads(resp.strip().replace("```", ""))
                except json.JSONDecodeError:
                    print("Skipping item due to JSON decode error")
                    continue
                
                pred = result.get("choice")
                is_correct = (pred == correct_letter)
                
                # Update skill counts
                for sk in skills:
                    norm = sk.replace('-', '').replace(' ', '').lower()
                    if norm not in skill_counts:
                        skill_counts[norm] = {'correct': 0, 'total': 0}
                    skill_counts[norm]['total'] += 1
                    if is_correct:
                        skill_counts[norm]['correct'] += 1
                        
            except Exception as e:
                print(f"Error processing entry: {e}")
                continue
    
    # Calculate accuracies
    skill_acc = {sk: (c['correct'] / c['total'] * 100) if c['total'] > 0 else 0.0 
                 for sk, c in skill_counts.items()}
    
    # If no filter, return all skills
    if not interactional_ability:
        return skill_acc
    
    # Normalize interactional_ability key
    key = interactional_ability.replace('-', '').replace(' ', '').lower()
    
    # Map categories
    cat_map = {cat.replace('-', '').replace(' ', '').lower(): vals for cat, vals in CATEGORIES.items()}
    
    # Category-level evaluation
    if key in cat_map:
        subs = [s.replace('-', '').replace(' ', '').lower() for s in cat_map[key]]
        vals = [skill_acc[s] for s in subs if s in skill_acc]
        return sum(vals) / len(vals) if vals else 0.0
    
    # Sub-skill level evaluation
    if key in skill_acc:
        return skill_acc[key]
    
    # Fallback - return all skills
    return skill_acc


def main():
    parser = argparse.ArgumentParser(description='Interpersonal Ability Evaluation (IAE)')
    parser.add_argument('--model', type=str, required=True, 
                        help='Model name for evaluation (e.g., gpt-4, deepseek-chat)')
    parser.add_argument('--data_path', type=str, required=True,
                        help='Path to interpersonal abilities data directory or file')
    parser.add_argument('--ability', type=str, default=None,
                        help='Specific interpersonal ability to evaluate (optional)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file to save results (optional)')
    
    args = parser.parse_args()
    
    print(f"Running Interpersonal Ability Evaluation...")
    print(f"Model: {args.model}")
    print(f"Data path: {args.data_path}")
    if args.ability:
        print(f"Specific ability: {args.ability}")
    
    try:
        results = eval_interpersonal_abilities(args.model, args.data_path, args.ability)
        
        print("\n=== Evaluation Results ===")
        if isinstance(results, dict):
            for skill, accuracy in sorted(results.items()):
                print(f"{skill}: {accuracy:.2f}%")
            avg_accuracy = sum(results.values()) / len(results) if results else 0.0
            print(f"\nOverall Average: {avg_accuracy:.2f}%")
        else:
            if args.ability:
                print(f"{args.ability}: {results:.2f}%")
            else:
                print(f"Result: {results:.2f}%")
        
        # Save results if output file specified
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump({
                    'model': args.model,
                    'data_path': args.data_path,
                    'ability_filter': args.ability,
                    'results': results
                }, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to {args.output}")
            
    except Exception as e:
        print(f"Error during evaluation: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())