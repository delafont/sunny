
# Called by processData.R
# Unique plotting function

machPlot <- function(plotData=NA, plotKurven=NA, plotAP=NULL, islinear=FALSE, xlab=NA, yLim=NA,
                     main=NA, PNGFileName=NA, fctname=NA, BMCtable=NA, iBild) {
if(!(is.na(PNGFileName))) {
    colList <- c("red","orange","blue","green","violet")
    pchList <- c(16,16,16,16,16,16,16)
    ltyList <- c(NA,NA,NA,NA,NA,NA,NA)
    expList <- NULL
    for(i in sort(unique(plotData$experiment))) {
        expList <- c(expList, paste("Experiment", i))
    }

    if ((iBild<=2) | (iBild==4)) {
        ylab="Response (percent of control)"
    } else {
        ylab="Normalized response"
    }

    FileName = sub(".png",paste("_", iBild, ".png", sep=""), PNGFileName)
    png(FileName, width=600, height=600)
    if (is.na(yLim)) {
        yLim=c(-10,140)
    }

    #plotAxisRange
    y <- seq(from = 0, to = max(140,yLim), length.out=length(unique(plotData$dose)))
    layout(matrix (c(1,1,2,2), 2, 2, byrow=TRUE),widths=c(1,1), heights=c(1, 0.3))
    par(mar=c(4,5,7,15))
    fakemodel <- try(fm<-drm(y~unique(plotData$dose),fct=LL.4()),silent=TRUE)
    plot(fakemodel,type="none",col="white", xlim=c(0, max(plotData$dose)), ylim=yLim, broken=TRUE,
         cex.lab=1.2,cex.main=1.8,pch=19,cex=1.2,ylab=ylab, xlab=xlab, main=main)


    if ((iBild==1) | (iBild==5)){
        for(i in sort(unique(plotData$experiment))) {
            points(plotData$response[plotData$experiment==i] ~ plotData$dose[plotData$experiment==i],
                   type="p",pch=19, col=colList[i], cex = 1.2)
        }
        if (!is.null(plotAP)) {
            points(plotAP$response ~ plotAP$dose, type="p",pch=19, col="black", cex = 1.2)
        }
        par(mar=c(5.1, 10.1, 10.1, 10.2), xpd=TRUE)
        legend("topright",
               inset=c(-0.4,0),
               c(expList),
               col=c(colList[1:length(expList)]),
               pch=c(pchList[1:length(expList)]),
               lty=c(ltyList[1:length(expList)]),
               lwd=2.0,
               seg.len=1.0,
               bty="n")
        dev.off()
    }


    if ((iBild==4) | (iBild==6)) {
        for(i in sort(unique(plotData$experiment))) {
            points(plotData$response[plotData$experiment==i] ~ plotData$dose[plotData$experiment==i],
                   type="p",pch=19, col=colList[i], cex = 1.2)
            if(!is.null (plotKurven[[i]])) {
                plot(plotKurven[[i]], type="none", broken=TRUE,add=TRUE,xlim=c(0, max(plotData$dose)),
                     lty="dashed", lwd=1.3, col=colList[i], cex.lab=1.2, cex.main=2, pch=19, cex=1.2,
                     ylab=ylab, xlab=xlab, main=main)
            }
        }
        if (!is.null(plotAP)) {
            points(plotAP$response ~ plotAP$dose, type="p",pch=19, col="black", cex = 1.2)
        }
        par(mar=c(5.1, 10.1, 10.1, 10.2), xpd=TRUE)
        legend("topright",
               inset=c(-0.4,0),
               c(expList,paste("model=",fctname)),
               col=c(colList[1:length(expList)],"black","black"),
               pch=c(pchList[1:length(expList)],NA,4,4),
               lty=c(ltyList[1:length(expList)],1,NA,NA),
               lwd=2.0,
               seg.len=1.0,
               bty="n")
        dev.off()
    }


    if ((iBild==2) | (iBild==3) | (iBild==7)) {
        for(i in sort(unique(plotData$experiment))) {
            points(plotData$response[plotData$experiment==i] ~ plotData$dose[plotData$experiment==i],
                   type="p",pch=19, col=colList[i], cex = 1.2)
        }
        if (islinear==FALSE) {
            plot(plotKurven,type="none",broken=TRUE,add=TRUE, xlim=c(0, max(plotData$dose)),
                 lwd=1.3,col="black",cex.lab=1.2,cex.main=2,pch=19,cex=1.2,ylab=ylab,xlab=xlab)
        } else {
            abline(plotKurven)
        }
        par(mar=c(5.1, 10.1, 10.1, 10.2), xpd=TRUE)
        legend("topright",
               inset=c(-0.4,0),
               c(expList,paste("model=",fctname)),
               col=c(colList[1:length(expList)],"black","black"),
               pch=c(pchList[1:length(expList)],NA,4,4),
               lty=c(ltyList[1:length(expList)],1,NA,NA),
               lwd=2.0,
               seg.len=1.0,
               bty="n")
    }


    if ((iBild==8)) {
        plot(plotKurven, type="bars", broken=TRUE,add=TRUE,xlim=c(0, max(plotData$dose)),
             lty=1, lwd=1.3, col="black", cex.lab=1.2, cex.main=2, pch=19, cex=1.2, ylab=ylab, xlab=xlab, main=main)
        par(mar=c(5.1, 10.1, 10.1, 10.2), xpd=TRUE)
        legend("topright",
               inset=c(-0.4,0),
               c(paste("model=",fctname)),
               col=c("black","black"),
               pch=c(NA,4,4),
               lty=c(1,NA,NA),
               lwd=2.0,
               seg.len=1.0,
               bty="n")
    }


    #Bild9: für Simulationsdaten zeichnet Singlecurves, EC10 aber nicht das Interval
    #Bild10: für Simulationsdaten, zeichnet Avgkurge und EC10 (also "traditionell")
    if (iBild>8) {
        for(i in sort(unique(plotData$experiment))) {
            points(plotData$response[plotData$experiment==i] ~ plotData$dose[plotData$experiment==i],
                   type="p",pch=19, col=colList[i], cex = 1.2)
            if ((iBild==9) | (iBild==11)){
                if((!is.null (plotKurven[[i]]))) {
                        plot(plotKurven[[i]], type="none", broken=TRUE,add=TRUE,xlim=c(0, max(plotData$dose)),
                             lty="dashed", lwd=1.3, col=colList[i], cex.lab=1.2, cex.main=1.5, pch=19, cex=1.2,
                             ylab=ylab, xlab=xlab, main=main)
                    }
            }
        }
        if (iBild==10) {
            plot(plotKurven,type="none",broken=TRUE,add=TRUE, xlim=c(0, max(plotData$dose)),lwd=1.3,col="black",
                 cex.lab=1.2,cex.main=1.5,pch=19,cex=1.2,ylab=ylab,xlab=xlab)
        }
        if (iBild==11) {
            plot(plotKurven[[i+1]],type="none",broken=TRUE,add=TRUE, xlim=c(0, max(plotData$dose)),
                 lwd=1.3,col="black",cex.lab=1.2,cex.main=1.5,pch=19,cex=1.2,ylab=ylab,xlab=xlab)
            ablineclip(h=1000,x1=0.00000001,x2=BMCtable[1,2],v=BMCtable[1,2],y1=min(yLim)-5,lty=4,col="blue")
            ablineclip(h=1000,x1=0.00000001,x2=BMCtable[2,2],v=BMCtable[2,2],y1=min(yLim)-5,lty=5,col="blue")
        }
        ablineclip(h=1000,x1=0.00000001,x2=BMCtable[1,1],v=BMCtable[1,1],y1=min(yLim)-5,lty=1,col="black")
        textplot(BMCtable, cex=1.4, show.rownames = TRUE, show.colnames = TRUE,mar=c(0, 0, 0, 15))
    }


    if ((iBild!=1) & (iBild!=4) & (iBild!=5) & (iBild!=6) & (iBild<9) & (islinear==FALSE)) {
        ablineclip(h=1000,x1=0.00000001,x2=BMCtable[1,1],v=BMCtable[1,1],y1=min(yLim)-5,lty=1,col="black")
        ablineclip(h=1000,x1=0.00000001,x2=BMCtable[1,2],v=BMCtable[1,2],y1=min(yLim)-5,lty=4,col="blue")
        ablineclip(h=1000,x1=0.00000001,x2=BMCtable[2,2],v=BMCtable[2,2],y1=min(yLim)-5,lty=5,col="blue")
        par(mar=c(5.1, 10.1, 10.1, 10.2), xpd=TRUE)
        legend("bottomleft",
                     c("BMCL10","BMCL15","BMC10"),
                     col=c("blue","blue","black"),
                     lty=c(4,5,1),
                     bty="n")
        par(mar=c(5.1, 10.1, 10.1, 10.2), xpd=TRUE)
        par(mar=c(0,0,6,0))
        par(mar=c(10,14,100,4))
        par(mar=c(5.1, 10.1, 10.1, 10.2), xpd=TRUE)
        textplot(BMCtable, cex=1.4, show.rownames = TRUE, show.colnames = TRUE,mar=c(0, 0, 0, 15))
        dev.off()
    }
}}



#------------------------------------------------------#
# This code was written by Sunniva Foerster            #
# Universitat Konstanz, Germany                        #
# Sunniva.Foerster@uni-konstanz.de                     #
#------------------------------------------------------#


