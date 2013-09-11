#kopiert vom Skript vom 27.2.13
library("gplots")
library("bmd")
library("splines")


# mydata: data.frame with dose/response/experiment columns
# title: graphs main title
# xlab: label of the graphs' x axis
# outfilename: name of the PNG produced
# cooksfilename: ?
# run: ? does things if run>=3
processData <- function(mydata, title, xlab, outfilename, cooksfilename, run) {
   cleanupDrcData()
   graphics.off()
   avgmodel <- NULL
   islinear <- NULL
   linplotdata <- NULL
   plotdata <- NULL
   potplotdata <- NULL
   badexperiment <- NULL
   norm <- NULL
   ancht <- NULL

# Plot 1
   machPlot(mydata, plotKurven=NA, xlab=xlab, main=title, PNGFileName=outfilename, iBild=1, plotAP=ancht)

   mlist <- bestModel(mydata[,1:2],linreg=FALSE)
   mlinear <- bestModel(mydata[,1:2],linreg=FALSE)
   fctname <- mlist[1]
   fctnamelinear <- mlinear[1]

   if (is.null(mlist)) { # data sucks, no model was found, just plot points
        print("No matching function found!")
   } else { # model was found
      print(paste("Function found! Best function is:", fctnamelinear))
      islinear <- (length(grep(fctnamelinear, c("Lin"))) > 0) #Linearedaten(nach loglinearem suchen...)
      # islinear: NULL: no model was found / TRUE: model is liner / FALSE: model is not linear
      if (!(is.null(islinear)) && islinear) { # model is linear
         print("Lineares Modell gefunden")
         switch (fctnamelinear,
            "Lin" = {
               lin <- glm(mydata$response ~ mydata$dose)
            },
            #"Quad" = {
            #   quad <- lm(mydata$response ~ mydata$dose + I(mydata$dose^2))
            #   lines(mydata$dose, predict(quad))
            #},
            #"Cubic" = {
            #   cubic <- lm(mydata$response ~ mydata$dose + I(mydata$dose^2) + I(mydata$dose^3))
            #   lines(mydata$dose, predict(cubic))
            #},
         )
# Plot 2
         machPlot(mydata, plotKurven=lin, xlab=xlab,  main=title, PNGFileName=outfilename, islinear=TRUE,
                 fctname=fctnamelinear, BMCtable=NA, iBild=2, plotAP=ancht)
         return=(list(BMCtable=NULL, FctName=fctnamelinear))

      } else { # model is not linear
         fct <- eval(parse(text=paste(fctname)))
         modell <- mydrm(mydata, fct=fctname)
         EC50 <- ED(modell, 50, display=FALSE)
         BMC<-ED(modell,c(10,15),interval=c("delta"),level=0.90,type="relative",display=FALSE)
         BMCround<-round(BMC,6)
         bmctable <- matrix(BMCround[c(1:2,5:8)],ncol=3)
         colnames(bmctable) <- c("BMC","BMCL","BMCU")
         rownames(bmctable)<- c("BMR=0.10","BMR=0.15")
         bmctable1 <- as.table(bmctable)
# Plot 2
         machPlot(mydata, plotKurven=modell, xlab=xlab, main=title, islinear=FALSE,
                  PNGFileName=outfilename, fctname=fctname, BMCtable=bmctable1, iBild=2, plotAP=ancht)
         BMC<-NULL
         BMCround<-NULL
        #alle Daten nochmals normieren, damit die avgkurve durch 100 geht (nur fuer das Bild 4)
         parm<-constraints(modell, fctname) #switchcase normalization
         allnorm = mydata
         allnorm$response = mydata$response/(parm$norm/100)
         allmodell <- mydrm(allnorm, fct=fctname)
         BMC<-ED(modell,c(10,15),interval=c("delta"),level=0.90,type="relative",display=FALSE)
         BMCround<-round(BMC,6)
         bmctable <- matrix(BMCround[c(1:2,5:8)],ncol=3)
         colnames(bmctable) <- c("BMC","BMCL","BMCU")
         rownames(bmctable)<- c("BMR=0.10","BMR=0.15")
         bmctable <- as.table(bmctable)
# PLot 3
         machPlot(plotData=allnorm, plotKurven=allmodell, xlab=xlab, main=title, islinear=FALSE,
                  PNGFileName=outfilename, fctname=fctname, BMCtable=bmctable, iBild=3, plotAP=ancht)
         BMC<-NULL
         BMCround<-NULL
         bmctable<-NULL
         if (run>=3) {
            print("***************** 1. Normierung findet statt *****************")
            curveListe=list()
            for (i in unique(mydata$experiment)) {
               print(paste("Experiment:", i))
               expresp <- mydata$response[mydata$experiment==i]
               expdose <- mydata$dose[mydata$experiment==i]
               expdata <- cbind(as.data.frame(expdose), as.data.frame(expresp))
               colnames(expdata) = c("dose","response")
               try(curveListe[[i]] <- mydrm(expdata, fct=fctname))
               if (!is.null(curveListe[[i]])) {
                  print("expmodel gefunden")
                  parm <- constraints(curveListe[[i]], fctname) #switchcase normalization
                  norm <- data.frame(dose=expdose,
                     response=(expresp/(parm$norm/100)),
                     experiment=i,
                     stringsAsFactors=F)
                     potplotdata <- rbind(potplotdata,norm) #save values for the average later (potential plot data)
               } else {
                  print("no expmodel gefunden")
                  badexperiment<-rbind(badexperiment,data.frame(dose=expdose,response=expresp,experiment=i))
               }
            }
# Plot 4
            machPlot(plotData=mydata, plotKurven=curveListe, PNGFileName=outfilename, xlab=xlab,
                     main=title, fctname=fctname,  iBild=4, plotAP=ancht)
            #avgdata = potplotdata

            print("***************** 2. Ankerpunkte werden definiert *****************")
            if (min(potplotdata$response)<5){
               # Wenn die response kleiner als fünf für ankerpunkt merken
               ankerpunktsubset <- subset(potplotdata, potplotdata$response<5)
               ankerpunkt <- ankerpunktsubset[which.min(ankerpunktsubset$dose),]
               anchtdose<-ankerpunkt$dose
               anchtresponse<-ankerpunkt$response
               print("optimierter Ankerpunkt wird verwendet")
            } else {
               # Ankerpunkt toxisch Zeilen von Johanna hinzugefügt
               anchtdose<-EC50[1]*200
               anchtresponse<-0
               print("traditioneller Ankerpunkt wird verwendet [Marcels arbiträre EC50*80 Definition")
            }
            norm<-NULL
            schlechtekurven<-NULL
            gutekurven<-NULL
            badnorm<-NULL

            print("***************** 3. Ankerpunkte hinzufuegen wenn noetig *****************")
            for(i in unique(potplotdata$experiment)) { #adds Anchorpoints for Normalized response
               print(paste("Experiment", i, ":"))
               expresp <- potplotdata$response[potplotdata$experiment==i]
               expdose <- potplotdata$dose[potplotdata$experiment==i]
               expdata <- cbind(as.data.frame(expdose), as.data.frame(expresp))
               colnames(expdata) = c("dose","response")
               expmodel <- mydrm(expdata,fct=fctname)
               parm<-constraints(expmodel, fctname)#switchcase normalization
               #print(paste("Parameters",parm))
               # Ankerpunkt toxisch
               #ancht <- data.frame(dose=(EC50[1]*80), #chefl?sung
               print(paste("kleinste Response =", round(min(potplotdata$response[potplotdata$experiment==i]),digits=2)))
               #Schlechte Einzelkurve, braucht AP
               if ((!is.null(anchtdose)) && min(potplotdata$response[potplotdata$experiment==i])>5) {
                  #calculate only if toxic data missing and add anchorpoint
                  badcurves <- data.frame(dose=expdose,
                                    response=expresp,
                                    experiment=i,
                                    stringsAsFactors=F)
                  #ankerpunkt toxisch
                  #ancht <- data.frame(dose=(anchtdose),
                  ancht <- data.frame(dose=(EC50[1]*200),
                                 response=(anchtresponse),
                                 experiment=i,
                                 stringsAsFactors=F)
                  # ankerpunkt nicht toxisch
                  #anchnt <- data.frame(dose=(0),
                  #                      response=100,
                  #                       experiment=i,
                  #                       stringsAsFactors=F)
                  badnorm<-rbind(badnorm,ancht,badcurves)
                  print(paste("Ancht bei Dosis=", round(ancht$dose, digits=6), " und Response=",
                              round(ancht$response,digits=2), sep=""))
               }
               #Gute Einzelkurve, braucht kein AP
               if (min(potplotdata$response[potplotdata$experiment==i])<=5){#calculate only if toxic data NOT missing
                  goodcurves <- data.frame(dose=expdose,
                                    response=expresp, #gute Kurven müssen NICHT nochmal normalisiert werden
                                    experiment=i,
                                    stringsAsFactors=F)
                  gutekurven<-rbind(gutekurven,goodcurves)
                  #print("braucht kein Ankerpunkt")
               }
            } #Ende for unique potplotdata$experiment

            #########################schlechte Kurven nochmals normieren ###########################
            if (!is.null(badnorm)){
               for (i in unique(badnorm$experiment)){#Normalization of BAD DATA
                  badnormexpdata <- cbind(as.data.frame(badnorm$dose[badnorm$experiment==i]),
                                          as.data.frame(badnorm$response[badnorm$experiment==i]))
                  colnames(badnormexpdata) = c("dose","response")
                  expmodel <- mydrm(badnormexpdata,fct=fctname)
                  parm<-constraints(expmodel, fctname) #switchcase normalization
                  badcurves <- data.frame(dose=badnorm$dose[badnorm$experiment==i],
                     response=(badnorm$response[badnorm$experiment==i]/(parm$norm/100)),
                     experiment=i,
                     stringsAsFactors=F)
                  schlechtekurven <- rbind(schlechtekurven, badcurves)
                  print(paste("Experiment", i, "wurde nochmals normiert"))
               }
            }

            #####################gute und schlechte Kurven wieder verbinden #######################
            if(!is.null(ancht)){
               einzelkurven <- rbind(schlechtekurven,gutekurven)#mit ankerpunkten
               schlechtekurven <- subset(schlechtekurven, (schlechtekurven$dose!=ancht$dose)
                                       & (schlechtekurven$response!=ancht$response)) #haut die ankerpunkte wieder raus
               #norm<-rbind(schlechtekurven,gutekurven) #jetzt ohne ankerpunkte
               norm <- einzelkurven #haut ankerpunkte nicht wieder raus
            } else {
               einzelkurven <- gutekurven
               norm <- gutekurven
            }
# Plot 5
            machPlot(plotData=einzelkurven, plotKurven=NA, PNGFileName=outfilename, xlab=xlab,
                     main=title, fctname=fctname, iBild=5, plotAP=ancht)

            print("***************** 4. Plotten der normierten Einzelkurven (mit AP) *****************")
            curveListe=list()
            for(i in sort(unique(einzelkurven$experiment))) {
               print(paste("Experiment",i, ":"))
               expresp <- einzelkurven$response[einzelkurven$experiment==i]
               expdose <- einzelkurven$dose[einzelkurven$experiment==i]
               expnummer <-einzelkurven$experiment[einzelkurven$experiment==i]
               expdata <- cbind(as.data.frame(expdose), as.data.frame(expresp), as.data.frame(expnummer))
               colnames(expdata) = c("dose","response", "experiment")
               expmlist <- bestModel(expdata, linreg=FALSE)
               #parm<-constraints(avgnorm, fctname)#switchcase normalization
               #print(parm)
               try(curveListe[[i]] <- drm(expresp ~ expdose, fct=fct(fixed=parm$fixedP))) #constraint option
               #try(curveListe[[i]] <- drm(expresp ~ expdose, fct=fct())) #no constraint option
               #try(curveListe[[i]] <- mydrm(expdata, fct=fctname)) #non constraint option
               if(!is.null (curveListe[[i]])) {
                  print("Einzelkurve gefunden")
               } else {
                  print("keine Einzelkurve gefunden")
               }
            }
# Plot 6
            #JN: einzelkurven enthaltet glaube ich die ankerpunkte!!!!!!!
            machPlot(plotData=einzelkurven, plotKurven=curveListe, PNGFileName=outfilename, xlab=xlab,
                     main=title, fctname=fctname, iBild=6, plotAP=ancht)

            if (run>3){
            if (!is.null(norm)) {
               print("***************** 5. Averagekurve wird gefittet *****************")
               avgmodel <- NULL
               try(avgmodel <- mydrm(norm,fct=fctname)) #constraint option
               if(!is.null(avgmodel)) {
                  avgnorm <- data.frame(dose=norm$dose,
                      response=norm$response,#/(parm$norm/100),
                      experiment=norm$experiment )
                  avgmodel <- NULL
                  #parm<-constraints(avgnorm, fctname) #switchcase normalization
                  try(avgmodel <- mydrm(avgnorm, fct=fctname)) #constraint option
                  curveListe[[max(unique(einzelkurven$experiment))+1]]=avgmodel
                  print("BMC wird berechnet")
                  BMC <- ED(avgmodel,c(10,15),interval=c("delta"),level=0.90,type="relative",display=FALSE)
                  BMCround <- round(BMC,6)
                  bmctable2 <- matrix(BMCround[c(1:2,5:8)],ncol=3)
                  colnames(bmctable2) <- c("BMC","BMCL","BMCU")
                  rownames(bmctable2)<- c("BMR=0.10","BMR=0.15")
                  bmctable2 <- as.table(bmctable2)
                  #print(bmctable2)
                  #print("dawid")
                  #print(str(avgnorm))
                  #save(avgnorm, avgmodel, outfilename, xlab,  title, fctname ,bmctable2, ancht,file="dawid.rda")
# Plots 7,8,9,11
                  machPlot(plotData=avgnorm, plotKurven=avgmodel, PNGFileName=outfilename, xlab=xlab,
                           main=title, fctname=fctname ,BMCtable=bmctable2, iBild=7,plotAP=ancht)
                  machPlot(plotData=avgnorm, plotKurven=avgmodel, PNGFileName=outfilename, xlab=xlab,
                           main=title, fctname=fctname ,BMCtable=bmctable2, iBild=8,plotAP=ancht)
                  machPlot(plotData=avgnorm, plotKurven=curveListe, PNGFileName=outfilename, xlab=xlab,
                           main=title, fctname=fctname ,BMCtable=bmctable2, iBild=9,plotAP=ancht)
                  machPlot(plotData=avgnorm, plotKurven=curveListe, PNGFileName=outfilename, xlab=xlab,
                           main=title, fctname=fctname ,BMCtable=bmctable2, iBild=11,plotAP=ancht)

                  # png("test.png")
                  # y <- seq(from = 0, to = max(140,0), length.out=length(unique(avgnorm$dose)))
                  #  layout(matrix (c(1,1,2,2), 2, 2, byrow=TRUE),widths=c(1,1), heights=c(1, 0.3))
                  #  par(mar=c(4,5,7,15))
                  #  fakemodel<-try(fm<-drm(y~unique(avgnorm$dose),fct=LL.4()),silent=TRUE)
                  # plot(fakemodel,type="none",col="white", xlim=c(0, max(avgnorm$dose)),
                  #      broken=TRUE,cex.lab=1.2,cex.main=1.8,pch=19,cex=1.2)
                  # plot(avgmodel,type="bars",broken=TRUE,add=TRUE,xlim=c(0, max(avgnorm$dose)),
                  #      lwd=1.3,col="black",cex.lab=1.2,cex.main=2,cex=1.2)
                  # graphics.off()

                  return=(list(BMCtable1=bmctable1, BMCtable2=bmctable2, FctName=fctname))

               } #Ende if avgmodel gefunden
            } #Ende if norm ist nicht null
            } #Ende if run groesser 3
   } #Ende if run strict. groesser 3
   } #Ende if model is not linear
   } #Ende model was found
} #Ende processData

#------------------------------------------------------#
# This code was written by Sunniva Foerster            #
# Universitat Konstanz, Germany                        #
# Sunniva.Foerster@uni-konstanz.de                     #
#------------------------------------------------------#
