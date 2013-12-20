
bestModel <- function(bmdrcdata, linreg=FALSE) {
    # bmdrcdata: data.frame from original file, with at least dose and response columns
    modelList <- list(LL.4(), LL.5(), W1.4(), W2.4(), LL.3())
    modell <- NULL
    for(n in seq(length(modelList))) {
        curModelName <- modelList[[n]]$name
        trymodeltxt <- paste("mydrm(bmdrcdata, fct='", curModelName,"')", sep="")
        capture.output(modell <- try(eval(parse(text=trymodeltxt))), file=nulldev())
        if (!(class(modell)=="try-error")) { break(); }
    }
    if (class(modell)=="try-error") { # no model found
        mynames <- NULL
    } else {
        best <- mselect(modell, fctList=modelList)
        mynames <- rownames(best)
    }
    return(mynames)
}


nulldev <- function() {
    os <- Sys.info()['sysname']
    if (os=="Linux") {
        n <- "/dev/null"
    }
    else if (os=="Windows") {
        n <- "NUL"
    } else {
        n <- "/dev/null"
    }
    return(n)
}


mydrm <- function(mydrcdata, fct) {
    if(length(grep('globaldrcdata', ls(.GlobalEnv)))==0) {
        .GlobalEnv$globaldrcdata <- list()
    }
    l <- length(.GlobalEnv$globaldrcdata)
    .GlobalEnv$globaldrcdata[l+1] <- list(mydrcdata)
    l <- length(.GlobalEnv$globaldrcdata)
    epdrm <- paste("drm(.GlobalEnv$globaldrcdata[[",  l,
                   "]]$response ~ .GlobalEnv$globaldrcdata[[",  l,
                   "]]$dose, fct=",  fct,
                   "())",  sep='')
    drc <- eval(parse(text=epdrm))
    return(drc)
}


cleanupDrcData <- function() {
    if (exists("globaldrcdata", envir=globalenv())) {
        rm("globaldrcdata", envir=globalenv())
    }
}



#------------------------------------------------------#
# This code was written by Sunniva Foerster            #
# Universitat Konstanz, Germany                        #
# Sunniva.Foerster@uni-konstanz.de                     #
#------------------------------------------------------#
