import os
import json
import random
from openai_util import gpt_call
from evalprompt import Skill_Evaluation_Prompt_zhou, Ending_Evaluation_Prompt_zhou

# Helper functions
def gpt_api(prompt, model_name='gpt-4'):
    for _ in range(10):
        try:
            return gpt_call(prompt, model=model_name)
        except Exception as e:
            print(f"GPT API error: {e}")
    raise RuntimeError("Failed to get a response from GPT API after multiple attempts.")

def rcpairs2str(rcpair):
    return "\n".join([f"{rc.get('role','system')}: {rc['content']}" for rc in rcpair])

def choices2str(choices):
    random.shuffle(choices)
    # Identify the correct answer letter
    answer = next(chr(65 + i) for i, c in enumerate(choices) if c.get("type") == "skill choice")
    text = "\n".join([f"{chr(65 + i)}. {c['content']['content']}" for i, c in enumerate(choices)])
    return text, answer

def simple_profile(profile):
    return {
        "name": profile.get("name"),
        "public": profile.get("public profile"),
        "private": profile.get("private profile"),
        "goal": profile.get("goal"),
    }

def simple_other_profile(profile):
    return {
        "name": profile.get("name"),
        "info": profile.get("public profile"),
    }

def simple_other_profiles(profiles):
    return [{"name": profile["name"], "public": profile.get("public profile", "")} for profile in profiles]

# Category definitions
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

# Main evaluation function
def eval_skill(model_name, interactional_ability=None):
    """
    Complete evaluation pipeline: runs model predictions, counts per-skill accuracy,
    and aggregates by category or returns individual skill accuracies.

    Args:
        model_name (str): e.g., 'deepseek-chat'
        interactional_ability (str, optional): if None, returns all skill accuracies;
            if matches a category name, returns that category's average accuracy;
            if matches a sub-skill, returns that skill's accuracy.
    Returns:
        dict or float: accuracy percentages.
    """
    # Initialize counters
    skill_counts = {}  # normalized_skill -> {'correct': int, 'total': int}
    eval_dir = './new_eval_json'

    for fname in os.listdir(eval_dir):
        if not fname.endswith('.json'):
            continue
        path = os.path.join(eval_dir, fname)
        with open(path, 'r', encoding='utf-8') as f:
            data_list = json.load(f)
        for entry in data_list:
            q_info = entry.get("question", [{}])[0]
            skills = [s.strip() for s in q_info.get("skill", [])]
            qs = q_info.get("question", [])
            if not qs:
                continue
            question = qs[0]
            # Build prompt
            self_prof = simple_profile(entry.get("profile", [])[0])
            other_profs = [simple_other_profile(p) for p in entry.get("profile", [])[1:]]
            dialog = rcpairs2str(entry.get("content", []))
            choices_text, correct_letter = choices2str(entry.get("choice", []))
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
            # Get prediction
            try:
                resp = gpt_api(prompt, model_name=model_name)
            except RuntimeError:
                continue
            # Extract JSON
            if "[My Output]" in resp:
                resp = resp.split("[My Output]")[-1]
            if "```json" in resp:
                resp = resp.split("```json")[-1]
            try:
                result = json.loads(resp.strip().replace("```", ""))
            except json.JSONDecodeError:
                continue
            pred = result.get("choice")
            is_correct = (pred == correct_letter)
            # Update counts
            for sk in skills:
                norm = sk.replace('-', '').replace(' ', '').lower()
                if norm not in skill_counts:
                    skill_counts[norm] = {'correct': 0, 'total': 0}
                skill_counts[norm]['total'] += 1
                if is_correct:
                    skill_counts[norm]['correct'] += 1

    # Calculate accuracies
    skill_acc = {sk: (c['correct'] / c['total'] * 100) for sk, c in skill_counts.items()}

    # If no filter, return all
    if not interactional_ability:
        return skill_acc

    # Normalize interactional_ability key
    key = interactional_ability.replace('-', '').replace(' ', '').lower()
    # Map categories
    cat_map = {cat.replace('-', '').replace(' ', '').lower(): vals for cat, vals in CATEGORIES.items()}

    # Category-level
    if key in cat_map:
        subs = [s.replace('-', '').replace(' ', '').lower() for s in cat_map[key]]
        vals = [skill_acc[s] for s in subs if s in skill_acc]
        return sum(vals) / len(vals) if vals else 0.0

    # Sub-skill level
    if key in skill_acc:
        return skill_acc[key]

    # Fallback
    return skill_acc

