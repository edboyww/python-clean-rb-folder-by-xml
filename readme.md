Deletes files from your Rekordbox folder which are not in the library based on an exported Rekordbox XML. *(Streaming URLs are not handled in the XML.)*

**Usage:**  
`clean_rb_python [-h] [-c] [-s] [--skip SKIP] [--include-streaming] [--details] [--results-file] [--version] rekordbox_xml`

**Positional arguments:**  
`rekordbox_xml` - The file name of the XML file from Rekordbox

**Options:**  
  `-h, --help` - show this help message and exit  
  `-c, --clean` - do the cleaning  
  `-s, --simulate` - simulate the cleaning to see what would be deleted (default behaviour)  
  `--skip SKIP` - skip the cleaning for these strings in the paths, divided by ',' (applies to both the local files and the paths in the XML file)
  `--details` - show the detailed results (per file) on console  
  `--details-file` - write the deatiled results to a text file: either `clean_details_<datetime>.txt` or `simulate_details_<datetime>.txt`  
  `--check-xml` - check if the XML has any URLs which does not exist in the filesystem
  `--version` - show program's version number and exit