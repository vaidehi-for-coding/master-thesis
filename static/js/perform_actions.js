var liked_news = [];
var liked_cat = [];

$(document).ready(function() {
    // all custom jQuery will go here
        $('#recommend_btn').click(function() {
        let js_data = JSON.stringify(liked_news);
        let unique_cat = [...new Set(liked_cat)];
        let js_cat = JSON.stringify(unique_cat);
        console.log("Sending request ...")
        const send_data = {
            d1: js_data,
            d2: js_cat
        };
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

<!-- Like button code -->
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

function getRecommendations() {
        let js_data = JSON.stringify(liked_news);
        console.log("Stringified news: ", js_data)
        $.ajax({
            url: '/news_recommender',
            type : 'post',
            contentType: 'application/json',
            dataType : 'json',
            data : js_data,
        }).done(function(result) {
            console.log(result);
            $("#data").html(result);
        }).fail(function(jqXHR, textStatus, errorThrown) {
            console.log("fail: ",textStatus, errorThrown);
        });
};




