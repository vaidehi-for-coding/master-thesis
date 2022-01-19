var liked_news = [];
var liked_cat = [];
var nLikedPerInteraction = 0

$(document).ready(function() {

        // post on click of get more recommendations button for R1
        $('#recommend_btn').click(function() {
            ajaxReq("/news_recommender-1");
    });

        // post on click of get more recommendations button for R2
        $('#recommend_btn_nr2').click(function() {
            ajaxReq("/news_recommender-2");
    });

        function ajaxReq(toPage) {
            if (nLikedPerInteraction < 3){
                window.alert("Like at least 3 articles. Only " +nLikedPerInteraction+ " liked!")
            } else if (nLikedPerInteraction > 5){
                window.alert(nLikedPerInteraction + " liked. Choose upto 5 articles only! Double-click on like button to revert choice.")
            } else{
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
                    beforeSend: function(){
                        $('#loading').html('<img src="https://upload.wikimedia.org/wikipedia/commons/b/b9/Youtube_loading_symbol_1_%28wobbly%29.gif"> loading...')
                        $('#loading').css("visibility", "visible");
                    },
                    complete: function(){
                        $('#loading').css("visibility", "hidden");
                    },
                    contentType: "application/json;charset=utf-8",
                    url: toPage,
                    traditional: "true",
                    data: JSON.stringify(send_data),
                    success: function (response) {
                        $("#elementToUpdate").html(response);
                    },
                    error: function (jqXHR, status, err) {
                        // console.log(jqXHR, status, err);
                    }
                });
            }
        }
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
                  // console.log("REM: ", liked_news)
                  // sessionStorage.removeItem(row_data[1].textContent);
                  // sessionStorage.removeItem(row_data[3].textContent);
                  nLikedPerInteraction--;
                }
            }
            else{
                liked_news.push(read_article)
                liked_cat.push(row_data[3].textContent)
                // console.log("ADD: ", liked_news)
                // sessionStorage.setItem(row_data[1].textContent, '-');
                // sessionStorage.setItem(row_data[3].textContent, '-');
                nLikedPerInteraction++;
            }
      });
}




