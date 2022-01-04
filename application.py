# flask imports
from flask import Flask, render_template, request
from flask_cors import CORS

# python imports
from sentence_transformers import SentenceTransformer
from sbert_recsys import *
import json

application = app = Flask(__name__)
CORS(application)

SERENDIPITY = False

# column headings for html page (display name and internal name)
disp_headings = ["Headline", "Snippet", "Link", "Category", "Like it?"]
act_heading = ['headline', 'short_description', 'link', 'category', 'rate']
disp_headings_2 = ["Headline", "Snippet", "Link", "Category", "Like it?", "Similarity"]
act_heading_2 = ['headline', 'short_description', 'link', 'category', 'rate', 'similarity']

# dataset used
NEWS_ARTICLES_JSON = "huffpost_dataset.json"
# corpus embeddings
CORPUS_EMBEDDINGS = "all-MiniLM-L6-v2-embeddings-2012-all-combined.npy"
# no of recommendations desired per page
closest_n = 10
# stores indices of previously liked articles
previously_liked_news = []
# stores indices of previously recommended news
previously_rec_news = []

# load model for semantic similarity
model = SentenceTransformer('all-MiniLM-L6-v2')
# get default dataframe
df = get_df()
# load sentence embeddings
all_corpus_embeddings = np.load(CORPUS_EMBEDDINGS)
# add column to dataframe
df["rate"] = ''


# home page
@application.route('/', methods=['GET'])
def main():
    if SERENDIPITY:
        return render_template("about_fb.html")
    else:
        return render_template("about_only_rc.html")


# instructions page
@application.route('/instructions', methods=['POST', 'GET'])
def instructions():
    return render_template("about_us.html")


# recommendations page
@application.route('/news_recommender', methods=['POST', 'GET'])
def rerouted():
    if request.method == 'GET':
        n = 2  # no of samples from each category
        to_display_df = df.groupby('category').apply(lambda x: x.sample(min(n, len(x)))).reset_index(drop=True)
        return render_template("news_table.html", column_names=disp_headings,
                               row_data=list(to_display_df[act_heading].values.tolist()),
                               like_col="Like it?", link_col="Link", zip=zip)
    else:
        predictions = recommend_movies()
        return render_template("news_table.html", column_names=disp_headings_2,
                               row_data=list(predictions[act_heading_2].values.tolist()),
                               like_col="Like it?", link_col="Link", zip=zip)


def recommend_movies():
    request_data = request.json
    queries = json.loads(request_data['d1'])  # desc
    query_categories = json.loads(request_data['d2'])  # cat

    # combine desc and headline for better semantic similarity measure
    combined_queries = get_combined_articles(queries, df, previously_liked_news)

    # create embeddings for liked news
    query_embeddings = model.encode(combined_queries, convert_to_tensor=True)

    # get article index and cosine similarity (already sorted from the most similar to the least similar)
    filtered_rec_list, unexp_list = get_recommendations(combined_queries, query_embeddings, all_corpus_embeddings,
                                                        previously_liked_news,
                                                        previously_rec_news, closest_n, SERENDIPITY)

    # get final recommendation indices
    rec_indices, cos_sim = get_final_rec_indices(filtered_rec_list, closest_n, unexp_list, query_categories,
                                                 SERENDIPITY, df)

    # add rec indices to prev recommended
    previously_rec_news.extend(rec_indices)

    # create final dataframe
    user_recommendations = df.iloc[rec_indices, :]
    user_recommendations["similarity"] = cos_sim
    return user_recommendations


if __name__ == '__main__':
    application.run(DEBUG=True)
