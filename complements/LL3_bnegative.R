

llog <- function(x,b,d,e){
    d/(1+exp(b*(log(x)-log(e))))
}

plot(1:100, llog(1:100, 4,100, 10))


# "Bad" samples: Geldanamycin_k, saha_g
