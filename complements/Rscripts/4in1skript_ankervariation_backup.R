#!/usr/bin/Rscript

nulldev <- function() {
    os <- Sys.info()['sysname']
    if (os=="Windows") {
        n <- "NUL"
    } else {
        n <- "/dev/null"
    }
    return(n)
}

# Extracts parameter "d" (intercept) from different models for the normalization
normalization<-function(objdrc, fctname){
    parameter <- matrix(coef(objdrc))
    switch(fctname,
         "LL.3" = {
           norm<-parameter[2]
           fixedP=c(NA, NA, NA)
           KoefName=c("b","d", "e")
           AnzK=3
         },
         "W1.4" = {
           norm<-parameter[3]
           fixedP=c(NA, 0, NA, NA)
           KoefName=c("b", "c", "d", "e")
           AnzK=3
         },
         "W2.4" = {
           norm<-parameter[3]
           fixedP=c(NA, 0, NA, NA)
           KoefName=c("b", "c", "d", "e")
           AnzK=3
         },
         "LL.4" = {norm<-parameter[3]
                   fixedP=c(NA, 0, NA, NA)
                   KoefName=c("b", "c", "d", "e")
                   AnzK=3
         },
         "LL.5" = {norm<-parameter[3]
                   fixedP=c(NA, 0, NA, NA, NA)
                   KoefName=c("b", "c", "d", "e", "f")
                   AnzK=4
         },
    )
    return(list(norm=norm, fixedP=fixedP, KoefName=KoefName, AnzK=AnzK))
}

makepng<-function(...) {
    png(...)
    return(dev.cur())
}

mydrm <- function(mydrcdata, fct) {
    if(length(grep('globaldrcdata', ls(.GlobalEnv)))==0) {
        .GlobalEnv$globaldrcdata <- list()
    }
    l <- length(.GlobalEnv$globaldrcdata)
    .GlobalEnv$globaldrcdata[l+1] <- list(mydrcdata)
    l <- length(.GlobalEnv$globaldrcdata)
    epdrm <- paste("drm(.GlobalEnv$globaldrcdata[[", l, "]]$response ~ .GlobalEnv$globaldrcdata[[", l, "]]$dose, fct=", fct, "())", sep="")
    drc <- eval(parse(text=epdrm))
    return(drc)
}

cleanupDrcData <- function() {
    if (exists("globaldrcdata", envir=globalenv())) {
        rm("globaldrcdata", envir=globalenv())
    }
}

# Use drc.mselect to choose the best model
bestModel <- function(bmdrcdata, linreg) {
    modelList <- list(LL.3(), LL.4(),LL.5(),W1.4(), W2.4())
    modell <- NULL
    for(n in seq(length(modelList))) {
        curModelName <- modelList[[n]]$name
        trymodeltxt <- paste("mydrm(bmdrcdata, fct='", curModelName,"')", sep="")
        capture.output(modell <- try(eval(parse(text=trymodeltxt))), file=nulldev())
        if (!(class(modell)=="try-error")) {
            break();
        }
    }
    if (class(modell)=="try-error") { # no model found
        mynames <- NULL
    } else {
        best <- mselect(modell, fctList=modelList, linreg=linreg)
        mynames <- rownames(best)
    }
    return(mynames)
}

# Create the frame of the plot by plotting white curves from a fake LL4 model ...
plotAxisRange <- function(x, xlab, ylab, main) {
    y <- seq(from = 0, to = 140, length.out=length(x))
    fm <- NULL
    layout(matrix (c(1,1,2,2), 2, 2, byrow=TRUE),widths=c(1,1), heights=c(1, 0.3))
    par(mar=c(4,5,7,15))
    fakemodel<-try(fm<-drm(y~x,fct=LL.4()),silent=TRUE)
    plot(fakemodel,type="all",xlim=c(0, max(x*10000)), ylim=c(-10,140),broken=TRUE,lty="dashed",
         lwd=1.3,col="white",cex.lab=1.2,cex.main=2,pch=19,cex=1.2,ylab=ylab, xlab=xlab, main=main)
}


############
# Julien's #
############


# Fits the model *fctname* on *data*, normalizes and refits the norm data.
# Returns the model and the normalized data in a list.
modeling <- function(data,fctname,normalize=TRUE,fixed=''){
    fct = eval(parse(text=paste(fctname)))
    dose = data$dose; response = data$response
    modell = drm(response ~ dose, fct=fct())
    if (normalize==TRUE){
        parm = normalization(modell, fctname)
        dataN = data.frame(dose=dose,
                           response=response/(parm$norm/100),
                           experiment=data$experiment)
        dose = dataN$dose; response = dataN$response
        modellN = drm(response ~ dose, fct=fct())
        return(list(model=modellN, data=dataN))
    } else {
        return(list(model=modell, data=data))
    }
}


