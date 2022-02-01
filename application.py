# flask imports
from flask import Flask, render_template, request, redirect
from flask_cors import CORS

# python imports
from sentence_transformers import SentenceTransformer
from pyth_code.sbert_recsys import *
import json
import string
import random
import webbrowser

application = app = Flask(__name__)
application.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
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
# stores how many articles were liked in each interaction
articles_liked_per_interaction = []
# stores indices of previously recommended news
previously_rec_news = []
# stores indices of unexpected articles that were liked
serendipitious_articles = []
# stores how many unexpected articles were liked in each interaction
unexp_articles_liked_per_interaction = []
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
# store categories user liked
categories = []

# generate unique id per session
unq_id = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(6))

# clear arrays before use
def reset_global_vars():
    previously_liked_news.clear()
    articles_liked_per_interaction.clear()
    previously_rec_news.clear()
    serendipitious_articles.clear()
    unexp_articles_liked_per_interaction.clear()
    s_score.clear()
    nInteractionsWithR1.clear()
    nInteractionsWithR2.clear()


# clear all globally declared arrays
reset_global_vars()

# home page
@application.route('/', methods=['GET'])
def main():
    return render_template("welcome.html")


# instructions page
@application.route('/instructions', methods=['POST', 'GET'])
def instructions():
    return render_template("about_us.html")


# welcome page
@application.route('/about', methods=['POST', 'GET'])
def about_rc():
    if SERENDIPITY:
        return render_template("about_rc_and_fb.html")
    else:
        return render_template("about_only_rc.html")


# filterbubble page
@application.route('/filterbubble', methods=['POST', 'GET'])
def filterbubble():
    return render_template("about_fb.html")


# survey page
@application.route('/survey', methods=['POST', 'GET'])
def go_to_survey():
    if len(nInteractionsWithR2) < 5:
        err_int = str(len(nInteractionsWithR2))
        err_stmt = "PLEASE INTERACT WITH R2 AT LEAST 5 TIMES. YOU INTERACTED: " + err_int + " TIMES"
        return render_template("fail_interactions.html", error_statement=err_stmt)
    else:
        write_to_file(unq_id, previously_liked_news, previously_rec_news, s_score,
                      articles_liked_per_interaction, unexp_articles_liked_per_interaction, nInteractionsWithR1,
                      nInteractionsWithR2)
        if SERENDIPITY:
            survey_link = "http://limesurvey.digitaltransformation.bayern/index.php/353413?lang=en&studyID=" + unq_id + \
                          "&sScore=" + str(len(s_score))
            webbrowser.open(survey_link, new=1, autoraise=True)
            return render_template("survey.html", survey_link=survey_link)
        else:  # go to some other link
            survey_link = "http://limesurvey.digitaltransformation.bayern/index.php/917924?lang=en&studyID=" + unq_id + \
                          "&sScore=" + str(len(s_score))
            webbrowser.open(survey_link, new=1, autoraise=True)
            return render_template("survey.html", survey_link=survey_link)


# recommendations page
@application.route('/news_recommender-1', methods=['POST', 'GET'])
def nr1():
    serendipity = False
    if request.method == 'GET':
        user_categories = json.loads(request.args['categoriesChosen'])
        user_categories = [w.replace('AND', '&') for w in user_categories]

        # CHECK
        categories.clear()
        categories.extend(user_categories)

        n = 2  # no of samples from each category
        to_display_df = df.loc[df['category'].isin(user_categories)]
        to_display_df = to_display_df.groupby('category').apply(lambda x: x.sample(min(n, len(x)))).reset_index(
            drop=True)
        return render_template("news_table.html", column_names=disp_headings,
                               row_data=list(to_display_df[act_heading].values.tolist()),
                               like_col="Like it?", link_col="Link", noOfInteractions=len(nInteractionsWithR1),
                               zip=zip)
    else:
        predictions = recommend_movies(serendipity)
        nInteractionsWithR1.append(1)
        return render_template("news_table.html", column_names=disp_headings_2,
                               row_data=list(predictions[act_heading_2].values.tolist()),
                               like_col="Like it?", link_col="Link", noOfInteractions=len(nInteractionsWithR1), zip=zip)


def recommend_movies(serendipity):
    request_data = request.json
    queries = json.loads(request_data['d1'])  # desc
    query_categories = json.loads(request_data['d2'])  # cat

    # combine desc and headline for better semantic similarity measure
    combined_queries = get_combined_articles(queries, df, previously_liked_news, serendipitious_articles, s_score,
                                             articles_liked_per_interaction, unexp_articles_liked_per_interaction)

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
        if len(nInteractionsWithR1) < 5:
            err_int = str(len(nInteractionsWithR1))
            err_stmt = "PLEASE INTERACT WITH R1 AT LEAST 5 TIMES. YOU INTERACTED: " + err_int + " TIMES"
            return render_template("fail_interactions.html", error_statement=err_stmt)
        else:
            n = 2  # no of samples from each category
            to_display_df = df.loc[df['category'].isin(categories)]
            to_display_df = to_display_df.groupby('category').apply(lambda x: x.sample(min(n, len(x)))).reset_index(
                drop=True)
            return render_template("news_table_nr2.html", column_names=disp_headings,
                                   row_data=list(to_display_df[act_heading].values.tolist()),
                                   like_col="Like it?", link_col="Link", noOfInteractions=len(nInteractionsWithR2),
                                   zip=zip)
    else:
        predictions = recommend_movies(serendipity)
        nInteractionsWithR2.append(1)
        return render_template("news_table_nr2.html", column_names=disp_headings_2,
                               row_data=list(predictions[act_heading_2].values.tolist()),
                               like_col="Like it?", link_col="Link", noOfInteractions=len(nInteractionsWithR2), zip=zip)


@application.route('/categories', methods=['GET'])
def getUserCategories():
    user_categories = df["category"].unique()
    categories.clear()
    categories.extend(user_categories)
    return render_template("news_categories.html", category=sorted(categories), column_names=["Category", "Like it?"])


if __name__ == '__main__':
    application.run(DEBUG=False)
