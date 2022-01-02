var liked_news = [];
var liked_cat = [];

$(document).ready(function() {
        // all custom jQuery will go here

        // post on click of get more recommendations button
        $('#recommend_btn').click(function() {
            // convert input to strings
            let js_data = JSON.stringify(liked_news);
            let unique_cat = [...new Set(liked_cat)];
            let js_cat = JSON.stringify(unique_cat);
            const send_data = {
                d1: js_data,
                d2: js_cat
            };

            // AJAX post request initialization
            $.ajax({
            type: "POST",
            contentType: "application/json;charset=utf-8",
            url: "/news_recommender",
            traditional: "true",
            data: JSON.stringify(send_data),
            success: function (response) {
                $("#elementToUpdate").html(response);
            },
            error: function (jqXHR, status, err) {
                console.log(jqXHR, status, err);
                // console.warn(jqXHR, status, err);
            }
        });
    });
});

// retrieve data from rows when user likes/unlikes an article and store for processing
function toggleLike(clicked_btn) {
        let row = clicked_btn.closest("tr");
        let row_data = row.getElementsByTagName("td");
        let read_article = row_data[1].textContent
        clicked_btn.addEventListener('click', function() {
            this.classList.toggle('green');
            if (liked_news.includes(read_article)) {
                const index = liked_news.indexOf(read_article)
                if (index > -1) {
                  liked_news.splice(index, 1);
                  liked_cat.splice(index, 1);
                  sessionStorage.removeItem(row_data[1].textContent);
                  sessionStorage.removeItem(row_data[3].textContent);
                }
            }
            else{
                liked_news.push(read_article)
                liked_cat.push(row_data[3].textContent)
                sessionStorage.setItem(row_data[1].textContent, '-');
                sessionStorage.setItem(row_data[3].textContent, '-');
            }
      });
}




