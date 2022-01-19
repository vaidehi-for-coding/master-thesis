# flask imports
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

# python imports
from sentence_transformers import SentenceTransformer
from pyth_code.sbert_recsys import *
import json
import string
import random

application = app = Flask(__name__)
CORS(application)

SERENDIPITY = True

# column headings for html page (display name and internal name)
disp_headings = ["Headline", "Snippet", "Link", "Category", "Like it?"]
act_heading = ['headline', 'short_description', 'link', 'category', 'rate']
disp_headings_2 = ["Headline", "Snippet", "Link", "Category", "Like it?"]
act_heading_2 = ['headline', 'short_description', 'link', 'category', 'rate']

# corpus embeddings
CORPUS_EMBEDDINGS = "all-MiniLM-L6-v2-embeddings-2012-all-combined.npy"
# no of recommendations desired per page
closest_n = 10
# stores indices of previously liked articles
previously_liked_news = []
# stores indices of previously recommended news
previously_rec_news = []
# stores indices of unexpected articles that were liked
serendipitious_articles = []
# stores number of times the unexpected articles were liked
s_score = []
# store number of interactions with nr1
nInteractionsWithR1 = []
# store number of interactions with nr2
nInteractionsWithR2 = []

# load model for semantic similarity
model = SentenceTransformer('all-MiniLM-L6-v2')
# get default dataframe
df = get_df()
# load sentence embeddings
all_corpus_embeddings = np.load(CORPUS_EMBEDDINGS)
# add column to dataframe
df["rate"] = ''

# generate unique id per session
unq_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))


# home page
@application.route('/', methods=['GET'])
def main():
    if SERENDIPITY:
        return render_template("about_rc_and_fb.html")
    else:
        return render_template("about_only_rc.html")


# instructions page
@application.route('/instructions', methods=['POST', 'GET'])
def instructions():
    return render_template("about_us.html")


# filterbubble page
@application.route('/filterbubble', methods=['POST', 'GET'])
def filterbubble():
    return render_template("about_fb.html")


# survey page
@application.route('/survey', methods=['POST', 'GET'])
def go_to_survey():
    if len(nInteractionsWithR2) < 1:
        err_int = str(len(nInteractionsWithR2))
        return jsonify(message='Please interact with R2 at least 5 times. Your interactions: ' + err_int), 500
    else:
        write_to_file(unq_id, previously_liked_news, previously_rec_news, s_score, "R2")
        if SERENDIPITY:
            # webbrowser.open("https://limesurvey.digitaltransformation.bayern/index.php/178969", new=1, autoraise=True)
            return jsonify(
                message='Success. Please fill out the survey at '
                        'https://limesurvey.digitaltransformation.bayern/index.php/178969 to '
                        'complete the last step in this study. Provide '
                        'the following details in the first and second question of the questionnaire. Study_id: ' + unq_id +
                        ' s_score: ' + str(len(s_score)))
        else:  # go to some other link
            # webbrowser.open("https://limesurvey.digitaltransformation.bayern/index.php/917924", new=0, autoraise=True)
            return jsonify(
                message='Success. Please fill out the survey at '
                        'https://limesurvey.digitaltransformation.bayern/index.php/917924 to '
                        'complete the last step in this study. Provide '
                        'the following details in the first and second question of the questionnaire. Study_id: ' + unq_id +
                        ' s_score: ' + str(len(s_score)))


# recommendations page
@application.route('/news_recommender-1', methods=['POST', 'GET'])
def nr1():
    serendipity = False
    if request.method == 'GET':
        n = 2  # no of samples from each category
        to_display_df = df.groupby('category').apply(lambda x: x.sample(min(n, len(x)))).reset_index(drop=True)
        return render_template("news_table.html", column_names=disp_headings,
                               row_data=list(to_display_df[act_heading].values.tolist()),
                               like_col="Like it?", link_col="Link", zip=zip)
    else:
        predictions = recommend_movies(serendipity)
        nInteractionsWithR1.append(1)
        return render_template("news_table.html", column_names=disp_headings_2,
                               row_data=list(predictions[act_heading_2].values.tolist()),
                               like_col="Like it?", link_col="Link", zip=zip)


def recommend_movies(serendipity):
    request_data = request.json
    queries = json.loads(request_data['d1'])  # desc
    query_categories = json.loads(request_data['d2'])  # cat

    # combine desc and headline for better semantic similarity measure
    combined_queries = get_combined_articles(queries, df, previously_liked_news, serendipitious_articles, s_score)

    # create embeddings for liked news
    query_embeddings = model.encode(combined_queries, convert_to_tensor=True)

    # get article index and cosine similarity (already sorted from the most similar to the least similar)
    filtered_rec_list, unexp_list = get_recommendations(combined_queries, query_embeddings, all_corpus_embeddings,
                                                        previously_liked_news,
                                                        previously_rec_news, closest_n, serendipity)

    # get final recommendation indices
    rec_indices = get_final_rec_indices(filtered_rec_list, closest_n, unexp_list, query_categories,
                                        serendipity, df)

    # add rec indices to prev recommended
    previously_rec_news.extend(rec_indices)

    # add unexpected indices to serendipitous articles list
    serendipitious_articles.extend(unexp_list)

    # create final dataframe
    user_recommendations = df.iloc[rec_indices, :]

    return user_recommendations


# recommendations page
@application.route('/news_recommender-2', methods=['POST', 'GET'])
def nr2():
    serendipity = True
    if request.method == 'GET':
        if len(nInteractionsWithR1) < 1:
            err_int = str(len(nInteractionsWithR1))
            return jsonify(message='Please interact with R1 at least 5 times. Your interactions: ' + err_int), 500
        else:
            write_to_file(unq_id, previously_liked_news, previously_rec_news, s_score, "R1")
            n = 2  # no of samples from each category
            to_display_df = df.groupby('category').apply(lambda x: x.sample(min(n, len(x)))).reset_index(drop=True)
            return render_template("news_table_nr2.html", column_names=disp_headings,
                                   row_data=list(to_display_df[act_heading].values.tolist()),
                                   like_col="Like it?", link_col="Link", zip=zip)
    else:
        predictions = recommend_movies(serendipity)
        nInteractionsWithR2.append(1)
        return render_template("news_table_nr2.html", column_names=disp_headings_2,
                               row_data=list(predictions[act_heading_2].values.tolist()),
                               like_col="Like it?", link_col="Link", zip=zip)


if __name__ == '__main__':
    application.run(DEBUG=True)
