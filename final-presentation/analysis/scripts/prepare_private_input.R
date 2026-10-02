# One-time provenance helper. The package's run.sh uses the resulting compact CSV.
# Invoke from the package root, passing the frozen audit directory as argument.
library(data.table)
args <- commandArgs(trailingOnly=TRUE)
stopifnot(length(args)==1L)
frozen <- args[1]
manifest <- fread(file.path(frozen,'data/processed/rq_analysis_main_manifest.csv'),
                  colClasses=c(id='character',host_id='character'))
raw <- as.data.table(readRDS(file.path(frozen,'data/processed/listings_clean.rds')))
# Use the exact identifier-normalisation function in the audited original script.
original <- readLines('reference/14_simple_logistic_original.R')
start <- grep('^canonical_id <- function',original)
end <- grep('^# Probability',original)-1L
eval(parse(text=original[start:end]))
raw[,id:=vapply(id,canonical_id,character(1))]
input <- merge(manifest,raw[,.(id,price_num,minimum_nights,n_amenities)],
               by='id',all.x=TRUE,sort=FALSE)
stopifnot(nrow(input)==3873L,!anyDuplicated(input$id),!anyNA(input$price_num),
          !anyNA(input$n_amenities),all(input$host_role=='analysis'))
fwrite(input,'private-inputs/analysis_input.csv')
cat('Prepared',nrow(input),'rows,',uniqueN(input$host_id),'hosts.\n')
