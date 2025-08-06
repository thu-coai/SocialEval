#!/usr/bin/env python3
"""
Goal Achievement Evaluation (GAE) Script

This script evaluates models on goal achievement in social scenarios based on the
SOCIALEVAL_FINAL3 worldtree dataset format.

Usage:
    python run_gae.py --model <model_name> --data_path <path_to_data> --lang <language>
"""

import os
import json
import random
import argparse
from typing import Dict, List, Optional, Tuple
from openai_util import gpt_call
from evalprompt import Ending_Evaluation_Prompt_zhou


def gpt_api(prompt: str, model_name: str = 'gpt-4o') -> str:
    """API call with retry logic."""
    for _ in range(10):
        try:
            return gpt_call(prompt, model=model_name)
        except Exception as e:
            print(f"GPT API error: {e}")
    raise RuntimeError("Failed to get a response from GPT API after multiple attempts.")


def simple_profile(profile: Dict) -> Dict:
    """Simplify profile format."""
    return {
        "name": profile.get("name"),
        "public": profile.get("public profile"),
        "private": profile.get("private profile"), 
        "goal": profile.get("goal"),
    }


def simple_other_profiles(profiles: List[Dict]) -> List[Dict]:
    """Simplify other character profiles format."""
    return [{"name": profile["name"], "public": profile.get("public profile", "")} for profile in profiles]


def get_interface_state(data: Dict, cids: List[int]) -> Tuple:
    """
    Extract interface state information from worldtree data.
    
    Args:
        data: The loaded JSON data
        cids: List of choice IDs representing the path taken
        
    Returns:
        Tuple containing interface state information
    """
    # Get category from predefined profiles
    category = str(data["predefined_profiles"][0]["orientation"])
    main_profile = simple_profile(data["predefined_profiles"][0])
    other_profiles = simple_other_profiles(data["predefined_profiles"][1:])
    dialogue = ""

    # Build dialogue from the path
    for cid in cids:
        plots = data["interactive_plot"]
        current_plot = None
        for plot in plots:
            if plot["cid"] == cid:
                current_plot = plot
                break
        
        if current_plot is None:
            continue
            
        # Add character profiles that appear in this plot
        for d in current_plot.get("dialog", []):
            if "profile" in d:
                other_profiles.append(simple_profile(d["profile"]))
            if "content" in d:
                role = d.get("role", "旁白")
                dialogue += f"{role}: {d['content']}\n"

    # Get current plot state
    plots = data["interactive_plot"]
    current_plot = None
    for plot in plots:
        if plot["cid"] == cids[-1]:
            current_plot = plot
            break
    
    choices = []
    nexts = []
    goal_achievement = -1
    
    if current_plot:
        if current_plot["type"] == "ending":
            goal_achievement = current_plot.get("goal achievement", -1)
        else:
            for choice in current_plot.get("choices", []):
                nexts.append(choice["cid"])
                content = choice.get("content", {})
                choice_text = f"{content.get('role', '')}: {content.get('content', '')}"
                choices.append(choice_text)
    
    return (
        main_profile,
        f"主角档案:\n名字: {main_profile['name']}\n公开信息: {main_profile['public']}\n隐私信息: {main_profile['private']}\n社交目标: {main_profile['goal']}",
        "\n".join([f"{profile['name']}: {profile['public']}" for profile in other_profiles]),
        dialogue,
        choices,
        nexts,
        goal_achievement,
        category
    )


