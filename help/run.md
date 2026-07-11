===================================================================
 HELP: --train | --prod
===================================================================
Usage:
  ./run.sh --train [file=...] [fast=...]
  ./run.sh --prod

Arguments:
  file  : Filepath of the input data. (Default: "data/historic.csv")
  fast  : Execution mode. If set to 'fast=--fast', no delay is added
          between ticks. Otherwise, a 100ms delay is applied.

Warning:
  The '--prod' mode uses stdin to stream real-time data, but this 
  implementation is currently WORK IN PROGRESS. 
  Please use ONLY '--train' mode for the moment.
===================================================================