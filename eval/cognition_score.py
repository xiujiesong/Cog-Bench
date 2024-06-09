import json
import argparse


def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line.strip())
            data.append(json_obj)
    return data

def cognition_score(model_eval_result_list):

    reasoning_types = ['Special Time Reasoning', 'Location Reasoning', 'Character Reasoning', 'Character Relationship Reasoning', 
                  'Event Reasoning', 'Event Relationship Reasoning', 'Next Moment Event Reasoning', 'Mental State Reasoning']

    sample_scores_dict = {}
    for sample in model_eval_result_list:
        img_name = sample['Image Name']
        sample_scores = {}
        for k, v in sample.items():
            if 'Reasoning' in k:
                reasoning_type = k
                reasoning_scores = list(v.values())
                sample_scores[reasoning_type] = reasoning_scores
        sample_scores_dict[img_name] = sample_scores

    reasoning_scores_dict = {}
    for reasoning_type in reasoning_types:
        reasoning_scores_dict[reasoning_type] = []
        for img_name in sample_scores_dict:
            if reasoning_type in sample_scores_dict[img_name]:
                reasoning_scores_dict[reasoning_type] += sample_scores_dict[img_name][reasoning_type]

    for reasoning_type in reasoning_types:
        print(reasoning_type + ": ", '%.3f' % (sum(reasoning_scores_dict[reasoning_type])/len(reasoning_scores_dict[reasoning_type])))
    
    print("Overall: ", '%.3f' % (sum([sum(reasoning_scores_dict[reasoning_type]) for reasoning_type in reasoning_types])/sum([len(reasoning_scores_dict[reasoning_type]) for reasoning_type in reasoning_types])))

def main(file_path):
    if file_path.endswith('.jsonl'):
        model_eval_result_list = read_jsonl(file_path)
    elif file_path.endswith('.json'):
        with open(file_path) as f:
            model_eval_result_list = json.load(f)
    else:
        raise ValueError("File type not supported")
    
    cognition_score(model_eval_result_list)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--eval_output_file_path",
        type=str,
        default="/path/to/eval_output_file.jsonl",
    )
    args = parser.parse_args()

    main(args.eval_output_file_path)