def get_ending_interface(file_name, cids):
    with open(file_name, 'r', encoding='utf-8') as f:
        data = json.load(f)
    category = str(data["prefined_profiles"][0]["orientation"])
    main_profile = simple_profile(data["predefined_profiles"][0])
    other_profiles = simple_other_profiles(data["predefined_profiles"][1:])
    dialogue = ""

    for cid in cids:
        plots = data["interactive plot"]
        for plot in plots:
            if plot["cid"] == cid:
                break
        for d in plot["dialog"]:
            if "profile" in d:
                other_profiles.append(simple_other_profile(d["profile"]))
            if "content" in d:
                if "role" not in d:
                    d["role"] = "旁白"
                dialogue += f"{d['role']}: {d['content']}\n"

    plots = data["interactive plot"]
    for now_plot in plots:
        if now_plot["cid"] == cids[-1]:
            break
    choices = []
    confusions = {}
    nexts = []
    if now_plot["type"] == "ending":
        goal_achievement = now_plot["goal achievement"]
    else:
        goal_achievement = -1
        for choice in now_plot["choices"]:
            nexts.append(choice["cid"])
            choices.append(f"{choice['content']['role']}: {choice['content']['content']}")
            choice_str = f"{choice['content']['role']}: {choice['content']['content']}"
            confusions[choice_str] = []
            for conf in choice["confusion"]:
                if conf["type"] == "skill confusion":
                    confusions[choice_str].append(f"{conf['content']['role']}: {conf['content']['content']}")
    now_dialogue = ""
    for d in now_plot["dialog"]:
        if "content" in d:
            if "role" not in d:
                continue
            now_dialogue += f"{d['role']}: {d['content']}\n"

    last_dialogue = ""
    if len(cids) > 1:
        for last_plot in plots:
            if last_plot["cid"] == cids[-2]:
                break
        for d in last_plot["dialog"]:
            if "content" in d:
                if "role" not in d:
                    continue
                last_dialogue += f"{d['role']}: {d['content']}\n"
    
    return (
        main_profile,
        f"主角档案:\n名字: {main_profile['name']}\n公开信息: {main_profile['public']}\n隐私信息: {main_profile['private']}\n社交目标: {main_profile['goal']}",
        "\n".join([f"{profile['name']}: {profile['public']}" for profile in other_profiles]),
        dialogue,
        choices,
        nexts,
        confusions,
        goal_achievement,
        category
    )

def eval_ending(model_name, world_category=None):
    ending_stats = {}
    data_dir = './new_json'
    for fname in os.listdir(data_dir):
        if not fname.endswith('.json'):
            continue
        file_path = os.path.join(data_dir, fname)
        for _ in range(10):
            path = [0]
            while True:
                # use get_ending_interface to get state
                main,main_str,others, dialogue, choices, nexts, goal_achieve, cat = get_ending_interface(file_path, path)
                if goal_achieve != -1:
                    stats = ending_stats.setdefault(cat, {'count': 0, 'success': 0})
                    stats['count'] += 1
                    if goal_achieve == 2:
                        stats['success'] += 1
                    break
                # build prompt and call GPT
                choices_str = '\n'.join([f"{chr(65+i)}: {c}" for i, c in enumerate(choices)])
                prompt = Ending_Evaluation_Prompt_zhou.format(
                    character_name=main['name'],
                    main_profile=json.dumps(main, ensure_ascii=False),
                    user_profile=json.dumps(others, ensure_ascii=False),
                    dialogue_context=dialogue,
                    choices=choices_str
                )
                resp = gpt_api(prompt, model_name=model_name)
                try:
                    res = eval(resp.strip())
                    ans = res['choice']
                except Exception:
                    continue
                path.append(nexts[ord(ans) - 65])
    # compute accuracies
    ending_acc = {c: v['success'] / v['count'] * 100 for c, v in ending_stats.items()}
    if not world_category or world_category not in ending_acc:
        return ending_acc
    return ending_acc[world_category]

def eval(model_name, world_category=None, interactional_ability=None):
    skill_results = eval_skill(model_name, interactional_ability)
    ending_results = eval_ending(model_name, world_category)
    return skill_results, ending_results