# Fit a first time to calculate the anchor
calculate_anchor <- function(mydata, fctname){
    M = modeling(mydata,fctname,TRUE)
    modell = M$model
    dataN = M$data
    anchtdose <- min(c(ED(modell,50,display=FALSE)[1]*100, max(mydata$dose)*100))  # anchor position
    cat("Anchor:",anchtdose,"\n")
    return(anchtdose)
}


# For each experiment, fit and normalize - NO anchor - then pool and fit the pooled data
fit_experiments_noanchor <- function(mydata, fctname, normalize=TRUE){
    experiments = unique(mydata$experiment)
    pooled <- NULL    # normalized experiments pooled
    modelsE <- NULL   # store individual models
    dataE <- NULL     # store individual normalized data
    experiments = unique(mydata$experiment)
    for(i in experiments){
        expdata = mydata[mydata$experiment==i,]
        expM = modeling(expdata, fctname, normalize=normalize)  # normalize only if run >=3 ..
        modellN = expM$model
        expdataN = expM$data
        pooled <- rbind(pooled,expdataN)  # Pool the normalized data
    }
    avgmodel = modeling(pooled, fctname, normalize=normalize)$model
    return(list(model=avgmodel,data=pooled))
}


# For each experiment, fit and normalize - WITH anchor - then pool and fit the pooled data
fit_experiments <- function(dataP, fctname, anchtdose){
    experiments = unique(dataP$experiment)
    ancht<-NULL           # point representing the anchor
    withanchor<-NULL      # exps with anchor added because of the 5%
    gutekurven<-NULL      # exps that did not need an anchor
    schlechtekurven<-NULL # with anchor, renormalized including the anchor
    einzelkurven<-NULL    # all normalized exps together, with their anchors if they needed one
    purgedeinzelkurven<-NULL # all normalized exps together, without the anchors even if they needed one

    # For each experiment, fit the model, then normalize
    # Add anchor if still necessary after normalization
    for (i in experiments) {
        expdata = dataP[dataP$experiment==i,]  # pooled exps without anchor
        expM = modeling(expdata, fctname, normalize=TRUE)  # normalize only if run >=3 ..
        expmodel = expM$model
        expdataN = expM$data
        # Missing toxic enough doses, add anchor
        if((!is.null(anchtdose)) && min(expdata$response)>5){
            # Anchorpoint at anchtdose
            ancht <- data.frame(dose=(anchtdose),
                response=(0),
                experiment=i,
                stringsAsFactors=F)
            withanchor <- rbind(withanchor, ancht,expdataN)
        }
        # Enough toxic data, anchor not needed
        if (min(expdata$response)<=5){
            gutekurven <- rbind(gutekurven, expdataN)
        }
    }
    # Fit experiments that needed an anchor, with their anchor added
    if(!is.null(withanchor)){
        for(i in unique(withanchor$experiment)){
            expdata = withanchor[withanchor$experiment==i,]
            expM = modeling(expdata, fctname, normalize=TRUE)  # normalize only if run >=3 ..
            expmodel = expM$model
            expdataN = expM$data
            schlechtekurven <- rbind(schlechtekurven, expdataN)
        }
    }
    # Put all exps back together, removing anchors now that they are normalized with it.
    if(!is.null(ancht)){
        einzelkurven <- rbind(schlechtekurven,gutekurven) # put them together, with the anchors
        schlechtekurven <- subset(schlechtekurven,
             schlechtekurven$dose!=ancht$dose&schlechtekurven$response!=ancht$response)
             # remove the anchor point from the ones that had it
        purgedeinzelkurven <- rbind(schlechtekurven,gutekurven) # put them together, without the anchor
    # No anchor added, all data is made of "good curves"
    } else {
        einzelkurven <- gutekurven
        purgedeinzelkurven <- gutekurven
    }
    # Fit the pooled normalized without anchor data, renormalize and plot
    # - was "purgedeinzelkurven" instead of "einzelkurven"
    if (!is.null(einzelkurven)) {
        if(run>=4) {
            M = modeling(einzelkurven, fctname, normalize=TRUE)
            avgmodel = M$model
            #print(avgmodel$coefficients)  # The final one!
        }
    }
    return(list(model=avgmodel, anchor=ancht,
                withanchor=einzelkurven, withoutanchor=purgedeinzelkurven))
}


# Scatter plot of data
plot_points <- function(mydata,xlab,outname){
    experiments = unique(mydata$experiment)
    ylab <- "Response (percent of control)"
    plotAxisRange(mydata$dose, xlab, ylab, outname)
    colList <- c("red","orange","blue","green","violet")
    for(i in experiments){
        expresp <- mydata$response[mydata$experiment==i]
        expdose <- mydata$dose[mydata$experiment==i]
        points(expresp ~ expdose, type="p", pch=19, col=colList[i], cex = 1.2)
    }
}


