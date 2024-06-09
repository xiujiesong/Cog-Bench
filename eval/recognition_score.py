import json
import spacy
import argparse
import numpy as np
import matplotlib.pyplot as plt

from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

nlp = spacy.load("en_core_web_sm")
model = SentenceTransformer('/path/to/all-mpnet-base-v2')


def read_jsonl(file_path):
    data = []
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            json_obj = json.loads(line.strip())
            data.append(json_obj)
    return data

def entity_recall(entity_list, description, threshold=0.5, is_print=False):
    
    doc = nlp(description)
    desc_noun_list = list(set([token.norm_ for token in doc if token.pos_ == "NOUN" or token.pos_ == "PROPN"]))
    
    if is_print:
        print("Entities: ", entity_list)
        print("Nouns in Description: ",desc_noun_list)

        print("Num. of Entities:             ", len(entity_list))
        print("Num. of Nouns in Description: ", len(desc_noun_list))
    
    entity_embeddings = model.encode(entity_list, convert_to_tensor=False)
    desc_noun_embeddings = model.encode(desc_noun_list, convert_to_tensor=False)

    sim_matrix = cosine_similarity(entity_embeddings, desc_noun_embeddings, dense_output=True)

    max_values = np.amax(sim_matrix, axis=1, keepdims=True)
    max_sim_matrix = np.where(sim_matrix == max_values, sim_matrix, 0)
    if is_print:
        print(max_sim_matrix)
    
    exist_matrix = np.where(max_sim_matrix > threshold, max_sim_matrix, 0)
    non_zero_count = np.count_nonzero(exist_matrix)
    # nonzero_indices = np.where(~np.all(exist_matrix == 0, axis=1))[0]
    # non_zero_count = len(nonzero_indices)

    recall = non_zero_count/len(entity_list)
    hitted_num = non_zero_count
    entity_num = len(entity_list)

    return recall, hitted_num, entity_num

def evaluator(description_json_file_path, model_output_file_path, threshold, is_print):

    with open(description_json_file_path, 'r') as json_file:
        data = json.load(json_file)
    
    model_output = read_jsonl(model_output_file_path)

    recall_scores = {}
    total_hitted_num = 0
    total_entity_num = 0
    for i in model_output:
        file_name = i['filename']
        model_description = i['model_output']
        img_id = file_name.split('.')[0]

        ann_entities = data[img_id]['Entities']
        r, hitted_num, entity_num = entity_recall(ann_entities, model_description, threshold, is_print)
        recall_scores[img_id] = r
        total_hitted_num += hitted_num
        total_entity_num += entity_num

    macro_avg_recall = sum(recall_scores.values())/len(recall_scores)
    micro_avg_recall = total_hitted_num/total_entity_num
    print("Total entity num: ", total_entity_num)

    return macro_avg_recall, micro_avg_recall


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
    args = parser.parse_args()

    macro_avg_recall, micro_avg_recall = evaluator(args.cogbench_description_file_path, args.model_output_file_path, threshold=0.6, is_print=False)
    
    print("Macro Avg. Recall: ", macro_avg_recall)
    print("Micro Avg. Recall: ", micro_avg_recall)