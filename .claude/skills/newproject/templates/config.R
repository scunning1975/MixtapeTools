# config.R — project paths
# Source at the top of every R script: source("[relative path to]/code/config.R")

root <- "{{PROJECT_ROOT}}"

data_raw    <- file.path(root, "data", "raw")
data_clean  <- file.path(root, "data", "clean")

output_figures <- file.path(root, "output", "figures")
output_tables  <- file.path(root, "output", "tables")
output_logs    <- file.path(root, "output", "logs")

code_download <- file.path(root, "code", "download")
code_data     <- file.path(root, "code", "data")
code_analysis <- file.path(root, "code", "analysis")
