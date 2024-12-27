Deletes files from your Rekordbox folder which are not in the library based on an
exported Rekordbox XML.

**Usage:**  
***clean_rb_python [-h] [-c] [-s] [--skip SKIP] [--include-streaming] [--details]
                       [--results-file] [--version]
                       rekordbox_xml***

**Positional arguments:**  
*rekordbox_xml*  
The file name of the XML file from Rekordbox

**Options:**  
  ***-h, --help***: show this help message and exit  
  ***-c, --clean***:          do the cleaning  
  ***-s, --simulate***:       simulate the cleaning to see what would be deleted (default
                       behaviour)  
  ***--skip SKIP***:          skip the cleaning for these strings in the paths, divided by ',' (applies to both the local files and the paths in the XML file)     
  ***--include-streaming***:  include stored streaming service file urls (they are skipped by adding 'tidal', 'soundcloud', 'beatport', 'itunes' to the skip list by default)  
  ***--details***:           show the detailed results (per file) on console  
  ***--results-file***:       write the deatiled results to a text file: either clean_results_<datetime>.txt or simulate_results_<datetime>.txt  
  ***--version***: show program's version number and exit