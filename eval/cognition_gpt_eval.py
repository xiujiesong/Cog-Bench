"""
    GPT-4 Eval.
"""

import re
import os
import copy
import json
import random
import argparse
from tqdm import tqdm
from openai import OpenAI


def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line.strip())
            data.append(json_obj)
    return data

def output_parse(model_output):

    # Check if the input string is just a single digit
    if re.match(r'^\d$', model_output):
        output = {"1": int(model_output)}
    # Check if the input string contains a single output in the format "[1]"
    elif re.match(r'\[\d\]', model_output):
        match = re.search(r'\[(\d)\]', model_output)
        output = {"1": int(match.group(1))}
    else:
        matches = re.findall(r'\d+\.\s\[(\d+)\]', model_output)
        output = {str(i + 1): int(match) for i, match in enumerate(matches)}

    return output

def gt_result_merge(gt, model_output):
    """
    Merge model output into data dict.
    """
    gt_with_output = copy.deepcopy(gt)
    for i in gt:
        gt_with_output[i]['Model Output'] = next(item for item in model_output if item['filename'] == gt_with_output[i]['Image Name'])['model_output']  # model_output[gt_with_output[i]['Image Name']]
    return gt_with_output

def evaluation_data_format(gt_with_result):
    simplified_gt_with_result = {}
    for i in gt_with_result:
        
        # drop fields with None value
        none_dropped = {k:v for k,v in gt_with_result[i].items() if v[0]!='None'}
        
        # extraction conclusion from Reasonings
        conclusion_extracted = {}
        for k,v in none_dropped.items():
            if 'Reasoning' in k and k!="Event Relationship Reasoning":
                conclusion_extracted[k] = [i.split('->')[-1].strip() for i in v]
            else:
                conclusion_extracted[k] = v
        simplified_gt_with_result[i] = conclusion_extracted    

    return simplified_gt_with_result

def gpt_eval_user_input(simplified_gt_with_result):
    """
        GPT Evaluation for Reasoning (w/o Entity Relationship Reasoning)
    """
    model_output = simplified_gt_with_result['Model Output']

    reasoning = ""
    c = 0
    reasoning_score_dict = {}
    for k, v in simplified_gt_with_result.items():
        if "Reasoning" in k and k!="Event Relationship Reasoning":
            index_of_reasoning = k.find("Reasoning")
            field = "[{}]: \n".format(k[:index_of_reasoning].strip())
            reasoning_score_dict[k] = {}
            for i in v:
                c += 1
                conclusion = "{}. {}\n".format(c, i)  
                reasoning_score_dict[k][conclusion.strip()] = []
                reasoning += conclusion

    user_template = "<DESCRIPTION>: \n{}\n\n<KEY POINT>: \n{}\n".format(model_output, reasoning)

    gpt_output_template = "Please write your answers in '[ ]' with 0 or 1 in the following format (number + square brackets):\n1. [1]  2. [0]\nYour answers to the {} <KEY POINT>(s) above:\n".format(c) #   3. [1]  4. [1]  5. [0] 6. [0]
    for i in range(1,c+1):
        gpt_output_template += "{}. [ ]  ".format(i)

    prompt = user_template + gpt_output_template
    return prompt, reasoning_score_dict

def gpt_eval_er_user_input(simplified_gt_with_result):
    """
        GPT Evaluation for Entity Relationship Reasoning
    """
    model_output = simplified_gt_with_result['Model Output']
    
    c = 0
    reasoning = ""
    reasoning_score_dict = {'Event Relationship Reasoning':{}}
    v = simplified_gt_with_result['Event Relationship Reasoning']
    for i in v:
        c += 1
        conclusion = "{}. {}\n".format(c, i)  
        reasoning_score_dict['Event Relationship Reasoning'][conclusion.strip()] = []
        reasoning += conclusion

    user_template = "<DESCRIPTION>: \n{}\n\n<EVENT RELATIONSHIP>: \n{}\n".format(model_output, reasoning)

    gpt_output_template = "Please write your answers in '[ ]' with 0 or 1 in the following format (number + square brackets):\n1. [1]  2. [0]\nYour answers to the {} <EVENT RELATIONSHIP>(s) above:\n".format(c)
    for i in range(1,c+1):
        gpt_output_template += "{}. [ ]  ".format(i)

    prompt = user_template + gpt_output_template
    return prompt, reasoning_score_dict