# Plot all separate experiment curves and the pooled one, including the possible anchors
plot_experiments <- function(einzelkurven,avgmodel,fctname,anchtdose,xlab,plotnr,plotname,outname){
    experiments = unique(einzelkurven$experiment)
    colList <- c("red","orange","blue","green","violet")
    plotnrs <- sprintf("%03d", plotnr)
    plotname <- sub(".png", paste("_", plotnrs, ".png", sep=""), plotname)
    ylab <- "Response (percent of control)"
    for(i in experiments) {
        expdata = einzelkurven[einzelkurven$experiment==i,]
        singlecurves = modeling(expdata, fctname)$model
        plot(singlecurves, type="all", broken=TRUE,add=TRUE,xlim=c(0, max(einzelkurven$dose)*100),
             lty="dashed", lwd=1.3, col=colList[i], cex.lab=1.2, cex.main=2, pch=19, cex=1.2,
             ylab=ylab, xlab=xlab, main=outname)
    }
    # Plot the whole thing (?)
    ylab <- "Response (percent of control)"
    plot(avgmodel,type="none",broken=TRUE,add=TRUE, xlim=c(0, max(einzelkurven$dose)),
         lwd=1.3,col="black",cex.lab=1.2,cex.main=2,pch=19,cex=1.2,ylab=ylab,xlab=xlab)
    if (!is.null(anchtdose)) {
        points(anchtdose,0,type="p",pch=17, col = "black", cex = 2)
    }
}


calculate_BMC <- function(avgmodel){
    BMRs = c(10,15)
    BMC <- ED(avgmodel,BMRs,interval=c("delta"),level=0.90,type="relative",display=FALSE)
    BMCdf <- data.frame(rbind(as.data.frame(BMRs)), BMC[,c("Estimate","Lower","Upper")])
    colnames(BMCdf) <- c("BMR", "BMC", "BMCL", "BMCU")
    rownames(BMCdf) <- NULL
    return(BMCdf)
}


# Adds the vertical lines to the plot
plot_bmc <- function(BMCdf){
    BMR = 10
    BMC10 = BMCdf[BMCdf$BMR==BMR,]
    EC10 = BMC10$BMC
    BMCL = BMC10$BMCL
    BMCU = BMC10$BMCU
    ECround <- round(EC10,6)
    ablineclip(h=1000,x1=0.00000001,x2=ECround,v=ECround,y1=-20,lty=1,col="black")
    ablineclip(h=1000,x1=0.00000001,x2=BMCL,v=BMCL,y1=-20,lty=3,col="blue")
    ablineclip(h=1000,x1=0.00000001,x2=BMCU,v=BMCU,y1=-20,lty=3,col="blue")
    legend("bottomleft",
        c("BMCL10","BMCL15","BMC10"),
        col=c("blue","blue","black"),
        lty=c(4,4,1),
        bty="n")
}


# Writes a log file with columns BMR,BMC,BMCL,BMCU,b,c,d,e,anchor,fitname
write_bmc <- function(BMCdf, avgmodel, fctname, anchtdose, outname, plotnrs){
    dateiname <- paste(outname,"_parameter.txt",sep="")
    nbmr = dim(BMCdf)[1]
    estimates = as.data.frame(avgmodel$coefficients)
    rownames(estimates) = normalization(avgmodel, fctname)[["KoefName"]]
    suppressWarnings(
    write.table(
        cbind(
            BMCdf,           # a mxn dataframe - m BMR values, 4 cols
            t(estimates),
            data.frame(anchtdose=anchtdose,fctname=fctname,plotnrs=plotnrs)
        ),
        file=dateiname,
        append=ifelse(plotnrs>0,TRUE,FALSE),
        row.names=FALSE, col.names=TRUE,
        sep="\t", quote=FALSE)
    )
}


