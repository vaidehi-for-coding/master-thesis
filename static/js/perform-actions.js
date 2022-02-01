var randomlinks = [];
randomlinks[0]="https://g1.recommender.digitaltransformation.bayern/";
randomlinks[1]="https://g2.recommender.digitaltransformation.bayern/";


// retrieve data from rows when user likes/unlikes an article and store for processing
function sendTo() {
    window.open(randomlinks[Math.floor(Math.random()*randomlinks.length)]);
}