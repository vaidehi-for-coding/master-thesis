# python imports
from datetime import datetime
import pandas as pd
import scipy
from torch import reshape as trs
import numpy as np
import os

# stored dataset
NEWS_ARTICLES_JSON = "huffpost_dataset.json"


# returns cleaned dataframe
def get_df():
    news = pd.read_json(NEWS_ARTICLES_JSON, lines=True)
    news = clean_df(news)
    return news


# cleans the loaded dataframe
def clean_df(df):
    df = df[df['date'] >= pd.Timestamp(2012, 1, 1)]
    df = df[df['headline'].apply(lambda x: len(x.split()) > 5)]  # remove all headlines shorter than 5 words
    df = df[df['short_description'].apply(lambda x: len(x.split()) > 1)]  # remove all desc shorter than 5 words
    df.sort_values('headline', inplace=True, ascending=False)
    duplicated_articles_series = df.duplicated('headline', keep=False)  # remove all duplicate headlines
    df = df[~duplicated_articles_series]
    df.index = range(df.shape[0])  # reindex the dataframe
    return df


# returns a sorted hashmap of article index vs cosine similarity (highest to lowest) and unexpected article indices
def get_recommendations(queries, query_embeddings, all_corpus_embeddings, prev_liked, prev_rec, closest_n, serendipity):
    all_results = []
    unexpected_indices = []

    # for each headline, store the similarity against every article in the dataframe (highest to lowest)
    for query, query_embedding in zip(queries, query_embeddings):
        distances = scipy.spatial.distance.cdist(trs(query_embedding, (1, query_embedding.shape[0])),
                                                 all_corpus_embeddings,
                                                 "cosine")[0]

        results = zip(range(len(distances)), distances)

        # sort from highest to lowest cosine similarity
        all_results.append(sorted(results, key=lambda x: x[1]))

    # create new corpus with articles that have not been previously liked or recommended
    remaining_articles = []
    for each_query_result in all_results:
        not_recommended_articles = []
        for art_no, cos_sim in each_query_result:
            if art_no not in prev_rec and art_no not in prev_liked:
                not_recommended_articles.append((art_no, cos_sim))
        remaining_articles.append(not_recommended_articles)

    if serendipity:
        unexpected_indices = get_unexpected_recs(remaining_articles, closest_n)

    return remaining_articles, unexpected_indices


# return articles that would be unexpected based on current choices
def get_unexpected_recs(cosine_sim_list, n_liked_items):
    sorted_articles = []

    for each_query_result in cosine_sim_list:
        each_query_result = sorted(each_query_result, key=lambda x: x[0])
        sorted_articles.append(each_query_result)

    item_item_mat = []
    # create item-item matrix
    for row in sorted_articles:
        item_item_mat.append([sim[1] for sim in row])

    # calculate unexpectedness of each article
    unexpectedness = 1 - (np.sum(item_item_mat, axis=0) / n_liked_items)
    unexpectedness = np.around(unexpectedness, decimals=4)
    idx_min = np.argpartition(unexpectedness, 2)

    unexpected_indices_act = [sorted_articles[0][idx_min[0]][0],
                              sorted_articles[0][idx_min[1]][0]]

    return unexpected_indices_act


# return headline and desc combined into a single sentence
def get_combined_articles(queries, df, previously_liked_news, serendipitious_articles, s_score,
                          articles_liked_per_interaction,
                          unexp_articles_liked_per_interaction):
    # combine desc and headline and store index of previously liked articles
    combined_articles = []
    unexp_tracker = 0
    normal_tracker = 0
    for i in range(len(queries)):
        article_number = df.index[(df['short_description'] == queries[i])].tolist()
        previously_liked_news.append(article_number[0])
        heads = df.at[article_number[0], 'headline']
        combined_articles.append((heads + " " + queries[i]))
        normal_tracker += 1
        if article_number[0] in serendipitious_articles:
            s_score.append(article_number[0])
            unexp_tracker += 1

    articles_liked_per_interaction.append(normal_tracker)
    unexp_articles_liked_per_interaction.append(unexp_tracker)

    return combined_articles


# return final article indices to be recommended
def get_final_rec_indices(filtered_rec_list, closest_n, unexp_list, query_categories, SERENDIPITY, df):
    rec_indices = []

    # aggressively recommend articles from the same category
    for each_query_result in filtered_rec_list:
        count = 0
        for idx, distance in each_query_result:
            if df.at[idx, 'category'] in query_categories:
                rec_indices.append(idx)
                count += 1
            if count == closest_n:
                break

    rec_np = np.array(rec_indices)
    p = np.random.permutation(len(rec_np))
    rec_np = rec_np[p].tolist()

    if SERENDIPITY:
        rec_np = rec_np[:8]
        # insert unexpected news at 3rd and 6th position in recommendations
        recs_shuffled = rec_np[:2] + [unexp_list[0]] + rec_np[2:4] + [unexp_list[1]] + rec_np[4:8]
        return recs_shuffled
    else:
        return rec_np[:10]


def write_to_file(user_id, prev_liked, prev_rec, serendipitous_articles, recommender, articles_liked_per_interaction,
                  unexp_articles_liked_per_interaction, nInteractionsWithR1, nInteractionsWithR2):
    # datetime object containing current date and time
    now = datetime.now()
    dt_string = now.strftime("%d%m%Y%H%M%S")
    file_name = f'{os.getcwd()}/data/{user_id}_{dt_string}_{recommender}.txt'
    with open(file_name, 'w') as f:
        f.write("Interactions with R1: " + str(len(nInteractionsWithR1)))
        f.write("\nInteractions with R2: " + str(len(nInteractionsWithR2)))
        f.write("\nLiked article indices: " + ' '.join(str(elem) for elem in prev_liked))
        f.write("\nNumber of articles liked per interaction: " + ' '.join(str(elem) for elem in
                                                                          articles_liked_per_interaction))
        f.write("\nRecommended articles indices: " + ' '.join(str(elem) for elem in prev_rec))
        f.write("\nSerendipitous articles that were liked indices: " + ' '.join(
            str(elem) for elem in serendipitous_articles))
        f.write("\nNumber of serendipitous articles liked per interaction: " + ' '.join(str(elem) for elem in
                                                                                        unexp_articles_liked_per_interaction))
        f.close()
