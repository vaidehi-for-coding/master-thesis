import pandas as pd
import scipy
from torch import reshape as trs
import numpy as np

NEWS_ARTICLES_JSON = "https://recsysfiles.s3.eu-central-1.amazonaws.com/huffpost_dataset.json"

def get_df():
    news = pd.read_json(NEWS_ARTICLES_JSON, lines=True)
    news = clean_df(news)
    return news


def clean_df(df):
    df = df[df['date'] >= pd.Timestamp(2012, 1, 1)]
    df = df[df['headline'].apply(lambda x: len(x.split()) > 5)]
    df = df[df['short_description'].apply(lambda x: len(x.split()) > 1)]
    df.sort_values('headline', inplace=True, ascending=False)
    duplicated_articles_series = df.duplicated('headline', keep=False)
    df = df[~duplicated_articles_series]
    df.index = range(df.shape[0])
    return df


def get_recommendations(queries, query_embeddings, all_corpus_embeddings, prev_liked, prev_rec, closest_n, serendipity):
    # get cosine similarities for all articles
    all_results = []
    unexpected_indices = []
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


def get_unexpected_recs(cosine_sim_list, n_liked_items):
    sorted_articles = []

    for each_query_result in cosine_sim_list:
        each_query_result = sorted(each_query_result, key=lambda x: x[0])
        sorted_articles.append(each_query_result)

    item_item_mat = []
    # create item-item matrix
    for row in sorted_articles:
        item_item_mat.append([sim[1] for sim in row])

    # calcuate unexpectedness of each article
    unexpectedness = 1 - (np.sum(item_item_mat, axis=0) / n_liked_items)
    unexpectedness = np.around(unexpectedness, decimals=4)
    idx_min = np.argpartition(unexpectedness, 2)

    unexpected_indices_act = [sorted_articles[0][idx_min[0]][0],
                              sorted_articles[0][idx_min[1]][0]]

    return unexpected_indices_act


def get_combined_articles(queries, df, previously_liked_news):
    # combine desc and headline and store index of previously liked articles
    combined_articles = []
    for i in range(len(queries)):
        article_number = df.index[(df['short_description'] == queries[i])].tolist()
        previously_liked_news.append(article_number[0])
        heads = df.at[article_number[0], 'headline']
        combined_articles.append((heads + " " + queries[i]))

    return combined_articles


def get_final_rec_indices(filtered_rec_list, closest_n, unexp_list, query_categories, SERENDIPITY, df):
    rec_indices = []
    cos_sim = []

    # aggressively recommend articles from the same category
    for each_query_result in filtered_rec_list:
        count = 0
        for idx, distance in each_query_result:
            if df.at[idx, 'category'] in query_categories:
                # if (1 - distance) >= 0.5:
                rec_indices.append(idx)
                cos_sim.append(1 - distance)
                count += 1
            if count == closest_n:
                break

    rec_np = np.array(rec_indices)
    sim_np = np.array(cos_sim)
    p = np.random.permutation(len(rec_np))
    rec_np = rec_np[p].tolist()
    sim_np = sim_np[p].tolist()

    if SERENDIPITY:
        rec_np = rec_np[:8]
        sim_np = sim_np[:8]
        rec_np.extend(unexp_list)
        sim_np.extend([0, 0])
        return rec_np, sim_np
    else:
        return rec_np[:10], sim_np[:10]
