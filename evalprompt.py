Skill_Evaluation_Prompt = \
"""请你扮演{character_name}，给定{character_name}的信息、与{character_name}进行对话交互的其他角色信息和对话上下文，请你基于提问从给定的选项中选择一个正确的答案并给出解释，输出json格式，输出示例: {{"choice": "A", "explanation": 解释}}。

[{character_name}信息]
{character_profile}

[其他角色信息]
{user_profile}

[对话上下文]
{dialogue_context}

[问题]
{question}

[选项]
{choices}"""



Ending_Evaluation_Prompt = \
"""请你扮演{character_name}，给定{character_name}的信息、与{character_name}进行对话交互的其他角色信息和对话上下文，请你基于你所扮演角色的社交目标，从给定的对话选项中选择一个最有可能达成目标结局的剧情选项，并给出解释，输出json格式，输出示例: {{"choice": "A", "explanation": 解释}}。

[{character_name}信息]
{character_profile}

[其他角色信息]
{user_profile}

[对话上下文]
{dialogue_context}

[问题]
{question}

[选项]
{choices}"""


Skill_Evaluation_Prompt_zhou = \
"""请你扮演{character_name}，给定{character_name}的信息，其中包含了{character_name}的公开信息、隐私信息和在社交场景中要实现的社交目标，同时，给定在社交中其他角色的信息，请你基于给定的角色信息、{character_name}和其他角色的对话上下文、和提问，从给定的选项中选择一个正确的答案并给出解释，输出json格式，输出示例(json有两个字段，explaination和choice）：{{"explaination": "解释", "choice": "A"}}。

[{character_name}的信息]
公开信息：{public}
隐私信息：{private}
社交目标：{goal}

[其他角色的信息]
{user_profile}

[对话上下文]
{dialogue_context}

[提问]
{question}

[选项]
{choices}"""

Skill_Evaluation_Prompt_zhou_nocot = \
"""请你扮演{character_name}，给定{character_name}的信息，其中包含了{character_name}的公开信息、隐私信息和在社交场景中要实现的社交目标，同时，给定在社交中其他角色的信息，请你基于给定的角色信息、{character_name}和其他角色的对话上下文、和提问，从给定的选项中选择一个正确的答案,只需给出答案，不需给出解释，输出json格式，输出示例：{{"choice": "A"}}。

[{character_name}的信息]
公开信息：{public}
隐私信息：{private}
社交目标：{goal}

[其他角色的信息]
{user_profile}

[对话上下文]
{dialogue_context}

[提问]
{question}

[选项]
{choices}"""

Skill_Evaluation_Prompt_zhou_nocot_en = \
"""
Please act as {character_name}. You are provided with information about {character_name}, which includes {character_name}'s public information, private information, and social goals to achieve in the social scenario. Additionally, information about other roles in the social interaction is provided. Based on the given role information, the dialogue context involving {character_name} and other roles, and the question, choose the correct answer from the given options. Only provide the answer without any explanation. Output the result in JSON format. Example output: {{"choice": "A"}}.

[{character_name}'s Information]
Public Information: {public}
Private Information: {private}
Social Goal: {goal}

[Other Roles' Information]
{user_profile}

[Dialogue Context]
{dialogue_context}

[Question]
{question}

[Options]
{choices}
"""

Skill_Evaluation_Prompt_zhou_en = \
"""
Please act as {character_name}. You are provided with information about {character_name}, which includes {character_name}'s public information, private information, and social goals to achieve in the social scenario. Additionally, information about other roles in the social interaction is provided. Based on the given role information, the dialogue context involving {character_name} and other roles, and the question, choose the correct answer from the given options. Only provide the answer without any explanation. Output the result in JSON format. Example output: {{"explaination":"explaination to your answer", "choice": "A"}}.

[{character_name}'s Information]
Public Information: {public}
Private Information: {private}
Social Goal: {goal}

[Other Roles' Information]
{user_profile}

[Dialogue Context]
{dialogue_context}

[Question]
{question}

[Options]
{choices}
"""


Ending_Evaluation_Prompt_zhou = \
"""请你扮演{character_name}，给定{character_name}的信息，其中包含了{character_name}的公开信息、隐私信息和在社交场景中要实现的社交目标，同时，给定在社交中其他角色的信息，请你基于给定{character_name}的角色信息、{character_name}的社交目标和{character_name}和其他角色的对话上下文，从给定的选项中选择一个最有可能达成目标结局的{character_name}的回复选项，并给出解释，输出json格式，输出示例: {{"explaination": 解释,"choice": "A"}}。
[{character_name}的信息]
{main_profile}

[其他角色的信息]
{user_profile}

[对话上下文]
{dialogue_context}

[选项]
{choices}
"""

Ending_Evaluation_Prompt_zhou_en = \
"""Please play the role of {character_name}. Given the information about {character_name}, which includes {character_name}'s public information, private information, and social goals to be achieved in a social scenario, and also given the information of other characters in the social setting, please choose the response option for {character_name} that is most likely to achieve the target outcome based on the given role information of {character_name}, {character_name}'s social goals, and the dialogue context between {character_name} and other characters. Provide an explanation and output in JSON format. Output example: {{"explanation": "explanation", "choice": "A"}}.
[{character_name}'s Information]
{main_profile}

[Other Characters' Information]
{user_profile}

[Dialogue Context]
{dialogue_context}

[Options]
{choices}
"""

Response_Prompt = \
"""请你扮演{character_name}，给定{character_name}的信息，其中包含了{character_name}的公开信息、隐私信息和在社交场景中要实现的社交目标，同时，给定在社交中其他角色的信息，请你基于给定{character_name}的角色信息、{character_name}的社交目标和{character_name}和其他角色的对话上下文，采用给定的社交技能之一，做出一个最有可能达成目标结局的且使用给定的社交技能之一的{character_name}的回复，回复长度要尽量与{len}相当, 并给出解释,输出json格式,输出示例: {{"explaination": 解释,"skill": 采用的社交技能, "answer": 回复}}。
注意：回复以对话形式给出，如：{character_name}: 回复内容
[{character_name}的信息]
{main_profile}

[其他角色的信息]
{user_profile}

[对话上下文]
{dialogue_context}

[参考长度]
{len}

[社交技能]
{social_skill}

注意:
要严格遵守角色档案的内容,使用口语化表述,使用符合角色的语言对话方式,不要使用心理描写, 你要沉浸式扮演角色;
"""

Response_Prompt_en = \
"""请你扮演{character_name}，给定{character_name}的信息，其中包含了{character_name}的公开信息、隐私信息和在社交场景中要实现的社交目标，同时，给定在社交中其他角色的信息，请你基于给定{character_name}的角色信息、{character_name}的社交目标和{character_name}和其他角色的对话上下文，采用给定的社交技能之一，做出一个最有可能达成目标结局的且使用给定的社交技能之一的{character_name}的回复，回复长度要尽量与{len}相当, 并给出解释,输出json格式,输出示例: {{"explaination": 解释,"skill": 采用的社交技能, "answer": 回复}}。
注意：回复以对话形式给出，如：{character_name}: 回复内容
[{character_name}的信息]
{main_profile}

[其他角色的信息]
{user_profile}

[对话上下文]
{dialogue_context}

[参考长度]
{len}

[社交技能]
{social_skill}

注意:
要严格遵守角色档案的内容,使用口语化表述,使用符合角色的语言对话方式,不要使用心理描写, 你要沉浸式扮演角色;
请输出英文,全部用英文输出;
"""

