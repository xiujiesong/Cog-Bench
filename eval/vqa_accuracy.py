import json
import argparse


def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line.strip())
            data.append(json_obj)
    return data

def accuracy(data):

    correct_num = 0
    cate_stat = {
        "time": {"total": 0, "correct_num": 0},
        "location": {"total": 0, "correct_num": 0},
        "character": {"total": 0, "correct_num": 0},
        "character_relationship": {"total": 0, "correct_num": 0},
        "event": {"total": 0, "correct_num": 0},
        "event_relationship": {"total": 0, "correct_num": 0},
        "next_event": {"total": 0, "correct_num": 0},
        "mental": {"total": 0, "correct_num": 0},
    }

    model_output = []
    for i in data:
        response = i['response'][0]
        answer = i['answer']
        model_output.append(response)

        cate_stat[i['category']]['total'] += 1

        if answer == response:
            correct_num += 1
            cate_stat[i['category']]['correct_num'] += 1
    
    print(set(model_output))
    # print(cate_stat)

    overall_acc = correct_num/len(data)
    time_acc = cate_stat['time']['correct_num']/cate_stat['time']['total']
    loc_acc = cate_stat['location']['correct_num']/cate_stat['location']['total']
    char_acc = cate_stat['character']['correct_num']/cate_stat['character']['total']
    char_re_acc = cate_stat['character_relationship']['correct_num']/cate_stat['character_relationship']['total']
    event_acc = cate_stat['event']['correct_num']/cate_stat['event']['total']
    event_re_acc = cate_stat['event_relationship']['correct_num']/cate_stat['event_relationship']['total']
    next_acc = cate_stat['next_event']['correct_num']/cate_stat['next_event']['total']
    mental_acc = cate_stat['mental']['correct_num']/cate_stat['mental']['total']

    return overall_acc, time_acc, loc_acc, char_acc, char_re_acc, event_acc, event_re_acc, next_acc, mental_acc


def main(qa_file_path):

    # jsonl
    if qa_file_path.endswith(".jsonl"):
        data = read_jsonl(qa_file_path)
    # json
    elif qa_file_path.endswith(".json"):
        with open(qa_file_path, 'r') as file:
            data = json.load(file)

    print(len(data))
    overall_acc, time_acc, loc_acc, char_acc, char_re_acc, event_acc, event_re_acc, next_acc, mental_acc = accuracy(data)
    print("Time Acc.: {}, Location Acc.: {}, Character Acc.: {}, Character Relationship Acc.: {}, Event Acc.: {}, Event Relationship Acc.: {}, Next Event Acc.: {}, Mental State Acc.: {}, Overall Acc.: {}".format(time_acc, 
                                                                                                                                                                                                                    loc_acc, 
                                                                                                                                                                                                                    char_acc, 
                                                                                                                                                                                                                    char_re_acc, 
                                                                                                                                                                                                                    event_acc, 
                                                                                                                                                                                                                    event_re_acc, 
                                                                                                                                                                                                                    next_acc, 
                                                                                                                                                                                                                    mental_acc, 
                                                                                                                                                                                                                    overall_acc))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model_output_file_path",
        type=str,
        default="/path/to/model_output_file.jsonl",
    )
    args = parser.parse_args()
    
    main(args.model_output_file_path)