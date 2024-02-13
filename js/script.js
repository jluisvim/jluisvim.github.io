//var counterContainer = document.querySelector(".website-counter");
//var resetButton = document.querySelector("#reset");
//var visitCount = localStorage.getItem("page_view");
//
//// Check if page_view entry is present
//if (visitCount) {
//    visitCount = Number(visitCount) + 1;
//    localStorage.setItem("page_view", visitCount);
//    } else {
//        visitCount = 1;
//        localStorage.setItem("page_view", 1);
//    }
//counterContainer.innerHTML = visitCount;
//
//// Adding onClick event listener
//resetButton.addEventListener("click", () => {
//    visitCount = 1;
//    localStorage.setItem("page_view", 1);
//    counterContainer.innerHTML = visitCount;
//    });
expiration = new Date;
expiration.setMonth(expiration.getMonth()+6)
counter = eval(cookieVal("total_visited"))
counter++
document.cookie = "total_visited="+counter+";expires=" + expiration.toGMTString()
 
 
function cookieVal(cookieName) {
    thisCookie = document.cookie.split("; ")
    for (i=0; i<thisCookie.length; i++){
                if (cookieName == thisCookie[i].split("=")[0]){
            return thisCookie[i].split("=")[1]
        }
    }
    return 0;
}
 
document.getElementById('result').innerHTML = "<center><h3>You visited this page <label style='font-size:40px;' class='text-info'>"+counter+"</label> times.</h3></center>";