# Set the legend of the BMC plot
set_legends <- function(run, mydata, fctname, kurvenbild){
    dev.set(kurvenbild) # makes "kurvenbild" the active device
    experiments = unique(mydata$experiment)
    par(mar=c(5.1, 10.1, 10.1, 10.2), xpd=TRUE)
    colList <- c("red","orange","blue","green","violet")
    pchList <- c(16,16,16,16,16,16,16)
    ltyList <- c(NA,NA,NA,NA,NA,NA,NA)
    expList <- c()
    for(i in experiments) {expList <- c(expList, paste("Experiment", i))}
    if (run==2){
        legend("topright",
            inset=c(-0.4,0),
            c(paste("model=",fctname)),
            text.col=c("black","white"),
            col=c("black","white"),
            pch=c(NA,NA),
            lty=c(1,1),
            lwd=2.0,
            seg.len=1.0,
            bty="n")
    } else if (run==3){
        dev.set(kurvenbild)
        legend("topright",
            inset=c(-0.4,0),
            c(expList),
            col=c(colList[1:length(expList)],"black","black"),
            pch=c(pchList[1:length(expList)],4,4),
            lty=c(ltyList[1:length(expList)],NA,NA),
            lwd=2.0,
            seg.len=1.0,
            bty="n")
    } else if(run>=5) {
        legend("topright",
            inset=c(-0.4,0),
            c(expList,paste("model=",fctname),"influential observations"),
            col=c(colList[1:length(expList)],"black","black","black"),
            pch=c(pchList[1:length(expList)],NA,4,4,4),
            lty=c(ltyList[1:length(expList)],1,NA,NA,NA),
            lwd=2.0,
            seg.len=1.0,
            bty="n")
    }
}


##################################################
#                    Main call                   #
##################################################


processData <- function(mydata, outname, xlab, plotname, run=4, plotnr=0, nsteps=0, figures=TRUE) {
    # plotname: name of the plot
    # outname: name of the output text file
    # run: decides which steps to follow
    # plotnr: simulation step

    cleanupDrcData()
    graphics.off()
    experiments = unique(mydata$experiment)

    # Choose the best model for the pooled data
    mlist <- bestModel(mydata[,1:2],linreg=FALSE)
    fctname <- mlist[1]
    cat("Run",run,"\n")
    cat("Fit chosen:",fctname,"\n")

    # Data sucks or run==1, just plot the points
    if (is.null(mlist) || run==1) {
        kurvenbild <- makepng(plotname, width = 600, height = 600)
        plot_points(mydata,xlab,outname)
        graphics.off()
        return(0)
    }

    # For each experiment, fit and normalize - no anchor - then pool and fit the pooled data
    normalize = ifelse(run>=3, TRUE, FALSE)
    ME = fit_experiments_noanchor(mydata,fctname,normalize=normalize)
    modelP = ME$model
    dataP = ME$data

    # Simulation stuff
    if (plotnr > 0){
        EC50 <- ED(modelP,50,display=FALSE)[1]   # simulation starting point : EC50
        interval <- lseq(from=(EC50*1),to=(EC50*400),length.out=nsteps)
        anchtdose = interval[plotnr]
        plotnrs <- sprintf("%03d", plotnr)
        cat("Step",plotnrs,"\n")
        plotname <- sub(".png", paste("_", plotnrs, ".png", sep=""), plotname)
    } else {
        anchtdose = NULL
        plotnrs = 0
    }

    ## Set plot options

    if (figures) {
        kurvenbild <- makepng(plotname, width = 600, height = 600)
        par(mar=c(5.1, 10.1, 10.1, 10.2), xpd=TRUE)
        ylab <- "Response (percent of control)"
        plotAxisRange(mydata$dose, xlab, ylab, outname)
    }

    if (run==2 && figures){
        plot_experiments(dataP,modelP,fctname,anchtdose,xlab,plotnr,plotname,outname)
    } else if (run>=3) {
        # Anchor calculation
        if (is.null(anchtdose)){  # Standard, as in the paper - not the simulation
            anchtdose = calculate_anchor(mydata, fctname)
        }
        # Fit the model, add anchors if necessary
        ME = fit_experiments(dataP, fctname, anchtdose)
        avgmodel = ME$model
        einzelkurven = ME$withanchor
        if (figures) {
            # Plot all separate experiment curves and the pooled one, including the possible anchors
            plot_experiments(einzelkurven,avgmodel,fctname,anchtdose,xlab,plotnr,plotname,outname)
        }
        # Calculate BMC and add to the plot
        if (run>=4 && !is.null(avgmodel)) {
            BMCdf = calculate_BMC(avgmodel)
            if (figures) {
                # Add the vertical lines to the plot
                plot_bmc(BMCdf)
                # Add the table at the bottom with the BMC values
                bmctable <- as.table(as.matrix(BMCdf))
                textplot(bmctable, cex=1.1, show.rownames = TRUE, show.colnames = TRUE,mar=c(0, 0, 0, 15))
                legend("bottomleft",
                    c("BMCL10","BMCL15","BMC10"),
                    col=c("blue","blue","black"),
                    lty=c(4,4,1),
                    bty="n")
            }
            # Write a log file with columns BMR,BMC,BMCL,BMCU,b,c,d,e,anchor,fitname
            write_bmc(BMCdf,avgmodel,fctname,anchtdose,outname,plotnrs)
        }
    }

    if (figures) {
        set_legends(run,mydata,fctname,kurvenbild)
        graphics.off()
    }
}