def chat_gpt_evaluation(model_config, system_prompt, user_input):
    
    client = OpenAI(api_key = model_config['key'],
                    base_url = "Set your URL here.")
    
    response = client.chat.completions.create(
        model=model_config['name'],
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
          ]
    )
    
    return response.choices[0].message.content.strip()

def evaluator(eval_model, eval_system, eval_er_system, gt_with_output, output_file):
    for fn, sample in tqdm(gt_with_output.items()): 

        # Reasoning
        r_prompt, r_score_dict = gpt_eval_user_input(sample)

        max_attempts = 5
        attempts = 0

        while attempts < max_attempts:
            r_eval_output = chat_gpt_evaluation(eval_model, eval_system, r_prompt)
        
            print(r_prompt)
            print(r_eval_output)
            try:
                output_dict_r = output_parse(r_eval_output)
                for i in r_score_dict:
                    for j in r_score_dict[i]:
                        r_score_dict[i][j] = output_dict_r[j.split('.')[0].strip()]
                break
            except Exception as e:
                attempts += 1
                if attempts == max_attempts:
                    print("Max attempts reached. Error:", e)
                    break
                print("Error encountered on attempt", attempts, ":", e)
        
        merged_score_dict = r_score_dict.copy()

        if 'Event Relationship Reasoning' in sample:
            # Event Relationship Reasoning
            er_prompt, er_score_dict = gpt_eval_er_user_input(sample)

            max_attempts_2 = 5
            attempts_2 = 0

            while attempts_2 < max_attempts_2:
                er_eval_output = chat_gpt_evaluation(eval_model, eval_er_system, er_prompt)

                print(er_prompt)
                print(er_eval_output)
                try:
                    output_dict_er = output_parse(er_eval_output)
                    for i in er_score_dict:
                        for j in er_score_dict[i]:
                            er_score_dict[i][j] = output_dict_er[j.split('.')[0].strip()]
                    break  
                except Exception as e:
                    attempts_2 += 1
                    if attempts_2 == max_attempts_2:
                        print("Max attempts reached. Error:", e)
                        break
                    print("Error encountered on attempt", attempts_2, ":", e)
            
            # merge the score dict
            merged_score_dict.update(er_score_dict)

        # remove the number in the key
        for i in merged_score_dict:
            new_dict = {}
            for key, value in merged_score_dict[i].items():
                new_key = key[3:].strip()
                new_dict[new_key] = value

            merged_score_dict[i] = new_dict
        
        merged_score_dict['Image Name'] = sample['Image Name']
        merged_score_dict['Model Output'] = sample['Model Output']

        with open(output_file, "a+") as f:
            json.dump(merged_score_dict, f)
            f.write('\n')


def main(ann_json_file_path, model_output_file_path, eval_output_file, gpt_name, api_key):
    
    # chatgpt config
    gpt = {"name": gpt_name,"key": api_key}

    with open(ann_json_file_path, 'r') as json_file:
        ann = json.load(json_file)
    
    # system instruction
    eval_system = open("system/eval_system_prompt_v2.txt", encoding="utf-8").read()
    eval_er_system = open("system/eval_system_prompt_er_v2.txt", encoding="utf-8").read()

    model_output = read_jsonl(model_output_file_path)
    gt_with_result = gt_result_merge(ann, model_output)
    simplified_gt_with_result = evaluation_data_format(gt_with_result)

    # simplified_gt_with_result = dict(list(simplified_gt_with_result.items())[243:])

    evaluator(gpt, eval_system, eval_er_system, simplified_gt_with_result, eval_output_file)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--cogbench_description_file_path",
        type=str,
        default="/path/to/cogbench_description_file",
        help="Download cogbench.zip and `unzip cogbench.zip` and change the path here",
    )
    parser.add_argument(
        "--model_output_file_path",
        type=str,
        default="/path/to/model_output_file.jsonl",
    )
    parser.add_argument(
        "--eval_output_file_path",
        type=str,
        default="/path/to/eval_output_file.jsonl",
    )
    parser.add_argument(
        "--gpt_name",
        type=str,
        default="gpt-4-turbo",
        help="GPT model name",
    )
    parser.add_argument(
        "--openai_api_key",
        type=str, 
        default=None,
        help="OpenAI API key"
    )
    args = parser.parse_args()

    main(args.cogbench_description_file_path, args.model_output_file_path, args.eval_output_file_path, args.gpt_name, args.openai_api_key)
    