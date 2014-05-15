#!/usr/bin/Rscript
library("gplots")
library("bmd")
library("splines")
library("plyr")
library("emdbook")

Sys.setlocale(locale="C") # Fixes "input string X is invalid in this locale"

outdir <- "testoutput"
sourcefilepattern<-".txt$"
testfolders <- c("testdata")


test <- function(){
    source("4in1skript_ankervariation_backup.R")
    for (testfolder in testfolders) {
        files <- list.files(path=testfolder, pattern = sourcefilepattern, all.files = FALSE, recursive = FALSE,
                          ignore.case = FALSE, include.dirs = FALSE)
        #print(files)
        #for (thisfile in files){
        thisfile = "Geldanamycin_k.txt"
        #thisfile = "BIBF_k.txt"
            nr <- as.integer(sub(unlist(strsplit(thisfile, "_"))[5], pattern=".txt", replacement=""))
            myData <- read.table(paste(testfolder,"/",thisfile,sep=""),header=TRUE)
            myData <- myData[, c("dose","response","experiment")]
            doseunit <- "Concentration"
            od <- paste(outdir, sep="/")
            dir.create(od, recursive=TRUE, showWarnings=FALSE)
            plotname <- paste(od, sub(".txt",".png", thisfile), sep="/") # for the plots
            outname <- sub(".txt","",thisfile) # for the tables
            outname <- sub("_", " ", outname)
            outname <- paste(od,"/",outname, sep="")
            doseunit<-paste("Concentration [AU]",sep="")

            simulation = TRUE
            nsteps = 100
            figures = FALSE
            run = 4

            # Simulation
            if (simulation) {
                for (plotnr in 1:nsteps) {
                    try(processData(myData,outname,doseunit,plotname,run=4,plotnr,nsteps,figures=figures))
                }
            } else {
                try(processData(myData,outname,doseunit,plotname,run,plotnr=0,figures=figures))
            }
    }
}