def eval_goal_achievement(model_name: str, data_path: str, lang: str = "cn", world_category: Optional[str] = None) -> Dict:
    """
    Evaluate goal achievement using the worldtree dataset.
    
    Args:
        model_name (str): Model name for evaluation
        data_path (str): Path to the worldtree data file
        lang (str): Language to evaluate ('cn' for Chinese, 'en' for English)
        world_category (str, optional): Specific world category to filter
        
    Returns:
        Dict: Goal achievement statistics by category
    """
    ending_stats = {}
    
    # Validate language parameter
    if lang not in ['cn', 'en']:
        raise ValueError("Language must be 'cn' for Chinese or 'en' for English")
    
    # Load data file
    if not os.path.exists(data_path):
        raise ValueError(f"Data file {data_path} does not exist")
    
    print(f"Loading data from {data_path} for {lang} language...")
    
    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
    except Exception as e:
        raise ValueError(f"Error loading data file: {e}")
    
    print(f"Processing {len(data_list)} data entries...")
    
    for entry in data_list:
        try:
            # Extract data based on language
            data_key = f"{lang}_data"
            if data_key not in entry:
                print(f"Warning: {data_key} not found in entry {entry.get('data_id', 'unknown')}")
                continue
                
            data = entry[data_key]
            print(f"Processing entry {entry.get('data_id', 'unknown')}")
            
            # Run multiple episodes for each scenario
            for episode in range(10):
                try:
                    path = [0]  # Start from the beginning
                    
                    while True:
                        # Get current interface state
                        main, main_str, others, dialogue, choices, nexts, goal_achieve, cat = get_interface_state(data, path)
                        
                        # Check if we've reached an ending
                        if goal_achieve != -1:
                            # Record the result
                            print("goal_achieve", goal_achieve)
                            stats = ending_stats.setdefault(cat, {'count': 0, 'success': 0})
                            stats['count'] += 1
                            if goal_achieve == 2:  # Successful goal achievement
                                stats['success'] += 1
                            break
                        
                        # If no choices available, break
                        if not choices or not nexts:
                            break
                        
                        # Build prompt and get model response
                        choices_str = '\n'.join([f"{chr(65+i)}: {c}" for i, c in enumerate(choices)])
                        prompt = Ending_Evaluation_Prompt_zhou.format(
                            character_name=main['name'],
                            main_profile=json.dumps(main, ensure_ascii=False),
                            user_profile=json.dumps(others, ensure_ascii=False),
                            dialogue_context=dialogue,
                            choices=choices_str
                        )
                        
                        try:
                            resp = gpt_api(prompt, model_name=model_name)
                            # Extract choice from response
                            result = eval(resp.strip().replace("```json", "").replace("```", ""))
                            ans = result['choice']
                            choice_idx = ord(ans) - 65
                            
                            # Validate choice index
                            if 0 <= choice_idx < len(nexts):
                                path.append(nexts[choice_idx])
                            else:
                                print(f"Invalid choice {ans} for {len(nexts)} options")
                                break
                                
                        except Exception as e:
                            print(f"Error getting model response: {e}")
                            break
                            
                except Exception as e:
                    print(f"Error in episode {episode} for entry {entry.get('data_id', 'unknown')}: {e}")
                    continue
                    
        except Exception as e:
            print(f"Error processing entry {entry.get('data_id', 'unknown')}: {e}")
            continue
    
    # Compute success rates
    ending_acc = {}
    for category, stats in ending_stats.items():
        if stats['count'] > 0:
            ending_acc[category] = stats['success'] / stats['count'] * 100
        else:
            ending_acc[category] = 0.0
    
    # Filter by world category if specified
    if world_category and world_category in ending_acc:
        return {world_category: ending_acc[world_category]}
    
    return ending_acc


def main():
    parser = argparse.ArgumentParser(description='Goal Achievement Evaluation (GAE)')
    parser.add_argument('--model', type=str, required=True,
                        help='Model name for evaluation (e.g., gpt-4, deepseek-chat)')
    parser.add_argument('--data_path', type=str, required=True,
                        help='Path to worldtree data file')
    parser.add_argument('--lang', type=str, default='cn', choices=['cn', 'en'],
                        help='Language to evaluate (cn for Chinese, en for English)')
    parser.add_argument('--category', type=str, default=None,
                        help='Specific world category to evaluate (optional)')
    parser.add_argument('--output', type=str, default=None,
                        help='Output file to save results (optional)')
    
    args = parser.parse_args()
    
    print(f"Running Goal Achievement Evaluation...")
    print(f"Model: {args.model}")
    print(f"Data path: {args.data_path}")
    print(f"Language: {args.lang}")
    if args.category:
        print(f"Category filter: {args.category}")
    
    try:
        results = eval_goal_achievement(args.model, args.data_path, args.lang, args.category)
        
        print("\n=== Goal Achievement Results ===")
        if isinstance(results, dict):
            for category, success_rate in sorted(results.items()):
                print(f"{category}: {success_rate:.2f}%")
            
            if len(results) > 1:
                avg_success_rate = sum(results.values()) / len(results)
                print(f"\nOverall Average: {avg_success_rate:.2f}%")
        else:
            print(f"Result: {results:.2f}%")
        
        # Save results if output file specified
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump({
                    'model': args.model,
                    'data_path': args.data_path,
                    'language': args.lang,
                    'category_filter': args.category,
                    'results': results
                }, f, indent=2, ensure_ascii=False)
            print(f"\nResults saved to {args.output}")
            
    except Exception as e:
        print(f"Error during evaluation: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
